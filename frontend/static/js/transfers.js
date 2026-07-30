document.addEventListener("DOMContentLoaded", async () => {
    const [students, classes] = await Promise.all([listStudents(), listClasses()]);

    const studentSelect = document.getElementById("student_id");
    const classSelect = document.getElementById("to_class_id");

    const studentMap = Object.fromEntries(students.map(s => [s.id, s]));

    function renderClasses(selectedStudentId) {
        const currentStudent = studentMap[selectedStudentId];
        const currentClassId = currentStudent ? currentStudent.class_id : null;

        classSelect.innerHTML = '<option value="">Transferência externa (sem turma)</option>' +
            classes.map(c => {
                const isCurrent = c.id === currentClassId;
                const label = isCurrent ? `${c.name} (${c.grade || "-"}) — Atual` : `${c.name} (${c.grade || "-"})`;
                return `<option value="${c.id}" ${isCurrent ? "disabled" : ""}>${label}</option>`;
            }).join("");
    }

    studentSelect.innerHTML = students.map(s => `
        <option value="${s.id}">${s.full_name} — ${s.class_name || "Sem turma"}</option>
    `).join("");

    studentSelect.addEventListener("change", (e) => {
        renderClasses(parseInt(e.target.value));
    });

    // initial render for first student
    if (students.length) {
        renderClasses(students[0].id);
    }

    document.getElementById("transferForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = {
            student_id: parseInt(document.getElementById("student_id").value),
            to_class_id: document.getElementById("to_class_id").value ? parseInt(document.getElementById("to_class_id").value) : null,
            transfer_type: document.getElementById("transfer_type").value,
            reason: document.getElementById("reason").value || null,
        };
        try {
            await createTransfer(data);
            alert("Transferência registrada");
            window.location.reload();
        } catch (err) {
            alert(err.message);
        }
    });
});
