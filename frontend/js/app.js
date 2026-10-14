let selectedSlide = null;

const presentation = {
    theme: {
        font_name: "Aptos",
        primary_color: "#0055AA",
        background_color: "#FFFFFF",
        title_size: 30,
        subtitle_size: 18
    },
    slides: []
};

async function save() {
    const response = await fetch(
        "/api/save",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(presentation)
        }
    );

    const text = await response.text();
    console.log("save():", text);
}

function render() {
    const container = document.getElementById("slides");

    container.innerHTML = "";

    presentation.slides.forEach((slide) => {
        const div = document.createElement("div");

        div.style.border = "1px solid #ccc";
        div.style.padding = "10px";
        div.style.marginBottom = "10px";
        div.style.cursor = "pointer";

        if (selectedSlide === slide) {
            div.style.border = "3px solid #0d6efd";
        }

        let backgroundInfo = "";

        if (slide.background_image) {
            backgroundInfo =
                `<p><strong>Background:</strong> ${slide.background_image}</p>`;
        }

        div.innerHTML = `
            <h3>${slide.title}</h3>
            <p>${slide.subtitle}</p>
            ${backgroundInfo}
        `;

        div.addEventListener("click", () => {
            selectedSlide = slide;
            render();
            updatePropertiesPanel();
        });

        container.appendChild(div);
    });
}

async function loadGallery() {
    const response = await fetch("/api/images");
    const images = await response.json();

    const gallery = document.getElementById("gallery");

    if (!gallery) {
        console.warn("gallery element not found");
        return;
    }

    gallery.innerHTML = "";

    for (const image of images) {
        const img = document.createElement("img");

        img.src = `/images/${image}`;

        img.style.width = "120px";
        img.style.height = "80px";
        img.style.objectFit = "cover";
        img.style.margin = "4px";
        img.style.cursor = "pointer";
        img.style.border = "2px solid transparent";

        img.title = image;

        img.addEventListener("click", async () => {
            if (!selectedSlide) {
                alert("Select a slide first.");
                return;
            }

            selectedSlide.background_image = image;

            await save();
            render();
        });

        gallery.appendChild(img);
    }
}

function updatePropertiesPanel() {
    document.getElementById("slide-title").value =
        selectedSlide?.title ?? "";

    document.getElementById("slide-subtitle").value =
        selectedSlide?.subtitle ?? "";

    document.getElementById("slide-author").value =
        selectedSlide?.author ?? "";

    document.getElementById("slide-institution").value =
        selectedSlide?.institution ?? "";

    document.getElementById("slide-date").value =
        selectedSlide?.date ?? "";
}

document
    .getElementById("add-title")
    .addEventListener("click", async () => {

        const slide = {
            type: "title",
            title: `Presentation ${presentation.slides.length + 1}`,
            subtitle: "Subtitle",
            author: "",
            institution: "",
            date: "",
            background_image: null
        };

        presentation.slides.push(slide);

        selectedSlide = slide;

        await save();
        render();
    });

document
    .getElementById("export-pptx")
    .addEventListener("click", () => {

        window.location = "/api/export/pptx";
    });

document
    .getElementById("slide-title")
    .addEventListener("input", async (e) => {

        if (!selectedSlide) {
            return;
        }

        selectedSlide.title = e.target.value;

        await save();
        render();
    });

document
    .getElementById("slide-subtitle")
    .addEventListener("input", async (e) => {

        if (!selectedSlide) {
            return;
        }

        selectedSlide.subtitle = e.target.value;

        await save();
        render();
    });

document
    .getElementById("slide-author")
    .addEventListener("input", async (e) => {

        if (!selectedSlide) {
            return;
        }

        selectedSlide.author = e.target.value;

        await save();
    });

document
    .getElementById("slide-institution")
    .addEventListener("input", async (e) => {

        if (!selectedSlide) {
            return;
        }

        selectedSlide.institution = e.target.value;

        await save();
    });

document
    .getElementById("slide-date")
    .addEventListener("input", async (e) => {

        if (!selectedSlide) {
            return;
        }

        selectedSlide.date = e.target.value;

        await save();
    });

render();
loadGallery();

updatePropertiesPanel();