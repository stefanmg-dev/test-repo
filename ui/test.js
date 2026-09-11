"use strict";

const CONFIG_URL = "/api/v1/config/document-types";
const EXTRACT_URL = "/extract-document";

const elements = {
    apiStatusIndicator: document.getElementById("apiStatusIndicator"),
    apiStatusText: document.getElementById("apiStatusText"),
    messageArea: document.getElementById("messageArea"),
    form: document.getElementById("documentTestForm"),
    documentType: document.getElementById("documentType"),
    documentFile: document.getElementById("documentFile"),
    extractButton: document.getElementById("extractButton"),
    processingSection: document.getElementById("processingSection"),
    resultSection: document.getElementById("resultSection"),
    diagnosticsSection: document.getElementById("diagnosticsSection"),
    resultSummary: document.getElementById("resultSummary"),
    validationBadge: document.getElementById("validationBadge"),
    validationErrors: document.getElementById("validationErrors"),
    resultFields: document.getElementById("resultFields"),
    diagnosticDocumentType: document.getElementById("diagnosticDocumentType"),
    diagnosticLlmValues: document.getElementById("diagnosticLlmValues"),
    diagnosticRawText: document.getElementById("diagnosticRawText"),
    resultFieldTemplate: document.getElementById("resultFieldTemplate")
};

const state = {
    documentTypes: {},
    processing: false
};

function showMessage(message, type = "success") {
    elements.messageArea.textContent = message;
    elements.messageArea.classList.remove("success", "error");
    elements.messageArea.classList.add(type);
}

function clearMessage() {
    elements.messageArea.textContent = "";
    elements.messageArea.classList.remove("success", "error");
}

function setApiStatus(online) {
    elements.apiStatusIndicator.classList.remove("online", "offline");
    elements.apiStatusIndicator.classList.add(online ? "online" : "offline");
    elements.apiStatusText.textContent = online ? "API е достъпно" : "API не е достъпно";
}

