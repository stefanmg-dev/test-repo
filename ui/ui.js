"use strict";

const API_BASE = "/api/v1/config";

const state = {
    documentTypes: {},
    resolvedDocumentTypes: {},
    documentTypeMetadata: {},
    selectedDocumentType: null,
    selectedFieldScope: "legacy",
    selectedProfileName: null,
    modalConfirmHandler: null,
    modalReturnFocus: null,
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
    fieldScopeSection: byId("fieldScopeSection"),
    fieldScope: byId("fieldScope"),
    profileSelector: byId("profileSelector"),
    openAddProfileButton: byId("openAddProfileButton"),
    deleteProfileButton: byId("deleteProfileButton"),
    defaultProfileName: byId("defaultProfileName"),
    profileMatchingSection: byId("profileMatchingSection"),
    profileMatchingList: byId("profileMatchingList"),
    editProfileMatchingButton: byId("editProfileMatchingButton"),
    fieldList: byId("fieldList"),
    collectionList: byId("collectionList"),
    summaryValidationSection: byId("summaryValidationSection"),
    summaryValidationList: byId("summaryValidationList"),
    messageArea: byId("messageArea"),
    modalBackdrop: byId("modalBackdrop"),
    configurationModal: byId("configurationModal"),
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
    openAddCollectionButton: byId("openAddCollectionButton"),
    openAddSummaryValidationButton: byId("openAddSummaryValidationButton"),
    fieldCardTemplate: byId("fieldCardTemplate"),
};

