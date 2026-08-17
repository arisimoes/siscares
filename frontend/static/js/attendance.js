let scanner = null;
let isProcessing = false;
let lastScanned = "";
let scannerStarted = false;
let scannerInitializing = false;

function logDebug(message, data) {
    const consoleEl = document.getElementById("debugConsole");
    if (!consoleEl) return;
    const timestamp = new Date().toLocaleTimeString("pt-BR", { hour12: false });
    let line = `[${timestamp}] ${message}`;
    if (data !== undefined) {
        try {
            line += "\n" + JSON.stringify(data, null, 2);
        } catch {
            line += "\n" + String(data);
        }
    }
    consoleEl.textContent += line + "\n";
    consoleEl.scrollTop = consoleEl.scrollHeight;
    if (typeof console !== "undefined") {
        console.log(message, data);
    }
}

window.clearDebugConsole = function () {
    const consoleEl = document.getElementById("debugConsole");
    if (consoleEl) consoleEl.textContent = "";
};

window.copyDebugConsole = async function () {
    const consoleEl = document.getElementById("debugConsole");
    if (!consoleEl) return;
    try {
        await navigator.clipboard.writeText(consoleEl.textContent);
        logDebug("Conteúdo do console copiado para a área de transferência");
    } catch (err) {
        logDebug("Falha ao copiar console", err?.message);
        alert("Não foi possível copiar automaticamente. Selecione o texto manualmente.");
    }
};

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
    logDebug("Inicializando página de chamada");
    const shift = getCurrentShift();
    document.getElementById("shiftInfo").textContent = `Turno atual: ${shift.name}`;
    logDebug("Turno detectado", shift);

    if (!canScan()) {
        setStatus("Leitura de QR Code permitida apenas entre 6h e 22h.", "error");
        logDebug("Fora da janela global de leitura (6h-22h)");
        return;
    }

    scanner = new Html5Qrcode("reader");
    logDebug("Scanner Html5Qrcode instanciado");
    const startButton = document.getElementById("startCameraBtn");
    if (startButton) {
        startButton.addEventListener("click", startScanner);
    }

    const isMobile = window.matchMedia("(pointer: coarse)").matches;
    logDebug("Contexto", { isMobile, secureContext: isSecureCameraContext(), host: location.hostname, protocol: location.protocol });
    if (!isMobile) {
        await startScanner();
    } else {
        setStatus("Toque em 'Ativar câmera' para iniciar a leitura do QR Code.", "warning");
    }
}

async function startScanner() {
    if (scannerInitializing || scannerStarted) return;
    logDebug("Solicitando início da câmera");

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
        logDebug("Câmeras detectadas", cameras.map(c => ({ id: c.id, label: c.label })));
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

        const screenShort = Math.min(window.innerWidth, window.innerHeight) || 360;
        const qrboxSize = Math.max(200, Math.min(320, Math.floor(screenShort * 0.7)));
        logDebug("Configuração do leitor", { fps: 15, qrbox: qrboxSize });

        let lastError = null;
        for (const candidate of cameraCandidates) {
            try {
                logDebug("Tentando câmera", typeof candidate === "string" ? candidate.slice(0, 40) + "..." : candidate);
                await scanner.start(
                    candidate,
                    {
                        fps: 15,
                        qrbox: { width: qrboxSize, height: qrboxSize },
                        aspectRatio: 1.0,
                        disableFlip: false,
                        experimentalFeatures: { useBarCodeDetectorIfSupported: true },
                        videoConstraints: {
                            facingMode: "environment",
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        }
                    },
                    onScanSuccess,
                    onScanFailure
                );
                scannerStarted = true;
                setStatus("Câmera pronta. Aponte o QR Code para a leitura.", "success");
                logDebug("Câmera iniciada com sucesso");
                return;
            } catch (error) {
                lastError = error;
                logDebug("Falha ao iniciar câmera", error?.message || error);
            }
        }

        throw lastError || new Error("Não foi possível iniciar a câmera.");
    } catch (error) {
        const message = error?.message || "Não foi possível iniciar a câmera.";
        logDebug("Erro ao iniciar scanner", message);
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
    if (isProcessing) {
        logDebug("Scan ignorado: processamento em andamento");
        return;
    }
    if (!canScan()) {
        showOverlay("Leitura encerrada até às 6h", "error");
        return;
    }

    const payload = decodedText.trim();
    logDebug("QR lido (raw)", payload.slice(0, 80) + (payload.length > 80 ? "..." : ""));

    if (!looksLikeFernet(payload)) {
        logDebug("Payload não parece Fernet", payload.slice(0, 50));
        return;
    }

    if (payload === lastScanned) {
        logDebug("QR repetido ignorado");
        return;
    }

    isProcessing = true;
    lastScanned = payload;
    const status = document.getElementById("statusMsg");

    try {
        const shift = getCurrentShift();
        logDebug("Registrando presença", { shift_id: shift.id, shift_name: shift.name });
        if (scannerStarted) {
            await scanner.pause();
        }
        await registerAttendance({ qr_payload: payload, shift_id: shift.id });
        status.textContent = "Presença registrada com sucesso!";
        status.className = "success";
        showOverlay("✓ Presença confirmada!");
        logDebug("Presença registrada com sucesso");
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        const msg = err.message || "";
        logDebug("Erro no registro de presença", msg);
        const isOutOfHours = msg.toLowerCase().includes("fora do horário") || msg.toLowerCase().includes("horário do turno");
        const isDuplicate = msg.toLowerCase().includes("já registrada");
        const isInvalidQr = msg.toLowerCase().includes("qr code") || msg.toLowerCase().includes("inválido") || msg.toLowerCase().includes("corrompido");
        const isInactive = msg.toLowerCase().includes("inativo") || msg.toLowerCase().includes("cancelada");

        if (isOutOfHours) {
            status.textContent = msg;
            status.className = "warning";
            showOverlay("⚠ " + msg, "warning");
        } else if (isDuplicate) {
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
    const ok = typeof token === "string" && token.startsWith("gAAAAAB") && token.length > 50;
    if (!ok) {
        logDebug("looksLikeFernet rejeitou", token);
    }
    return ok;
}

let failureCount = 0;
function onScanFailure(error) {
    failureCount++;
    // Loga a cada 30 falhas para não poluir, mas dá visibilidade se há erro persistente.
    if (failureCount % 30 === 1) {
        logDebug("onScanFailure (a cada 30 tentativas)", error);
    }
}

document.addEventListener("DOMContentLoaded", init);