async function readJson(response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

function responseError(response, body) {
    const detail = body?.detail;
    if (Array.isArray(detail)) {
        return detail.map((item) => `${item.loc?.join(".") || "request"}: ${item.msg}`).join("\n");
    }
    return typeof detail === "string" ? detail : `HTTP ${response.status}`;
}

async function checkApiHealth() {
    try {
        const response = await fetch("/health", { headers: { Accept: "application/json" } });
        setApiStatus(response.ok);
    } catch {
        setApiStatus(false);
    }
}

async function loadDocumentTypes() {
    elements.documentType.innerHTML = '<option value="">Зареждане...</option>';

    try {
        const response = await fetch(CONFIG_URL, { headers: { Accept: "application/json" } });
        const body = await readJson(response);
        if (!response.ok) throw new Error(responseError(response, body));

        state.documentTypes = body?.document_types || {};
        elements.documentType.replaceChildren();

        const readyTypes = Object.entries(state.documentTypes).filter(
            ([, config]) => Array.isArray(config.fields) && config.fields.length > 0
        );

        if (!readyTypes.length) {
            const option = new Option("Няма готови типове документи", "");
            option.disabled = true;
            option.selected = true;
            elements.documentType.appendChild(option);
            elements.extractButton.disabled = true;
            return;
        }

        for (const [name, config] of readyTypes) {
            elements.documentType.appendChild(
                new Option(`${name} (${config.fields.length} полета)`, name)
            );
        }

        elements.extractButton.disabled = false;
    } catch (error) {
        elements.documentType.innerHTML = '<option value="">Грешка при зареждане</option>';
        elements.extractButton.disabled = true;
        showMessage(`Неуспешно зареждане на типовете: ${error.message}`, "error");
    }
}

function setProcessing(processing) {
    state.processing = processing;
    elements.extractButton.disabled = processing;
    elements.documentType.disabled = processing;
    elements.documentFile.disabled = processing;
    elements.extractButton.textContent = processing ? "Обработване..." : "Разпознай документа";
    elements.processingSection.classList.toggle("hidden", !processing);

    if (processing) {
        elements.resultSection.classList.add("hidden");
        elements.diagnosticsSection.classList.add("hidden");
    }
}

function fieldLabel(documentType, fieldName) {
    const fields = state.documentTypes[documentType]?.fields || [];
    const field = fields.find((item) => item.name === fieldName);
    return field?.label?.bg || field?.label?.en || fieldName;
}

function formatValue(value) {
    if (value === null || value === undefined || value === "") {
        return "Не е извлечена стойност";
    }
    return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}

function renderValidationErrors(errors) {
    elements.validationErrors.replaceChildren();
    const entries = Object.entries(errors || {});
    if (!entries.length) return;

    const box = document.createElement("div");
    box.className = "message-area error";
    const list = document.createElement("ul");

    for (const [fieldName, messages] of entries) {
        for (const message of messages) {
            const item = document.createElement("li");
            item.textContent = `${fieldName}: ${message}`;
            list.appendChild(item);
        }
    }

    box.appendChild(list);
    elements.validationErrors.appendChild(box);
}

function renderFields(documentType, values, errors) {
    elements.resultFields.replaceChildren();
    const configured = state.documentTypes[documentType]?.fields || [];
    const names = configured.length ? configured.map((field) => field.name) : Object.keys(values || {});

    for (const name of names) {
        const fragment = elements.resultFieldTemplate.content.cloneNode(true);
        const card = fragment.querySelector(".field-card");
        const badge = fragment.querySelector(".field-type-badge");
        const value = values?.[name];
        const fieldErrors = errors?.[name] || [];

        fragment.querySelector(".field-title").textContent = fieldLabel(documentType, name);
        fragment.querySelector(".field-name").textContent = name;
        fragment.querySelector(".field-detail-value").textContent = formatValue(value);

        if (value === null || value === undefined || value === "") {
            badge.textContent = "MISSING";
            badge.style.background = "#fef2f2";
            badge.style.color = "#b91c1c";
        } else if (fieldErrors.length) {
            badge.textContent = "INVALID";
            badge.style.background = "#fff7ed";
            badge.style.color = "#c2410c";
        } else {
            badge.textContent = "VALID";
            badge.style.background = "#f0fdf4";
            badge.style.color = "#15803d";
        }

        if (fieldErrors.length) {
            card.style.borderColor = "#fecaca";
            const errorContainer = fragment.querySelector(".field-validation-errors");
            errorContainer.textContent = fieldErrors.join("; ");
            errorContainer.style.color = "#b91c1c";
        }

        elements.resultFields.appendChild(fragment);
    }
}

function renderResult(body) {
    const values = body.final_values || {};
    const validation = body.validation || { valid: false, errors: {} };
    const extracted = Object.values(values).filter(
        (value) => value !== null && value !== undefined && value !== ""
    ).length;

    elements.resultSummary.textContent = `${extracted} от ${Object.keys(values).length} полета са извлечени.`;
    elements.validationBadge.textContent = validation.valid ? "VALID" : "INVALID";
    elements.validationBadge.style.background = validation.valid ? "#f0fdf4" : "#fef2f2";
    elements.validationBadge.style.color = validation.valid ? "#15803d" : "#b91c1c";

    renderValidationErrors(validation.errors);
    renderFields(body.document_type, values, validation.errors || {});

    elements.diagnosticDocumentType.textContent = body.document_type || "";
    elements.diagnosticLlmValues.textContent = JSON.stringify(body.llm_values || {}, null, 2);
    elements.diagnosticRawText.textContent = body.raw_text || "";

    elements.resultSection.classList.remove("hidden");
    elements.diagnosticsSection.classList.remove("hidden");
}

async function submitDocument(event) {
    event.preventDefault();
    clearMessage();
    if (state.processing || !elements.form.reportValidity()) return;

    const documentType = elements.documentType.value;
    const file = elements.documentFile.files[0];
    if (!documentType || !file) return;

    const allowed = [".pdf", ".jpg", ".jpeg", ".png"];
    if (!allowed.some((extension) => file.name.toLowerCase().endsWith(extension))) {
        showMessage("Неподдържан файлов формат.", "error");
        return;
    }

    const data = new FormData();
    data.append("document_type", documentType);
    data.append("file", file);

    setProcessing(true);

    try {
        const response = await fetch(EXTRACT_URL, { method: "POST", body: data });
        const body = await readJson(response);
        if (!response.ok) throw new Error(responseError(response, body));

        renderResult(body);
        showMessage(
            body.validation?.valid
                ? "Документът е извлечен и валидиран успешно."
                : "Документът е обработен, но има невалидни или липсващи полета.",
            body.validation?.valid ? "success" : "error"
        );
    } catch (error) {
        elements.resultSection.classList.add("hidden");
        elements.diagnosticsSection.classList.add("hidden");
        showMessage(`Грешка при обработване: ${error.message}`, "error");
    } finally {
        setProcessing(false);
    }
}

elements.form.addEventListener("submit", submitDocument);

async function initializeApplication() {
    await checkApiHealth();
    await loadDocumentTypes();
}

initializeApplication();
