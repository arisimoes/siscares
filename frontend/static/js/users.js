let currentUser = null;
let allUsers = [];
let currentPermissions = {
    manage_classes: false,
    manage_students: false,
    manage_cards: false,
    manage_attendance: false,
    manage_reports: false,
    manage_transfers: false,
    manage_users: false,
    manage_calendar: false,
    manage_logs: false,
};

const PERM_FIELDS = [
    { key: "manage_classes", id: "perm_classes" },
    { key: "manage_students", id: "perm_students" },
    { key: "manage_cards", id: "perm_cards" },
    { key: "manage_attendance", id: "perm_attendance" },
    { key: "manage_reports", id: "perm_reports" },
    { key: "manage_transfers", id: "perm_transfers" },
    { key: "manage_users", id: "perm_users" },
    { key: "manage_calendar", id: "perm_calendar" },
    { key: "manage_logs", id: "perm_logs" },
];

async function init() {
    currentUser = await getMe();
    if (!currentUser || !["school_admin", "secretary"].includes(currentUser.role)) {
        alert("Acesso restrito. Apenas diretores e secretarias podem gerenciar administrativo.");
        window.location.href = "/static/pages/index.html";
        return;
    }
    await loadUsers();
    document.getElementById("userForm").addEventListener("submit", saveUser);
    togglePermissionBtn();

    // Ao mudar de papel, limpar permissões apenas se for novo cadastro
    document.getElementById("role").addEventListener("change", () => {
        if (!document.getElementById("userId").value) {
            resetCurrentPermissions();
        }
        togglePermissionBtn();
    });
}

async function loadUsers() {
    const users = await listUsers();
    allUsers = users.filter(u => {
        return u.school_id === currentUser.school_id && !["super_admin", "school_admin"].includes(u.role);
    });
    renderUsers();
}

function renderUsers() {
    const tbody = document.querySelector("#usersTable tbody");
    tbody.innerHTML = allUsers.map(u => `
        <tr>
            <td>${u.full_name}</td>
            <td>${u.email}</td>
            <td>${roleLabel(u.role)}</td>
            <td>${u.is_active ? "Sim" : "Não"}</td>
            <td>
                <button onclick="editUser(${u.id})">Editar</button>
                <button onclick="toggleUserActive(${u.id}, ${!u.is_active})">${u.is_active ? "Desativar" : "Ativar"}</button>
            </td>
        </tr>
    `).join("");
}

function roleLabel(role) {
    const labels = {
        staff: "Administrativo",
        secretary: "Secretaria",
        school_admin: "Diretor",
        super_admin: "Super Admin",
    };
    return labels[role] || role;
}

function togglePermissionBtn() {
    const role = document.getElementById("role").value;
    document.getElementById("permBtn").style.display = role === "school_admin" ? "none" : "inline-block";
}

window.openPermissionsModal = function() {
    PERM_FIELDS.forEach(({ key, id }) => {
        document.getElementById(id).checked = currentPermissions[key] || false;
    });
    document.getElementById("permissionsModal").classList.remove("hidden");
};

window.closePermissionsModal = function() {
    document.getElementById("permissionsModal").classList.add("hidden");
};

window.savePermissionsFromModal = function() {
    PERM_FIELDS.forEach(({ key, id }) => {
        currentPermissions[key] = document.getElementById(id).checked;
    });
    closePermissionsModal();
};

async function saveUser(e) {
    e.preventDefault();
    const id = document.getElementById("userId").value;
    const role = document.getElementById("role").value;
    const payload = {
        full_name: document.getElementById("full_name").value,
        email: document.getElementById("email").value,
        role: role,
        school_id: currentUser.school_id,
        permissions: { ...currentPermissions },
    };
    const password = document.getElementById("password").value;
    if (password) payload.password = password;

    try {
        if (id) {
            await updateUser(id, payload);
        } else {
            await createUser(payload);
        }
        resetForm();
        await loadUsers();
    } catch (err) {
        alert(err.message);
    }
}

window.editUser = function(id) {
    const u = allUsers.find(x => x.id === id);
    if (!u) return;
    document.getElementById("userId").value = u.id;
    document.getElementById("full_name").value = u.full_name;
    document.getElementById("email").value = u.email;
    document.getElementById("role").value = u.role;
    document.getElementById("password").value = "";

    resetCurrentPermissions();
    if (u.permissions) {
        Object.keys(currentPermissions).forEach(k => currentPermissions[k] = !!u.permissions[k]);
    }
    togglePermissionBtn();
};

window.toggleUserActive = async function(id, isActive) {
    if (!confirm(isActive ? "Ativar usuário?" : "Desativar usuário?")) return;
    try {
        await updateUser(id, { is_active: isActive });
        await loadUsers();
    } catch (err) {
        alert(err.message);
    }
};

window.resetForm = function() {
    document.getElementById("userForm").reset();
    document.getElementById("userId").value = "";
    resetCurrentPermissions();
    togglePermissionBtn();
};

function resetCurrentPermissions() {
    currentPermissions = {
        manage_classes: false,
        manage_students: false,
        manage_cards: false,
        manage_attendance: false,
        manage_reports: false,
        manage_transfers: false,
        manage_users: false,
        manage_calendar: false,
        manage_logs: false,
    };
}

document.addEventListener("DOMContentLoaded", init);
