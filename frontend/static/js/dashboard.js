const MODULE_LINKS = {
    manage_classes: "/static/pages/classes.html",
    manage_students: "/static/pages/students.html",
    manage_cards: "/static/pages/card.html",
    manage_attendance: "/static/pages/attendance.html",
    manage_reports: "/static/pages/reports.html",
    manage_transfers: "/static/pages/transfers.html",
    manage_users: "/static/pages/users.html",
    manage_calendar: "/static/pages/calendar.html",
    manage_logs: "/static/pages/logs.html",
};

const MODULE_CODE_TO_CARD = {
    cards: "nav-card",
    attendance: "nav-attendance",
    reports: "nav-reports",
    transfers: "nav-transfers",
    calendar: "nav-calendar",
    logs: "nav-logs",
};

const CORE_CODE_TO_CARD = {
    core: ["nav-users", "nav-classes", "nav-students"],
};

async function initDashboard() {
    const me = await getMe();
    console.log("Dashboard - usuário:", me);
    if (!me) return;

    document.getElementById("userName").textContent = `${me.full_name} (${me.role})`;

    // Carrega módulos habilitados da escola do usuário para exibir cards corretos
    let enabledModules = [];
    if (me.school_id) {
        try {
            const settings = await listSchoolModules(me.school_id);
            console.log("Dashboard - módulos habilitados:", settings);
            enabledModules = settings.filter(s => s.is_enabled).map(s => s.module.code);
        } catch (err) {
            console.error("Erro ao carregar módulos da escola:", err);
        }
    }

    if (me.role === "super_admin") {
        document.getElementById("admin-modules")?.classList.remove("hidden");
        document.querySelectorAll('.cards a.card').forEach(link => {
            const href = link.getAttribute('href');
            if (href !== '/static/pages/schools.html' && href !== '/static/pages/managers.html') {
                link.classList.add('hidden');
            }
        });
        loadModuleSchoolList();
    } else {
        // Controla visibilidade dos cards de módulos opcionais para gestores escolares
        document.querySelectorAll('.cards a.card').forEach(link => {
            const moduleCode = Object.keys(MODULE_CODE_TO_CARD).find(code => link.id === MODULE_CODE_TO_CARD[code]);
            if (moduleCode) {
                link.classList.toggle('hidden', !enabledModules.includes(moduleCode));
            }
        });

        // Controla visibilidade dos cards do módulo core
        Object.values(CORE_CODE_TO_CARD).flat().forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.toggle('hidden', !enabledModules.includes("core"));
            }
        });

        // Gestores escolares não gerenciam escolas nem gestores
        document.getElementById("nav-schools")?.classList.add("hidden");
        document.getElementById("nav-managers")?.classList.add("hidden");
    }

    // Esconde cards que o usuário não tem permissão granular, exceto gestores/super_admin
    if (me.role !== "school_admin" && me.role !== "super_admin") {
        document.querySelectorAll(".cards a.card").forEach(link => {
            const href = link.getAttribute("href");
            const hasPermission = Object.entries(MODULE_LINKS).some(([perm, url]) => {
                return url === href && me.permissions && me.permissions[perm];
            });
            console.log("Card", href, "hasPermission", hasPermission);
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

        // Separate core and optional modules
        const coreModules = modules.filter(m => m.is_core);
        const optionalModules = modules.filter(m => !m.is_core);

        for (const school of schools) {
            const settings = await listSchoolModules(school.id);

            const card = document.createElement("div");
            card.className = "module-school-card";
            card.innerHTML = `
                <div class="module-school-header">
                    <div class="module-school-name">${school.name}</div>
                    <div class="module-school-sub">${school.city || ""} ${school.state || ""}</div>
                </div>
                <div class="module-section">
                    <div class="module-section-title">Módulos principais (sempre ativos)</div>
                    <div class="module-list">
                        ${coreModules.map(m => `
                            <label class="module-item module-item-core" title="${m.description || ""}">
                                <input type="checkbox" checked disabled>
                                <span>${m.name}</span>
                            </label>
                        `).join("")}
                    </div>
                </div>
                <div class="module-section">
                    <div class="module-section-title">Módulos opcionais</div>
                    <div class="module-list">
                        ${optionalModules.map(m => {
                            const setting = settings.find(s => s.module.id === m.id);
                            const enabled = setting ? setting.is_enabled : false;
                            return `
                                <label class="module-item" title="${m.description || ""}">
                                    <input type="checkbox" ${enabled ? "checked" : ""}
                                        onchange="toggleSchoolModule(${school.id}, ${m.id}, this.checked)"
                                        data-school="${school.id}" data-module="${m.id}">
                                    <span>${m.name}</span>
                                </label>
                            `;
                        }).join("")}
                    </div>
                </div>
            `;
            container.appendChild(card);
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
