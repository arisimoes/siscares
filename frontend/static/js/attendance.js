let scanner = null;
let isProcessing = false;
let lastScanned = "";
let scannerStarted = false;
let scannerInitializing = false;

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

function setStatus(message, type = "") {
    const status = document.getElementById("statusMsg");
    status.textContent = message;
    status.className = type;
}

function isSecureCameraContext() {
    return window.isSecureContext || location.hostname === "localhost" || location.hostname === "127.0.0.1";
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
        setStatus("Leitura de QR Code permitida apenas entre 6h e 22h.", "error");
        return;
    }

    scanner = new Html5Qrcode("reader");
    const startButton = document.getElementById("startCameraBtn");
    if (startButton) {
        startButton.addEventListener("click", startScanner);
    }

    const isMobile = window.matchMedia("(pointer: coarse)").matches;
    if (!isMobile) {
        await startScanner();
    } else {
        setStatus("Toque em 'Ativar câmera' para iniciar a leitura do QR Code.", "warning");
    }
}

async function startScanner() {
    if (scannerInitializing || scannerStarted) return;

    const button = document.getElementById("startCameraBtn");
    if (button) {
        button.disabled = true;
    }

    scannerInitializing = true;
    setStatus("Solicitando acesso à câmera...", "warning");

    try {
        if (!isSecureCameraContext()) {
            throw new Error("A câmera só funciona em uma conexão segura. Use HTTPS ou acesse pelo endereço localhost.");
        }

        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("Este navegador não suporta acesso à câmera.");
        }

        const cameras = await Html5Qrcode.getCameras();
        if (!cameras || !cameras.length) {
            throw new Error("Nenhuma câmera disponível para este dispositivo.");
        }

        const cameraCandidates = [];
        const rearCamera = cameras.find(c => c.label.toLowerCase().includes("back") || c.label.toLowerCase().includes("traseira") || c.label.toLowerCase().includes("environment"));
        if (rearCamera) cameraCandidates.push(rearCamera.id);
        if (cameras[0]) cameraCandidates.push(cameras[0].id);
        cameraCandidates.push({ facingMode: { ideal: "environment" } });
        cameraCandidates.push({ facingMode: "environment" });
        cameraCandidates.push({ facingMode: "user" });

        let lastError = null;
        for (const candidate of cameraCandidates) {
            try {
                await scanner.start(
                    candidate,
                    {
                        fps: 10,
                        qrbox: { width: 250, height: 250 },
                        aspectRatio: 1.0,
                        disableFlip: false,
                        videoConstraints: {
                            facingMode: "environment"
                        }
                    },
                    onScanSuccess,
                    onScanFailure
                );
                scannerStarted = true;
                setStatus("Câmera pronta. Aponte o QR Code para a leitura.", "success");
                return;
            } catch (error) {
                lastError = error;
            }
        }

        throw lastError || new Error("Não foi possível iniciar a câmera.");
    } catch (error) {
        const message = error?.message || "Não foi possível iniciar a câmera.";
        if (message.includes("Permission") || message.includes("perm") || message.includes("denied")) {
            setStatus("Permissão de câmera negada. Libere o acesso no navegador e tente novamente.", "error");
        } else {
            setStatus(message, "error");
        }
    } finally {
        scannerInitializing = false;
        if (button) {
            button.disabled = false;
        }
    }
}

async function onScanSuccess(decodedText) {
    if (isProcessing) return;
    if (!canScan()) {
        showOverlay("Leitura encerrada até às 6h", "error");
        return;
    }

    const payload = decodedText.trim();

    if (!looksLikeFernet(payload)) {
        return;
    }

    if (payload === lastScanned) return;

    isProcessing = true;
    lastScanned = payload;
    const status = document.getElementById("statusMsg");

    try {
        if (scannerStarted) {
            await scanner.pause();
        }
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
            if (scannerStarted && scanner) await scanner.resume();
            isProcessing = false;
        }, 2500);
    }
}

function looksLikeFernet(token) {
    return typeof token === "string" && token.startsWith("gAAAAAB") && token.length > 50;
}

function onScanFailure() {
}

document.addEventListener("DOMContentLoaded", init);
