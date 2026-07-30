let academicYears = [];

document.addEventListener("DOMContentLoaded", async () => {
    await loadAcademicYears();
    await loadShifts();
    await loadClasses();

    document.getElementById("shiftForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        await createShift({
            name: document.getElementById("shift_name").value,
            start_time: document.getElementById("start_time").value,
            end_time: document.getElementById("end_time").value,
        });
        e.target.reset();
        await loadShifts();
    });

    document.getElementById("classForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const classId = document.getElementById("class_id").value;
        const shiftId = document.getElementById("shift_id").value;
        const data = {
            name: document.getElementById("class_name").value,
            grade: document.getElementById("grade").value || null,
            year: parseInt(document.getElementById("year").value),
            shift_id: shiftId ? parseInt(shiftId, 10) : null,
        };
        if (classId) {
            await updateClass(classId, data);
        } else {
            await createClass(data);
        }
        resetClassForm();
        await loadShifts();
        await loadClasses();
        renderClasses();
    });

    document.getElementById("cancelEdit").addEventListener("click", resetClassForm);
    document.getElementById("filter_year")?.addEventListener("change", renderClasses);
});

async function loadAcademicYears() {
    try {
        const me = await getMe();
        if (!me || !me.school_id) {
            academicYears = [];
            return;
        }
        academicYears = await listAcademicYears(me.school_id);

        const classYearSelect = document.getElementById("year");
        const currentClassYear = classYearSelect.value;
        classYearSelect.innerHTML = '<option value="">Selecione o ano letivo</option>' +
            academicYears.map(y => `<option value="${y.year}">${y.year}</option>`).join("");
        if (currentClassYear && academicYears.some(y => String(y.year) === currentClassYear)) {
            classYearSelect.value = currentClassYear;
        } else if (academicYears.length > 0) {
            const active = academicYears.find(y => y.is_active);
            classYearSelect.value = active ? active.year : academicYears[0].year;
        }

        const filterSelect = document.getElementById("filter_year");
        if (filterSelect) {
            const currentFilter = filterSelect.value;
            filterSelect.innerHTML = '<option value="">Todos os anos</option>' +
                academicYears.map(y => `<option value="${y.year}">${y.year}</option>`).join("");
            if (currentFilter && academicYears.some(y => String(y.year) === currentFilter)) {
                filterSelect.value = currentFilter;
            }
        }
    } catch (err) {
        console.error("Erro ao carregar anos letivos:", err);
        academicYears = [];
    }
}

async function loadShifts() {
    const shifts = await listShifts();
    document.getElementById("shiftsList").innerHTML = shifts.map(s => `
        <li>${s.name}: ${s.start_time || "--:--"} - ${s.end_time || "--:--"}</li>
    `).join("");

    const select = document.getElementById("shift_id");
    if (select) {
        const current = select.value;
        select.innerHTML = '<option value="">Selecione o turno</option>' +
            shifts.map(s => `<option value="${s.id}">${s.name} (${s.start_time || "--:--"} - ${s.end_time || "--:--"})</option>`).join("");
        if (current) select.value = current;
    }
}

let allClasses = [];

async function loadClasses() {
    allClasses = await listClasses();
    renderClasses();
}

function renderClasses() {
    const filterYear = document.getElementById("filter_year")?.value || "";
    const classes = filterYear
        ? allClasses.filter(c => String(c.year) === filterYear)
        : allClasses;

    const list = document.getElementById("classesList");
    if (!classes.length) {
        list.innerHTML = "<li class='empty-state'>Nenhuma turma cadastrada.</li>";
        return;
    }
    list.innerHTML = classes.map(c => `
        <li class="class-row">
            <span class="class-info">${c.name} (${c.grade || "-"}) - ${c.year} - Turno: ${c.shift_name || "-"}</span>
            <span class="class-actions">
                <button class="btn-secondary" onclick="editClass(${c.id}, '${escapeHtml(c.name)}', '${escapeHtml(c.grade || "")}', ${c.year}, ${c.shift_id || 'null'})">Editar</button>
                <button class="btn-danger" onclick="deleteClassItem(${c.id})">Excluir</button>
            </span>
        </li>
    `).join("");
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/\u003c/g, "\u0026lt;")
        .replace(/\u003e/g, "\u0026gt;")
        .replace(/"/g, "\u0026quot;")
        .replace(/'/g, "\u0026#039;")
        .replace(/\u0026/g, "\u0026amp;");
}

window.editClass = async function(id, name, grade, year, shiftId) {
    document.getElementById("class_id").value = id;
    document.getElementById("class_name").value = name;
    document.getElementById("grade").value = grade || "";
    document.getElementById("year").value = year;
    document.getElementById("shift_id").value = shiftId || "";
    document.getElementById("cancelEdit").classList.remove("hidden");
    window.scrollTo({ top: document.getElementById("classForm").offsetTop - 80, behavior: "smooth" });
};

window.deleteClassItem = async function(id) {
    if (!confirm("Deseja realmente excluir esta turma?")) return;
    await deleteClass(id);
    await loadClasses();
};

function resetClassForm() {
    document.getElementById("classForm").reset();
    document.getElementById("class_id").value = "";
    const yearSelect = document.getElementById("year");
    yearSelect.innerHTML = '<option value="">Selecione o ano letivo</option>' +
        academicYears.map(y => `<option value="${y.year}">${y.year}</option>`).join("");
    if (academicYears.length > 0) {
        const active = academicYears.find(y => y.is_active);
        yearSelect.value = active ? active.year : academicYears[0].year;
    }
    document.getElementById("cancelEdit").classList.add("hidden");
}
