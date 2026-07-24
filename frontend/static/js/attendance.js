let scanner = null;

function getCurrentShift() {
    const hour = new Date().getHours();
    if (hour >= 18) return { id: 3, name: "Noturno" };
    if (hour >= 12) return { id: 2, name: "Vespertino" };
    return { id: 1, name: "Matutino" };
}

async function init() {
    const shift = getCurrentShift();
    document.getElementById("shiftInfo").textContent = `Turno atual: ${shift.name}`;

    scanner = new Html5Qrcode("reader");
    Html5Qrcode.getCameras().then(cameras => {
        if (cameras && cameras.length) {
            // Preferir câmera traseira (ambiente)
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
    const status = document.getElementById("statusMsg");
    const shiftId = getCurrentShift().id;
    try {
        await registerAttendance({ qr_payload: decodedText, shift_id: shiftId });
        status.textContent = "Presença registrada com sucesso!";
        status.className = "success";
        await scanner.pause();
        setTimeout(() => { status.textContent = ""; scanner.resume(); }, 2000);
    } catch (err) {
        status.textContent = err.message;
        status.className = "error";
    }
}

function onScanFailure(error) {
    // ignorar erros de leitura contínua
}

document.addEventListener("DOMContentLoaded", init);
