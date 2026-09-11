// ===============================
// LOAD CONFIG
// ===============================
async function loadConfig() {
    const res = await fetch(`/get-document-types?t=${Date.now()}`, {
        headers: { "X-API-Key": "imamrabota" }
    });

    const data = await res.json();
    console.log("CONFIG FROM SERVER:", data);

    const content = document.getElementById("content");
    content.innerHTML = "";   // ← КРИТИЧНО

    let html = "";

    for (const [type, cfg] of Object.entries(data)) {
        html += `<div class="doc-section"><h2>${cfg.label.bg} (${type})</h2>`;

        cfg.fields.forEach(field => {
            const title = field.label.bg || field.label.en || field.name;

            html += `
                <div class="field-block">
                    <div><strong>${title}</strong></div>
                    <div><strong>name:</strong> ${field.name}</div>
                    <div><strong>type:</strong> ${field.type}</div>
                    ${field.type === "regex" ? `<div><strong>rule:</strong> ${field.rule}</div>` : ""}

                    <button 
                        data-type="${type}"
                        data-name="${field.name}"
                        data-bg="${field.label.bg}"
                        data-en="${field.label.en}"
                        data-fieldtype="${field.type}"
                        data-rule="${field.rule ? field.rule : ''}"
                        onclick="editField(this)"
                        style="background:#0d6efd; margin-right:10px;">
                        Edit
                    </button>

                    <button onclick="deleteField('${type}', '${field.name}')" style="background:#dc3545;">
                        Delete
                    </button>
                </div>
            `;
        });

        html += `</div>`;
    }

    content.innerHTML = html;
}


// ===============================
// EDIT POPUP
// ===============================
let currentEdit = {};

function editField(btn) {
    currentEdit = {
        documentType: btn.dataset.type,
        fieldName: btn.dataset.name
    };

    document.getElementById("editLabelBg").value = btn.dataset.bg;
    document.getElementById("editLabelEn").value = btn.dataset.en;
    document.getElementById("editType").value = btn.dataset.fieldtype;

    const ruleInput = document.getElementById("editRule");
    if (btn.dataset.fieldtype === "regex") {
        ruleInput.style.display = "block";
        ruleInput.value = btn.dataset.rule;
    } else {
        ruleInput.style.display = "none";
        ruleInput.value = "";
    }

    document.getElementById("editPopup").style.display = "flex";
}

function closeEditPopup() {
    document.getElementById("editPopup").style.display = "none";
}

// ===============================
// SAVE EDIT
// ===============================
async function saveEdit() {
    const formData = new FormData();
    formData.append("document_type", currentEdit.documentType);
    formData.append("field_name", currentEdit.fieldName);
    formData.append("label_bg", document.getElementById("editLabelBg").value);
    formData.append("label_en", document.getElementById("editLabelEn").value);
    formData.append("type", document.getElementById("editType").value);

    const typeValue = document.getElementById("editType").value;
    formData.append("rule", typeValue === "regex" ? document.getElementById("editRule").value : "");

    await fetch("/update-field", {
        method: "POST",
        headers: { "X-API-Key": "imamrabota" },
        body: formData
    });

    closeEditPopup();
    await loadConfig();   // ← КРИТИЧНО
}


// ===============================
// DELETE FIELD
// ===============================
async function deleteField(documentType, fieldName) {
    await fetch(`/delete-field?document_type=${documentType}&field_name=${fieldName}`, {
        method: "DELETE",
        headers: { "X-API-Key": "imamrabota" }
    });

    await loadConfig();
}

// ===============================
// ADD FIELD
// ===============================
document.getElementById("field_type").addEventListener("change", function() {
    const ruleInput = document.getElementById("rule");
    ruleInput.style.display = this.value === "regex" ? "block" : "none";
});

document.getElementById("editType").addEventListener("change", function() {
    const ruleInput = document.getElementById("editRule");
    ruleInput.style.display = this.value === "regex" ? "block" : "none";
});

function addField() {
    document.getElementById("addFieldForm").dispatchEvent(new Event("submit"));
}

document.getElementById("addFieldForm").onsubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    if (formData.get("field_type") === "llm") {
        formData.delete("rule");
    }

    await fetch("/add-field", {
        method: "POST",
        headers: { "X-API-Key": "imamrabota" },
        body: formData
    });

    await loadConfig();
};

// ===============================
// INITIAL LOAD
// ===============================
loadConfig();
