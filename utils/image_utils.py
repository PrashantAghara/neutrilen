import io
import base64
import hashlib
from PIL import Image


def load_image_b64(path: str, max_px: int = 1024) -> str:
    """
    Open an image from file path, resize so longest side <= max_px,
    return base64-encoded JPEG string.
    Used in notebook testing.
    """
    img = Image.open(path).convert("RGB")
    return _encode_image(img, max_px)


def pil_to_b64(img: Image.Image, max_px: int = 1024) -> str:
    """
    Convert a PIL Image object directly to base64 JPEG string.
    Used in Streamlit pages with st.camera_input() and st.file_uploader().
    """
    return _encode_image(img, max_px)


def bytes_to_b64(image_bytes: bytes, max_px: int = 1024) -> str:
    """
    Convert raw image bytes to base64 JPEG string.
    Used when reading uploaded files from Streamlit.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return _encode_image(img, max_px)


def md5_hash(image_bytes: bytes) -> str:
    """
    Compute MD5 hex digest of raw image bytes.
    Used for image deduplication before calling Groq.
    """
    return hashlib.md5(image_bytes).hexdigest()


def _encode_image(img: Image.Image, max_px: int = 1024) -> str:
    """
    Internal helper — resize and base64 encode a PIL image.
    """
    w, h = img.size
    if max(w, h) > max_px:
        scale = max_px / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
