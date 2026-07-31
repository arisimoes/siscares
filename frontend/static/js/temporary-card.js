function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/\u003c/g, "\u0026lt;")
        .replace(/\u003e/g, "\u0026gt;")
        .replace(/"/g, "\u0026quot;")
        .replace(/'/g, "\u0026#039;")
        .replace(/\u0026/g, "\u0026amp;");
}

async function renderTemporaryCard() {
    const params = new URLSearchParams(window.location.search);
    const studentId = params.get("student_id");
    const cardId = params.get("card_id");
    const validity = params.get("validity") || "Válido até o fim do turno";
    const qrBase64 = params.get("qr");

    if (!studentId || !cardId) {
        document.getElementById("cardSheet").innerHTML = "\u003cp class='error'\u003eDados da carteirinha provisória ausentes.\u003c/p\u003e";
        return;
    }

    try {
        const data = await getStudentCard(studentId);
        const classDisplay = escapeHtml(data.class_name || "-") || "-";
        const shiftText = data.shift_name ? ` - Turno: ${escapeHtml(data.shift_name)}` : "";
        const classLine = `${classDisplay}${shiftText}`;
        const schoolPhotoHtml = data.school_photo_url
            ? `\u003cimg class="card-school-photo" src="${data.school_photo_url}" alt="Foto da escola"\u003e`
            : `\u003cdiv class="card-school-photo empty"\u003e\u003c/div\u003e`;
        const qrHtml = qrBase64
            ? `\u003cimg class="card-qrcode" src="data:image/png;base64,${qrBase64}" alt="QR Code"\u003e`
            : `\u003cdiv class="card-qrcode" style="display:flex;align-items:center;justify-content:center;font-size:0.6rem;color:#999;"\u003eQR indisponível\u003c/div\u003e`;

        document.getElementById("cardSheet").innerHTML = `
            \u003cdiv class="card-preview single-card"\u003e
                \u003cdiv class="card-header"\u003e
                    \u003cdiv class="school-name"\u003e${escapeHtml(data.school_name || "ESCOLA MUNICIPAL")}\u003c/div\u003e
                    \u003cdiv class="system-name"\u003eSisCarEs\u003c/div\u003e
                \u003c/div\u003e
                \u003cdiv class="card-body"\u003e
                    \u003cdiv class="card-main"\u003e
                        \u003cdiv class="temporary-stamp"\u003eAcesso Único - Provisório\u003c/div\u003e
                        \u003cdiv class="card-student-name"\u003e${escapeHtml(data.full_name)}\u003c/div\u003e
                        \u003cdiv class="card-class"\u003e${classLine}\u003c/div\u003e
                        \u003cdiv class="card-school-photo-area"\u003e${schoolPhotoHtml}\u003c/div\u003e
                        \u003cdiv class="card-line"\u003e
                            \u003cdiv class="card-block"\u003e
                                \u003cdiv class="label"\u003eMatrícula\u003c/div\u003e
                                \u003cdiv class="value"\u003e${escapeHtml(data.registration_code || "-")}\u003c/div\u003e
                            \u003c/div\u003e
                            \u003cdiv class="card-block"\u003e
                                \u003cdiv class="label"\u003eValidade\u003c/div\u003e
                                \u003cdiv class="value temporary-validity"\u003e${escapeHtml(validity)}\u003c/div\u003e
                            \u003c/div\u003e
                        \u003c/div\u003e
                    \u003c/div\u003e
                    \u003cdiv class="card-qrcode-wrap"\u003e
                        ${qrHtml}
                        \u003cdiv class="card-qrcode-hint"\u003eLeia na portaria para registrar frequência\u003c/div\u003e
                    \u003c/div\u003e
                \u003c/div\u003e
                \u003cdiv class="card-footer"\u003e
                    Carteirinha provisória - válida apenas para o turno de hoje
                \u003c/div\u003e
            \u003c/div\u003e
        `;
    } catch (err) {
        document.getElementById("cardSheet").innerHTML = `\u003cp class='error'\u003e${err.message}\u003c/p\u003e`;
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderTemporaryCard);
} else {
    renderTemporaryCard();
}
