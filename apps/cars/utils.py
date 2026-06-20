import io
import os

import pillow_heif
from django.core.files.base import ContentFile
from PIL import Image

pillow_heif.register_heif_opener()

HEIC_EXTENSIONS = (".heic", ".heif")


def to_browser_safe_image(uploaded_file):
    """Convert HEIC/HEIF files to JPEG — browsers can't render HEIC directly."""
    name = getattr(uploaded_file, "name", "") or ""
    if not name.lower().endswith(HEIC_EXTENSIONS):
        return uploaded_file

    uploaded_file.seek(0)
    image = Image.open(uploaded_file).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    base_name = os.path.splitext(os.path.basename(name))[0] + ".jpg"
    return ContentFile(buffer.read(), name=base_name)
