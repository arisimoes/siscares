document.addEventListener("DOMContentLoaded", async () => {
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
    });

    document.getElementById("cancelEdit").addEventListener("click", resetClassForm);
});

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

async function loadClasses() {
    const classes = await listClasses();
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
    document.getElementById("year").value = "2026";
    document.getElementById("cancelEdit").classList.add("hidden");
}
