document.getElementById("uploadButton").addEventListener("click", async function() {
    const jobDesc = document.getElementById("jobDescription").value;
    const files = document.getElementById("resumeFiles").files;

    if (!jobDesc || files.length === 0) {
        alert("⚠️ Please enter a job description and upload resumes.");
        return;
    }

    let formData = new FormData();
    formData.append("job_description", jobDesc);
    for (let file of files) {
        formData.append("resumes", file);
    }

    document.getElementById("loading").style.display = "block";

    try {
        const response = await fetch("http://127.0.0.1:5000/screen_resumes", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        displayCandidates(data.candidates);
    } catch (error) {
        console.error("Error:", error);
        alert("❌ Error screening resumes.");
    } finally {
        document.getElementById("loading").style.display = "none";
    }
});

function displayCandidates(candidates) {
    const candidateList = document.getElementById("candidateList");
    candidateList.innerHTML = "";

    candidates.forEach((candidate, index) => {
        const li = document.createElement("li");
        li.innerHTML = `#${index + 1} <strong>${candidate.name}</strong> - Score: ${candidate.score}%`;
        candidateList.appendChild(li);
    });

    if (candidates.length === 0) {
        candidateList.innerHTML = "<li>No suitable candidates found.</li>";
    }
}
