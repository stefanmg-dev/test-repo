const API_BASE = "/api/v1/config";

const state = {
    documentTypes: {},
    selectedDocumentType: null,
    modalConfirmHandler: null
};


const elements = {
    apiStatusIndicator: document.getElementById(
        "apiStatusIndicator"
    ),
    apiStatusText: document.getElementById(
        "apiStatusText"
    ),
    documentTypeCount: document.getElementById(
        "documentTypeCount"
    ),
    documentTypeList: document.getElementById(
        "documentTypeList"
    ),
    emptyEditorState: document.getElementById(
        "emptyEditorState"
    ),
    documentEditor: document.getElementById(
        "documentEditor"
    ),
    selectedDocumentTypeName: document.getElementById(
        "selectedDocumentTypeName"
    ),
    selectedDocumentTypeSummary: document.getElementById(
        "selectedDocumentTypeSummary"
    ),
    fieldList: document.getElementById(
        "fieldList"
    ),
    messageArea: document.getElementById(
        "messageArea"
    ),
    modalBackdrop: document.getElementById(
        "modalBackdrop"
    ),
    modalTitle: document.getElementById(
        "modalTitle"
    ),
    modalBody: document.getElementById(
        "modalBody"
    ),
    confirmModalButton: document.getElementById(
        "confirmModalButton"
    ),
    cancelModalButton: document.getElementById(
        "cancelModalButton"
    ),
    closeModalButton: document.getElementById(
        "closeModalButton"
    ),
    navRefresh: document.getElementById(
        "navRefresh"
    ),
    openCreateDocumentTypeButton: document.getElementById(
        "openCreateDocumentTypeButton"
    ),
    renameDocumentTypeButton: document.getElementById(
        "renameDocumentTypeButton"
    ),
    deleteDocumentTypeButton: document.getElementById(
        "deleteDocumentTypeButton"
    ),
    openAddFieldButton: document.getElementById(
        "openAddFieldButton"
    ),
    fieldCardTemplate: document.getElementById(
        "fieldCardTemplate"
    )
};


async function apiRequest(
    path,
    options = {}
) {
    const requestOptions = {
        ...options,
        headers: {
            Accept: "application/json",
            ...(options.body
                ? { "Content-Type": "application/json" }
                : {}),
            ...(options.headers || {})
        }
    };

    const response = await fetch(
        `${API_BASE}${path}`,
        requestOptions
    );

    if (response.status === 204) {
        return null;
    }

    let responseBody = null;

    try {
        responseBody = await response.json();
    } catch {
        responseBody = null;
    }

    if (!response.ok) {
        const detail = responseBody?.detail;

        if (Array.isArray(detail)) {
            const messages = detail.map((item) => {
                const location = item.loc
                    ? item.loc.join(".")
                    : "request";

                return `${location}: ${item.msg}`;
            });

            throw new Error(messages.join("\n"));
        }

        throw new Error(
            detail ||
            `HTTP ${response.status}`
        );
    }

    return responseBody;
}


