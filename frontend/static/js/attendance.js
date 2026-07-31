let scanner = null;
let isProcessing = false;
let lastScanned = "";

function getCurrentShift() {
    const hour = new Date().getHours();
    if (hour >= 18) return { id: 3, name: "Noturno" };
    if (hour >= 12) return { id: 2, name: "Vespertino" };
    return { id: 1, name: "Matutino" };
}

function canScan() {
    const hour = new Date().getHours();
    return hour >= 6 && hour < 22;
}

function showOverlay(message, type = "success") {
    const overlay = document.getElementById("scanOverlay");
    const text = document.getElementById("overlayText");
    overlay.className = `scan-overlay ${type} show`;
    text.textContent = message;
}

function hideOverlay() {
    const overlay = document.getElementById("scanOverlay");
    overlay.classList.remove("show");
}

async function init() {
    const shift = getCurrentShift();
    document.getElementById("shiftInfo").textContent = `Turno atual: ${shift.name}`;

    if (!canScan()) {
        document.getElementById("statusMsg").textContent = "Leitura de QR Code permitida apenas entre 6h e 22h.";
        document.getElementById("statusMsg").className = "error";
        return;
    }

    scanner = new Html5Qrcode("reader");
    Html5Qrcode.getCameras().then(cameras => {
        if (cameras && cameras.length) {
            const rearCamera = cameras.find(c => c.label.toLowerCase().includes("back") || c.label.toLowerCase().includes("traseira") || c.label.toLowerCase().includes("environment"));
            const cameraId = rearCamera ? rearCamera.id : cameras[0].id;
            scanner.start(
                cameraId,
                { fps: 10, qrbox: { width: 250, height: 250 } },
                onScanSuccess,
                onScanFailure
            );
        } else {
            document.getElementById("statusMsg").textContent = "Nenhuma câmera encontrada.";
        }
    });
}

async function onScanSuccess(decodedText) {
    if (isProcessing) return;
    if (!canScan()) {
        showOverlay("Leitura encerrada até às 6h", "error");
        return;
    }

    const payload = decodedText.trim();
    console.log("QR raw:", decodedText);
    console.log("QR trimmed:", payload);
    console.log("QR length:", payload.length);
    console.log("QR fernet?", looksLikeFernet(payload));

    if (!looksLikeFernet(payload)) {
        console.warn("QR lido não parece um token SisCarEs; ignorando.");
        return;
    }

    if (payload === lastScanned) return;

    isProcessing = true;
    lastScanned = payload;
    const status = document.getElementById("statusMsg");

    try {
        await scanner.pause();
        await registerAttendance({ qr_payload: payload, shift_id: getCurrentShift().id });
        status.textContent = "Presença registrada com sucesso!";
        status.className = "success";
        showOverlay("✓ Presença confirmada!");
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        const msg = err.message || "";
        const isDuplicate = msg.toLowerCase().includes("já registrada");
        const isInvalidQr = msg.toLowerCase().includes("qr code") || msg.toLowerCase().includes("inválido") || msg.toLowerCase().includes("corrompido");
        const isInactive = msg.toLowerCase().includes("inativo") || msg.toLowerCase().includes("cancelada");

        if (isDuplicate) {
            status.textContent = msg;
            status.className = "warning";
            showOverlay("⚠ " + msg, "warning");
        } else if (isInactive || msg.toLowerCase().includes("transferido")) {
            status.textContent = msg;
            status.className = "error";
            showOverlay("✕ " + msg, "error");
        } else if (isInvalidQr) {
            status.textContent = "QR Code inválido";
            status.className = "error";
            showOverlay("✕ QR Code inválido", "error");
        } else {
            status.textContent = msg;
            status.className = "error";
            showOverlay("✕ " + msg, "error");
        }
        lastScanned = "";
    } finally {
        setTimeout(async () => {
            hideOverlay();
            status.textContent = "";
            if (scanner) await scanner.resume();
            isProcessing = false;
        }, 2500);
    }
}

function looksLikeFernet(token) {
    return typeof token === "string" && token.startsWith("gAAAAAB") && token.length > 50;
}

function onScanFailure(error) {
    // ignorar erros de leitura contínua
}

document.addEventListener("DOMContentLoaded", init);
