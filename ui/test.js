"use strict";


const CONFIG_URL = "/api/v1/config/document-types";
const EXTRACT_URL = "/extract-document";


const elements = {
    apiStatusIndicator: document.getElementById(
        "apiStatusIndicator"
    ),

    apiStatusText: document.getElementById(
        "apiStatusText"
    ),

    messageArea: document.getElementById(
        "messageArea"
    ),

    form: document.getElementById(
        "documentTestForm"
    ),

    documentType: document.getElementById(
        "documentType"
    ),

    documentFile: document.getElementById(
        "documentFile"
    ),

    extractButton: document.getElementById(
        "extractButton"
    ),

    processingSection: document.getElementById(
        "processingSection"
    ),

    resultSection: document.getElementById(
        "resultSection"
    ),

    qualitySection: document.getElementById(
        "qualitySection"
    ),

    qualityBadge: document.getElementById(
        "qualityBadge"
    ),

    qualitySummary: document.getElementById(
        "qualitySummary"
    ),

    qualityWarnings: document.getElementById(
        "qualityWarnings"
    ),

    qualityDetails: document.getElementById(
        "qualityDetails"
    ),

    diagnosticsSection: document.getElementById(
        "diagnosticsSection"
    ),

    resultSummary: document.getElementById(
        "resultSummary"
    ),

    processingStatusBadge: document.getElementById(
        "processingStatusBadge"
    ),

    validationBadge: document.getElementById(
        "validationBadge"
    ),

    validationErrors: document.getElementById(
        "validationErrors"
    ),

    summaryValidationPanel: document.getElementById(
        "summaryValidationPanel"
    ),

    summaryValidationBadge: document.getElementById(
        "summaryValidationBadge"
    ),

    summaryValidationSummary: document.getElementById(
        "summaryValidationSummary"
    ),

    summaryValidationErrors: document.getElementById(
        "summaryValidationErrors"
    ),

    resultFields: document.getElementById(
        "resultFields"
    ),

    resultCollections: document.getElementById(
        "resultCollections"
    ),

    diagnosticDocumentType: document.getElementById(
        "diagnosticDocumentType"
    ),

    diagnosticProfile: document.getElementById(
        "diagnosticProfile"
    ),

    diagnosticLlmValues: document.getElementById(
        "diagnosticLlmValues"
    ),

    diagnosticRawText: document.getElementById(
        "diagnosticRawText"
    ),

    resultFieldTemplate: document.getElementById(
        "resultFieldTemplate"
    )
};


const state = {
    documentTypes: {},
    resolvedDocumentTypes: {},
    documentTypeMetadata: {},
    processing: false
};


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
    elements.messageArea.setAttribute(
        "role",
        type === "error" ? "alert" : "status"
    );
    elements.messageArea.setAttribute(
        "aria-live",
        type === "error" ? "assertive" : "polite"
    );
}


function clearMessage() {
    elements.messageArea.textContent = "";

    elements.messageArea.classList.remove(
        "success",
        "error"
    );
    elements.messageArea.setAttribute(
        "role",
        "status"
    );
    elements.messageArea.setAttribute(
        "aria-live",
        "polite"
    );
}


function setApiStatus(online) {
    elements.apiStatusIndicator.classList.remove(
        "online",
        "offline"
    );

    elements.apiStatusIndicator.classList.add(
        online ? "online" : "offline"
    );

    elements.apiStatusText.textContent = online
        ? "API е достъпно"
        : "API не е достъпно";
}


async function readJson(response) {
    try {
        return await response.json();

    } catch {
        return null;
    }
}


function responseError(
    response,
    body
) {
    const detail = body?.detail;

    if (Array.isArray(detail)) {
        return detail
            .map((item) => {
                const location = Array.isArray(item.loc)
                    ? item.loc.join(".")
                    : "request";

                return `${location}: ${item.msg}`;
            })
            .join("\n");
    }

    if (
        typeof detail === "string" &&
        detail.trim()
    ) {
        return detail;
    }

    return `HTTP ${response.status}`;
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

        setApiStatus(response.ok);

    } catch {
        setApiStatus(false);
    }
}


