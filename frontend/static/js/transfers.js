document.addEventListener("DOMContentLoaded", async () => {
    const [students, classes] = await Promise.all([listStudents(), listClasses()]);

    document.getElementById("student_id").innerHTML = students.map(s => `
        <option value="${s.id}">${s.full_name}</option>
    `).join("");

    const classSelect = document.getElementById("to_class_id");
    classSelect.innerHTML += classes.map(c => `
        <option value="${c.id}">${c.name}</option>
    `).join("");

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
            e.target.reset();
        } catch (err) {
            alert(err.message);
        }
    });
});
