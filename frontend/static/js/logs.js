async function loadLogs() {
    try {
        const typeFilter = document.getElementById("filterType").value.toLowerCase();
        const studentFilter = document.getElementById("filterStudent").value.trim().toLowerCase();

        const logs = await listLogs();
        const filtered = logs.filter(log => {
            if (typeFilter && log.type.toLowerCase() !== typeFilter) return false;
            if (studentFilter && !log.student_name.toLowerCase().includes(studentFilter)) return false;
            return true;
        });

        const tbody = document.getElementById("logsTable");
        if (!filtered.length) {
            tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Nenhum registro encontrado.</td></tr>`;
            return;
        }

        tbody.innerHTML = filtered.map(log => {
            const date = new Date(log.registered_at).toLocaleString("pt-BR", { timeZone: "UTC" });
            const isTransfer = log.type.toLowerCase() === "transferência";
            return `
                <tr>
                    <td>${date}</td>
                    <td>${log.type}</td>
                    <td>${escapeHtml(log.student_name)}</td>
                    <td>${isTransfer ? escapeHtml(log.from_class_name || "-") : "-"}</td>
                    <td>${isTransfer ? escapeHtml(log.to_class_name || "-") : "-"}</td>
                    <td>${log.date ? formatDate(log.date) : "-"}</td>
                    <td>${escapeHtml(log.reason || "-")}</td>
                    <td>${escapeHtml(log.registered_by_name || "-")}</td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        document.getElementById("logsTable").innerHTML = `<tr><td colspan="8" class="error">${err.message}</td></tr>`;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return "-";
    const [y, m, d] = dateStr.split("-");
    return `${d}/${m}/${y}`;
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/&/g, "&amp;");
}

function applyFilters() {
    loadLogs();
}

document.addEventListener("DOMContentLoaded", loadLogs);