async function loadDocumentTypes() {
    elements.documentType.innerHTML = (
        '<option value="">Зареждане...</option>'
    );

    elements.extractButton.disabled = true;

    try {
        const response = await window.documentAuth.authenticatedFetch(
            CONFIG_URL,
            {
                headers: {
                    Accept: "application/json"
                }
            }
        );

        const body = await readJson(response);

        if (!response.ok) {
            throw new Error(
                responseError(
                    response,
                    body
                )
            );
        }

        state.documentTypes =
            body?.document_types || {};

        state.resolvedDocumentTypes =
            body?.resolved_document_types || {};

        state.documentTypeMetadata =
            body?.document_type_metadata || {};

        renderDocumentTypes();

    } catch (error) {
        state.documentTypes = {};
        state.resolvedDocumentTypes = {};
        state.documentTypeMetadata = {};

        elements.documentType.innerHTML = (
            '<option value="">'
            + "Грешка при зареждане"
            + "</option>"
        );

        elements.extractButton.disabled = true;

        showMessage(
            `Неуспешно зареждане на типовете: `
            + error.message,
            "error"
        );
    }
}


function renderDocumentTypes() {
    elements.documentType.replaceChildren();

    const readyDocumentTypes = Object.keys(
        state.documentTypes
    ).filter((documentType) => {
        const metadata =
            state.documentTypeMetadata[
                documentType
            ];

        return metadata?.ready === true;
    });

    if (!readyDocumentTypes.length) {
        const option = new Option(
            "Няма готови типове документи",
            ""
        );

        option.disabled = true;
        option.selected = true;

        elements.documentType.appendChild(option);
        elements.extractButton.disabled = true;

        return;
    }

    for (const documentType of readyDocumentTypes) {
        const metadata =
            state.documentTypeMetadata[
                documentType
            ];

        const option = new Option(
            `${documentType} `
            + `(${metadata.field_count} полета)`,
            documentType
        );

        elements.documentType.appendChild(option);
    }

    elements.extractButton.disabled = false;
}


function setProcessing(processing) {
    state.processing = processing;

    elements.extractButton.disabled = processing;
    elements.documentType.disabled = processing;
    elements.documentFile.disabled = processing;

    elements.extractButton.textContent = processing
        ? "Обработване..."
        : "Разпознай документа";

    elements.processingSection.classList.toggle(
        "hidden",
        !processing
    );

    if (processing) {
        elements.resultSection.classList.add(
            "hidden"
        );

        elements.qualitySection.classList.add(
            "hidden"
        );

        elements.diagnosticsSection.classList.add(
            "hidden"
        );
    }
}


function fieldLabel(
    documentType,
    fieldName
) {
    const fields =
        state.resolvedDocumentTypes[
            documentType
        ]?.fields || [];

    const field = fields.find(
        (item) => item.name === fieldName
    );

    return (
        field?.label?.bg ||
        field?.label?.en ||
        fieldName
    );
}


function formatValue(value) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "Не е извлечена стойност";
    }

    if (typeof value === "object") {
        return JSON.stringify(
            value,
            null,
            2
        );
    }

    return String(value);
}


function renderValidationErrors(errors) {
    elements.validationErrors.replaceChildren();

    const entries = Object.entries(
        errors || {}
    );

    if (!entries.length) {
        return;
    }

    const box = document.createElement("div");
    box.className = "message-area error";
    box.setAttribute("role", "alert");
    box.setAttribute("aria-live", "assertive");
    box.setAttribute("aria-atomic", "true");

    const heading = document.createElement(
        "strong"
    );

    heading.textContent = (
        "Документът съдържа невалидни "
        + "или липсващи полета:"
    );

    const list = document.createElement("ul");

    for (
        const [fieldName, messages]
        of entries
    ) {
        for (const message of messages) {
            const item = document.createElement(
                "li"
            );

            item.textContent =
                `${fieldName}: ${message}`;

            list.appendChild(item);
        }
    }

    box.append(
        heading,
        list
    );

    elements.validationErrors.appendChild(box);
}


