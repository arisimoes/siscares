import json
import qrcode
import io
import base64
from typing import Dict, Any
from app.core.crypto import encrypt_value, decrypt_value


def build_student_qr_payload(student) -> Dict[str, Any]:
    return {
        "sid": student.id,
        "name": student.full_name,
        "school": student.school_id,
        "class": student.class_id,
    }


def generate_encrypted_qr_payload(student) -> str:
    payload = json.dumps(build_student_qr_payload(student), separators=(",", ":"), ensure_ascii=False)
    return encrypt_value(payload)


def decrypt_qr_payload(token: str) -> Dict[str, Any]:
    decrypted = decrypt_value(token)
    return json.loads(decrypted)


def generate_qr_code_base64(payload: str, size: int = 16) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
