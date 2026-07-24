document.addEventListener("DOMContentLoaded", async () => {
    await loadClasses();
    await loadStudents();

    document.getElementById("studentForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = {
            full_name: document.getElementById("full_name").value,
            birth_date: document.getElementById("birth_date").value || null,
            cpf: document.getElementById("cpf").value || null,
            registration_code: document.getElementById("registration_code").value || null,
            class_id: parseInt(document.getElementById("class_id").value),
        };
        try {
            await createStudent(data);
            e.target.reset();
            await loadStudents();
        } catch (err) {
            alert(err.message);
        }
    });
});

async function loadClasses() {
    const classes = await listClasses();
    const select = document.getElementById("class_id");
    select.innerHTML = classes.map(c => `<option value="${c.id}">${c.name} (${c.grade})</option>`).join("");
}

async function loadStudents() {
    const students = await listStudents();
    const tbody = document.getElementById("studentsTable");
    tbody.innerHTML = students.map(s => `
        <tr>
            <td>${s.full_name}</td>
            <td>${s.class_id || "-"}</td>
            <td>${s.registration_code || "-"}</td>
            <td><a class="btn" href="/static/pages/card.html?student_id=${s.id}">Ver carteirinha</a></td>
        </tr>
    `).join("");
}
