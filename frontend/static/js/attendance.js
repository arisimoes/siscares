let scanner = null;
let isProcessing = false;
let lastScanned = "";
let scannerStarted = false;
let scannerInitializing = false;
let availableShifts = [];
let currentShift = null;
let availableCameras = [];
let torchOn = false;

async function loadShifts() {
    try {
        availableShifts = await listShifts();
        if (!availableShifts || !availableShifts.length) {
            logDebug("Nenhum turno cadastrado na escola");
            return;
        }
        currentShift = detectCurrentShift(availableShifts);
        logDebug("Turnos disponíveis", availableShifts.map(s => ({ id: s.id, name: s.name, start_time: s.start_time, end_time: s.end_time })));
        logDebug("Turno atual detectado", currentShift);
    } catch (err) {
        logDebug("Erro ao carregar turnos", err?.message);
    }
}

function _parseTime(value) {
    if (!value) return null;
    const [h, m] = value.split(":").map(Number);
    return { h, m: m || 0 };
}

function _minutesSinceMidnight(value) {
    const t = _parseTime(value);
    return t ? t.h * 60 + t.m : null;
}

function detectCurrentShift(shifts) {
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();

    let bestMatch = null;
    for (const shift of shifts) {
        const start = _minutesSinceMidnight(shift.start_time);
        const end = _minutesSinceMidnight(shift.end_time);
        if (start === null || end === null) continue;

        const inWindow = start < end
            ? currentMinutes >= start && currentMinutes <= end
            : currentMinutes >= start || currentMinutes <= end;

        if (inWindow) {
            bestMatch = shift;
            break;
        }
    }

    // Fallback: se nenhum turno encaixar no horário, escolhe o mais próximo.
    if (!bestMatch && shifts.length) {
        bestMatch = shifts.reduce((prev, curr) => {
            const prevStart = _minutesSinceMidnight(prev.start_time) || 0;
            const currStart = _minutesSinceMidnight(curr.start_time) || 0;
            return Math.abs(currStart - currentMinutes) < Math.abs(prevStart - currentMinutes) ? curr : prev;
        });
    }
    return bestMatch;
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
    await loadShifts();

    if (!currentShift) {
        setStatus("Nenhum turno cadastrado. Cadastre turnos em Turmas > Turnos.", "error");
        return;
    }

    document.getElementById("shiftInfo").textContent = `Turno atual: ${currentShift.name}`;

    if (!canScan()) {
        setStatus("Leitura de QR Code permitida apenas entre 6h e 22h.", "error");
        return;
    }

    scanner = new Html5Qrcode("reader");
    const startButton = document.getElementById("startCameraBtn");
    if (startButton) {
        startButton.addEventListener("click", toggleScanner);
    }

    const isMobile = window.matchMedia("(pointer: coarse)").matches;
    if (!isMobile) {
        await startScanner();
    } else {
        setStatus("Toque em 'Ativar câmera' para iniciar a leitura do QR Code.", "warning");
    }
}

function getRearCamera() {
    return availableCameras.find((c) => {
        const label = c.label.toLowerCase();
        return label.includes("back") || label.includes("traseira") || label.includes("environment") || label.includes("rear");
    });
}

async function toggleScanner() {
    if (scannerStarted) {
        await stopScanner();
    } else {
        await startScanner();
    }
}

async function stopScanner() {
    if (!scanner || !scannerStarted) return;
    try {
        await scanner.stop();
    } catch (e) {
        // ignore
    }
    scannerStarted = false;
    torchOn = false;
    updateStartButton();
    setStatus("Câmera desativada.", "warning");
    const torchBtn = document.getElementById("torchBtn");
    if (torchBtn) {
        torchBtn.classList.add("hidden");
        torchBtn.textContent = "Ligar lanterna";
    }
}