async function checkApiHealth() {
    try {
        const response = await fetch(
            "/health",
            {
                headers: {
                    Accept: "application/json"
                }
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        elements.apiStatusIndicator.classList.remove(
            "offline"
        );

        elements.apiStatusIndicator.classList.add(
            "online"
        );

        elements.apiStatusText.textContent =
            "API е достъпно";

    } catch {
        elements.apiStatusIndicator.classList.remove(
            "online"
        );

        elements.apiStatusIndicator.classList.add(
            "offline"
        );

        elements.apiStatusText.textContent =
            "API не е достъпно";
    }
}


function showMessage(
    message,
    type = "success"
) {
    elements.messageArea.textContent = message;

    elements.messageArea.classList.remove(
        "success",
        "error"
    );

    elements.messageArea.classList.add(type);

    window.clearTimeout(
        showMessage.timeoutId
    );

    showMessage.timeoutId = window.setTimeout(
        clearMessage,
        5000
    );
}


function clearMessage() {
    elements.messageArea.textContent = "";

    elements.messageArea.classList.remove(
        "success",
        "error"
    );
}


function getFieldLabel(field) {
    return (
        field.label?.bg ||
        field.label?.en ||
        field.name
    );
}


function createDetailElement(
    label,
    value
) {
    const wrapper = document.createElement("div");
    wrapper.className = "field-detail";

    const labelElement = document.createElement("span");
    labelElement.className = "field-detail-label";
    labelElement.textContent = label;

    const valueElement = document.createElement("span");
    valueElement.className = "field-detail-value";

    if (
        typeof value === "object" &&
        value !== null
    ) {
        valueElement.textContent = JSON.stringify(
            value,
            null,
            2
        );
    } else {
        valueElement.textContent =
            value === undefined ||
            value === null ||
            value === ""
                ? "Няма стойност"
                : String(value);
    }

    wrapper.append(
        labelElement,
        valueElement
    );

    return wrapper;
}


function renderDocumentTypes() {
    const entries = Object.entries(
        state.documentTypes
    );

    elements.documentTypeCount.textContent =
        String(entries.length);

    elements.documentTypeList.replaceChildren();

    if (!entries.length) {
        const emptyElement = document.createElement(
            "div"
        );

        emptyElement.className = "loading-state";
        emptyElement.textContent =
            "Няма конфигурирани типове.";

        elements.documentTypeList.appendChild(
            emptyElement
        );

        selectDocumentType(null);
        return;
    }

    for (
        const [documentType, documentConfig]
        of entries
    ) {
        const button = document.createElement(
            "button"
        );

        button.type = "button";
        button.className = "document-type-item";

        if (
            documentType ===
            state.selectedDocumentType
        ) {
            button.classList.add("active");
        }

        const nameElement = document.createElement(
            "span"
        );

        nameElement.className =
            "document-type-item-name";

        nameElement.textContent = documentType;

        const countElement = document.createElement(
            "span"
        );

        countElement.className =
            "document-type-item-count";

        const fieldCount =
            documentConfig.fields?.length || 0;

        countElement.textContent =
            `${fieldCount} полета`;

        button.append(
            nameElement,
            countElement
        );

        button.addEventListener(
            "click",
            () => selectDocumentType(documentType)
        );

        elements.documentTypeList.appendChild(
            button
        );
    }
}


function renderFieldDetails(
    container,
    field
) {
    const ignoredProperties = new Set([
        "name",
        "label",
        "validation"
    ]);

    for (
        const [propertyName, propertyValue]
        of Object.entries(field)
    ) {
        if (
            ignoredProperties.has(propertyName)
        ) {
            continue;
        }

        container.appendChild(
            createDetailElement(
                propertyName,
                propertyValue
            )
        );
    }

    if (field.validation?.length) {
        container.appendChild(
            createDetailElement(
                "validation",
                field.validation
            )
        );
    }
}


function renderFields(documentConfig) {
    elements.fieldList.replaceChildren();

    const fields = documentConfig.fields || [];

    if (!fields.length) {
        const emptyElement = document.createElement(
            "div"
        );

        emptyElement.className = "loading-state";
        emptyElement.textContent =
            "Този тип документ още няма полета.";

        elements.fieldList.appendChild(
            emptyElement
        );

        return;
    }

    for (const field of fields) {
        const fragment =
            elements.fieldCardTemplate.content
                .cloneNode(true);

        const titleElement =
            fragment.querySelector(".field-title");

        const typeElement =
            fragment.querySelector(
                ".field-type-badge"
            );

        const nameElement =
            fragment.querySelector(".field-name");

        const detailsElement =
            fragment.querySelector(
                ".field-details"
            );

        const editButton =
            fragment.querySelector(
                ".edit-field-button"
            );

        const deleteButton =
            fragment.querySelector(
                ".delete-field-button"
            );

        titleElement.textContent =
            getFieldLabel(field);

        typeElement.textContent = field.type;
        nameElement.textContent = field.name;

        renderFieldDetails(
            detailsElement,
            field
        );

        editButton.addEventListener(
            "click",
            () => openFieldModal(field)
        );

        deleteButton.addEventListener(
            "click",
            () => confirmDeleteField(field)
        );

        elements.fieldList.appendChild(
            fragment
        );
    }
}


function selectDocumentType(documentType) {
    state.selectedDocumentType = documentType;

    renderDocumentTypes();

    if (!documentType) {
        elements.emptyEditorState.classList.remove(
            "hidden"
        );

        elements.documentEditor.classList.add(
            "hidden"
        );

        return;
    }

    const documentConfig =
        state.documentTypes[documentType];

    if (!documentConfig) {
        selectDocumentType(null);
        return;
    }

    elements.emptyEditorState.classList.add(
        "hidden"
    );

    elements.documentEditor.classList.remove(
        "hidden"
    );

    elements.selectedDocumentTypeName.textContent =
        documentType;

    const fieldCount =
        documentConfig.fields?.length || 0;

    elements.selectedDocumentTypeSummary.textContent =
        `${fieldCount} конфигурирани полета`;

    renderFields(documentConfig);
}


async function loadConfiguration(
    preserveSelection = true
) {
    clearMessage();

    elements.documentTypeList.innerHTML =
        '<div class="loading-state">Зареждане...</div>';

    try {
        const response = await apiRequest(
            "/document-types"
        );

        state.documentTypes =
            response.document_types || {};

        const availableTypes = Object.keys(
            state.documentTypes
        );

        if (
            !preserveSelection ||
            !state.selectedDocumentType ||
            !state.documentTypes[
                state.selectedDocumentType
            ]
        ) {
            state.selectedDocumentType =
                availableTypes[0] || null;
        }

        renderDocumentTypes();

        selectDocumentType(
            state.selectedDocumentType
        );

    } catch (error) {
        state.documentTypes = {};
        state.selectedDocumentType = null;

        renderDocumentTypes();
        selectDocumentType(null);

        showMessage(
            error.message,
            "error"
        );
    }
}


function openModal({
    title,
    body,
    confirmText = "Запази",
    onConfirm
}) {
    elements.modalTitle.textContent = title;
    elements.modalBody.replaceChildren();

    if (typeof body === "string") {
        elements.modalBody.innerHTML = body;
    } else {
        elements.modalBody.appendChild(body);
    }

    elements.confirmModalButton.textContent =
        confirmText;

    state.modalConfirmHandler = onConfirm;

    elements.modalBackdrop.classList.remove(
        "hidden"
    );

    const firstInput =
        elements.modalBody.querySelector(
            "input, select, textarea"
        );

    firstInput?.focus();
}


function closeModal() {
    elements.modalBackdrop.classList.add(
        "hidden"
    );

    elements.modalBody.replaceChildren();

    state.modalConfirmHandler = null;
}


function createTextInput({
    id,
    label,
    value = "",
    help = "",
    required = false,
    pattern = null,
    fullWidth = true
}) {
    const group = document.createElement("div");

    group.className = fullWidth
        ? "form-group full-width"
        : "form-group";

    const labelElement = document.createElement(
        "label"
    );

    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const input = document.createElement("input");

    input.id = id;
    input.className = "form-control";
    input.type = "text";
    input.value = value;
    input.required = required;

    if (pattern) {
        input.pattern = pattern;
    }

    group.append(
        labelElement,
        input
    );

    if (help) {
        const helpElement = document.createElement(
            "div"
        );

        helpElement.className = "form-help";
        helpElement.textContent = help;

        group.appendChild(helpElement);
    }

    return {
        group,
        input
    };
}


function openCreateDocumentTypeModal() {
    const form = document.createElement("form");
    form.className = "form-grid";

    const documentTypeInput = createTextInput({
        id: "newDocumentType",
        label: "Системно име",
        help: (
            "Използвай малки латински букви, " +
            "цифри и долна черта."
        ),
        required: true,
        pattern: "^[a-z][a-z0-9_]*$"
    });

    form.appendChild(
        documentTypeInput.group
    );

    openModal({
        title: "Нов тип документ",
        body: form,
        confirmText: "Създай",

        onConfirm: async () => {
            if (!form.reportValidity()) {
                return;
            }

            const documentType =
                documentTypeInput.input.value.trim();

            await apiRequest(
                "/document-types",
                {
                    method: "POST",
                    body: JSON.stringify({
                        document_type: documentType
                    })
                }
            );

            state.selectedDocumentType =
                documentType;

            closeModal();

            await loadConfiguration();

            showMessage(
                `Типът '${documentType}' е създаден.`
            );
        }
    });
}


function openRenameDocumentTypeModal() {
    const currentName =
        state.selectedDocumentType;

    if (!currentName) {
        return;
    }

    const form = document.createElement("form");
    form.className = "form-grid";

    const nameInput = createTextInput({
        id: "renamedDocumentType",
        label: "Ново системно име",
        value: currentName,
        required: true,
        pattern: "^[a-z][a-z0-9_]*$"
    });

    form.appendChild(nameInput.group);

    openModal({
        title: `Преименуване на '${currentName}'`,
        body: form,

        onConfirm: async () => {
            if (!form.reportValidity()) {
                return;
            }

            const newName =
                nameInput.input.value.trim();

            await apiRequest(
                `/document-types/${encodeURIComponent(
                    currentName
                )}/rename`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        new_document_type: newName
                    })
                }
            );

            state.selectedDocumentType = newName;

            closeModal();

            await loadConfiguration();

            showMessage(
                `Типът е преименуван на '${newName}'.`
            );
        }
    });
}