function renderSummaryValidation(summaryValidation) {
    const result = summaryValidation || {
        valid: true,
        errors: {}
    };
    const entries = Object.entries(result.errors || {});

    elements.summaryValidationBadge.textContent = result.valid
        ? "SUMMARY VALID"
        : "SUMMARY INVALID";
    elements.summaryValidationBadge.style.background = result.valid
        ? "#f0fdf4"
        : "#fef2f2";
    elements.summaryValidationBadge.style.color = result.valid
        ? "#15803d"
        : "#b91c1c";
    elements.summaryValidationSummary.textContent = result.valid
        ? "Обобщаващите проверки са успешни."
        : "Има несъответствия между collection стойности и scalar полета.";
    elements.summaryValidationErrors.replaceChildren();

    if (!entries.length) return;

    const list = document.createElement("ul");
    for (const [errorPath, messages] of entries) {
        const targetField = errorPath.startsWith("_summary.")
            ? errorPath.slice("_summary.".length)
            : errorPath;
        for (const message of messages) {
            const item = document.createElement("li");
            item.textContent = `${targetField}: ${message}`;
            list.appendChild(item);
        }
    }
    elements.summaryValidationErrors.style.color = "#b91c1c";
    elements.summaryValidationErrors.appendChild(list);
}


function renderFields(
    documentType,
    values,
    errors,
    evidence,
    llmValues
) {
    elements.resultFields.replaceChildren();

    const configuredFields =
        state.resolvedDocumentTypes[
            documentType
        ]?.fields || [];

    const fieldNames = configuredFields.length
        ? configuredFields.map(
            (field) => field.name
        )
        : Object.keys(values || {});

    if (!fieldNames.length) {
        const emptyElement =
            document.createElement("div");

        emptyElement.className = "loading-state";

        emptyElement.textContent =
            "Няма върнати полета.";

        elements.resultFields.appendChild(
            emptyElement
        );

        return;
    }

    for (const fieldName of fieldNames) {
        const fragment =
            elements.resultFieldTemplate.content
                .cloneNode(true);

        const card = fragment.querySelector(
            ".field-card"
        );

        const badge = fragment.querySelector(
            ".field-type-badge"
        );

        const title = fragment.querySelector(
            ".field-title"
        );

        const name = fragment.querySelector(
            ".field-name"
        );

        const valueElement =
            fragment.querySelector(
                ".field-final-value"
            );

        const llmValueElement =
            fragment.querySelector(
                ".field-llm-value"
            );

        const llmComparison =
            fragment.querySelector(
                ".field-llm-comparison"
            );

        const sourceMethodElement =
            fragment.querySelector(
                ".field-source-method"
            );

        const errorContainer =
            fragment.querySelector(
                ".field-validation-errors"
            );

        const value = values?.[fieldName];

        const fieldErrors =
            errors?.[fieldName] || [];

        const fieldEvidence =
            evidence?.[fieldName];

        const hasLlmValue = Object.prototype.hasOwnProperty.call(
            llmValues || {},
            fieldName
        );
        const llmValue = hasLlmValue
            ? llmValues[fieldName]
            : undefined;

        title.textContent = fieldLabel(
            documentType,
            fieldName
        );

        name.textContent = fieldName;

        valueElement.textContent = formatValue(
            value
        );

        llmValueElement.textContent = hasLlmValue
            ? formatValue(llmValue)
            : "Няма LLM стойност";
        llmComparison.classList.toggle(
            "hidden",
            !hasLlmValue
        );
        sourceMethodElement.textContent =
            fieldEvidence?.method || "unknown";

        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
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

        const diagnosticMessages = [
            ...fieldErrors,
        ];

        if (fieldEvidence) {
            const evidenceParts = [
                `Метод: ${fieldEvidence.method}`,
                fieldEvidence.matched
                    ? "Съвпадение: да"
                    : "Съвпадение: не",
            ];

            if (fieldEvidence.normalized) {
                evidenceParts.push("Нормализирано: да");
            }
            if (fieldEvidence.occurrence) {
                evidenceParts.push(
                    `Позиция: ${fieldEvidence.occurrence}`
                );
            }
            if (fieldEvidence.rule_index !== undefined) {
                evidenceParts.push(
                    `Правило: ${fieldEvidence.rule_index + 1}`
                );
            }
            if (fieldEvidence.anchor_found !== undefined) {
                evidenceParts.push(
                    fieldEvidence.anchor_found
                        ? "Anchor: намерен"
                        : "Anchor: липсва"
                );
            }
            if (fieldEvidence.failure_reason) {
                evidenceParts.push(
                    `Причина: ${fieldEvidence.failure_reason}`
                );
            }

            diagnosticMessages.push(
                evidenceParts.join(" · ")
            );
        }

        if (diagnosticMessages.length) {
            errorContainer.textContent =
                diagnosticMessages.join("; ");

            errorContainer.style.color = fieldErrors.length
                ? "#b91c1c"
                : "#475569";
        }

        if (fieldErrors.length) {
            card.style.borderColor = "#fecaca";
        }

        elements.resultFields.appendChild(
            fragment
        );
    }
}


