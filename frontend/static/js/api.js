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

async function login(loginValue, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login: loginValue, password }),
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
async function deleteSchool(id) { return api(`/schools/${id}`, { method: "DELETE" }); }

async function listClasses() { return api("/classes"); }
async function createClass(data) { return api("/classes", { method: "POST", body: JSON.stringify(data) }); }
async function updateClass(id, data) { return api(`/classes/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
async function deleteClass(id) { return api(`/classes/${id}`, { method: "DELETE" }); }

async function listShifts() { return api("/classes/shifts"); }
async function createShift(data) { return api("/classes/shifts", { method: "POST", body: JSON.stringify(data) }); }

async function listStudents(filters = {}) {
    const params = new URLSearchParams();
    if (filters.class_id) params.set("class_id", filters.class_id);
    if (filters.name) params.set("name", filters.name);
    if (filters.shift_id) params.set("shift_id", filters.shift_id);
    const query = params.toString() ? `?${params.toString()}` : "";
    return api(`/students${query}`);
}
async function createStudent(data) { return api("/students", { method: "POST", body: JSON.stringify(data) }); }
async function updateStudent(id, data) { return api(`/students/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
async function deleteStudent(id, password) { return api(`/students/${id}`, { method: "DELETE", body: JSON.stringify({ password }) }); }
async function getStudentCard(id) { return api(`/students/${id}/card`); }
async function createTemporaryCard(studentId) { return api(`/students/${studentId}/temporary-card`, { method: "POST" }); }

async function registerAttendance(data) { return api("/attendance", { method: "POST", body: JSON.stringify(data) }); }
async function justifyAbsence(studentId, data) { return api(`/attendance/justify/${studentId}`, { method: "POST", body: JSON.stringify(data) }); }
async function getFrequencyReport(month, filters = {}) {
    const params = new URLSearchParams({ month });
    if (filters.class_id) params.set("class_id", filters.class_id);
    if (filters.day) params.set("day", filters.day);
    if (filters.student_name) params.set("student_name", filters.student_name);
    if (filters.bolsa_familia !== undefined && filters.bolsa_familia !== "") params.set("bolsa_familia", filters.bolsa_familia);
    return api(`/reports/frequency?${params.toString()}`);
}

async function listModules() { return api("/modules"); }
async function listSchoolModules(schoolId) { return api(`/modules/school/${schoolId}`); }
async function listLogs() { return api("/logs/records"); }
async function toggleModule(schoolId, moduleId, isEnabled) {
    return api(`/modules/school/${schoolId}/${moduleId}?is_enabled=${isEnabled}`, { method: "POST" });
}

async function createTransfer(data) { return api("/transfers", { method: "POST", body: JSON.stringify(data) }); }
async function listTransfers(studentId) { return api(`/transfers/student/${studentId}`); }

async function listUsers() { return api("/auth/users"); }
async function createUser(data) { return api("/auth/users", { method: "POST", body: JSON.stringify(data) }); }
async function updateUser(id, data) { return api(`/auth/users/${id}`, { method: "PUT", body: JSON.stringify(data) }); }

async function listManagers() { return api("/auth/managers"); }
async function createManager(data) { return api("/auth/managers", { method: "POST", body: JSON.stringify(data) }); }
async function updateManager(id, data) { return api(`/auth/managers/${id}`, { method: "PUT", body: JSON.stringify(data) }); }

async function uploadSchoolPhoto(schoolId, file) {
    const formData = new FormData();
    formData.append("file", file);
    const token = getToken();
    const res = await fetch(`${API_BASE}/uploads/school/${schoolId}/photo`, {
        method: "POST",
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
        body: formData,
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Erro ${res.status}`);
    }
    return res.json();
}

async function removeSchoolPhotoApi(schoolId) {
    return api(`/uploads/school/${schoolId}/photo`, { method: "DELETE" });
}

async function listAcademicYears(schoolId) { return api(`/calendar/school/${schoolId}/years`); }
async function createAcademicYear(schoolId, data) { return api(`/calendar/school/${schoolId}/years`, { method: "POST", body: JSON.stringify(data) }); }
async function updateAcademicYear(schoolId, yearId, data) { return api(`/calendar/school/${schoolId}/years/${yearId}`, { method: "PUT", body: JSON.stringify(data) }); }
async function listCalendarDays(schoolId, year) { return api(`/calendar/school/${schoolId}/days?year=${year}`); }
async function saveCalendarDay(schoolId, data) { return api(`/calendar/school/${schoolId}/days`, { method: "POST", body: JSON.stringify(data) }); }
async function updateCalendarDay(schoolId, dayId, data) { return api(`/calendar/school/${schoolId}/days/${dayId}`, { method: "PUT", body: JSON.stringify(data) }); }
async function deleteCalendarDay(schoolId, dayId) { return api(`/calendar/school/${schoolId}/days/${dayId}`, { method: "DELETE" }); }
async function generateDefaultCalendar(schoolId, year) { return api(`/calendar/school/${schoolId}/generate/${year}`, { method: "POST" }); }
