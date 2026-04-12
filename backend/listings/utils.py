import qrcode
from io import BytesIO
import base64


def generate_qr_code(data: str) -> str:
    """
    生成二维码并返回 base64 编码的 data URL
    
    Args:
        data: 要编码到二维码中的数据
        
    Returns:
        str: 包含二维码的 base64 编码 data URL
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 将二维码图片转换为 base64 编码
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{qr_base64}"
