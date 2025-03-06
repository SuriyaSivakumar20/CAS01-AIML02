async function screenResumes() {
    const formData = new FormData();
    formData.append("jobDescription", jobDescription.value);

    Array.from(resumeFiles.files).forEach(file => {
        formData.append("resumes", file);
    });

    loading.style.display = "block";

    try {
        const response = await fetch("http://127.0.0.1:5000/screen", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        candidateList.innerHTML = "";
        
        if (data.message) {
            candidateList.innerHTML = `<li>${data.message}</li>`;
        } else {
            data.candidates.forEach((candidate, index) => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span>#${index + 1} <strong>${candidate.name}</strong></span>
                    <div>
                        <span class="score">Similarity: ${candidate.similarityScore}%</span>
                        <span class="ats-score">ATS: ${candidate.atsScore}%</span>
                    </div>
                    <p><strong>Matched Keywords:</strong> ${candidate.matchedKeywords.join(', ') || 'None'}</p>
                    <p><strong>Experience:</strong> ${candidate.experienceYears} years</p>
                `;
                candidateList.appendChild(li);
            });
        }
    } catch (error) {
        console.error("Error:", error);
        alert("❌ Error screening resumes.");
    } finally {
        loading.style.display = "none";
    }
}
