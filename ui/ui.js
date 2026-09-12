"use strict";

const API_BASE = "/api/v1/config";

const state = {
    documentTypes: {},
    documentTypeMetadata: {},
    selectedDocumentType: null,
    modalConfirmHandler: null,
};

const byId = (id) => document.getElementById(id);

const el = {
    apiStatusIndicator: byId("apiStatusIndicator"),
    apiStatusText: byId("apiStatusText"),
    documentTypeCount: byId("documentTypeCount"),
    documentTypeList: byId("documentTypeList"),
    emptyEditorState: byId("emptyEditorState"),
    documentEditor: byId("documentEditor"),
    selectedDocumentTypeName: byId("selectedDocumentTypeName"),
    selectedDocumentTypeSummary: byId("selectedDocumentTypeSummary"),
    fieldList: byId("fieldList"),
    messageArea: byId("messageArea"),
    modalBackdrop: byId("modalBackdrop"),
    modalTitle: byId("modalTitle"),
    modalBody: byId("modalBody"),
    confirmModalButton: byId("confirmModalButton"),
    cancelModalButton: byId("cancelModalButton"),
    closeModalButton: byId("closeModalButton"),
    navRefresh: byId("navRefresh"),
    openCreateDocumentTypeButton: byId("openCreateDocumentTypeButton"),
    renameDocumentTypeButton: byId("renameDocumentTypeButton"),
    deleteDocumentTypeButton: byId("deleteDocumentTypeButton"),
    openAddFieldButton: byId("openAddFieldButton"),
    fieldCardTemplate: byId("fieldCardTemplate"),
};

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            Accept: "application/json",
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {}),
        },
    });

    if (response.status === 204) return null;

    let body = null;
    try {
        body = await response.json();
    } catch {
        body = null;
    }

    if (!response.ok) {
        const detail = body?.detail;
        if (Array.isArray(detail)) {
            throw new Error(detail.map((item) => `${item.loc?.join(".") || "request"}: ${item.msg}`).join("\n"));
        }
        throw new Error(detail || `HTTP ${response.status}`);
    }

    return body;
}

function showMessage(message, type = "success") {
    el.messageArea.textContent = message;
    el.messageArea.classList.remove("success", "error");
    el.messageArea.classList.add(type);
    clearTimeout(showMessage.timer);
    showMessage.timer = setTimeout(() => {
        el.messageArea.textContent = "";
        el.messageArea.classList.remove("success", "error");
    }, 5000);
}

