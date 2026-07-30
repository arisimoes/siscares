let currentUser = null;
let schoolId = null;
let years = [];
let currentYear = null;
let calendarDays = {};
let editingYearId = null;

const MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];
const WEEKDAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

async function init() {
    currentUser = await getMe();
    if (!currentUser) return;
    document.getElementById("userName").textContent = `${currentUser.full_name} (${currentUser.role})`;
    schoolId = currentUser.school_id;
    if (!schoolId) {
        alert("Usuário sem escola associada.");
        return;
    }
    await loadYears();
    if (years.length > 0) {
        const select = document.getElementById("yearSelect");
        select.value = years.find(y => y.is_active)?.year || years[0].year;
        await changeYear();
    }
}

async function loadYears() {
    const select = document.getElementById("yearSelect");
    select.innerHTML = "";
    years = await listAcademicYears(schoolId);
    years.forEach(y => {
        const opt = document.createElement("option");
        opt.value = y.year;
        opt.textContent = `${y.year} (${y.start_date} a ${y.end_date})`;
        select.appendChild(opt);
    });
}

async function changeYear() {
    currentYear = parseInt(document.getElementById("yearSelect").value);
    const yearObj = years.find(y => y.year === currentYear);
    document.getElementById("yearInfo").textContent = yearObj
        ? `Início: ${yearObj.start_date} | Término: ${yearObj.end_date}`
        : "";
    const days = await listCalendarDays(schoolId, currentYear);
    calendarDays = {};
    days.forEach(d => { calendarDays[d.date] = d; });
    renderYear(currentYear);
}

function renderYear(year) {
    const grid = document.getElementById("yearGrid");
    grid.innerHTML = "";
    for (let month = 0; month < 12; month++) {
        const card = document.createElement("div");
        card.className = "month-card";
        card.innerHTML = `
            <h4>${MONTH_NAMES[month]}</h4>
            <div class="month-days" id="month-${month}">
                ${WEEKDAYS.map(d => `<div class="weekday">${d}</div>`).join("")}
            </div>
        `;
        grid.appendChild(card);
        renderMonth(year, month, card.querySelector(".month-days"));
    }
}

const TYPE_CYCLE = ["school", "holiday", "event", "weekend"];

function renderMonth(year, month, container) {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startOffset = firstDay.getDay();
    for (let i = 0; i < startOffset; i++) {
        const empty = document.createElement("div");
        container.appendChild(empty);
    }
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const date = new Date(year, month, day);
        const dateStr = toISODate(date);
        const dayData = calendarDays[dateStr];
        const isWeekend = date.getDay() === 0 || date.getDay() === 6;
        const dayType = dayData ? dayData.day_type : (isWeekend ? "weekend" : "school");
        const el = document.createElement("div");
        el.className = `day ${dayType}`;
        el.textContent = day;
        el.title = dayData?.description || "";
        el.dataset.date = dateStr;
        el.dataset.id = dayData?.id || "";
        el.onclick = () => cycleDayType(el);
        container.appendChild(el);
    }
}

function toISODate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

async function cycleDayType(el) {
    const dateStr = el.dataset.date;
    const currentType = el.classList.contains("holiday") ? "holiday"
        : el.classList.contains("event") ? "event"
        : el.classList.contains("weekend") ? "weekend"
        : "school";
    const nextIndex = (TYPE_CYCLE.indexOf(currentType) + 1) % TYPE_CYCLE.length;
    const nextType = TYPE_CYCLE[nextIndex];

    const dayData = calendarDays[dateStr];
    const data = { date: dateStr, day_type: nextType, description: dayData?.description || "" };
    await saveCalendarDay(schoolId, data);
    await changeYear();
}

function addYear() {
    editingYearId = null;
    const now = new Date();
    document.getElementById("yearModalTitle").textContent = "Cadastrar ano letivo";
    document.getElementById("newYear").value = now.getFullYear();
    document.getElementById("newYear").readOnly = false;
    document.getElementById("newYearStart").value = `${now.getFullYear()}-02-01`;
    document.getElementById("newYearEnd").value = `${now.getFullYear()}-12-20`;
    document.getElementById("yearModal").classList.remove("hidden");
}

function editCurrentYear() {
    if (!currentYear) return;
    const yearObj = years.find(y => y.year === currentYear);
    if (!yearObj) return;
    editingYearId = yearObj.id;
    document.getElementById("yearModalTitle").textContent = "Editar ano letivo";
    document.getElementById("newYear").value = yearObj.year;
    document.getElementById("newYear").readOnly = true;
    document.getElementById("newYearStart").value = yearObj.start_date;
    document.getElementById("newYearEnd").value = yearObj.end_date;
    document.getElementById("yearModal").classList.remove("hidden");
}

function closeYearModal() {
    document.getElementById("yearModal").classList.add("hidden");
    editingYearId = null;
}

async function saveYear() {
    const year = parseInt(document.getElementById("newYear").value);
    const start = document.getElementById("newYearStart").value;
    const end = document.getElementById("newYearEnd").value;
    if (!year || !start || !end) {
        alert("Preencha todos os campos.");
        return;
    }
    try {
        if (editingYearId) {
            await updateAcademicYear(schoolId, editingYearId, { start_date: start, end_date: end });
        } else {
            await createAcademicYear(schoolId, { year, start_date: start, end_date: end });
        }
        closeYearModal();
        await loadYears();
        document.getElementById("yearSelect").value = year;
        await changeYear();
    } catch (err) {
        alert(err.message || "Erro ao salvar ano letivo.");
    }
}

async function generateYear() {
    if (!currentYear) return;
    if (!confirm(`Gerar calendário base para ${currentYear}? Isso marcará fins de semana automaticamente.`)) return;
    try {
        const res = await generateDefaultCalendar(schoolId, currentYear);
        alert(`Calendário gerado: ${res.created} criados, ${res.updated} atualizados.`);
        await changeYear();
    } catch (err) {
        alert(err.message || "Erro ao gerar calendário.");
    }
}

document.getElementById("yearSelect")?.addEventListener("change", changeYear);

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
