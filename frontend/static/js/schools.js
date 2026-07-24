document.addEventListener("DOMContentLoaded", async () => {
    await loadSchools();

    document.getElementById("schoolForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById("name").value,
            cnpj: document.getElementById("cnpj").value || null,
            phone: document.getElementById("phone").value || null,
            city: document.getElementById("city").value || null,
            state: document.getElementById("state").value || null,
        };
        try {
            await createSchool(data);
            e.target.reset();
            await loadSchools();
        } catch (err) {
            alert(err.message);
        }
    });
});

async function loadSchools() {
    const schools = await listSchools();
    document.getElementById("schoolsTable").innerHTML = schools.map(s => `
        <tr>
            <td>${s.name}</td>
            <td>${s.cnpj || "-"}</td>
            <td>${s.city || ""}/${s.state || ""}</td>
            <td>${s.is_active ? "Sim" : "Não"}</td>
        </tr>
    `).join("");
}