async function startScanner(preferredCameraId = null) {
    if (scannerInitializing || scannerStarted) return;

    const button = document.getElementById("startCameraBtn");
    if (button) button.disabled = true;

    scannerInitializing = true;
    setStatus("Solicitando acesso à câmera...", "warning");

    try {
        if (!isSecureCameraContext()) {
            throw new Error("A câmera só funciona em uma conexão segura. Use HTTPS ou acesse pelo endereço localhost.");
        }

        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("Este navegador não suporta acesso à câmera.");
        }

        if (!availableCameras.length) {
            availableCameras = await Html5Qrcode.getCameras();
        }
        if (!availableCameras || !availableCameras.length) {
            throw new Error("Nenhuma câmera disponível para este dispositivo.");
        }

        const cameraCandidates = [];
        cameraCandidates.push({ facingMode: { exact: "environment" } });
        cameraCandidates.push({ facingMode: "environment" });
        if (preferredCameraId) {
            cameraCandidates.push(preferredCameraId);
        }
        const rearCamera = getRearCamera();
        if (rearCamera) cameraCandidates.push(rearCamera.id);
        if (availableCameras[0]) cameraCandidates.push(availableCameras[0].id);
        cameraCandidates.push({ facingMode: "user" });

        const screenShort = Math.min(window.innerWidth, window.innerHeight) || 360;
        const qrboxSize = Math.max(180, Math.min(260, Math.floor(screenShort * 0.55)));

        let lastError = null;
        for (const candidate of cameraCandidates) {
            try {
                await scanner.start(
                    candidate,
                    {
                        fps: 30,
                        qrbox: { width: qrboxSize, height: qrboxSize },
                        aspectRatio: 1.0,
                        disableFlip: false,
                        experimentalFeatures: { useBarCodeDetectorIfSupported: true },
                        videoConstraints: {
                            facingMode: candidate && typeof candidate === "object" && candidate.facingMode ? candidate.facingMode : "environment",
                            width: { ideal: 1920 },
                            height: { ideal: 1080 },
                            focusMode: "continuous",
                            exposureMode: "continuous"
                        }
                    },
                    onScanSuccess,
                    onScanFailure
                );
                scannerStarted = true;
                setStatus("Câmera pronta. Aproxime o QR Code do quadrado e segure firme.", "success");
                updateStartButton();
                setupTorchButton();
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
            updateStartButton();
        }
    }
}

function updateStartButton() {
    const btn = document.getElementById("startCameraBtn");
    if (!btn) return;
    btn.textContent = scannerStarted ? "Desativar câmera" : "Ativar câmera";
}

async function toggleTorch() {
    const btn = document.getElementById("torchBtn");
    try {
        const stream = scanner?._elementRef?.srcObject || document.querySelector("#reader video")?.srcObject;
        if (!stream) return;
        const track = stream.getVideoTracks()[0];
        if (!track || !track.getCapabilities().torch) return;
        torchOn = !torchOn;
        await track.applyConstraints({ advanced: [{ torch: torchOn }] });
        if (btn) btn.textContent = torchOn ? "Desligar lanterna" : "Ligar lanterna";
    } catch (err) {
        // ignore
    }
}

function setupTorchButton() {
    const btn = document.getElementById("torchBtn");
    if (!btn) return;
    btn.classList.remove("hidden");
    btn.onclick = toggleTorch;
}

async function onScanSuccess(decodedText) {
    if (isProcessing) return;
    if (!canScan()) {
        showOverlay("Leitura encerrada até às 6h", "error");
        return;
    }

    const payload = decodedText.trim();

    if (!looksLikeFernet(payload)) return;

    if (payload === lastScanned) return;

    isProcessing = true;
    lastScanned = payload;
    const status = document.getElementById("statusMsg");

    try {
        if (!currentShift) {
            throw new Error("Turno não detectado");
        }
        if (scannerStarted) {
            await scanner.pause();
        }
        await registerAttendance({ qr_payload: payload, shift_id: currentShift.id });
        status.textContent = "Presença registrada com sucesso!";
        status.className = "success";
        showOverlay("✓ Presença confirmada!");
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        const msg = err.message || "";
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
    return typeof token === "string" && token.startsWith("gAAAAAB") && token.length > 50;
}

function onScanFailure() {
    // silently ignored
}

document.addEventListener("DOMContentLoaded", init);