async function checkApiHealth() {
    try {
        const response = await fetch("/health", { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error();
        el.apiStatusIndicator.classList.remove("offline");
        el.apiStatusIndicator.classList.add("online");
        el.apiStatusText.textContent = "API е достъпно";
    } catch {
        el.apiStatusIndicator.classList.remove("online");
        el.apiStatusIndicator.classList.add("offline");
        el.apiStatusText.textContent = "API не е достъпно";
    }
}

function getFieldLabel(field) {
    return field.label?.bg || field.label?.en || field.name;
}

function hasValue(value) {
    if (value === null || value === undefined || value === "") return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    return true;
}

function addDetail(container, label, value) {
    if (!hasValue(value)) return;

    const wrapper = document.createElement("div");
    wrapper.className = "field-detail";

    const labelElement = document.createElement("span");
    labelElement.className = "field-detail-label";
    labelElement.textContent = label;

    const valueElement = document.createElement("span");
    valueElement.className = "field-detail-value";
    valueElement.textContent = Array.isArray(value) ? value.join("\n") : String(value);

    wrapper.append(labelElement, valueElement);
    container.appendChild(wrapper);
}

function validationSummary(rule) {
    const parts = [rule.type];
    if (rule.pattern) parts.push(`pattern: ${rule.pattern}`);
    if (rule.format) parts.push(`format: ${rule.format}`);
    if (rule.minimum !== null && rule.minimum !== undefined) parts.push(`min: ${rule.minimum}`);
    if (rule.maximum !== null && rule.maximum !== undefined) parts.push(`max: ${rule.maximum}`);
    if (rule.message) parts.push(rule.message);
    return parts.join(" | ");
}

function renderFieldDetails(container, field) {
    addDetail(container, "type", field.type);

    if (field.type === "constant") addDetail(container, "value", field.value);
    if (field.type === "regex") addDetail(container, "rule", field.rule);
    if (field.type === "regex_list") addDetail(container, "rules", field.rules);
    if (field.type === "nearby") {
        addDetail(container, "anchor", field.anchor);
        addDetail(container, "pattern", field.pattern);
        addDetail(container, "direction", field.direction || "both");
        addDetail(container, "window_size", field.window_size || 400);
    }

    if (["regex", "regex_list", "nearby"].includes(field.type)) {
        addDetail(container, "occurrence", field.occurrence || "last");
    }

    for (const rule of field.validation || []) {
        addDetail(container, "validation", validationSummary(rule));
    }
}

function renderDocumentTypes() {
    const entries = Object.entries(state.documentTypes);
    el.documentTypeCount.textContent = String(entries.length);
    el.documentTypeList.replaceChildren();

    if (!entries.length) {
        const empty = document.createElement("div");
        empty.className = "loading-state";
        empty.textContent = "Няма конфигурирани типове.";
        el.documentTypeList.appendChild(empty);
        selectDocumentType(null);
        return;
    }

    for (const [name, config] of entries) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "document-type-item";
        if (name === state.selectedDocumentType) button.classList.add("active");

        const nameElement = document.createElement("span");
        nameElement.className = "document-type-item-name";
        nameElement.textContent = name;

        const countElement = document.createElement("span");
        countElement.className = "document-type-item-count";
        const metadata =
            state.documentTypeMetadata[name] || {
                status: "draft",
                ready: false,
                field_count: 0
            };

        countElement.textContent =
            `${metadata.status.toUpperCase()} · `
            + `${metadata.field_count} полета`;

        button.append(nameElement, countElement);
        button.addEventListener("click", () => selectDocumentType(name));
        el.documentTypeList.appendChild(button);
    }
}

function renderFields(config) {
    el.fieldList.replaceChildren();
    const fields = config.fields || [];

    if (!fields.length) {
        const empty = document.createElement("div");
        empty.className = "loading-state";
        empty.textContent = "Този тип документ още няма полета.";
        el.fieldList.appendChild(empty);
        return;
    }

    for (const field of fields) {
        const fragment = el.fieldCardTemplate.content.cloneNode(true);
        fragment.querySelector(".field-title").textContent = getFieldLabel(field);
        fragment.querySelector(".field-type-badge").textContent = field.type;
        fragment.querySelector(".field-name").textContent = field.name;
        renderFieldDetails(fragment.querySelector(".field-details"), field);
        fragment.querySelector(".edit-field-button").addEventListener("click", () => openFieldModal(field));
        fragment.querySelector(".delete-field-button").addEventListener("click", () => confirmDeleteField(field));
        el.fieldList.appendChild(fragment);
    }
}

function selectDocumentType(name) {
    state.selectedDocumentType = name;
    renderDocumentTypes();

    if (!name || !state.documentTypes[name]) {
        el.emptyEditorState.classList.remove("hidden");
        el.documentEditor.classList.add("hidden");
        return;
    }

    const config = state.documentTypes[name];
    el.emptyEditorState.classList.add("hidden");
    el.documentEditor.classList.remove("hidden");
    el.selectedDocumentTypeName.textContent = name;
    const metadata =
        state.documentTypeMetadata[name] || {
            status: "draft",
            ready: false,
            field_count: 0
        };

    el.selectedDocumentTypeSummary.textContent =
        `${metadata.status.toUpperCase()} · `
        + `${metadata.field_count} конфигурирани полета`;
    renderFields(config);
}

async function loadConfiguration(preserveSelection = true) {
    el.documentTypeList.innerHTML = '<div class="loading-state">Зареждане...</div>';

    try {
        const response = await apiRequest("/document-types");
        state.documentTypes =
            response.document_types || {};

        state.documentTypeMetadata =
            response.document_type_metadata || {};

        const names = Object.keys(
            state.documentTypes
        );

        if (!preserveSelection || !state.selectedDocumentType || !state.documentTypes[state.selectedDocumentType]) {
            state.selectedDocumentType = names[0] || null;
        }

        selectDocumentType(state.selectedDocumentType);
    } catch (error) {
        state.documentTypes = {};
        state.documentTypeMetadata = {};
        state.selectedDocumentType = null;
        renderDocumentTypes();
        selectDocumentType(null);
        showMessage(error.message, "error");
    }
}

function openModal({ title, body, confirmText = "Запази", onConfirm }) {
    el.modalTitle.textContent = title;
    el.modalBody.replaceChildren();
    el.modalBody.appendChild(body);
    el.confirmModalButton.textContent = confirmText;
    state.modalConfirmHandler = onConfirm;
    el.modalBackdrop.classList.remove("hidden");
    el.modalBody.querySelector("input, select, textarea")?.focus();
}

function closeModal() {
    el.modalBackdrop.classList.add("hidden");
    el.modalBody.replaceChildren();
    state.modalConfirmHandler = null;
}

function textInput(id, label, value = "", options = {}) {
    const group = document.createElement("div");
    group.className = options.fullWidth === false ? "form-group" : "form-group full-width";

    const labelElement = document.createElement("label");
    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const input = document.createElement("input");
    input.id = id;
    input.className = "form-control";
    input.type = options.type || "text";
    input.value = value;
    input.required = Boolean(options.required);
    if (options.pattern) input.pattern = options.pattern;
    if (options.min !== undefined) input.min = String(options.min);
    if (options.max !== undefined) input.max = String(options.max);

    group.append(labelElement, input);
    if (options.help) {
        const help = document.createElement("div");
        help.className = "form-help";
        help.textContent = options.help;
        group.appendChild(help);
    }
    return { group, input };
}

function selectInput(id, label, value, options) {
    const group = document.createElement("div");
    group.className = "form-group";

    const labelElement = document.createElement("label");
    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const select = document.createElement("select");
    select.id = id;
    select.className = "form-control";

    for (const item of options) {
        const option = document.createElement("option");
        option.value = item;
        option.textContent = item;
        option.selected = item === value;
        select.appendChild(option);
    }

    group.append(labelElement, select);
    return { group, select };
}

function textareaInput(id, label, value = "", help = "") {
    const group = document.createElement("div");
    group.className = "form-group full-width";

    const labelElement = document.createElement("label");
    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const textarea = document.createElement("textarea");
    textarea.id = id;
    textarea.className = "form-control";
    textarea.value = value;

    group.append(labelElement, textarea);
    if (help) {
        const helpElement = document.createElement("div");
        helpElement.className = "form-help";
        helpElement.textContent = help;
        group.appendChild(helpElement);
    }
    return { group, textarea };
}

function checkboxInput(id, label, checked = false) {
    const group = document.createElement("div");
    group.className = "form-group";

    const wrapper = document.createElement("label");
    wrapper.htmlFor = id;
    wrapper.style.display = "flex";
    wrapper.style.alignItems = "center";
    wrapper.style.gap = "8px";

    const input = document.createElement("input");
    input.id = id;
    input.type = "checkbox";
    input.checked = checked;

    const text = document.createElement("span");
    text.textContent = label;

    wrapper.append(input, text);
    group.appendChild(wrapper);
    return { group, input };
}

function existingValidation(field, type) {
    return (field?.validation || []).find((rule) => rule.type === type) || {};
}

function buildValidationEditor(field) {
    const requiredRule = existingValidation(field, "required");
    const regexRule = existingValidation(field, "regex");
    const dateRule = existingValidation(field, "date");
    const decimalRule = existingValidation(field, "decimal");

    const requiredEnabled = checkboxInput("validationRequiredEnabled", "Задължително поле", Boolean(requiredRule.type));
    const requiredMessage = textInput("validationRequiredMessage", "Съобщение при липсваща стойност", requiredRule.message || "", { fullWidth: false });

    const formatType = selectInput(
        "validationFormatType",
        "Допълнителна валидация",
        regexRule.type ? "regex" : dateRule.type ? "date" : decimalRule.type ? "decimal" : "none",
        ["none", "regex", "date", "decimal"]
    );

    const pattern = textInput("validationPattern", "Validation regex", regexRule.pattern || "", { fullWidth: false });
    const dateFormat = textInput("validationDateFormat", "Формат на дата", dateRule.format || "%d.%m.%Y", { fullWidth: false });
    const minimum = textInput("validationMinimum", "Минимум", decimalRule.minimum ?? "", { fullWidth: false });
    const maximum = textInput("validationMaximum", "Максимум", decimalRule.maximum ?? "", { fullWidth: false });
    const formatMessage = textInput(
        "validationFormatMessage",
        "Съобщение при невалидна стойност",
        regexRule.message || dateRule.message || decimalRule.message || "",
        { fullWidth: false }
    );

    return {
        requiredEnabled,
        requiredMessage,
        formatType,
        pattern,
        dateFormat,
        minimum,
        maximum,
        formatMessage,
    };
}

function updateValidationVisibility(validation) {
    const type = validation.formatType.select.value;
    validation.pattern.group.classList.toggle("hidden", type !== "regex");
    validation.dateFormat.group.classList.toggle("hidden", type !== "date");
    validation.minimum.group.classList.toggle("hidden", type !== "decimal");
    validation.maximum.group.classList.toggle("hidden", type !== "decimal");
    validation.formatMessage.group.classList.toggle("hidden", type === "none");
}

function buildValidationPayload(validation) {
    const rules = [];

    if (validation.requiredEnabled.input.checked) {
        const rule = { type: "required" };
        const message = validation.requiredMessage.input.value.trim();
        if (message) rule.message = message;
        rules.push(rule);
    }

    const type = validation.formatType.select.value;
    if (type === "regex") {
        const rule = { type: "regex", pattern: validation.pattern.input.value.trim() };
        const message = validation.formatMessage.input.value.trim();
        if (message) rule.message = message;
        rules.push(rule);
    }
    if (type === "date") {
        const rule = { type: "date", format: validation.dateFormat.input.value.trim() || "%d.%m.%Y" };
        const message = validation.formatMessage.input.value.trim();
        if (message) rule.message = message;
        rules.push(rule);
    }
    if (type === "decimal") {
        const rule = { type: "decimal" };
        const minimum = validation.minimum.input.value.trim();
        const maximum = validation.maximum.input.value.trim();
        const message = validation.formatMessage.input.value.trim();
        if (minimum) rule.minimum = minimum;
        if (maximum) rule.maximum = maximum;
        if (message) rule.message = message;
        rules.push(rule);
    }

    return rules;
}

function openCreateDocumentTypeModal() {
    const form = document.createElement("form");
    form.className = "form-grid";
    const name = textInput("newDocumentType", "Системно име", "", {
        required: true,
        pattern: "^[a-z][a-z0-9_]*$",
        help: "Малки латински букви, цифри и долна черта.",
    });
    form.appendChild(name.group);

    openModal({
        title: "Нов тип документ",
        body: form,
        confirmText: "Създай",
        onConfirm: async () => {
            if (!form.reportValidity()) return;
            const documentType = name.input.value.trim();
            await apiRequest("/document-types", {
                method: "POST",
                body: JSON.stringify({ document_type: documentType }),
            });
            state.selectedDocumentType = documentType;
            closeModal();
            await loadConfiguration();
            showMessage(`Типът '${documentType}' е създаден.`);
        },
    });
}

function openRenameDocumentTypeModal() {
    const current = state.selectedDocumentType;
    if (!current) return;

    const form = document.createElement("form");
    form.className = "form-grid";
    const name = textInput("renamedDocumentType", "Ново системно име", current, {
        required: true,
        pattern: "^[a-z][a-z0-9_]*$",
    });
    form.appendChild(name.group);

    openModal({
        title: `Преименуване на '${current}'`,
        body: form,
        onConfirm: async () => {
            if (!form.reportValidity()) return;
            const newName = name.input.value.trim();
            await apiRequest(`/document-types/${encodeURIComponent(current)}/rename`, {
                method: "PUT",
                body: JSON.stringify({ new_document_type: newName }),
            });
            state.selectedDocumentType = newName;
            closeModal();
            await loadConfiguration();
            showMessage(`Типът е преименуван на '${newName}'.`);
        },
    });
}

function confirmDeleteDocumentType() {
    const documentType = state.selectedDocumentType;
    if (!documentType) return;

    const body = document.createElement("div");
    body.textContent = `Изтриване на '${documentType}' и всички негови полета?`;

    openModal({
        title: "Изтриване на тип документ",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            await apiRequest(`/document-types/${encodeURIComponent(documentType)}`, { method: "DELETE" });
            state.selectedDocumentType = null;
            closeModal();
            await loadConfiguration(false);
            showMessage(`Типът '${documentType}' е изтрит.`);
        },
    });
}

