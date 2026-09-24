"""Background images the admin uploads, stored in DATA_DIR/uploads.

Every upload is decoded and written again as a fresh JPEG. That drops EXIF,
including GPS position, and means only real pixel data ever reaches the disk,
whatever the uploaded file claimed to be.
"""

import io
import secrets
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

UPLOADS_NAME = "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_EDGE = 2560
THUMB_EDGE = 480
# Guards against decompression bombs: a tiny file that expands to gigapixels.
Image.MAX_IMAGE_PIXELS = 60_000_000
# iPhone photos arrive as HEIC, which Pillow cannot read on its own.
register_heif_opener()


class UploadError(Exception):
    pass


def uploads_dir(data_dir: Path) -> Path:
    return data_dir / UPLOADS_NAME


def list_uploads(data_dir: Path) -> list[str]:
    folder = uploads_dir(data_dir)
    if not folder.is_dir():
        return []
    return sorted(p.stem for p in folder.glob("*.jpg") if not p.stem.endswith(".thumb"))


def save_upload(data_dir: Path, payload: bytes) -> str:
    if len(payload) > MAX_UPLOAD_BYTES:
        raise UploadError("upload_too_large")
    image = decode_image(payload)
    name = secrets.token_hex(8)
    folder = uploads_dir(data_dir)
    folder.mkdir(exist_ok=True)
    write_jpeg(image, folder / f"{name}.jpg", MAX_EDGE, 82)
    write_jpeg(image, folder / f"{name}.thumb.jpg", THUMB_EDGE, 72)
    return name


def decode_image(payload: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(payload))
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise UploadError("upload_not_an_image") from error


def write_jpeg(image: Image.Image, target: Path, edge: int, quality: int) -> None:
    copy = image.copy()
    copy.thumbnail((edge, edge))
    copy.save(target, "JPEG", quality=quality, progressive=True, optimize=True)


def resolve_upload(data_dir: Path, name: str, thumb: bool = False) -> Path | None:
    """Returns the stored file itself, so a request can only reach names that list_uploads knows."""
    match = next((stem for stem in list_uploads(data_dir) if stem == name), None)
    if match is None:
        return None
    suffix = ".thumb.jpg" if thumb else ".jpg"
    candidates = uploads_dir(data_dir).glob(f"*{suffix}")
    return next((p for p in candidates if p.name == match + suffix), None)


def delete_upload(data_dir: Path, name: str) -> bool:
    main = resolve_upload(data_dir, name)
    if main is None:
        return False
    thumb = resolve_upload(data_dir, name, thumb=True)
    main.unlink()
    if thumb is not None:
        thumb.unlink()
    return True
