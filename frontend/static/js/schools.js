document.addEventListener("DOMContentLoaded", async () => {
    await loadSchools();

    document.getElementById("schoolPhoto").addEventListener("change", previewPhoto);

    document.getElementById("schoolForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const schoolId = document.getElementById("school_id").value;
        const data = {
            name: document.getElementById("name").value,
            cnpj: document.getElementById("cnpj").value || null,
            phone: document.getElementById("phone").value || null,
            city: document.getElementById("city").value || null,
            state: document.getElementById("state").value || null,
            is_active: document.getElementById("is_active").checked,
        };
        try {
            if (schoolId) {
                await updateSchool(schoolId, data);
                const fileInput = document.getElementById("schoolPhoto");
                if (fileInput.files.length) {
                    await uploadSchoolPhoto(schoolId, fileInput.files[0]);
                }
            } else {
                const created = await createSchool(data);
                const fileInput = document.getElementById("schoolPhoto");
                if (created && created.id && fileInput.files.length) {
                    await uploadSchoolPhoto(created.id, fileInput.files[0]);
                }
            }
            resetForm();
            await loadSchools();
        } catch (err) {
            alert(err.message);
        }
    });

    document.getElementById("cancelEdit").addEventListener("click", resetForm);
});

function previewPhoto(e) {
    const file = e.target.files[0];
    if (!file) return;
    const preview = document.getElementById("photoPreview");
    const reader = new FileReader();
    reader.onload = (ev) => {
        preview.innerHTML = `\u003cimg src="${ev.target.result}" alt="Preview"\u003e`;
        preview.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
}

function updatePhotoPreview(url) {
    const preview = document.getElementById("photoPreview");
    const removeBtn = document.getElementById("removePhotoBtn");
    if (url) {
        preview.innerHTML = `\u003cimg src="${url}" alt="Imagem da escola"\u003e`;
        preview.classList.remove("hidden");
        removeBtn.classList.remove("hidden");
    } else {
        preview.innerHTML = "";
        preview.classList.add("hidden");
        removeBtn.classList.add("hidden");
    }
}

window.removeSchoolPhoto = async function() {
    const schoolId = document.getElementById("school_id").value;
    if (!schoolId) {
        document.getElementById("schoolPhoto").value = "";
        updatePhotoPreview(null);
        return;
    }
    if (!confirm("Deseja remover a imagem desta escola?")) return;
    try {
        await removeSchoolPhotoApi(schoolId);
        document.getElementById("schoolPhoto").value = "";
        updatePhotoPreview(null);
        await loadSchools();
    } catch (err) {
        alert(err.message);
    }
};

async function loadSchools() {
    const schools = await listSchools();
    document.getElementById("schoolsTable").innerHTML = schools.map(s => `
        <tr>
            <td>${s.name}</td>
            <td>${s.cnpj || "-"}</td>
            <td>${s.city || ""}/${s.state || ""}</td>
            <td>${s.is_active ? "Sim" : "Não"}${s.photo_url ? " 📷" : ""}</td>
            <td class="actions">
                <button class="btn-secondary" onclick="editSchool(${s.id}, '${escapeHtml(s.name)}', '${escapeHtml(s.cnpj || "")}', '${escapeHtml(s.phone || "")}', '${escapeHtml(s.city || "")}', '${escapeHtml(s.state || "")}', ${s.is_active}, '${s.photo_url || ""}')">Editar</button>
                <button class="btn" onclick="openModules(${s.id})">Módulos</button>
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

window.editSchool = async function(id, name, cnpj, phone, city, state, isActive, photoUrl) {
    document.getElementById("school_id").value = id;
    document.getElementById("name").value = name;
    document.getElementById("cnpj").value = cnpj || "";
    document.getElementById("phone").value = phone || "";
    document.getElementById("city").value = city || "";
    document.getElementById("state").value = state || "";
    document.getElementById("is_active").checked = !!isActive;
    document.getElementById("schoolPhoto").value = "";
    updatePhotoPreview(photoUrl || null);
    document.getElementById("submitBtn").textContent = "Salvar";
    document.getElementById("cancelEdit").classList.remove("hidden");
    window.scrollTo({ top: document.getElementById("schoolForm").offsetTop - 80, behavior: "smooth" });
};

window.openModules = async function(schoolId) {
    const panel = document.getElementById("modulesPanel");
    const list = document.getElementById("modulesList");
    panel.dataset.schoolId = schoolId;
    panel.classList.remove("hidden");

    const [modules, schoolSettings] = await Promise.all([
        listModules(),
        listSchoolModules(schoolId),
    ]);

    const enabledByModuleId = {};
    for (const setting of schoolSettings) {
        enabledByModuleId[setting.module.id] = setting.is_enabled;
    }

    list.innerHTML = modules.map(m => `
        <div class="module-row">
            <label>
                <input type="checkbox" onchange="toggleModuleForSchool(${schoolId}, ${m.id}, this.checked)" ${enabledByModuleId[m.id] ? "checked" : ""}>
                ${m.name} ${m.is_core ? "(core)" : ""}
            </label>
        </div>
    `).join("");

    window.scrollTo({ top: panel.offsetTop - 80, behavior: "smooth" });
};

window.toggleModuleForSchool = async function(schoolId, moduleId, isEnabled) {
    try {
        await toggleModule(schoolId, moduleId, isEnabled);
    } catch (err) {
        alert(err.message);
        await openModules(schoolId);
    }
};

function resetForm() {
    const form = document.getElementById("schoolForm");
    form.reset();
    document.getElementById("school_id").value = "";
    document.getElementById("is_active").checked = true;
    document.getElementById("schoolPhoto").value = "";
    updatePhotoPreview(null);
    document.getElementById("submitBtn").textContent = "Cadastrar";
    document.getElementById("cancelEdit").classList.add("hidden");
    document.getElementById("modulesPanel").classList.add("hidden");
}