async function apiRequest(path, options = {}) {
    const response = await window.documentAuth.authenticatedFetch(`${API_BASE}${path}`, {
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

function getSelectedProfile(config) {
    const profiles = config.profiles || {};
    if (state.selectedProfileName in profiles) {
        return state.selectedProfileName;
    }
    return config.default_profile || Object.keys(profiles)[0] || null;
}

function getSelectedFields(config) {
    if (Array.isArray(config.fields)) {
        return config.fields;
    }

    if (state.selectedFieldScope === "common") {
        return config.common_fields || [];
    }

    const profileName = getSelectedProfile(config);
    return config.profiles?.[profileName]?.fields || [];
}

function updateFieldScope(config) {
    const usesProfiles = !Array.isArray(config.fields);
    const profileName = getSelectedProfile(config);

    el.fieldScope.replaceChildren();
    el.profileSelector.replaceChildren();
    el.fieldScopeSection.classList.toggle(
        "hidden",
        !usesProfiles
    );
    el.defaultProfileName.textContent =
        config.default_profile || "Няма избран профил";

    if (!usesProfiles) {
        state.selectedFieldScope = "legacy";
        state.selectedProfileName = null;
        return;
    }

    state.selectedProfileName = profileName;
    for (const name of Object.keys(config.profiles || {}).sort()) {
        const option = new Option(name, name);
        option.selected = name === profileName;
        el.profileSelector.append(option);
    }
    el.profileSelector.disabled = !profileName;
    el.deleteProfileButton.disabled = (
        !profileName || profileName === config.default_profile
    );
    el.deleteProfileButton.title = (
        profileName === config.default_profile
            ? "Профилът по подразбиране не може да бъде изтрит."
            : ""
    );

    if (!["common", "profile"].includes(state.selectedFieldScope)) {
        state.selectedFieldScope = "common";
    }

    const commonOption = new Option("Общи полета", "common");
    const profileOption = new Option(
        `Профил: ${profileName || "няма"}`,
        "profile"
    );
    commonOption.selected = state.selectedFieldScope === "common";
    profileOption.selected = state.selectedFieldScope === "profile";
    profileOption.disabled = !profileName;
    el.fieldScope.append(commonOption, profileOption);
}

function renderProfileMatching(config) {
    const profileName = getSelectedProfile(config);
    const profile = config.profiles?.[profileName];
    const visible = Boolean(profileName && profile);
    el.profileMatchingSection.classList.toggle("hidden", !visible);
    el.profileMatchingList.replaceChildren();
    if (!visible) return;

    const rules = profile.matching?.any_of || [];
    if (!rules.length) {
        const empty = document.createElement("div");
        empty.className = "loading-state";
        empty.textContent = "Профилът още няма supplier matching правила.";
        el.profileMatchingList.appendChild(empty);
        return;
    }

    for (const rule of rules) {
        const card = document.createElement("article");
        card.className = "field-card";
        const title = document.createElement("h3");
        title.className = "field-title";
        title.textContent = rule.code;
        const details = document.createElement("div");
        details.className = "field-details";
        const detail = document.createElement("div");
        detail.className = "field-detail";
        const label = document.createElement("span");
        label.className = "field-detail-label";
        label.textContent = "Regex pattern";
        const value = document.createElement("span");
        value.className = "field-detail-value";
        value.textContent = rule.pattern;
        detail.append(label, value);
        details.appendChild(detail);
        card.append(title, details);
        el.profileMatchingList.appendChild(card);
    }
}

function createMatchingRuleEditor(rule, index, onRemove) {
    const row = document.createElement("div");
    row.className = "field-card full-width";
    row.dataset.matchingRule = String(index);

    const form = document.createElement("div");
    form.className = "form-grid";
    const code = textInput(
        `matchingCode${index}`,
        "Evidence code",
        rule.code || "",
        {
            required: true,
            pattern: "^[a-z][a-z0-9_]*$",
            fullWidth: false,
        }
    );
    const pattern = textareaInput(
        `matchingPattern${index}`,
        "Regex pattern",
        rule.pattern || "",
        "Pattern against normalized OCR text."
    );
    pattern.textarea.required = true;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "button button-danger-outline";
    remove.textContent = "Премахни правило";
    remove.addEventListener("click", () => onRemove(row));

    form.append(code.group, pattern.group);
    row.append(form, remove);
    return { row, code: code.input, pattern: pattern.textarea };
}

function confirmDeleteProfile() {
    const config = state.documentTypes[state.selectedDocumentType];
    const profileName = getSelectedProfile(config);
    if (!profileName) return;
    if (profileName === config.default_profile) {
        showMessage(
            "Профилът по подразбиране не може да бъде изтрит.",
            "error"
        );
        return;
    }

    const body = document.createElement("div");
    body.textContent = `Изтриване на профил '${profileName}'?`;
    openModal({
        title: "Изтриване на supplier profile",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            const endpoint = (
                `/document-types/${encodeURIComponent(state.selectedDocumentType)}`
                + `/profiles/${encodeURIComponent(profileName)}`
            );
            await apiRequest(endpoint, { method: "DELETE" });
            const remainingProfiles = Object.keys(config.profiles || {})
                .filter((name) => name !== profileName)
                .sort();
            state.selectedProfileName = (
                config.default_profile
                && remainingProfiles.includes(config.default_profile)
                    ? config.default_profile
                    : remainingProfiles[0] || null
            );
            state.selectedFieldScope = state.selectedProfileName
                ? "profile"
                : "common";
            closeModal();
            await loadConfiguration();
            showMessage(`Профилът '${profileName}' е изтрит.`);
        },
    });
}

function openAddProfileModal() {
    const config = state.documentTypes[state.selectedDocumentType];
    if (!config || Array.isArray(config.fields)) return;

    const form = document.createElement("form");
    form.className = "form-grid";
    const name = textInput("newProfileName", "Системно име на профила", "", {
        required: true,
        pattern: "^[a-z][a-z0-9_]*$",
        help: "Малки латински букви, цифри и долна черта.",
    });
    const rulesContainer = document.createElement("div");
    rulesContainer.className = "form-group full-width";
    const editors = [];

    const removeEditor = (row) => {
        if (editors.length <= 1) {
            showMessage("Новият профил изисква поне едно matching правило.", "error");
            return;
        }
        const index = editors.findIndex((editor) => editor.row === row);
        if (index >= 0) editors.splice(index, 1);
        row.remove();
    };

    const addEditor = (rule = {}) => {
        const editor = createMatchingRuleEditor(
            rule,
            editors.length,
            removeEditor
        );
        editors.push(editor);
        rulesContainer.appendChild(editor.row);
    };
    addEditor();

    const addRuleButton = document.createElement("button");
    addRuleButton.type = "button";
    addRuleButton.className = "button button-secondary full-width";
    addRuleButton.textContent = "Добави matching правило";
    addRuleButton.addEventListener("click", () => addEditor());
    form.append(name.group, rulesContainer, addRuleButton);

    openModal({
        title: "Нов supplier profile",
        body: form,
        confirmText: "Създай",
        onConfirm: async () => {
            if (!form.reportValidity()) return;
            const profileName = name.input.value.trim();
            const anyOf = editors.map((editor) => ({
                code: editor.code.value.trim(),
                pattern: editor.pattern.value.trim(),
            }));
            const endpoint = (
                `/document-types/${encodeURIComponent(state.selectedDocumentType)}`
                + `/profiles/${encodeURIComponent(profileName)}`
            );
            await apiRequest(endpoint, {
                method: "POST",
                body: JSON.stringify({
                    profile: {
                        matching: { any_of: anyOf },
                        fields: [],
                        collections: {},
                        summary_validations: [],
                    },
                }),
            });
            state.selectedProfileName = profileName;
            state.selectedFieldScope = "profile";
            closeModal();
            await loadConfiguration();
            showMessage(`Профилът '${profileName}' е създаден.`);
        },
    });
}

function openProfileMatchingModal() {
    const config = state.documentTypes[state.selectedDocumentType];
    const profileName = getSelectedProfile(config);
    if (!profileName) return;

    const form = document.createElement("form");
    form.className = "form-grid";
    const rulesContainer = document.createElement("div");
    rulesContainer.className = "form-group full-width";
    const editors = [];

    const removeEditor = (row) => {
        if (editors.length <= 1) {
            showMessage("Matching изисква поне едно правило.", "error");
            return;
        }
        const index = editors.findIndex((editor) => editor.row === row);
        if (index >= 0) editors.splice(index, 1);
        row.remove();
    };

    const addEditor = (rule = {}) => {
        const editor = createMatchingRuleEditor(
            rule,
            editors.length,
            removeEditor
        );
        editors.push(editor);
        rulesContainer.appendChild(editor.row);
    };

    const existingRules = (
        config.profiles?.[profileName]?.matching?.any_of || []
    );
    for (const rule of existingRules) addEditor(rule);
    if (!editors.length) addEditor();

    const addRuleButton = document.createElement("button");
    addRuleButton.type = "button";
    addRuleButton.className = "button button-secondary full-width";
    addRuleButton.textContent = "Добави matching правило";
    addRuleButton.addEventListener("click", () => addEditor());
    form.append(rulesContainer, addRuleButton);

    openModal({
        title: `Supplier matching за '${profileName}'`,
        body: form,
        onConfirm: async () => {
            if (!form.reportValidity()) return;
            const anyOf = editors.map((editor) => ({
                code: editor.code.value.trim(),
                pattern: editor.pattern.value.trim(),
            }));
            const endpoint = (
                `/document-types/${encodeURIComponent(state.selectedDocumentType)}`
                + `/profiles/${encodeURIComponent(profileName)}/matching`
            );
            await apiRequest(endpoint, {
                method: "PUT",
                body: JSON.stringify({ matching: { any_of: anyOf } }),
            });
            closeModal();
            await loadConfiguration();
            showMessage(`Matching правилата за '${profileName}' са актуализирани.`);
        },
    });
}

function buildFieldEndpoint(
    documentType,
    fieldName = null,
    collectionName = null,
    collectionProfileName = null
) {
    const encodedType = encodeURIComponent(documentType);
    let endpoint;

    if (collectionName) {
        const profilePath = collectionProfileName
            ? `/profiles/${encodeURIComponent(collectionProfileName)}`
            : "";
        endpoint = (
            `/document-types/${encodedType}`
            + profilePath
            + `/collections/${encodeURIComponent(collectionName)}`
            + "/fields"
        );
    } else if (state.selectedFieldScope === "common") {
        endpoint = `/document-types/${encodedType}/common-fields`;
    } else if (state.selectedFieldScope === "profile") {
        const config = state.documentTypes[documentType];
        const selectedProfile = getSelectedProfile(config);
        if (!selectedProfile) {
            throw new Error("Няма избран профил за редакция.");
        }
        const profileName = encodeURIComponent(selectedProfile);
        endpoint = `/document-types/${encodedType}/profiles/${profileName}/fields`;
    } else {
        endpoint = `/document-types/${encodedType}/fields`;
    }

    return fieldName
        ? `${endpoint}/${encodeURIComponent(fieldName)}`
        : endpoint;
}

function renderFields(config) {
    el.fieldList.replaceChildren();
    const fields = getSelectedFields(config);

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

function collectionEndpoint(
    documentType,
    collectionName,
    profileName = null
) {
    const documentPath = (
        `/document-types/${encodeURIComponent(documentType)}`
    );
    const profilePath = profileName
        ? `/profiles/${encodeURIComponent(profileName)}`
        : "";
    return (
        documentPath
        + profilePath
        + `/collections/${encodeURIComponent(collectionName)}`
    );
}

function getSelectedCollectionContext(config) {
    if (state.selectedFieldScope === "profile") {
        const profileName = getSelectedProfile(config);
        return {
            collections: (
                config.profiles?.[profileName]?.collections || {}
            ),
            profileName,
        };
    }
    return {
        collections: config.collections || {},
        profileName: null,
    };
}

function renderCollections(config) {
    el.collectionList.replaceChildren();
    const { collections, profileName } = (
        getSelectedCollectionContext(config)
    );
    const entries = Object.entries(collections).sort(
        ([left], [right]) => left.localeCompare(right)
    );

    if (!entries.length) {
        const empty = document.createElement("div");
        empty.className = "loading-state";
        empty.textContent = "Този тип документ още няма колекции.";
        el.collectionList.appendChild(empty);
        return;
    }

    for (const [name, collection] of entries) {
        const card = document.createElement("article");
        card.className = "field-card";

        const header = document.createElement("div");
        header.className = "field-header";

        const titleGroup = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "field-title";
        title.textContent = name;
        const badge = document.createElement("span");
        badge.className = "field-type-badge";
        badge.textContent = collection.cardinality || "zero_or_more";
        titleGroup.append(title, badge);

        const actions = document.createElement("div");
        actions.className = "field-actions";
        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "button button-secondary";
        editButton.textContent = "Редактирай";
        editButton.addEventListener(
            "click",
            () => openCollectionModal(name, collection, profileName)
        );
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "button button-danger-outline";
        deleteButton.textContent = "Изтрий";
        deleteButton.addEventListener(
            "click",
            () => confirmDeleteCollection(name, profileName)
        );
        actions.append(editButton, deleteButton);
        header.append(titleGroup, actions);

        const details = document.createElement("div");
        details.className = "field-details";
        addDetail(
            details,
            "start_pattern",
            collection.start_pattern || "няма"
        );
        addDetail(
            details,
            "fields",
            (collection.fields || []).length
        );
        addDetail(
            details,
            "item_validations",
            (collection.item_validations || []).length
        );

        const fieldSection = document.createElement("div");
        fieldSection.className = "field-details";
        const fieldHeading = document.createElement("strong");
        fieldHeading.textContent = "Полетата в колекцията";
        const addFieldButton = document.createElement("button");
        addFieldButton.type = "button";
        addFieldButton.className = "button button-secondary";
        addFieldButton.textContent = "Добави поле в колекцията";
        addFieldButton.addEventListener(
            "click",
            () => openFieldModal(null, name, profileName)
        );
        fieldSection.append(fieldHeading, addFieldButton);

        const collectionFields = collection.fields || [];
        if (!collectionFields.length) {
            const emptyFields = document.createElement("div");
            emptyFields.className = "form-help";
            emptyFields.textContent = "Колекцията още няма полета.";
            fieldSection.appendChild(emptyFields);
        }

        for (const field of collectionFields) {
            const row = document.createElement("div");
            row.className = "field-detail";

            const summary = document.createElement("span");
            summary.className = "field-detail-label";
            summary.textContent = `${field.name} · ${field.type}`;

            const fieldActions = document.createElement("span");
            fieldActions.className = "field-actions";
            const editFieldButton = document.createElement("button");
            editFieldButton.type = "button";
            editFieldButton.className = "button button-secondary";
            editFieldButton.textContent = "Редактирай поле";
            editFieldButton.addEventListener(
                "click",
                () => openFieldModal(field, name, profileName)
            );
            const deleteFieldButton = document.createElement("button");
            deleteFieldButton.type = "button";
            deleteFieldButton.className = "button button-danger-outline";
            deleteFieldButton.textContent = "Изтрий поле";
            deleteFieldButton.addEventListener(
                "click",
                () => confirmDeleteField(field, name, profileName)
            );
            fieldActions.append(editFieldButton, deleteFieldButton);
            row.append(summary, fieldActions);
            fieldSection.appendChild(row);
        }


        const validationSection = document.createElement("div");
        validationSection.className = "field-details";
        const validationHeading = document.createElement("strong");
        validationHeading.textContent = "Item validations";
        const addValidationButton = document.createElement("button");
        addValidationButton.type = "button";
        addValidationButton.className = "button button-secondary";
        addValidationButton.textContent = "Добави item validation";
        addValidationButton.addEventListener(
            "click",
            () => openItemValidationModal(
                name,
                collection,
                profileName
            )
        );
        validationSection.append(
            validationHeading,
            addValidationButton
        );

        const itemValidations = collection.item_validations || [];
        if (!itemValidations.length) {
            const emptyValidations = document.createElement("div");
            emptyValidations.className = "form-help";
            emptyValidations.textContent = (
                "Колекцията още няма item validations."
            );
            validationSection.appendChild(emptyValidations);
        }

        itemValidations.forEach((validation, index) => {
            const row = document.createElement("div");
            row.className = "field-detail";
            const summary = document.createElement("span");
            summary.className = "field-detail-label";
            summary.textContent = (
                `${validation.result} = ${validation.minuend}`
                + ` - ${validation.subtrahend}`
            );
            const validationActions = document.createElement("span");
            validationActions.className = "field-actions";
            const editValidationButton = document.createElement("button");
            editValidationButton.type = "button";
            editValidationButton.className = "button button-secondary";
            editValidationButton.textContent = "Редактирай validation";
            editValidationButton.addEventListener(
                "click",
                () => openItemValidationModal(
                    name,
                    collection,
                    profileName,
                    index
                )
            );
            const deleteValidationButton = document.createElement("button");
            deleteValidationButton.type = "button";
            deleteValidationButton.className = (
                "button button-danger-outline"
            );
            deleteValidationButton.textContent = "Изтрий validation";
            deleteValidationButton.addEventListener(
                "click",
                () => confirmDeleteItemValidation(
                    name,
                    collection,
                    profileName,
                    index
                )
            );
            validationActions.append(
                editValidationButton,
                deleteValidationButton
            );
            row.append(summary, validationActions);
            validationSection.appendChild(row);
        });

        card.append(
            header,
            details,
            fieldSection,
            validationSection
        );
        el.collectionList.appendChild(card);
    }
}


async function saveCollectionDefinition(
    collectionName,
    collection,
    profileName
) {
    await apiRequest(
        collectionEndpoint(
            state.selectedDocumentType,
            collectionName,
            profileName
        ),
        {
            method: "PUT",
            body: JSON.stringify({ collection }),
        }
    );
}

function openItemValidationModal(
    collectionName,
    collection,
    profileName = null,
    validationIndex = null
) {
    const isEditing = validationIndex !== null;
    const existingValidation = isEditing
        ? collection.item_validations?.[validationIndex]
        : null;
    const fieldNames = (collection.fields || []).map(
        (field) => field.name
    );
    if (!fieldNames.length) {
        showMessage(
            "Добавете поне едно поле преди item validation.",
            "error"
        );
        return;
    }

    const formElement = document.createElement("form");
    formElement.className = "form-grid";
    const type = selectInput(
        "itemValidationType",
        "Validation тип",
        existingValidation?.type || "difference_equals",
        ["difference_equals"]
    );
    const minuend = selectInput(
        "itemValidationMinuend",
        "Minuend поле",
        existingValidation?.minuend || fieldNames[0],
        fieldNames
    );
    const subtrahend = selectInput(
        "itemValidationSubtrahend",
        "Subtrahend поле",
        existingValidation?.subtrahend || fieldNames[0],
        fieldNames
    );
    const result = selectInput(
        "itemValidationResult",
        "Result поле",
        existingValidation?.result || fieldNames[0],
        fieldNames
    );
    const message = textInput(
        "itemValidationMessage",
        "Съобщение при грешка",
        existingValidation?.message || ""
    );
    formElement.append(
        type.group,
        minuend.group,
        subtrahend.group,
        result.group,
        message.group
    );

    openModal({
        title: isEditing
            ? "Редакция на item validation"
            : "Добавяне на item validation",
        body: formElement,
        onConfirm: async () => {
            if (!formElement.reportValidity()) return;
            const validation = {
                type: type.select.value,
                minuend: minuend.select.value,
                subtrahend: subtrahend.select.value,
                result: result.select.value,
            };
            const validationMessage = message.input.value.trim();
            if (validationMessage) {
                validation.message = validationMessage;
            }
            const updatedCollection = structuredClone(collection);
            const validations = [
                ...(updatedCollection.item_validations || []),
            ];
            if (isEditing) {
                validations[validationIndex] = validation;
            } else {
                validations.push(validation);
            }
            updatedCollection.item_validations = validations;
            await saveCollectionDefinition(
                collectionName,
                updatedCollection,
                profileName
            );
            closeModal();
            await loadConfiguration();
            showMessage(
                isEditing
                    ? "Item validation е актуализирана."
                    : "Item validation е добавена."
            );
        },
    });
}

function confirmDeleteItemValidation(
    collectionName,
    collection,
    profileName,
    validationIndex
) {
    const body = document.createElement("div");
    body.textContent = "Изтриване на item validation?";
    openModal({
        title: "Изтриване на item validation",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            const updatedCollection = structuredClone(collection);
            updatedCollection.item_validations = [
                ...(updatedCollection.item_validations || []),
            ];
            updatedCollection.item_validations.splice(
                validationIndex,
                1
            );
            await saveCollectionDefinition(
                collectionName,
                updatedCollection,
                profileName
            );
            closeModal();
            await loadConfiguration();
            showMessage("Item validation е изтрита.");
        },
    });
}

function buildCollectionPayload(form, existingCollection) {
    const collection = {
        cardinality: form.cardinality.select.value,
        fields: structuredClone(existingCollection?.fields || []),
        item_validations: structuredClone(
            existingCollection?.item_validations || []
        ),
    };
    const startPattern = form.startPattern.input.value.trim();
    if (startPattern) collection.start_pattern = startPattern;
    return collection;
}

function openCollectionModal(
    existingName = null,
    existingCollection = null,
    profileName = null
) {
    const isEditing = Boolean(existingName);
    const formElement = document.createElement("form");
    formElement.className = "form-grid";

    const name = textInput(
        "collectionName",
        "Системно име",
        existingName || "",
        {
            required: true,
            pattern: "^[a-z][a-z0-9_]*$",
            fullWidth: false,
        }
    );
    name.input.disabled = isEditing;

    const cardinality = selectInput(
        "collectionCardinality",
        "Кардиналност",
        existingCollection?.cardinality || "zero_or_more",
        ["zero_or_more", "one_or_more", "exactly_one"]
    );
    const startPattern = textInput(
        "collectionStartPattern",
        "Start pattern",
        existingCollection?.start_pattern || "",
        {
            help: "Optional regex, marking the start of each item.",
        }
    );

    const preserved = document.createElement("div");
    preserved.className = "form-help form-group full-width";
    preserved.textContent = isEditing
        ? "Полетата и item validations се запазват непроменени."
        : "Полетата и item validations се добавят в следващата стъпка.";

    formElement.append(
        name.group,
        cardinality.group,
        startPattern.group,
        preserved
    );

    const form = { name, cardinality, startPattern };
    openModal({
        title: isEditing
            ? `Редакция на колекция '${existingName}'`
            : "Добавяне на колекция",
        body: formElement,
        onConfirm: async () => {
            if (!formElement.reportValidity()) return;
            const collectionName = isEditing
                ? existingName
                : name.input.value.trim();
            const collection = buildCollectionPayload(
                form,
                existingCollection
            );
            await apiRequest(
                collectionEndpoint(
                    state.selectedDocumentType,
                    collectionName,
                    profileName
                ),
                {
                    method: isEditing ? "PUT" : "POST",
                    body: JSON.stringify({ collection }),
                }
            );
            closeModal();
            await loadConfiguration();
            showMessage(
                isEditing
                    ? `Колекцията '${collectionName}' е актуализирана.`
                    : `Колекцията '${collectionName}' е добавена.`
            );
        },
    });
}

function confirmDeleteCollection(
    collectionName,
    profileName = null
) {
    const body = document.createElement("div");
    body.textContent = (
        `Изтриване на колекцията '${collectionName}' `
        + "заедно с нейните полета и validations?"
    );
    openModal({
        title: "Изтриване на колекция",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            await apiRequest(
                collectionEndpoint(
                    state.selectedDocumentType,
                    collectionName,
                    profileName
                ),
                { method: "DELETE" }
            );
            closeModal();
            await loadConfiguration();
            showMessage(
                `Колекцията '${collectionName}' е изтрита.`
            );
        },
    });
}


function summaryValidationEndpoint(
    documentType,
    profileName,
    validationIndex = null
) {
    const base = (
        `/document-types/${encodeURIComponent(documentType)}`
        + `/profiles/${encodeURIComponent(profileName)}`
        + "/summary-validations"
    );
    return validationIndex === null
        ? base
        : `${base}/${validationIndex}`;
}

function getProfileScalarFieldNames(config, profileName) {
    return [
        ...(config.common_fields || []),
        ...(config.profiles?.[profileName]?.fields || []),
    ].map((field) => field.name);
}

function renderSummaryValidations(config) {
    const profileName = getSelectedProfile(config);
    const profileScope = (
        state.selectedFieldScope === "profile" && profileName
    );
    el.summaryValidationSection.classList.toggle(
        "hidden",
        !profileScope
    );
    el.summaryValidationList.replaceChildren();
    if (!profileScope) return;

    const validations = (
        config.profiles?.[profileName]?.summary_validations || []
    );
    if (!validations.length) {
        const empty = document.createElement("div");
        empty.className = "loading-state";
        empty.textContent = "Профилът още няма summary validations.";
        el.summaryValidationList.appendChild(empty);
        return;
    }

    validations.forEach((validation, index) => {
        const card = document.createElement("article");
        card.className = "field-card";
        const title = document.createElement("h3");
        title.className = "field-title";
        title.textContent = (
            `${validation.collection}.${validation.item_field}`
            + ` = ${validation.target_field}`
        );
        const details = document.createElement("div");
        details.className = "field-details";
        addDetail(details, "type", validation.type);
        addDetail(details, "message", validation.message || "няма");
        const actions = document.createElement("div");
        actions.className = "field-actions";
        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "button button-secondary";
        editButton.textContent = "Редактирай";
        editButton.addEventListener(
            "click",
            () => openSummaryValidationModal(
                config,
                profileName,
                index,
                validation
            )
        );
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "button button-danger-outline";
        deleteButton.textContent = "Изтрий";
        deleteButton.addEventListener(
            "click",
            () => confirmDeleteSummaryValidation(profileName, index)
        );
        actions.append(editButton, deleteButton);
        card.append(title, details, actions);
        el.summaryValidationList.appendChild(card);
    });
}

function openSummaryValidationModal(
    config,
    profileName,
    validationIndex = null,
    existingValidation = null
) {
    const profile = config.profiles?.[profileName] || {};
    const collections = profile.collections || {};
    const collectionNames = Object.keys(collections).sort();
    const targetFields = getProfileScalarFieldNames(config, profileName);
    if (!collectionNames.length || !targetFields.length) {
        showMessage(
            "Summary validation изисква profile collection и scalar target поле.",
            "error"
        );
        return;
    }

    const form = document.createElement("form");
    form.className = "form-grid";
    const type = selectInput(
        "summaryValidationType",
        "Validation тип",
        existingValidation?.type || "collection_sum_equals_field",
        ["collection_sum_equals_field"]
    );
    const collection = selectInput(
        "summaryValidationCollection",
        "Колекция",
        existingValidation?.collection || collectionNames[0],
        collectionNames
    );
    const itemField = selectInput(
        "summaryValidationItemField",
        "Collection item поле",
        existingValidation?.item_field || "",
        []
    );
    const targetField = selectInput(
        "summaryValidationTargetField",
        "Target scalar поле",
        existingValidation?.target_field || targetFields[0],
        targetFields
    );
    const message = textInput(
        "summaryValidationMessage",
        "Съобщение при грешка",
        existingValidation?.message || ""
    );

    function refreshItemFields() {
        const fieldNames = (
            collections[collection.select.value]?.fields || []
        ).map((field) => field.name);
        const preferred = itemField.select.value
            || existingValidation?.item_field;
        itemField.select.replaceChildren();
        for (const name of fieldNames) {
            const option = new Option(name, name);
            option.selected = name === preferred;
            itemField.select.append(option);
        }
        itemField.select.required = true;
    }
    collection.select.addEventListener("change", refreshItemFields);
    refreshItemFields();
    form.append(
        type.group,
        collection.group,
        itemField.group,
        targetField.group,
        message.group
    );

    const isEditing = validationIndex !== null;
    openModal({
        title: isEditing
            ? "Редакция на summary validation"
            : "Добавяне на summary validation",
        body: form,
        onConfirm: async () => {
            if (!form.reportValidity()) return;
            const validation = {
                type: type.select.value,
                collection: collection.select.value,
                item_field: itemField.select.value,
                target_field: targetField.select.value,
            };
            const validationMessage = message.input.value.trim();
            if (validationMessage) validation.message = validationMessage;
            await apiRequest(
                summaryValidationEndpoint(
                    state.selectedDocumentType,
                    profileName,
                    validationIndex
                ),
                {
                    method: isEditing ? "PUT" : "POST",
                    body: JSON.stringify({ validation }),
                }
            );
            closeModal();
            await loadConfiguration();
            showMessage(
                isEditing
                    ? "Summary validation е актуализирана."
                    : "Summary validation е добавена."
            );
        },
    });
}

function confirmDeleteSummaryValidation(profileName, validationIndex) {
    const body = document.createElement("div");
    body.textContent = "Изтриване на summary validation?";
    openModal({
        title: "Изтриване на summary validation",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            await apiRequest(
                summaryValidationEndpoint(
                    state.selectedDocumentType,
                    profileName,
                    validationIndex
                ),
                { method: "DELETE" }
            );
            closeModal();
            await loadConfiguration();
            showMessage("Summary validation е изтрита.");
        },
    });
}

