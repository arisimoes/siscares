let reportClasses = [];

async function loadClassesFilter() {
    try {
        reportClasses = await listClasses();
        renderClassFilter();
    } catch (err) {
        console.error("Erro ao carregar turmas:", err);
    }
}

async function loadAcademicYears() {
    try {
        const me = await getMe();
        if (!me || !me.school_id) return;
        const years = await listAcademicYears(me.school_id);
        const select = document.getElementById("filterYear");
        select.innerHTML = '<option value="">Todos</option>' +
            years.map(y => `<option value="${y.year}">${y.year}</option>`).join("");
        select.addEventListener("change", renderClassFilter);
    } catch (err) {
        console.error("Erro ao carregar anos letivos:", err);
    }
}

(async function init() {
    await loadAcademicYears();
    await loadClassesFilter();
})();

function renderClassFilter() {
    const yearFilter = document.getElementById("filterYear")?.value || "";
    const classes = yearFilter
        ? reportClasses.filter(c => String(c.year) === yearFilter)
        : reportClasses;
    const select = document.getElementById("filterClass");
    const current = select.value;
    select.innerHTML = '<option value="">Todas</option>' +
        classes.map(c => `<option value="${c.id}">${c.name} (${c.grade || "-"}) - ${c.year}</option>`).join("");
    if (classes.some(c => String(c.id) === current)) {
        select.value = current;
    } else {
        select.value = "";
    }
}

async function loadReport() {
    const month = document.getElementById("month").value;
    const table = document.getElementById("reportTable");
    const tbody = document.getElementById("reportBody");
    const yearFilter = document.getElementById("filterYear")?.value || "";
    const bolsaValue = document.getElementById("filterBolsa")?.value || "";
    const filters = {
        class_id: document.getElementById("filterClass").value || undefined,
        day: document.getElementById("filterDay").value || undefined,
        student_name: document.getElementById("filterStudent").value.trim() || undefined,
        bolsa_familia: bolsaValue === "" ? undefined : bolsaValue,
    };
    try {
        const report = await getFrequencyReport(month, filters);
        let items = report.items || [];
        if (yearFilter) {
            items = items.filter(i => String(i.class_year || "").includes(yearFilter));
        }
        tbody.innerHTML = items.map(i => {
            const boldClass = i.bolsa_familia ? "bolsa-bold" : "";
            return `
            <tr class="${boldClass}">
                <td>${i.class_name}</td>
                <td>${i.student_name}</td>
                <td>${i.total_classes}</td>
                <td>${i.present_count}</td>
                <td>${i.absent_count}</td>
                <td>${i.justified_count}</td>
                <td>${i.frequency_percentage}%</td>
            </tr>`;
        }).join("");
        table.style.display = "table";
        updatePrintHeader(items, filters, month);
    } catch (err) {
        alert(err.message);
    }
}

function updatePrintHeader(items, filters, month) {
    const header = document.getElementById("printHeader");
    const printFilters = document.getElementById("printFilters");
    if (!header || !printFilters) return;

    const classSelect = document.getElementById("filterClass");
    const classText = classSelect?.value ? classSelect.selectedOptions[0].text : "Todas";
    const yearText = document.getElementById("filterYear")?.value || "Todos";
    const dayText = filters.day || "Todo o mês";
    const bolsaText = filters.bolsa_familia === "true" ? "Sim" : filters.bolsa_familia === "false" ? "Não" : "Nenhum";

    printFilters.innerHTML = `
        Mês: ${month} | Ano letivo: ${yearText} | Turma: ${classText} | Dia: ${dayText} | Bolsa Família: ${bolsaText}
        \u003cbr\u003eTotal de alunos: ${items.length}
    `;
}

document.getElementById("month").value = new Date().toISOString().slice(0, 7);