function updateFieldVisibility(form) {
    const type = form.type.select.value;
    form.primary.group.classList.toggle("hidden", type === "llm");
    form.anchor.group.classList.toggle("hidden", type !== "nearby");
    form.direction.group.classList.toggle("hidden", type !== "nearby");
    form.windowSize.group.classList.toggle("hidden", type !== "nearby");
    form.occurrence.group.classList.toggle("hidden", !["regex", "regex_list", "nearby"].includes(type));

    const label = form.primary.group.querySelector("label");
    const help = form.primary.group.querySelector(".form-help");
    if (type === "constant") {
        label.textContent = "Константна стойност";
        help.textContent = "Стойността се връща без търсене.";
    } else if (type === "regex") {
        label.textContent = "Regex правило";
        help.textContent = "Regex с capture group за стойността.";
    } else if (type === "regex_list") {
        label.textContent = "Regex правила";
        help.textContent = "По едно правило на ред.";
    } else if (type === "nearby") {
        label.textContent = "Regex pattern";
        help.textContent = "Regex в прозореца около anchor.";
    }
}

function buildFieldPayload(form, existingField) {
    const type = form.type.select.value;
    const field = {
        name: form.name.input.value.trim(),
        type,
        validation: buildValidationPayload(form.validation),
    };

    const bg = form.labelBg.input.value.trim();
    const en = form.labelEn.input.value.trim();
    if (bg || en) {
        field.label = {};
        if (bg) field.label.bg = bg;
        if (en) field.label.en = en;
    }

    if (type === "constant") field.value = form.primary.textarea.value;
    if (type === "regex") field.rule = form.primary.textarea.value.trim();
    if (type === "regex_list") {
        field.rules = form.primary.textarea.value.split("\n").map((line) => line.trim()).filter(Boolean);
    }
    if (type === "nearby") {
        field.anchor = form.anchor.input.value.trim();
        field.pattern = form.primary.textarea.value.trim();
        field.direction = form.direction.select.value;
        field.window_size = Number(form.windowSize.input.value);
    }
    if (["regex", "regex_list", "nearby"].includes(type)) {
        field.occurrence = form.occurrence.select.value;
    }

    if (existingField && !field.validation.length && existingField.validation?.length) {
        field.validation = structuredClone(existingField.validation);
    }

    return field;
}

