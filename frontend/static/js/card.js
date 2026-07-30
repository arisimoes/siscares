const CARDS_PER_A4_PAGE = 9;

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/\u003c/g, "\u0026lt;")
        .replace(/\u003e/g, "\u0026gt;")
        .replace(/"/g, "\u0026quot;")
        .replace(/'/g, "\u0026#039;")
        .replace(/\u0026/g, "\u0026amp;");
}

async function loadClassesFilter() {
    try {
        const classes = await listClasses();
        const select = document.getElementById("classFilter");
        select.innerHTML = '<option value="">Selecione uma turma</option>' +
            classes.map(c => `<option value="${c.id}">${c.name} (${c.grade || "-"})</option>`).join("");
    } catch (err) {
        console.error(err);
    }
}

async function loadSheet() {
    const classId = document.getElementById("classFilter").value;
    const container = document.getElementById("cardSheet");
    const summary = document.getElementById("pageSummary");
    const totalCardsEl = document.getElementById("totalCards");
    const totalPagesEl = document.getElementById("totalPages");
    const cardsPerPageEl = document.getElementById("cardsPerPage");

    if (!classId) {
        container.innerHTML = "<p class='empty-state'>Selecione uma turma.</p>";
        container.classList.add('sheet-wrapper');
        container.classList.remove('card-sheet');
        return;
    }

    try {
        const students = await listStudents({ class_id: classId });
        if (!students.length) {
            container.innerHTML = "<p class='empty-state'>Nenhum aluno encontrado nesta turma.</p>";
            container.classList.add('sheet-wrapper');
            container.classList.remove('card-sheet');
            summary.classList.add("hidden");
            return;
        }

        const cardsHtml = await Promise.all(students.map(async (s) => {
            let cardData = null;
            let qrHtml = "";
            let validity = "31/12/" + (new Date().getFullYear() + 1);
            try {
                cardData = await getStudentCard(s.id);
                validity = cardData.validity || validity;
                qrHtml = `\u003cimg class="card-qrcode" src="data:image/png;base64,${cardData.qr_base64}" alt="QR Code"\u003e`;
            } catch (e) {
                qrHtml = `<div class="card-qrcode" style="display:flex;align-items:center;justify-content:center;font-size:0.6rem;color:#999;">QR não gerado</div>`;
            }

            const classDisplay = escapeHtml(s.class_name || "-") || "-";
            const shiftText = s.shift_name ? ` - Turno: ${escapeHtml(s.shift_name)}` : "";
            const classLine = `${classDisplay}${shiftText}`;
            const schoolPhotoHtml = s.school_photo_url
                ? `\u003cimg class="card-school-photo" src="${s.school_photo_url}" alt="Foto da escola"\u003e`
                : `\u003cdiv class="card-school-photo empty"\u003e\u003c/div\u003e`;

            return `
                <div class="card-preview">
                    <div class="card-header">
                        <div class="school-name">${escapeHtml(s.school_name || "ESCOLA MUNICIPAL")}</div>
                        <div class="system-name">SisCares</div>
                    </div>
                    <div class="card-body">
                        <div class="card-main">
                            <div class="card-student-name">${escapeHtml(s.full_name)}</div>
                            <div class="card-class">${classLine}</div>
                            <div class="card-school-photo-area">${schoolPhotoHtml}</div>
                            <div class="card-line">
                                <div class="card-block">
                                    <div class="label">Matrícula</div>
                                    <div class="value">${escapeHtml(s.registration_code || "-")}</div>
                                </div>
                                <div class="card-block">
                                    <div class="label">Validade</div>
                                    <div class="value">${validity}</div>
                                </div>
                            </div>
                        </div>
                        <div class="card-qrcode-wrap">
                            ${qrHtml}
                        </div>
                    </div>
                    <div class="card-footer">
                        Leia na portaria para registrar frequência
                    </div>
                </div>
            `;
        }));

        const totalPages = Math.ceil(cardsHtml.length / CARDS_PER_A4_PAGE);
        let pagesHtml = "";
        for (let page = 0; page < totalPages; page++) {
            const start = page * CARDS_PER_A4_PAGE;
            const slice = cardsHtml.slice(start, start + CARDS_PER_A4_PAGE);
            pagesHtml += `<div class="sheet-page" data-page-label="Folha A4 ${page + 1}/${totalPages}">${slice.join("")}</div>`;
        }
        container.innerHTML = pagesHtml;
        container.classList.add('sheet-wrapper');
        container.classList.remove('card-sheet');
        summary.classList.remove("hidden");
        totalCardsEl.textContent = students.length;
        totalPagesEl.textContent = totalPages;
        cardsPerPageEl.textContent = CARDS_PER_A4_PAGE;
        // ajustar escala após renderização do DOM
        adjustSheetScale();
        setTimeout(adjustSheetScale, 100);
    } catch (err) {
        container.innerHTML = `<p class='error'>${err.message}</p>`;
        summary.classList.add("hidden");
    }
}

function adjustSheetScale() {
    const pages = document.querySelectorAll('.sheet-page');
    if (!pages.length) return;

    const controls = document.querySelector('.card-controls');
    const summary = document.getElementById('pageSummary');
    const heading = document.querySelector('main.dashboard h2');
    let usedHeight = 0;
    if (controls) usedHeight += controls.getBoundingClientRect().height + 24;
    if (summary && !summary.classList.contains('hidden')) usedHeight += summary.getBoundingClientRect().height + 24;
    if (heading) usedHeight += heading.getBoundingClientRect().height + 24;
    usedHeight += 64; // padding/margens gerais + label da folha

    const availableWidth = window.innerWidth - 32;
    const availableHeight = Math.max(window.innerHeight - usedHeight, 180);

    const pageWidthMm = 297;
    const pageHeightMm = 210;

    // 1mm em pixels considerando 96 DPI
    const pxPerMm = 96 / 25.4;
    const naturalWidth = pageWidthMm * pxPerMm;  // ~1123 px
    const naturalHeight = pageHeightMm * pxPerMm; // ~794 px

    const scaleX = availableWidth / naturalWidth;
    const scaleY = availableHeight / naturalHeight;
    const scale = Math.max(0.25, Math.min(scaleX, scaleY, 1));

    document.documentElement.style.setProperty('--a4-scale', scale.toFixed(4));

    pages.forEach(page => {
        page.style.marginBottom = `${naturalHeight * scale - naturalHeight + 16}px`;
    });
}

window.addEventListener("resize", adjustSheetScale);

async function renderSingleCard() {
    const params = new URLSearchParams(window.location.search);
    const studentId = params.get("student_id");
    if (!studentId) return;

    try {
        const data = await getStudentCard(studentId);
        const validity = data.validity || `31/12/${new Date().getFullYear() + 1}`;

        const classDisplay = escapeHtml(data.class_name || "-") || "-";
        const shiftText = data.shift_name ? ` - Turno: ${escapeHtml(data.shift_name)}` : "";
        const classLine = `${classDisplay}${shiftText}`;
        const schoolPhotoHtml = data.school_photo_url
            ? `<img class="card-school-photo" src="${data.school_photo_url}" alt="Foto da escola">`
            : `<div class="card-school-photo empty"></div>`;

        document.getElementById("cardSheet").innerHTML = `
            <div class="card-preview single-card">
                <div class="card-header">
                    <div class="school-name">${escapeHtml(data.school_name || "ESCOLA MUNICIPAL")}</div>
                    <div class="system-name">SisCares</div>
                </div>
                <div class="card-body">
                    <div class="card-main">
                        <div class="card-student-name">${escapeHtml(data.full_name)}</div>
                        <div class="card-class">${classLine}</div>
                        <div class="card-school-photo-area">${schoolPhotoHtml}</div>
                        <div class="card-line">
                            <div class="card-block">
                                <div class="label">Matrícula</div>
                                <div class="value">${escapeHtml(data.registration_code || "-")}</div>
                            </div>
                            <div class="card-block">
                                <div class="label">Validade</div>
                                <div class="value">${validity}</div>
                            </div>
                        </div>
                    </div>
                    <div class="card-qrcode-wrap">
                        <img class="card-qrcode" src="data:image/png;base64,${data.qr_base64}" alt="QR Code">
                        <div class="card-qrcode-hint">Leia na portaria para registrar frequência</div>
                    </div>
                </div>
                <div class="card-footer">
                    Carteirinha escolar válida com assinatura digital SisCares
                </div>
            </div>
        `;
    } catch (err) {
        document.getElementById("cardSheet").innerHTML = `<p class='error'>${err.message}</p>`;
    }
}

async function initCardPage() {
    await loadClassesFilter();
    const params = new URLSearchParams(window.location.search);
    if (params.get("student_id")) {
        renderSingleCard();
    }
}

function exportPdf() {
    const element = document.getElementById("cardSheet");
    if (!element || element.querySelector(".empty-state")) {
        alert("Gere a folha A4 antes de exportar.");
        return;
    }

    const className = document.getElementById("classFilter")?.selectedOptions?.[0]?.text?.replace(/[^a-zA-Z0-9\- ]/g, "").trim() || "carteirinhas";
    const opt = {
        margin: 0,
        filename: `siscares-${className}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
            scale: 3,
            useCORS: true,
            logging: false,
            backgroundColor: "#ffffff",
            width: 1123,
            windowWidth: 1123,
            imageTimeout: 0,
            onclone: (clonedDoc) => {
                clonedDoc.querySelectorAll(".card-school-photo").forEach(img => {
                    img.style.imageRendering = "auto";
                });
            }
        },
        jsPDF: {
            unit: "mm",
            format: "a4",
            orientation: "landscape"
        },
        pagebreak: { mode: ["css", "legacy"] }
    };

    const wrapper = document.createElement("div");
    wrapper.style.width = "297mm";
    wrapper.style.boxSizing = "border-box";
    wrapper.style.background = "white";
    wrapper.style.padding = "0";
    wrapper.style.margin = "0";
    wrapper.style.position = "relative";

    const clone = element.cloneNode(true);
    clone.style.cssText = "";
    clone.querySelectorAll(".sheet-page").forEach(page => {
        page.classList.remove("sheet-page");
        page.classList.add("print-a4-page");
        page.style.cssText = "";
        // Substituir imagens por clones absolutamente posicionados para evitar distorção no html2canvas
        page.querySelectorAll(".card-school-photo").forEach(img => {
            if (!img.src || img.classList.contains("empty")) return;
            const rect = img.getBoundingClientRect();
            const container = img.parentElement;
            const containerRect = container.getBoundingClientRect();
            const cloneImg = document.createElement("img");
            cloneImg.src = img.src;
            cloneImg.style.position = "absolute";
            cloneImg.style.left = "0";
            cloneImg.style.top = "0";
            cloneImg.style.width = rect.width + "px";
            cloneImg.style.height = rect.height + "px";
            cloneImg.style.objectFit = "contain";
            cloneImg.style.display = "block";
            cloneImg.style.imageRendering = "auto";
            const overlay = document.createElement("div");
            overlay.style.position = "absolute";
            overlay.style.left = (rect.left - containerRect.left) + "px";
            overlay.style.top = (rect.top - containerRect.top) + "px";
            overlay.style.width = rect.width + "px";
            overlay.style.height = rect.height + "px";
            overlay.style.overflow = "hidden";
            overlay.appendChild(cloneImg);
            container.style.position = "relative";
            container.appendChild(overlay);
        });
    });

    wrapper.appendChild(clone);

    html2pdf().set(opt).from(wrapper).save();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCardPage);
} else {
    initCardPage();
}
