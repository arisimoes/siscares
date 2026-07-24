const API_BASE = "/api/v1";

function getToken() {
    return localStorage.getItem("token");
}

async function api(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/static/pages/login.html";
        return;
    }
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Erro ${res.status}`);
    }
    return res.status === 204 ? null : res.json();
}

async function getMe() {
    return api("/auth/me");
}

async function login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: email, password }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Login inválido");
    }
    return res.json();
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/static/pages/login.html";
}

async function listSchools() { return api("/schools"); }
async function createSchool(data) { return api("/schools", { method: "POST", body: JSON.stringify(data) }); }
async function updateSchool(id, data) { return api(`/schools/${id}`, { method: "PUT", body: JSON.stringify(data) }); }

async function listClasses() { return api("/classes"); }
async function createClass(data) { return api("/classes", { method: "POST", body: JSON.stringify(data) }); }

async function listShifts() { return api("/classes/shifts"); }
async function createShift(data) { return api("/classes/shifts", { method: "POST", body: JSON.stringify(data) }); }

async function listStudents(classId) {
    const query = classId ? `?class_id=${classId}` : "";
    return api(`/students${query}`);
}
async function createStudent(data) { return api("/students", { method: "POST", body: JSON.stringify(data) }); }
async function getStudentCard(id) { return api(`/students/${id}/card`); }

async function registerAttendance(data) { return api("/attendance", { method: "POST", body: JSON.stringify(data) }); }
async function getFrequencyReport(month) { return api(`/reports/frequency?month=${month}`); }

async function listModules() { return api("/modules"); }
async function listSchoolModules(schoolId) { return api(`/modules/school/${schoolId}`); }
async function toggleModule(schoolId, moduleId, isEnabled) {
    return api(`/modules/school/${schoolId}/${moduleId}?is_enabled=${isEnabled}`, { method: "POST" });
}

async function createTransfer(data) { return api("/transfers", { method: "POST", body: JSON.stringify(data) }); }
async function listTransfers(studentId) { return api(`/transfers/student/${studentId}`); }

async function listUsers() { return api("/auth/users"); }
async function createUser(data) { return api("/auth/users", { method: "POST", body: JSON.stringify(data) }); }
async function updateUser(id, data) { return api(`/auth/users/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