function formatCollectionEvidence(evidence) {
    if (!evidence) {
        return "";
    }

    const parts = [
        `Метод: ${evidence.method}`,
        evidence.matched
            ? "Съвпадение: да"
            : "Съвпадение: не",
    ];

    if (evidence.normalized) {
        parts.push("Нормализирано: да");
    }
    if (evidence.occurrence) {
        parts.push(`Позиция: ${evidence.occurrence}`);
    }
    if (evidence.rule_index !== undefined) {
        parts.push(`Правило: ${evidence.rule_index + 1}`);
    }
    if (evidence.failure_reason) {
        parts.push(`Причина: ${evidence.failure_reason}`);
    }

    return parts.join(" · ");
}


function renderCollections(
    collections,
    collectionEvidence,
    validationErrors
) {
    elements.resultCollections.replaceChildren();

    for (const [collectionName, items] of Object.entries(
        collections || {}
    )) {
        const section = document.createElement("section");
        section.className = "field-card";

        const heading = document.createElement("h3");
        heading.className = "field-title";
        heading.textContent = `${collectionName} (${items.length})`;
        section.appendChild(heading);

        if (!items.length) {
            const empty = document.createElement("p");
            empty.className = "field-name";
            empty.textContent = "Няма извлечени записи.";
            section.appendChild(empty);
        }

        items.forEach((item, itemIndex) => {
            const itemBox = document.createElement("div");
            itemBox.className = "field-details";

            const itemTitle = document.createElement("strong");
            itemTitle.textContent = `Запис ${itemIndex + 1}`;
            itemBox.appendChild(itemTitle);

            for (const [fieldName, value] of Object.entries(item)) {
                const detail = document.createElement("div");
                detail.className = "field-detail";

                const label = document.createElement("span");
                label.className = "field-detail-label";
                label.textContent = fieldName;

                const renderedValue = document.createElement("span");
                renderedValue.className = "field-detail-value";
                renderedValue.textContent = formatValue(value);

                detail.append(label, renderedValue);
                itemBox.appendChild(detail);

                const evidence = collectionEvidence?.[collectionName]
                    ?.[itemIndex]?.[fieldName];
                const errorPath = (
                    `${collectionName}[${itemIndex}].${fieldName}`
                );
                const fieldErrors = [
                    ...(validationErrors?.[errorPath] || []),
                ];

                if (evidence) {
                    const evidenceDetails = document.createElement("div");
                    evidenceDetails.className = (
                        "field-details collection-evidence-details"
                    );

                    const addEvidenceDetail = (labelText, valueText) => {
                        const evidenceDetail = document.createElement("div");
                        evidenceDetail.className = "field-detail";
                        const evidenceLabel = document.createElement("span");
                        evidenceLabel.className = "field-detail-label";
                        evidenceLabel.textContent = labelText;
                        const evidenceValue = document.createElement("span");
                        evidenceValue.className = "field-detail-value";
                        evidenceValue.textContent = valueText;
                        evidenceDetail.append(evidenceLabel, evidenceValue);
                        evidenceDetails.appendChild(evidenceDetail);
                    };

                    addEvidenceDetail(
                        "Extraction method",
                        evidence.method || "unknown"
                    );
                    addEvidenceDetail(
                        "Match status",
                        evidence.matched ? "Съвпадение" : "Няма съвпадение"
                    );
                    addEvidenceDetail(
                        "Normalization",
                        evidence.normalized ? "Приложена" : "Не е приложена"
                    );
                    if (evidence.occurrence) {
                        addEvidenceDetail("Occurrence", evidence.occurrence);
                    }
                    if (evidence.rule_index !== undefined) {
                        addEvidenceDetail(
                            "Rule",
                            String(evidence.rule_index + 1)
                        );
                    }
                    if (evidence.failure_reason) {
                        addEvidenceDetail(
                            "Failure reason",
                            evidence.failure_reason
                        );
                        evidenceDetails.style.borderColor = "#fecaca";
                    }
                    itemBox.appendChild(evidenceDetails);
                }

                if (fieldErrors.length) {
                    const diagnostics = document.createElement("div");
                    diagnostics.className = "field-validation-errors";
                    diagnostics.textContent = (
                        `Validation: ${fieldErrors.join("; ")}`
                    );
                    diagnostics.style.color = "#b91c1c";
                    itemBox.appendChild(diagnostics);
                }
            }

            section.appendChild(itemBox);
        });

        elements.resultCollections.appendChild(section);
    }
}