function confirmDeleteDocumentType() {
    const documentType =
        state.selectedDocumentType;

    if (!documentType) {
        return;
    }

    const body = document.createElement("div");

    const text = document.createElement("p");

    text.textContent =
        `Сигурен ли си, че искаш да изтриеш ` +
        `типа '${documentType}' и всички негови полета?`;

    body.appendChild(text);

    openModal({
        title: "Изтриване на тип документ",
        body,
        confirmText: "Изтрий",

        onConfirm: async () => {
            await apiRequest(
                `/document-types/${encodeURIComponent(
                    documentType
                )}`,
                {
                    method: "DELETE"
                }
            );

            state.selectedDocumentType = null;

            closeModal();

            await loadConfiguration(false);

            showMessage(
                `Типът '${documentType}' е изтрит.`
            );
        }
    });
}


function createSelectInput({
    id,
    label,
    value,
    options
}) {
    const group = document.createElement("div");
    group.className = "form-group";

    const labelElement = document.createElement(
        "label"
    );

    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const select = document.createElement("select");

    select.id = id;
    select.className = "form-control";

    for (const optionValue of options) {
        const option = document.createElement(
            "option"
        );

        option.value = optionValue;
        option.textContent = optionValue;

        if (optionValue === value) {
            option.selected = true;
        }

        select.appendChild(option);
    }

    group.append(
        labelElement,
        select
    );

    return {
        group,
        select
    };
}


