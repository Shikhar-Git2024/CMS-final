document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("mlForm");
    const resultDiv = document.getElementById("mlResult");

    form.addEventListener("submit", async function (e) {
        e.preventDefault(); // stop redirect

        const formData = new FormData(form);

        const res = await fetch("/predict", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        resultDiv.innerHTML = `
            <h3>Prediction Result</h3>
            <p><b>Detected Crowd:</b> ${data.crowd_count}</p>
            <p><b>Predicted Crowd:</b> ${data.predicted_crowd}</p>
            <p><b>Wait Time:</b> ${data.wait_time} min</p>
            <p><b>Risk:</b> ${data.risk}</p>

            <video width="400" controls>
                <source src="/${data.video_path}" type="video/mp4">
            </video>
        `;
    });
});