function addQualityDetail(label, value) {
    const detail = document.createElement("div");
    detail.className = "field-detail";

    const labelElement = document.createElement("span");
    labelElement.className = "field-detail-label";
    labelElement.textContent = label;

    const valueElement = document.createElement("span");
    valueElement.className = "field-detail-value";
    valueElement.textContent = value;

    detail.append(labelElement, valueElement);
    elements.qualityDetails.appendChild(detail);
}


function renderInputQuality(quality) {
    elements.qualityWarnings.replaceChildren();
    elements.qualityDetails.replaceChildren();

    if (!quality) {
        elements.qualityBadge.textContent = "UNKNOWN";
        elements.qualitySummary.textContent = "Няма налична оценка за входа.";
        elements.qualitySection.classList.remove("hidden");
        return;
    }

    const requiresReview = quality.requires_review === true;
    const input = quality.input || {};

    elements.qualityBadge.textContent = requiresReview
        ? "REVIEW"
        : "ACCEPTED";

    elements.qualityBadge.style.background = requiresReview
        ? "#fff7ed"
        : "#f0fdf4";

    elements.qualityBadge.style.color = requiresReview
        ? "#c2410c"
        : "#15803d";

    elements.qualitySummary.textContent = requiresReview
        ? "Входът е обработен, но изисква човешка проверка."
        : "Входът покрива текущите критерии за OCR качество.";

    if (input.format) {
        addQualityDetail("Формат", String(input.format));
    }

    if (input.width && input.height) {
        addQualityDetail(
            "Размери",
            `${input.width} × ${input.height} px`
        );
    }

    if (input.source) {
        addQualityDetail("Източник", String(input.source));
    }

    if (input.page_count !== undefined) {
        addQualityDetail("Страници", String(input.page_count));
    }

    if (input.mode) {
        addQualityDetail("Цветови режим", String(input.mode));
    }

    if (input.dpi) {
        addQualityDetail("DPI", input.dpi.join(" × "));
    }

    if (quality.warnings?.length) {
        const warningBox = document.createElement("div");
        warningBox.className = "message-area error";

        const list = document.createElement("ul");

        for (const warning of quality.warnings) {
            const item = document.createElement("li");
            item.textContent = warning.message || warning.code;
            list.appendChild(item);
        }

        warningBox.appendChild(list);
        elements.qualityWarnings.appendChild(warningBox);
    }

    elements.qualitySection.classList.remove("hidden");
}


function renderProcessingStatus(status) {
    const styles = {
        accepted: {
            label: "ACCEPTED",
            background: "#f0fdf4",
            color: "#15803d"
        },
        review: {
            label: "REVIEW",
            background: "#fff7ed",
            color: "#c2410c"
        },
        invalid: {
            label: "INVALID",
            background: "#fef2f2",
            color: "#b91c1c"
        }
    };
    const selected = styles[status] || {
        label: "UNKNOWN",
        background: "#f8fafc",
        color: "#475569"
    };
    elements.processingStatusBadge.textContent = selected.label;
    elements.processingStatusBadge.style.background = selected.background;
    elements.processingStatusBadge.style.color = selected.color;
}