function createTextarea({
    id,
    label,
    value = "",
    help = ""
}) {
    const group = document.createElement("div");
    group.className = "form-group full-width";

    const labelElement = document.createElement(
        "label"
    );

    labelElement.htmlFor = id;
    labelElement.textContent = label;

    const textarea = document.createElement(
        "textarea"
    );

    textarea.id = id;
    textarea.className = "form-control";
    textarea.value = value;

    group.append(
        labelElement,
        textarea
    );

    if (help) {
        const helpElement = document.createElement(
            "div"
        );

        helpElement.className = "form-help";
        helpElement.textContent = help;

        group.appendChild(helpElement);
    }

    return {
        group,
        textarea
    };
}


function buildFieldPayload(formElements) {
    const fieldType =
        formElements.type.select.value;

    const field = {
        name: formElements.name.input.value.trim(),
        type: fieldType,
        occurrence:
            formElements.occurrence.select.value,
        validation: []
    };

    const labelBg =
        formElements.labelBg.input.value.trim();

    const labelEn =
        formElements.labelEn.input.value.trim();

    if (labelBg || labelEn) {
        field.label = {};

        if (labelBg) {
            field.label.bg = labelBg;
        }

        if (labelEn) {
            field.label.en = labelEn;
        }
    }

    if (fieldType === "constant") {
        field.value =
            formElements.primaryValue
                .textarea.value;
    }

    if (fieldType === "regex") {
        field.rule =
            formElements.primaryValue
                .textarea.value.trim();
    }

    if (fieldType === "regex_list") {
        field.rules =
            formElements.primaryValue
                .textarea.value
                .split("\n")
                .map((value) => value.trim())
                .filter(Boolean);
    }

    if (fieldType === "nearby") {
        field.anchor =
            formElements.anchor.input.value.trim();

        field.pattern =
            formElements.primaryValue
                .textarea.value.trim();

        field.direction =
            formElements.direction.select.value;

        field.window_size = Number(
            formElements.windowSize.input.value
        );
    }

    return field;
}


