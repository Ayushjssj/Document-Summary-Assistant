const API_URL = "https://document-summary-assistant-a6xo.onrender.com/process";

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const lengthSelect = document.getElementById("lengthSelect");

    if (fileInput.files.length === 0) {
        alert("Please upload a PDF file.");
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("length", lengthSelect.value);

    document.getElementById("extractedText").value = "Extracting text...";
    document.getElementById("summaryText").value = "Summarizing...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById("extractedText").value = data.extracted_text;
        document.getElementById("summaryText").value = data.summary;
    } catch (error) {
        alert("Error connecting to backend: " + error);
    }
}

function downloadTXT() {
    const text = document.getElementById("summaryText").value;
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "summary.txt";
    link.click();
}

function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const text = document.getElementById("summaryText").value;
    doc.text(text, 10, 10);
    doc.save("summary.pdf");
}