function openFieldModal(existingField = null) {
    const isEditing = Boolean(existingField);
    const formElement = document.createElement("form");
    formElement.className = "form-grid";

    const name = textInput("fieldName", "Системно име", existingField?.name || "", {
        required: true,
        pattern: "^[a-z][a-z0-9_]*$",
        fullWidth: false,
    });
    const type = selectInput("fieldType", "Extraction тип", existingField?.type || "regex", [
        "constant", "regex", "regex_list", "nearby", "llm",
    ]);
    const labelBg = textInput("fieldLabelBg", "Етикет на български", existingField?.label?.bg || "", { fullWidth: false });
    const labelEn = textInput("fieldLabelEn", "Етикет на английски", existingField?.label?.en || "", { fullWidth: false });

    let primaryValue = "";
    if (existingField?.type === "constant") primaryValue = existingField.value ?? "";
    if (existingField?.type === "regex") primaryValue = existingField.rule || "";
    if (existingField?.type === "regex_list") primaryValue = (existingField.rules || []).join("\n");
    if (existingField?.type === "nearby") primaryValue = existingField.pattern || "";

    const primary = textareaInput("fieldPrimaryValue", "Правило или стойност", primaryValue, "Extraction конфигурация.");
    const occurrence = selectInput("fieldOccurrence", "Избор на съвпадение", existingField?.occurrence || "last", ["first", "last"]);
    const direction = selectInput("fieldDirection", "Посока", existingField?.direction || "both", ["before", "after", "both"]);
    const anchor = textInput("fieldAnchor", "Anchor", existingField?.anchor || "", { fullWidth: false });
    const windowSize = textInput("fieldWindowSize", "Размер на прозореца", String(existingField?.window_size || 400), {
        type: "number", min: 1, max: 10000, fullWidth: false,
    });
    const validation = buildValidationEditor(existingField);

    const section = document.createElement("div");
    section.className = "form-group full-width";
    const heading = document.createElement("h3");
    heading.textContent = "Валидация";
    section.appendChild(heading);

    formElement.append(
        name.group, type.group, labelBg.group, labelEn.group,
        occurrence.group, direction.group, anchor.group, windowSize.group,
        primary.group, section,
        validation.requiredEnabled.group, validation.requiredMessage.group,
        validation.formatType.group, validation.pattern.group,
        validation.dateFormat.group, validation.minimum.group,
        validation.maximum.group, validation.formatMessage.group
    );

    const form = { name, type, labelBg, labelEn, primary, occurrence, direction, anchor, windowSize, validation };
    type.select.addEventListener("change", () => updateFieldVisibility(form));
    validation.formatType.select.addEventListener("change", () => updateValidationVisibility(validation));
    updateFieldVisibility(form);
    updateValidationVisibility(validation);

    openModal({
        title: isEditing ? `Редакция на '${existingField.name}'` : "Добавяне на поле",
        body: formElement,
        onConfirm: async () => {
            if (!formElement.reportValidity()) return;
            const field = buildFieldPayload(form, existingField);
            const documentType = state.selectedDocumentType;

            if (isEditing) {
                await apiRequest(`/document-types/${encodeURIComponent(documentType)}/fields/${encodeURIComponent(existingField.name)}`, {
                    method: "PUT",
                    body: JSON.stringify({ field }),
                });
            } else {
                await apiRequest(`/document-types/${encodeURIComponent(documentType)}/fields`, {
                    method: "POST",
                    body: JSON.stringify({ field }),
                });
            }

            closeModal();
            await loadConfiguration();
            showMessage(isEditing ? `Полето '${existingField.name}' е актуализирано.` : `Полето '${field.name}' е добавено.`);
        },
    });
}