function updateFieldFormVisibility(
    formElements
) {
    const fieldType =
        formElements.type.select.value;

    const isNearby =
        fieldType === "nearby";

    formElements.anchor.group.classList.toggle(
        "hidden",
        !isNearby
    );

    formElements.direction.group.classList.toggle(
        "hidden",
        !isNearby
    );

    formElements.windowSize.group.classList.toggle(
        "hidden",
        !isNearby
    );

    const primaryLabel =
        formElements.primaryValue
            .group.querySelector("label");

    const primaryHelp =
        formElements.primaryValue
            .group.querySelector(".form-help");

    formElements.primaryValue.group.classList.toggle(
        "hidden",
        fieldType === "llm"
    );

    if (fieldType === "constant") {
        primaryLabel.textContent = "Константна стойност";
        primaryHelp.textContent =
            "Стойността се връща без търсене.";
    }

    if (fieldType === "regex") {
        primaryLabel.textContent = "Regex правило";
        primaryHelp.textContent =
            "Постави regex с capture group за стойността.";
    }

    if (fieldType === "regex_list") {
        primaryLabel.textContent =
            "Regex правила";

        primaryHelp.textContent =
            "По едно regex правило на ред.";
    }

    if (fieldType === "nearby") {
        primaryLabel.textContent =
            "Regex pattern";

        primaryHelp.textContent =
            "Regex, приложен в прозореца около anchor.";
    }
}


function openFieldModal(existingField = null) {
    const isEditing = Boolean(existingField);

    const form = document.createElement("form");
    form.className = "form-grid";

    const name = createTextInput({
        id: "fieldName",
        label: "Системно име",
        value: existingField?.name || "",
        required: true,
        pattern: "^[a-z][a-z0-9_]*$",
        fullWidth: false
    });

    const type = createSelectInput({
        id: "fieldType",
        label: "Extraction тип",
        value: existingField?.type || "regex",
        options: [
            "constant",
            "regex",
            "regex_list",
            "nearby",
            "llm"
        ]
    });

    const labelBg = createTextInput({
        id: "fieldLabelBg",
        label: "Етикет на български",
        value: existingField?.label?.bg || "",
        fullWidth: false
    });

    const labelEn = createTextInput({
        id: "fieldLabelEn",
        label: "Етикет на английски",
        value: existingField?.label?.en || "",
        fullWidth: false
    });

    let primaryValue = "";

    if (existingField?.type === "constant") {
        primaryValue =
            existingField.value ?? "";
    }

    if (existingField?.type === "regex") {
        primaryValue =
            existingField.rule || "";
    }

    if (existingField?.type === "regex_list") {
        primaryValue =
            (existingField.rules || []).join("\n");
    }

    if (existingField?.type === "nearby") {
        primaryValue =
            existingField.pattern || "";
    }

    const primaryValueElement = createTextarea({
        id: "fieldPrimaryValue",
        label: "Правило или стойност",
        value: primaryValue,
        help: "Extraction конфигурация."
    });

    const occurrence = createSelectInput({
        id: "fieldOccurrence",
        label: "Избор на съвпадение",
        value:
            existingField?.occurrence || "last",
        options: [
            "first",
            "last"
        ]
    });

    const direction = createSelectInput({
        id: "fieldDirection",
        label: "Посока",
        value:
            existingField?.direction || "both",
        options: [
            "before",
            "after",
            "both"
        ]
    });

    const anchor = createTextInput({
        id: "fieldAnchor",
        label: "Anchor",
        value: existingField?.anchor || "",
        fullWidth: false
    });

    const windowSize = createTextInput({
        id: "fieldWindowSize",
        label: "Размер на прозореца",
        value: String(
            existingField?.window_size || 400
        ),
        fullWidth: false
    });

    windowSize.input.type = "number";
    windowSize.input.min = "1";
    windowSize.input.max = "10000";

    const formElements = {
        name,
        type,
        labelBg,
        labelEn,
        primaryValue: primaryValueElement,
        occurrence,
        direction,
        anchor,
        windowSize
    };

    form.append(
        name.group,
        type.group,
        labelBg.group,
        labelEn.group,
        occurrence.group,
        direction.group,
        anchor.group,
        windowSize.group,
        primaryValueElement.group
    );

    type.select.addEventListener(
        "change",
        () => updateFieldFormVisibility(
            formElements
        )
    );

    updateFieldFormVisibility(formElements);

    openModal({
        title: isEditing
            ? `Редакция на '${existingField.name}'`
            : "Добавяне на поле",

        body: form,

        onConfirm: async () => {
            if (!form.reportValidity()) {
                return;
            }

            const field =
                buildFieldPayload(formElements);

            const documentType =
                state.selectedDocumentType;

            if (isEditing) {
                await apiRequest(
                    `/document-types/${encodeURIComponent(
                        documentType
                    )}/fields/${encodeURIComponent(
                        existingField.name
                    )}`,
                    {
                        method: "PUT",
                        body: JSON.stringify({
                            field
                        })
                    }
                );

                showMessage(
                    `Полето '${existingField.name}' ` +
                    "е актуализирано."
                );

            } else {
                await apiRequest(
                    `/document-types/${encodeURIComponent(
                        documentType
                    )}/fields`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            field
                        })
                    }
                );

                showMessage(
                    `Полето '${field.name}' е добавено.`
                );
            }

            closeModal();

            await loadConfiguration();
        }
    });
}