function renderResult(body) {
    renderInputQuality(body.quality);
    renderProcessingStatus(body.processing_status);

    const values =
        body.final_values || {};

    const validation =
        body.validation || {
            valid: false,
            errors: {}
        };

    const extractedCount = Object.values(
        values
    ).filter((value) => (
        value !== null &&
        value !== undefined &&
        value !== ""
    )).length;

    const totalCount = Object.keys(
        values
    ).length;

    elements.resultSummary.textContent = (
        `${extractedCount} от ${totalCount} `
        + "полета са извлечени."
    );

    elements.validationBadge.textContent =
        validation.valid
            ? "VALIDATION VALID"
            : "VALIDATION INVALID";

    elements.validationBadge.style.background =
        validation.valid
            ? "#f0fdf4"
            : "#fef2f2";

    elements.validationBadge.style.color =
        validation.valid
            ? "#15803d"
            : "#b91c1c";

    renderValidationErrors(
        validation.errors
    );
    renderSummaryValidation(
        body.summary_validation
    );

    renderFields(
        body.document_type,
        values,
        validation.errors || {},
        body.field_evidence || {},
        body.llm_values || {}
    );

    renderCollections(
        body.collections || {},
        body.collection_evidence || {},
        body.collection_validation?.errors || {}
    );

    elements.diagnosticDocumentType.textContent =
        body.document_type || "";

    elements.diagnosticProfile.textContent =
        body.profile || "Няма избран профил";

    elements.diagnosticLlmValues.textContent =
        JSON.stringify(
            body.llm_values || {},
            null,
            2
        );

    elements.diagnosticRawText.textContent =
        body.raw_text || "";

    elements.resultSection.classList.remove(
        "hidden"
    );

    elements.diagnosticsSection.classList.remove(
        "hidden"
    );
}



function processingStatusMessage(status) {
    if (status === "accepted") {
        return {
            message: (
                "Документът е извлечен "
                + "и валидиран успешно."
            ),
            type: "success"
        };
    }

    if (status === "review") {
        return {
            message: (
                "Документът е извлечен, "
                + "но изисква човешка проверка."
            ),
            type: "warning"
        };
    }

    return {
        message: (
            "Документът е обработен, "
            + "но има невалидни "
            + "или липсващи полета."
        ),
        type: "error"
    };
}

async function submitDocument(event) {
    event.preventDefault();

    clearMessage();

    if (
        state.processing ||
        !elements.form.reportValidity()
    ) {
        return;
    }

    const documentType =
        elements.documentType.value;

    const file =
        elements.documentFile.files[0];

    if (!documentType) {
        showMessage(
            "Избери готов тип документ.",
            "error"
        );

        return;
    }

    if (!file) {
        showMessage(
            "Избери файл за обработване.",
            "error"
        );

        return;
    }

    const allowedExtensions = [
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png"
    ];

    const fileName =
        file.name.toLowerCase();

    const allowedFile = allowedExtensions.some(
        (extension) => (
            fileName.endsWith(extension)
        )
    );

    if (!allowedFile) {
        showMessage(
            "Неподдържан файлов формат.",
            "error"
        );

        return;
    }

    const formData = new FormData();

    formData.append(
        "document_type",
        documentType
    );

    formData.append(
        "file",
        file
    );

    setProcessing(true);

    try {
        const response = await window.documentAuth.authenticatedFetch(
            EXTRACT_URL,
            {
                method: "POST",
                body: formData
            }
        );

        const body = await readJson(response);

        if (!response.ok) {
            throw new Error(
                responseError(
                    response,
                    body
                )
            );
        }

        renderResult(body);

        const processingMessage = (
            processingStatusMessage(
                body.processing_status
            )
        );

        showMessage(
            processingMessage.message,
            processingMessage.type
        );

    } catch (error) {
        elements.resultSection.classList.add(
            "hidden"
        );

        elements.qualitySection.classList.add(
            "hidden"
        );

        elements.diagnosticsSection.classList.add(
            "hidden"
        );

        showMessage(
            `Грешка при обработване: `
            + error.message,
            "error"
        );

    } finally {
        setProcessing(false);
    }
}


elements.form.addEventListener(
    "submit",
    submitDocument
);


async function initializeApplication() {
    await window.documentAuth.initialize();
    await checkApiHealth();
    await loadDocumentTypes();
}


initializeApplication();