function selectDocumentType(name) {
    if (state.selectedDocumentType !== name) {
        state.selectedProfileName = null;
    }
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
    updateFieldScope(config);
    renderProfileMatching(config);
    renderFields(config);
    renderCollections(config);
    renderSummaryValidations(config);
}

async function loadConfiguration(preserveSelection = true) {
    el.documentTypeList.innerHTML = '<div class="loading-state">Зареждане...</div>';

    try {
        const response = await apiRequest("/document-types");
        state.documentTypes =
            response.document_types || {};

        state.resolvedDocumentTypes =
            response.resolved_document_types || {};

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
        state.resolvedDocumentTypes = {};
        state.documentTypeMetadata = {};
        state.selectedDocumentType = null;
        renderDocumentTypes();
        selectDocumentType(null);
        showMessage(error.message, "error");
    }
}

function getModalFocusableElements() {
    return Array.from(
        el.configurationModal.querySelectorAll(
            'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
        )
    ).filter((element) => !element.closest(".hidden"));
}

function openModal({ title, body, confirmText = "Запази", onConfirm }) {
    state.modalReturnFocus =
        document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;
    el.modalTitle.textContent = title;
    el.modalBody.replaceChildren();
    el.modalBody.appendChild(body);
    el.confirmModalButton.textContent = confirmText;
    state.modalConfirmHandler = onConfirm;
    el.modalBackdrop.classList.remove("hidden");
    const initialFocus =
        el.modalBody.querySelector("input, select, textarea")
        || el.closeModalButton;
    initialFocus.focus();
}

