async function loadClassesFilter() {
    const select = document.getElementById("filterClass");
    try {
        const classes = await listClasses();
        select.innerHTML = '<option value="">Todas</option>' +
            classes.map(c => `<option value="${c.id}">${c.name} (${c.grade || "-"})</option>`).join("");
    } catch (err) {
        console.error("Erro ao carregar turmas:", err);
    }
}

async function loadReport() {
    const month = document.getElementById("month").value;
    const table = document.getElementById("reportTable");
    const tbody = document.getElementById("reportBody");
    const filters = {
        class_id: document.getElementById("filterClass").value || undefined,
        day: document.getElementById("filterDay").value || undefined,
        student_name: document.getElementById("filterStudent").value.trim() || undefined,
    };
    try {
        const report = await getFrequencyReport(month, filters);
        tbody.innerHTML = report.items.map(i => `
            <tr>
                <td>${i.class_name}</td>
                <td>${i.student_name}</td>
                <td>${i.total_classes}</td>
                <td>${i.present_count}</td>
                <td>${i.absent_count}</td>
                <td>${i.justified_count}</td>
                <td>${i.frequency_percentage}%</td>
            </tr>
        `).join("");
        table.style.display = "table";
    } catch (err) {
        alert(err.message);
    }
}

document.getElementById("month").value = new Date().toISOString().slice(0, 7);
loadClassesFilter();
