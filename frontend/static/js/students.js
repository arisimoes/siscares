document.addEventListener("DOMContentLoaded", async () => {
    await loadClasses();
    await loadFilterClasses();
    await loadStudents();

    document.getElementById("studentForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const studentId = document.getElementById("student_id").value;
        const data = {
            full_name: document.getElementById("full_name").value,
            birth_date: document.getElementById("birth_date").value || null,
            cpf: document.getElementById("cpf").value || null,
            registration_code: document.getElementById("registration_code").value || null,
            class_id: parseInt(document.getElementById("class_id").value),
            bolsa_familia: document.getElementById("bolsa_familia").checked,
        };
        try {
            if (studentId) {
                await updateStudent(studentId, data);
            } else {
                await createStudent(data);
            }
            resetForm();
            await loadStudents();
        } catch (err) {
            alert(err.message);
        }
    });

    document.getElementById("cancelEdit").addEventListener("click", resetForm);
});

async function loadClasses() {
    const classes = await listClasses();
    const select = document.getElementById("class_id");
    select.innerHTML = classes.map(c => `<option value="${c.id}">${c.name} (${c.grade})</option>`).join("");
}

async function loadFilterClasses() {
    const classes = await listClasses();
    const select = document.getElementById("filterClass");
    select.innerHTML = '<option value="">Todas</option>' +
        classes.map(c => `<option value="${c.id}">${c.name} (${c.grade})</option>`).join("");
}

async function loadStudents() {
    const classFilter = document.getElementById("filterClass").value;
    const nameFilter = document.getElementById("filterName").value.trim();
    const filters = {};
    if (classFilter) filters.class_id = classFilter;
    if (nameFilter) filters.name = nameFilter;
    const students = await listStudents(filters);
    students.sort((a, b) => a.full_name.localeCompare(b.full_name, "pt-BR", { sensitivity: "base" }));
    const tbody = document.getElementById("studentsTable");
    tbody.innerHTML = students.map(s => `
        <tr>
            <td>${s.full_name}</td>
            <td>${s.class_name || (s.class_id || "-")}</td>
            <td>${s.registration_code || "-"}</td>
            <td>${s.bolsa_familia ? "Sim" : "Não"}</td>
            <td class="actions">
                <button class="btn-justify" onclick="openJustifyModal(${s.id}, '${escapeHtml(s.full_name)}')">Justificar</button>
                <a class="btn" href="/static/pages/card.html?student_id=${s.id}">Carteirinha</a>
                <button class="btn-secondary" onclick="editStudent(${s.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(s.birth_date || "")}', '${escapeHtml(s.cpf || "")}', '${escapeHtml(s.registration_code || "")}', ${s.class_id || 'null'}, ${s.bolsa_familia})">Editar</button>
                <button class="btn-danger" onclick="deleteStudentItem(${s.id})">Excluir</button>
            </td>
        </tr>
    `).join("");
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/\u003c/g, "\u0026lt;")
        .replace(/\u003e/g, "\u0026gt;")
        .replace(/"/g, "\u0026quot;")
        .replace(/'/g, "\u0026#039;")
        .replace(/\u0026/g, "\u0026amp;");
}

window.openJustifyModal = function(studentId, fullName) {
    document.getElementById("justifyStudentId").value = studentId;
    document.getElementById("justifyStudentName").textContent = fullName;
    document.getElementById("justifyDate").value = "";
    document.getElementById("justifyText").value = "";
    document.getElementById("justifyModal").classList.remove("hidden");
};

window.closeJustifyModal = function() {
    document.getElementById("justifyModal").classList.add("hidden");
};

window.submitJustification = async function() {
    const studentId = document.getElementById("justifyStudentId").value;
    const date = document.getElementById("justifyDate").value;
    const justification = document.getElementById("justifyText").value.trim();
    if (!date || !justification) {
        alert("Preencha a data e a justificativa.");
        return;
    }
    try {
        await justifyAbsence(studentId, { date, justification });
        alert("Falta justificada com sucesso.");
        closeJustifyModal();
    } catch (err) {
        alert(err.message || "Erro ao justificar falta.");
    }
};

window.editStudent = async function(id, full_name, birth_date, cpf, registration_code, class_id, bolsa_familia) {
    document.getElementById("student_id").value = id;
    document.getElementById("full_name").value = full_name;
    document.getElementById("birth_date").value = birth_date || "";
    document.getElementById("cpf").value = cpf || "";
    document.getElementById("registration_code").value = registration_code || "";
    document.getElementById("class_id").value = class_id || "";
    document.getElementById("bolsa_familia").checked = !!bolsa_familia;
    document.getElementById("submitBtn").textContent = "Salvar";
    document.getElementById("cancelEdit").classList.remove("hidden");
    window.scrollTo({ top: document.getElementById("studentForm").offsetTop - 80, behavior: "smooth" });
};

window.deleteStudentItem = async function(id) {
    const password = prompt("Digite sua senha para confirmar a exclusão:");
    if (!password) return;
    if (!confirm("Deseja realmente excluir este aluno?")) return;
    try {
        await deleteStudent(id, password);
        await loadStudents();
    } catch (err) {
        alert(err.message);
    }
};

window.applyFilters = async function() {
    await loadStudents();
};

function resetForm() {
    const form = document.getElementById("studentForm");
    form.reset();
    document.getElementById("student_id").value = "";
    document.getElementById("submitBtn").textContent = "Cadastrar";
    document.getElementById("cancelEdit").classList.add("hidden");
}
