let pdfBytes = null;
let pdfDoc = null;
let scale = 1.3;

const backendURL = "YOUR_BACKEND_URL_HERE";  // example: https://yourapp.onrender.com

document.getElementById("pdfUpload").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    pdfBytes = await file.arrayBuffer();

    await renderPDF();
    await analyzePDF(file);
});

async function renderPDF() {
    const viewer = document.getElementById("viewerContainer");
    viewer.innerHTML = "";

    pdfDoc = await pdfjsLib.getDocument({ data: pdfBytes }).promise;

    for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale });

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        canvas.width = viewport.width;
        canvas.height = viewport.height;

        viewer.appendChild(canvas);

        await page.render({ canvasContext: ctx, viewport: viewport }).promise;
    }
}

async function analyzePDF(file) {
    const formData = new FormData();
    formData.append("pdf", file);

    const res = await fetch(backendURL + "/analyze", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    const tbody = document.querySelector("#fontTable tbody");
    tbody.innerHTML = "";

    data.forEach(page => {
        page.texts.forEach(item => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${page.page}</td>
                <td>${item.text}</td>
                <td>${item.font}</td>
                <td>${item.size}</td>
            `;

            // CLICK ACTION → scroll to text coordinates
            row.onclick = () => scrollToText(page.page, item.bbox);

            tbody.appendChild(row);
        });
    });
}

function scrollToText(pageNum, bbox) {
    const viewer = document.getElementById("viewerContainer");
    const canvasList = viewer.getElementsByTagName("canvas");

    const canvas = canvasList[pageNum - 1];
    const [x1, y1] = bbox;

    viewer.scrollTo({
        top: canvas.offsetTop + (y1 * scale) - 200,
        behavior: "smooth"
    });
}