function confirmDeleteField(field) {
    const body = document.createElement("div");

    const text = document.createElement("p");

    text.textContent =
        `Сигурен ли си, че искаш да изтриеш ` +
        `полето '${field.name}'?`;

    body.appendChild(text);

    openModal({
        title: "Изтриване на поле",
        body,
        confirmText: "Изтрий",

        onConfirm: async () => {
            const documentType =
                state.selectedDocumentType;

            await apiRequest(
                `/document-types/${encodeURIComponent(
                    documentType
                )}/fields/${encodeURIComponent(
                    field.name
                )}`,
                {
                    method: "DELETE"
                }
            );

            closeModal();

            await loadConfiguration();

            showMessage(
                `Полето '${field.name}' е изтрито.`
            );
        }
    });
}


elements.confirmModalButton.addEventListener(
    "click",
    async () => {
        if (!state.modalConfirmHandler) {
            return;
        }

        elements.confirmModalButton.disabled = true;

        try {
            await state.modalConfirmHandler();

        } catch (error) {
            showMessage(
                error.message,
                "error"
            );

        } finally {
            elements.confirmModalButton.disabled =
                false;
        }
    }
);


elements.cancelModalButton.addEventListener(
    "click",
    closeModal
);


elements.closeModalButton.addEventListener(
    "click",
    closeModal
);


elements.modalBackdrop.addEventListener(
    "click",
    (event) => {
        if (
            event.target ===
            elements.modalBackdrop
        ) {
            closeModal();
        }
    }
);


document.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Escape" &&
            !elements.modalBackdrop.classList.contains(
                "hidden"
            )
        ) {
            closeModal();
        }
    }
);


elements.navRefresh.addEventListener(
    "click",
    async () => {
        await loadConfiguration();

        showMessage(
            "Конфигурацията е обновена."
        );
    }
);


elements.openCreateDocumentTypeButton.addEventListener(
    "click",
    openCreateDocumentTypeModal
);


elements.renameDocumentTypeButton.addEventListener(
    "click",
    openRenameDocumentTypeModal
);


elements.deleteDocumentTypeButton.addEventListener(
    "click",
    confirmDeleteDocumentType
);


elements.openAddFieldButton.addEventListener(
    "click",
    () => openFieldModal()
);


async function initializeApplication() {
    await checkApiHealth();
    await loadConfiguration(false);
}


initializeApplication();