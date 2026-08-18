import json
import qrcode
import io
import base64
from typing import Dict, Any
from app.core.crypto import encrypt_value, decrypt_value, sign_value, verify_signature


def build_student_qr_payload(student, minimal: bool = False) -> Dict[str, Any]:
    # Ano letivo vinculado à turma atual do aluno.
    academic_year = student.class_.year if student.class_ else None
    if minimal:
        # Payload mínimo para leitura fácil em câmeras de celular; escola/turma/status resolvidos no servidor.
        return {
            "sid": student.id,
            "mat": student.registration_code,
            "year": academic_year,
        }
    return {
        "sid": student.id,
        "sch": student.school_id,
        "cls": student.class_id,
        "act": student.is_active,
        "year": academic_year,
    }


def generate_encrypted_qr_payload(
    student=None,
    payload_dict=None,
    minimal_payload: bool = False,
) -> str:
    if payload_dict is not None:
        payload_dict = dict(payload_dict)
    elif student is not None:
        payload_dict = build_student_qr_payload(student, minimal=minimal_payload)
    else:
        raise ValueError("Informe student ou payload_dict")

    payload = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=False)
    return encrypt_value(payload)


def decrypt_qr_payload(token: str, verify: bool = True) -> Dict[str, Any]:
    decrypted = decrypt_value(token)
    return json.loads(decrypted)


def generate_qr_code_base64(
    payload: str,
    size: int = 8,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=size,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
