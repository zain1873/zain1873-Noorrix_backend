"""Copy MEDIA_ROOT to the R2 bucket, preserving relative paths.

This runs *before* USE_R2 is switched on, so it talks to R2 through its own
boto3 client rather than Django's default storage. Nothing under MEDIA_ROOT is
read-modified or deleted -- the volume is only ever read from.

Keys match what the database already stores: a CarImage whose ``image.name``
is ``cars/photo.jpg`` becomes the R2 object ``cars/photo.jpg``, so every
existing row resolves once the flag flips. No data migration needed.
"""

import mimetypes
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from decouple import config as env
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def build_client():
    missing = [
        name
        for name in ('R2_BUCKET_NAME', 'R2_ENDPOINT_URL', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY')
        if not env(name, default='')
    ]
    if missing:
        raise CommandError('Missing R2 settings: ' + ', '.join(missing))

    client = boto3.client(
        's3',
        endpoint_url=env('R2_ENDPOINT_URL'),
        aws_access_key_id=env('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=env('R2_SECRET_ACCESS_KEY'),
        region_name='auto',
        config=Config(signature_version='s3v4'),
    )
    return client, env('R2_BUCKET_NAME')


def remote_sizes(client, bucket):
    """Every key already in the bucket, mapped to its size."""
    sizes = {}
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get('Contents', []):
            sizes[obj['Key']] = obj['Size']
    return sizes


class Command(BaseCommand):
    help = 'Copy files under MEDIA_ROOT to the R2 bucket. Never deletes anything.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List what would be uploaded without writing to R2.',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Only compare local and remote; upload nothing.',
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.is_dir():
            raise CommandError(f'MEDIA_ROOT does not exist: {media_root}')

        local = {
            path.relative_to(media_root).as_posix(): path
            for path in sorted(media_root.rglob('*'))
            if path.is_file()
        }
        if not local:
            self.stdout.write(self.style.WARNING(f'No files under {media_root}.'))
            return

        client, bucket = build_client()
        remote = remote_sizes(client, bucket)

        self.stdout.write(f'MEDIA_ROOT : {media_root}')
        self.stdout.write(f'Bucket     : {bucket}')
        self.stdout.write(f'Local      : {len(local)} file(s)')
        self.stdout.write(f'Remote     : {len(remote)} object(s)')

        pending = [
            key for key, path in local.items()
            if remote.get(key) != path.stat().st_size
        ]

        if options['verify']:
            missing = [key for key in local if key not in remote]
            mismatched = [key for key in pending if key in remote]
            extra = [key for key in remote if key not in local]
            for key in missing:
                self.stdout.write(self.style.ERROR(f'  missing on R2 : {key}'))
            for key in mismatched:
                self.stdout.write(self.style.ERROR(f'  size differs  : {key}'))
            for key in extra:
                self.stdout.write(f'  only on R2    : {key}')
            if missing or mismatched:
                raise CommandError(f'{len(missing) + len(mismatched)} file(s) not in sync.')
            self.stdout.write(self.style.SUCCESS('All local files present on R2 with matching sizes.'))
            return

        if not pending:
            self.stdout.write(self.style.SUCCESS('Already in sync -- nothing to upload.'))
            return

        self.stdout.write(f'To upload  : {len(pending)} file(s)')

        if options['dry_run']:
            for key in pending:
                self.stdout.write(f'  would upload {key} ({local[key].stat().st_size} bytes)')
            self.stdout.write(self.style.WARNING('Dry run -- nothing was written.'))
            return

        uploaded = 0
        failed = []
        for key in pending:
            content_type = mimetypes.guess_type(key)[0] or 'application/octet-stream'
            try:
                client.upload_file(
                    str(local[key]),
                    bucket,
                    key,
                    ExtraArgs={'ContentType': content_type},
                )
            except ClientError as exc:
                failed.append(key)
                self.stdout.write(self.style.ERROR(f'  FAILED {key}: {exc.response["Error"]["Code"]}'))
                continue
            uploaded += 1
            self.stdout.write(f'  uploaded {key}')

        self.stdout.write(self.style.SUCCESS(f'Uploaded {uploaded} file(s).'))
        if failed:
            raise CommandError(f'{len(failed)} file(s) failed. Re-run to retry just those.')
