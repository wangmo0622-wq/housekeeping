import base64
import os
import random
import string
from io import BytesIO

from django.core.cache import cache
from PIL import Image, ImageDraw, ImageFont


def _random_code(length=4):
    return "".join(random.choice(string.digits) for _ in range(length))


def create_captcha(captcha_id=None):
    if not captcha_id:
        captcha_id = base64.urlsafe_b64encode(os.urandom(9)).decode("ascii").rstrip("=")

    code = _random_code(4)
    cache.set(f"admin_captcha:{captcha_id}", code, timeout=300)

    image = Image.new("RGB", (120, 40), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("Arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 8), code, fill=(33, 33, 33), font=font)

    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return captcha_id, buf


def verify_captcha(captcha_id, captcha_code):
    cached = cache.get(f"admin_captcha:{captcha_id}")
    if not cached:
        return False, "验证码已过期"
    if str(cached).lower() != str(captcha_code or "").strip().lower():
        return False, "验证码错误"
    cache.delete(f"admin_captcha:{captcha_id}")
    return True, ""