function confirmDeleteField(field) {
    const body = document.createElement("div");
    body.textContent = `Изтриване на полето '${field.name}'?`;

    openModal({
        title: "Изтриване на поле",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            await apiRequest(`/document-types/${encodeURIComponent(state.selectedDocumentType)}/fields/${encodeURIComponent(field.name)}`, {
                method: "DELETE",
            });
            closeModal();
            await loadConfiguration();
            showMessage(`Полето '${field.name}' е изтрито.`);
        },
    });
}

el.confirmModalButton.addEventListener("click", async () => {
    if (!state.modalConfirmHandler) return;
    el.confirmModalButton.disabled = true;
    try {
        await state.modalConfirmHandler();
    } catch (error) {
        showMessage(error.message, "error");
    } finally {
        el.confirmModalButton.disabled = false;
    }
});

el.cancelModalButton.addEventListener("click", closeModal);
el.closeModalButton.addEventListener("click", closeModal);
el.modalBackdrop.addEventListener("click", (event) => {
    if (event.target === el.modalBackdrop) closeModal();
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !el.modalBackdrop.classList.contains("hidden")) closeModal();
});
el.navRefresh.addEventListener("click", async () => {
    await loadConfiguration();
    showMessage("Конфигурацията е обновена.");
});
el.openCreateDocumentTypeButton.addEventListener("click", openCreateDocumentTypeModal);
el.renameDocumentTypeButton.addEventListener("click", openRenameDocumentTypeModal);
el.deleteDocumentTypeButton.addEventListener("click", confirmDeleteDocumentType);
el.openAddFieldButton.addEventListener("click", () => openFieldModal());

async function initializeApplication() {
    await checkApiHealth();
    await loadConfiguration(false);
}

initializeApplication();
