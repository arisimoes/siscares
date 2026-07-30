let currentUser = null;
let allManagers = [];
let schools = [];

async function init() {
    currentUser = await getMe();
    if (!currentUser || currentUser.role !== "super_admin") {
        alert("Acesso restrito. Apenas administradores podem gerenciar gestores.");
        window.location.href = "/static/pages/index.html";
        return;
    }
    await loadSchools();
    await loadManagers();
    document.getElementById("managerForm").addEventListener("submit", saveManager);
}

async function loadSchools() {
    schools = await listSchools();
    const select = document.getElementById("school_id");
    select.innerHTML = '<option value="">Selecione a escola</option>' +
        schools.map(s => `<option value="${s.id}">${s.name}</option>`).join("");
}

async function loadManagers() {
    allManagers = await listManagers();
    renderManagers();
}

function renderManagers() {
    const tbody = document.querySelector("#managersTable tbody");
    tbody.innerHTML = allManagers.map(m => {
        const school = schools.find(s => s.id === m.school_id);
        return `
        <tr>
            <td>${m.full_name}</td>
            <td>${m.email}</td>
            <td>${school ? school.name : "-"}</td>
            <td>${m.is_active ? "Sim" : "Não"}</td>
            <td>
                <button onclick="editManager(${m.id})">Editar</button>
                <button onclick="toggleManagerActive(${m.id}, ${!m.is_active})">${m.is_active ? "Desativar" : "Ativar"}</button>
            </td>
        </tr>
        `;
    }).join("");
}

async function saveManager(e) {
    e.preventDefault();
    const id = document.getElementById("managerId").value;
    const payload = {
        full_name: document.getElementById("full_name").value,
        email: document.getElementById("email").value,
        role: "school_admin",
        school_id: parseInt(document.getElementById("school_id").value, 10),
    };
    const password = document.getElementById("password").value;
    if (password) payload.password = password;

    try {
        if (id) {
            await updateManager(id, payload);
        } else {
            await createManager(payload);
        }
        resetForm();
        await loadManagers();
    } catch (err) {
        alert(err.message);
    }
}

window.editManager = function(id) {
    const m = allManagers.find(x => x.id === id);
    if (!m) return;
    document.getElementById("managerId").value = m.id;
    document.getElementById("full_name").value = m.full_name;
    document.getElementById("email").value = m.email;
    document.getElementById("school_id").value = m.school_id || "";
    document.getElementById("password").value = "";
};

window.toggleManagerActive = async function(id, isActive) {
    if (!confirm(isActive ? "Ativar gestor?" : "Desativar gestor?")) return;
    try {
        await updateManager(id, { is_active: isActive });
        await loadManagers();
    } catch (err) {
        alert(err.message);
    }
};

window.resetForm = function() {
    document.getElementById("managerForm").reset();
    document.getElementById("managerId").value = "";
};

document.addEventListener("DOMContentLoaded", init);