function closeModal() {
    if (el.modalBackdrop.classList.contains("hidden")) return;
    el.modalBackdrop.classList.add("hidden");
    el.modalBody.replaceChildren();
    state.modalConfirmHandler = null;
    const returnFocus = state.modalReturnFocus;
    state.modalReturnFocus = null;
    if (returnFocus?.isConnected) returnFocus.focus();
}

function trapModalFocus(event) {
    if (
        event.key !== "Tab"
        || el.modalBackdrop.classList.contains("hidden")
    ) {
        return;
    }

    const focusable = getModalFocusableElements();
    if (!focusable.length) {
        event.preventDefault();
        el.configurationModal.focus();
        return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
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

function openFieldModal(
    existingField = null,
    collectionName = null,
    collectionProfileName = null
) {
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
        title: collectionName
            ? (
                isEditing
                    ? `Редакция на '${existingField.name}' в '${collectionName}'`
                    : `Добавяне на поле в '${collectionName}'`
            )
            : (
                isEditing
                    ? `Редакция на '${existingField.name}'`
                    : "Добавяне на поле"
            ),
        body: formElement,
        onConfirm: async () => {
            if (!formElement.reportValidity()) return;
            const field = buildFieldPayload(form, existingField);
            const documentType = state.selectedDocumentType;

            const endpoint = buildFieldEndpoint(
                documentType,
                isEditing ? existingField.name : null,
                collectionName,
                collectionProfileName
            );

            await apiRequest(endpoint, {
                method: isEditing ? "PUT" : "POST",
                body: JSON.stringify({ field }),
            });

            closeModal();
            await loadConfiguration();
            showMessage(
                isEditing
                    ? `Полето '${existingField.name}' е актуализирано.`
                    : `Полето '${field.name}' е добавено.`
            );
        },
    });
}

