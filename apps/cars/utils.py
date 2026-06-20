import io
import os

import pillow_heif
from django.core.files.base import ContentFile
from PIL import Image

pillow_heif.register_heif_opener()

HEIC_EXTENSIONS = (".heic", ".heif")
MAX_DIMENSION = 1920
JPEG_QUALITY = 85


def to_browser_safe_image(uploaded_file):
    """Convert HEIC/HEIF to JPEG and downscale oversized photos.

    Browsers can't render HEIC directly, and full-resolution phone photos
    (often 4000px+, 1-3MB each) make a 70+ image gallery very slow to load.
    Leaves already-small, already-supported images untouched.
    """
    name = getattr(uploaded_file, "name", "") or ""
    is_heic = name.lower().endswith(HEIC_EXTENSIONS)

    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    too_big = image.width > MAX_DIMENSION or image.height > MAX_DIMENSION

    if not is_heic and not too_big:
        uploaded_file.seek(0)
        return uploaded_file

    image = image.convert("RGB")
    if too_big:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)

    base_name = os.path.splitext(os.path.basename(name))[0] + ".jpg"
    return ContentFile(buffer.read(), name=base_name)
