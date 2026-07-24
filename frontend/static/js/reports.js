async function loadReport() {
    const month = document.getElementById("month").value;
    const table = document.getElementById("reportTable");
    const tbody = document.getElementById("reportBody");
    try {
        const report = await getFrequencyReport(month);
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
