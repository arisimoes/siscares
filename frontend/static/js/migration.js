let allStudents = [];
let filteredStudents = [];
let targetClassesByYear = {};

const sourceYearEl = document.getElementById("sourceYear");
const filterClassEl = document.getElementById("filterClass");
const searchNameEl = document.getElementById("searchName");
const targetClassEl = document.getElementById("targetClass");
const targetYearHintEl = document.getElementById("targetYearHint");
const studentsTableBody = document.querySelector("#studentsTable tbody");
const resultTableBody = document.querySelector("#resultTable tbody");
const resultSection = document.getElementById("resultSection");
const resultSummary = document.getElementById("resultSummary");
const emptyState = document.getElementById("emptyState");
const checkAllEl = document.getElementById("checkAll");
const btnSelectAll = document.getElementById("btnSelectAll");
const btnMigrate = document.getElementById("btnMigrate");
const btnSearch = document.getElementById("btnSearch");

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadSourceYears();
        await loadTargetClasses();
    } catch (err) {
        alert(err.message);
        console.error(err);
    }

    sourceYearEl.addEventListener("change", async () => {
        await loadSourceClasses();
        await searchStudents();
    });

    filterClassEl.addEventListener("change", searchStudents);
    searchNameEl.addEventListener("input", debounce(searchStudents, 300));
    btnSearch.addEventListener("click", searchStudents);

    checkAllEl.addEventListener("change", (e) => {
        const checked = e.target.checked;
        document.querySelectorAll(".student-check").forEach(cb => cb.checked = checked);
        updateMigrateButton();
    });

    btnSelectAll.addEventListener("click", () => {
        const anyUnchecked = !!document.querySelector(".student-check:not(:checked)");
        document.querySelectorAll(".student-check").forEach(cb => cb.checked = anyUnchecked);
        updateMigrateButton();
    });

    targetClassEl.addEventListener("change", updateMigrateButton);

    btnMigrate.addEventListener("click", async () => {
        const selectedIds = Array.from(document.querySelectorAll(".student-check:checked")).map(cb => parseInt(cb.value));
        if (!selectedIds.length) {
            alert("Selecione pelo menos um aluno.");
            return;
        }
        const targetClassId = parseInt(targetClassEl.value);
        if (!targetClassId) {
            alert("Selecione a turma de destino.");
            return;
        }
        if (!confirm(`Confirma a migração de ${selectedIds.length} aluno(s) para a turma selecionada?`)) return;

        try {
            const result = await migrateStudents(selectedIds, targetClassId);
            showResult(result);
            await searchStudents();
            checkAllEl.checked = false;
            updateMigrateButton();
        } catch (err) {
            alert(err.message);
        }
    });
});

async function loadSourceYears() {
    const years = await listMigrationYears();
    sourceYearEl.innerHTML = years.length
        ? years.map(y => `<option value="${y}">${y}</option>`).join("")
        : `<option value="">Nenhum ano letivo ativo</option>`;
    if (years.length) {
        await loadSourceClasses();
        await searchStudents();
    }
}

async function loadSourceClasses() {
    const year = parseInt(sourceYearEl.value);
    if (!year) {
        filterClassEl.innerHTML = `<option value="">Todas</option>`;
        return;
    }
    const classes = await listMigrationClasses(year);
    filterClassEl.innerHTML = `<option value="">Todas</option>` +
        classes.map(c => `<option value="${c.id}">${c.name}${c.grade ? ` (${c.grade})` : ""}${c.shift_name ? ` - ${c.shift_name}` : ""}</option>`).join("");
}

async function loadTargetClasses() {
    const years = await listMigrationYears();
    for (const year of years) {
        targetClassesByYear[year] = await listMigrationClasses(year);
    }
    renderTargetClasses();
}

function renderTargetClasses() {
    const year = parseInt(sourceYearEl.value);
    const targetYear = year ? year + 1 : null;
    const classes = targetYear ? (targetClassesByYear[targetYear] || []) : [];

    targetClassEl.innerHTML = `<option value="">Selecione a turma de destino</option>` +
        classes.map(c => `<option value="${c.id}">${c.name}${c.grade ? ` (${c.grade})` : ""}${c.shift_name ? ` - ${c.shift_name}` : ""}</option>`).join("");

    if (targetYear) {
        targetYearHintEl.textContent = classes.length
            ? `Ano letivo de destino: ${targetYear}`
            : `Ano letivo de destino ${targetYear} não possui turmas cadastradas. Crie a turma e o ano letivo primeiro.`;
    } else {
        targetYearHintEl.textContent = "";
    }
}

async function searchStudents() {
    const year = parseInt(sourceYearEl.value);
    if (!year) {
        studentsTableBody.innerHTML = "";
        emptyState.classList.add("hidden");
        return;
    }
    const filters = {
        class_id: filterClassEl.value || undefined,
        name: searchNameEl.value.trim() || undefined,
    };
    try {
        const data = await listMigrationStudents(year, filters);
        allStudents = data.students || [];
        filteredStudents = allStudents;
        renderStudents();
        renderTargetClasses();
    } catch (err) {
        alert(err.message);
    }
}

function renderStudents() {
    studentsTableBody.innerHTML = filteredStudents.map(s => `
        <tr>
            <td><input type="checkbox" class="student-check" value="${s.id}"></td>
            <td>${s.registration_code || "-"}</td>
            <td>${s.full_name}</td>
            <td>${s.current_class_name || "-"}</td>
        </tr>
    `).join("");

    emptyState.classList.toggle("hidden", filteredStudents.length > 0);
    btnSelectAll.disabled = filteredStudents.length === 0;
    checkAllEl.checked = false;
    updateMigrateButton();

    document.querySelectorAll(".student-check").forEach(cb => {
        cb.addEventListener("change", () => {
            checkAllEl.checked = !document.querySelector(".student-check:not(:checked)");
            updateMigrateButton();
        });
    });
}

function updateMigrateButton() {
    const hasSelected = document.querySelectorAll(".student-check:checked").length > 0;
    const hasTarget = !!targetClassEl.value;
    btnMigrate.disabled = !(hasSelected && hasTarget);
}

function showResult(result) {
    resultSection.classList.remove("hidden");
    resultSummary.textContent = `Migrados com sucesso: ${result.migrated} | Falhas: ${result.failed}`;
    resultTableBody.innerHTML = result.results.map(r => `
        <tr>
            <td>${r.full_name || `#${r.student_id}`}</td>
            <td>${r.success ? "✅ Migrado" : "❌ Falhou"}</td>
            <td>${r.detail || r.new_class_name || "-"}</td>
        </tr>
    `).join("");
}

function debounce(fn, ms) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), ms);
    };
}
