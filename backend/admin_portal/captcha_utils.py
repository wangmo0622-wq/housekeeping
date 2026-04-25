import base64
import os
import random
import string
from io import BytesIO

from django.core.cache import cache
from PIL import Image, ImageDraw


CAPTCHA_WIDTH = 140
CAPTCHA_HEIGHT = 52


def _random_code(length=4):
    return "".join(random.choice(string.digits) for _ in range(length))


def _draw_segment_digit(draw, digit, x, y, width=28, height=42, thickness=6, color=(33, 33, 33)):
    # 七段数码管：不依赖系统字体，容器环境也能稳定显示大号数字。
    segments_map = {
        "0": ("a", "b", "c", "d", "e", "f"),
        "1": ("b", "c"),
        "2": ("a", "b", "g", "e", "d"),
        "3": ("a", "b", "g", "c", "d"),
        "4": ("f", "g", "b", "c"),
        "5": ("a", "f", "g", "c", "d"),
        "6": ("a", "f", "g", "e", "c", "d"),
        "7": ("a", "b", "c"),
        "8": ("a", "b", "c", "d", "e", "f", "g"),
        "9": ("a", "b", "c", "d", "f", "g"),
    }
    if digit not in segments_map:
        return

    top = y
    mid = y + (height // 2) - (thickness // 2)
    bottom = y + height - thickness
    left = x
    right = x + width - thickness
    upper = y + thickness
    lower = y + (height // 2)
    v_height = (height // 2) - thickness
    h_width = width - 2 * thickness

    segments = {
        "a": (left + thickness, top, left + thickness + h_width, top + thickness),
        "b": (right, upper, right + thickness, upper + v_height),
        "c": (right, lower, right + thickness, lower + v_height),
        "d": (left + thickness, bottom, left + thickness + h_width, bottom + thickness),
        "e": (left, lower, left + thickness, lower + v_height),
        "f": (left, upper, left + thickness, upper + v_height),
        "g": (left + thickness, mid, left + thickness + h_width, mid + thickness),
    }

    radius = 2
    for seg in segments_map[digit]:
        draw.rounded_rectangle(segments[seg], radius=radius, fill=color)


def _normalize_captcha_input(s):
    """统一验证码输入：去首尾空白、忽略中间空格、全角数字转半角。"""
    if s is None:
        return ""
    out = []
    for ch in str(s).strip():
        if ch.isspace():
            continue
        o = ord(ch)
        if 0xFF10 <= o <= 0xFF19:
            out.append(chr(o - 0xFF10 + ord("0")))
        elif ch.isdigit():
            out.append(ch)
    return "".join(out)


def create_captcha(captcha_id=None):
    if not captcha_id:
        captcha_id = base64.urlsafe_b64encode(os.urandom(9)).decode("ascii").rstrip("=")

    code = _random_code(4)
    cache.set(f"admin_captcha:{captcha_id}", code, timeout=300)

    image = Image.new("RGB", (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    digit_w = 28
    digit_h = 42
    gap = 4
    total_w = len(code) * digit_w + (len(code) - 1) * gap
    start_x = (CAPTCHA_WIDTH - total_w) // 2
    start_y = (CAPTCHA_HEIGHT - digit_h) // 2

    for i, ch in enumerate(code):
        jitter_y = random.randint(-1, 1)
        x = start_x + i * (digit_w + gap)
        _draw_segment_digit(draw, ch, x, start_y + jitter_y, width=digit_w, height=digit_h, thickness=6)

    buf = BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return captcha_id, buf


def verify_captcha(captcha_id, captcha_code):
    # captcha_id 为空常见于前端尚未拉取完验证码就提交
    if not captcha_id or not str(captcha_id).strip():
        return False, "请等待验证码加载完成后再登录"
    # 验证码存在 default 缓存（生产须 Redis 等多进程共享后端；LocMem + 多 Gunicorn worker 会读不到彼此写入的键）
    cached = cache.get(f"admin_captcha:{captcha_id}")
    if not cached:
        return False, "验证码已过期，请刷新验证码"
    entered = _normalize_captcha_input(captcha_code)
    if str(cached) != entered:
        return False, "验证码错误"
    cache.delete(f"admin_captcha:{captcha_id}")
    return True, ""
