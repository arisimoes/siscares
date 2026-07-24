document.addEventListener("DOMContentLoaded", async () => {
    await loadShifts();
    await loadClasses();

    document.getElementById("shiftForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        await createShift({
            name: document.getElementById("shift_name").value,
            start_time: document.getElementById("start_time").value,
            end_time: document.getElementById("end_time").value,
        });
        e.target.reset();
        await loadShifts();
    });

    document.getElementById("classForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        await createClass({
            name: document.getElementById("class_name").value,
            grade: document.getElementById("grade").value || null,
            year: parseInt(document.getElementById("year").value),
        });
        e.target.reset();
        await loadClasses();
    });
});

async function loadShifts() {
    const shifts = await listShifts();
    document.getElementById("shiftsList").innerHTML = shifts.map(s => `
        <li>${s.name}: ${s.start_time} - ${s.end_time}</li>
    `).join("");
}

async function loadClasses() {
    const classes = await listClasses();
    document.getElementById("classesList").innerHTML = classes.map(c => `
        <li>${c.name} (${c.grade || "-"}) - ${c.year}</li>
    `).join("");
}