function confirmDeleteField(
    field,
    collectionName = null,
    collectionProfileName = null
) {
    const body = document.createElement("div");
    body.textContent = `Изтриване на полето '${field.name}'?`;

    openModal({
        title: "Изтриване на поле",
        body,
        confirmText: "Изтрий",
        onConfirm: async () => {
            const endpoint = buildFieldEndpoint(
                state.selectedDocumentType,
                field.name,
                collectionName,
                collectionProfileName
            );
            await apiRequest(endpoint, {
                method: "DELETE",
            });
            closeModal();
            await loadConfiguration();
            showMessage(`Полето '${field.name}' е изтрито.`);
        },
    });
}

el.openAddSummaryValidationButton.addEventListener(
    "click",
    () => {
        const config = state.documentTypes[
            state.selectedDocumentType
        ];
        const profileName = getSelectedProfile(config);
        openSummaryValidationModal(config, profileName);
    }
);

el.openAddCollectionButton.addEventListener(
    "click",
    () => {
        const config = state.documentTypes[
            state.selectedDocumentType
        ];
        const { profileName } = getSelectedCollectionContext(config);
        openCollectionModal(null, null, profileName);
    }
);

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
    if (
        event.key === "Escape"
        && !el.modalBackdrop.classList.contains("hidden")
    ) {
        closeModal();
        return;
    }
    trapModalFocus(event);
});
el.navRefresh.addEventListener("click", async () => {
    await loadConfiguration();
    showMessage("Конфигурацията е обновена.");
});
el.openCreateDocumentTypeButton.addEventListener("click", openCreateDocumentTypeModal);
el.renameDocumentTypeButton.addEventListener("click", openRenameDocumentTypeModal);
el.deleteDocumentTypeButton.addEventListener("click", confirmDeleteDocumentType);
el.openAddFieldButton.addEventListener("click", () => openFieldModal());
el.openAddProfileButton.addEventListener("click", openAddProfileModal);
el.deleteProfileButton.addEventListener("click", confirmDeleteProfile);
el.editProfileMatchingButton.addEventListener(
    "click",
    openProfileMatchingModal
);
el.profileSelector.addEventListener("change", () => {
    state.selectedProfileName = el.profileSelector.value || null;
    state.selectedFieldScope = "profile";
    const config = state.documentTypes[state.selectedDocumentType];
    updateFieldScope(config);
    renderProfileMatching(config);
    renderFields(config);
    renderCollections(config);
    renderSummaryValidations(config);
});
el.fieldScope.addEventListener("change", () => {
    state.selectedFieldScope = el.fieldScope.value;
    const config = state.documentTypes[state.selectedDocumentType];
    renderFields(config);
    renderCollections(config);
    renderSummaryValidations(config);
});

async function initializeApplication() {
    await window.documentAuth.initialize();
    await checkApiHealth();
    await loadConfiguration(false);
}

initializeApplication();
