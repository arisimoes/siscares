const MODULE_LINKS = {
    manage_classes: "/static/pages/classes.html",
    manage_students: "/static/pages/students.html",
    manage_cards: "/static/pages/card.html",
    manage_attendance: "/static/pages/attendance.html",
    manage_reports: "/static/pages/reports.html",
    manage_transfers: "/static/pages/transfers.html",
    manage_users: "/static/pages/users.html",
};

async function initDashboard() {
    const me = await getMe();
    if (!me) return;

    document.getElementById("userName").textContent = `${me.full_name} (${me.role})`;

    if (me.role === "super_admin") {
        document.getElementById("admin-modules")?.classList.remove("hidden");
        document.querySelectorAll('.cards a.card').forEach(link => {
            const href = link.getAttribute('href');
            if (href !== '/static/pages/schools.html' && href !== '/static/pages/users.html') {
                link.classList.add('hidden');
            }
        });
        loadModuleSchoolList();
    } else {
        // Gestores escolares não gerenciam escolas
        document.getElementById("nav-schools")?.classList.add("hidden");
    }

    // Esconde cards que o usuário não tem permissão, exceto gestores/super_admin
    if (me.role !== "school_admin" && me.role !== "super_admin") {
        document.querySelectorAll(".cards a.card").forEach(link => {
            const href = link.getAttribute("href");
            const hasPermission = Object.entries(MODULE_LINKS).some(([perm, url]) => {
                return url === href && me.permissions && me.permissions[perm];
            });
            if (!hasPermission) {
                link.classList.add("hidden");
            }
        });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
} else {
    initDashboard();
}

async function loadModuleSchoolList() {
    const container = document.getElementById("moduleSchoolList");
    try {
        const schools = await listSchools();
        const modules = await listModules();
        container.innerHTML = "";

        for (const school of schools) {
            const settings = await listSchoolModules(school.id);
            const div = document.createElement("div");
            div.className = "card";
            div.innerHTML = `
                <h4>${school.name}</h4>
                <form onsubmit="event.preventDefault(); return false;">
                    ${modules.map(m => {
                        const setting = settings.find(s => s.module.id === m.id);
                        const enabled = setting ? setting.is_enabled : m.is_core;
                        return `
                            <label>
                                <input type="checkbox" ${m.is_core ? "disabled" : ""} ${enabled ? "checked" : ""}
                                    onchange="toggleSchoolModule(${school.id}, ${m.id}, this.checked)">
                                ${m.name}
                            </label>
                        `;
                    }).join("")}
                </form>
            `;
            container.appendChild(div);
        }
    } catch (err) {
        container.innerHTML = `<p class="error">${err.message}</p>`;
    }
}

async function toggleSchoolModule(schoolId, moduleId, isEnabled) {
    try {
        await toggleModule(schoolId, moduleId, isEnabled);
    } catch (err) {
        alert(err.message);
    }
}

const token = localStorage.getItem("token");
if (!token && !window.location.pathname.includes("login")) {
    window.location.href = "/static/pages/login.html";
}
