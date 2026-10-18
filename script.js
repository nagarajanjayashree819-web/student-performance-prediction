const form = document.getElementById("studentForm");

let subjectChart = null;

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const error = document.getElementById("error");
    const button = document.getElementById("predictBtn");

    error.textContent = "";

    const fields = [
        "english",
        "mathematics",
        "science",
        "social_studies",
        "attendance",
        "study_hours"
    ];

    const values = {};

    for (const field of fields) {
        const input = document.getElementById(field);
        const value = Number(input.value);

        const maximum =
            field === "study_hours" ? 24 : 100;

        if (
            input.value.trim() === "" ||
            !Number.isFinite(value) ||
            value < 0 ||
            value > maximum
        ) {
            error.textContent =
                `Enter a valid ${field.replaceAll("_", " ")} value.`;
            input.focus();
            return;
        }

        values[field] = value;
    }

    button.disabled = true;
    button.textContent = "Analyzing...";

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(values)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Prediction failed.");
        }

        document.getElementById("welcome").hidden = true;
        document.getElementById("results").hidden = false;

        document.getElementById("average").textContent =
            data.overall_average + "%";

        document.getElementById("predicted").textContent =
            data.predicted_average + "%";

        document.getElementById("category").textContent =
            data.category;

        document.getElementById("strongest").textContent =
            data.strongest_subject;

        document.getElementById("weakest").textContent =
            data.improvement_subject;

        document.getElementById("mae").textContent =
            data.mae;

        document.getElementById("r2").textContent =
            data.r2;

        document.getElementById("recommendation").textContent =
            `Continue developing strengths in ${data.strongest_subject}. ` +
            `Consider additional practice in ${data.improvement_subject}.`;

        // Create subject-wise bar chart
        const labels = Object.keys(data.subject_marks);
        const marks = Object.values(data.subject_marks);

        const canvas = document.getElementById("subjectChart");

        if (typeof Chart === "undefined") {
            throw new Error(
                "Chart library unavailable. Check your internet connection."
            );
        }

        if (subjectChart) {
            subjectChart.destroy();
        }

        subjectChart = new Chart(canvas, {
            type: "bar",

            data: {
                labels: labels,

                datasets: [{
                    label: "Marks (%)",
                    data: marks,
                    backgroundColor: [
                        "#8b80f9",
                        "#6558d9",
                        "#42b994",
                        "#f2b45d"
                    ],
                    borderRadius: 7
                }]
            },

            options: {
                responsive: true,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });

        document.getElementById("results")
            .scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

    } catch (err) {
        error.textContent = err.message;
    } finally {
        button.disabled = false;
        button.textContent = "Predict Performance →";
    }
});