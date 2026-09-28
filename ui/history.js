"use strict";

const HISTORY_URL = "/api/v1/processing-runs";
const INVOICE_SHADOW_SUMMARY_URL = `${HISTORY_URL}/invoice-shadow-summary`;
const PAGE_SIZE = 20;

const byId = (id) => document.getElementById(id);
const elements = {
    apiStatusIndicator: byId("apiStatusIndicator"),
    apiStatusText: byId("apiStatusText"),
    messageArea: byId("historyMessageArea"),
    filters: byId("historyFilters"),
    documentType: byId("filterDocumentType"),
    status: byId("filterStatus"),
    profile: byId("filterProfile"),
    review: byId("filterReview"),
    reviewStatus: byId("filterReviewStatus"),
    invoiceShadowStatus: byId("filterInvoiceShadowStatus"),
    invoiceSchemaVersion: byId("filterInvoiceSchemaVersion"),
    clearFilters: byId("clearHistoryFiltersButton"),
    refresh: byId("refreshHistoryButton"),
    rows: byId("historyRows"),
    summary: byId("historySummary"),
    reviewSummaryStatus: byId("reviewSummaryStatus"),
    reviewTotal: byId("reviewTotal"),
    reviewPending: byId("reviewPending"),
    reviewApproved: byId("reviewApproved"),
    reviewCorrected: byId("reviewCorrected"),
    reviewRejected: byId("reviewRejected"),
    reviewAverageDuration: byId("reviewAverageDuration"),
    invoiceShadowSummaryStatus: byId("invoiceShadowSummaryStatus"),
    invoiceShadowTotal: byId("invoiceShadowTotal"),
    invoiceShadowSucceeded: byId("invoiceShadowSucceeded"),
    invoiceShadowFailed: byId("invoiceShadowFailed"),
    invoiceShadowNotApplicable: byId("invoiceShadowNotApplicable"),
    invoiceShadowSuccessRate: byId("invoiceShadowSuccessRate"),
    invoiceShadowSchemaVersions: byId("invoiceShadowSchemaVersions"),
    invoiceShadowFailureReasons: byId("invoiceShadowFailureReasons"),
    pageInfo: byId("historyPageInfo"),
    previous: byId("previousPageButton"),
    next: byId("nextPageButton"),
    dialog: byId("historyDetailDialog"),
    dialogTitle: byId("historyDetailTitle"),
    dialogBody: byId("historyDetailBody"),
    closeDialog: byId("closeHistoryDetailButton"),
};

const state = { offset: 0, total: 0, loading: false };

async function readJson(response) {
    try { return await response.json(); } catch { return null; }
}

function showMessage(message, type = "error") {
    elements.messageArea.textContent = message;
    elements.messageArea.className = `message-area ${type}`;
}

function clearMessage() {
    elements.messageArea.textContent = "";
    elements.messageArea.className = "message-area";
}

function setApiStatus(online) {
    elements.apiStatusIndicator.classList.toggle("online", online);
    elements.apiStatusIndicator.classList.toggle("offline", !online);
    elements.apiStatusText.textContent = online ? "API е достъпно" : "API не е достъпно";
}

function buildQuery() {
    const params = new URLSearchParams({
        offset: String(state.offset),
        limit: String(PAGE_SIZE),
    });
    const values = {
        document_type: elements.documentType.value.trim(),
        processing_status: elements.status.value,
        profile: elements.profile.value.trim(),
        requires_review: elements.review.value,
        review_status: elements.reviewStatus.value,
        invoice_shadow_validation_status:
            elements.invoiceShadowStatus.value,
        invoice_schema_version:
            elements.invoiceSchemaVersion.value.trim(),
    };
    for (const [key, value] of Object.entries(values)) {
        if (value !== "") params.set(key, value);
    }
    return params.toString();
}

function createCell(value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    return cell;
}

function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString("bg-BG");
}

function statusBadge(status) {
    const badge = document.createElement("span");
    badge.className = `history-status history-status-${status}`;
    badge.textContent = status;
    return badge;
}

function renderRows(items) {
    elements.rows.replaceChildren();
    if (!items.length) {
        const row = document.createElement("tr");
        const cell = createCell("Няма намерени обработки.");
        cell.colSpan = 8;
        cell.className = "history-empty";
        row.appendChild(cell);
        elements.rows.appendChild(row);
        return;
    }
    for (const item of items) {
        const row = document.createElement("tr");
        if (item.review_status === "pending") {
            row.classList.add("history-row-review-pending");
        }
        row.appendChild(createCell(formatDate(item.created_at)));
        row.appendChild(createCell(item.filename));
        row.appendChild(createCell(item.document_type));
        row.appendChild(createCell(item.profile || "—"));
        const statusCell = document.createElement("td");
        statusCell.appendChild(statusBadge(item.processing_status));
        row.appendChild(statusCell);

        const reviewCell = document.createElement("td");
        reviewCell.appendChild(
            statusBadge(item.review_status || "not-required")
        );
        row.appendChild(reviewCell);

        row.appendChild(createCell(
            item.duration_ms == null
                ? "—"
                : `${item.duration_ms} ms`
        ));
        const actionCell = document.createElement("td");
        actionCell.className = "history-row-actions";
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button-small button-secondary";
        button.textContent = "Отвори";
        button.addEventListener("click", () => loadDetail(item.id));
        actionCell.appendChild(button);

        if (item.document_type === "invoice") {
            const universalInvoiceButton = document.createElement("button");
            universalInvoiceButton.type = "button";
            universalInvoiceButton.className = (
                "button button-small button-secondary"
            );
            universalInvoiceButton.textContent = "Universal Invoice";
            universalInvoiceButton.addEventListener(
                "click",
                () => loadUniversalInvoice(item.id, item.filename),
            );
            actionCell.appendChild(universalInvoiceButton);
        }
        row.appendChild(actionCell);
        elements.rows.appendChild(row);
    }
}

function updatePagination() {
    const page = Math.floor(state.offset / PAGE_SIZE) + 1;
    const pages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));
    elements.pageInfo.textContent = `Страница ${page} от ${pages}`;
    elements.previous.disabled = state.loading || state.offset === 0;
    elements.next.disabled = state.loading || state.offset + PAGE_SIZE >= state.total;
}

function formatDuration(milliseconds) {
    if (milliseconds == null) return "—";
    if (milliseconds < 1000) return `${milliseconds} ms`;

    const seconds = milliseconds / 1000;
    return `${seconds.toFixed(seconds < 10 ? 1 : 0)} s`;
}

function resetReviewSummary() {
    elements.reviewTotal.textContent = "—";
    elements.reviewPending.textContent = "—";
    elements.reviewApproved.textContent = "—";
    elements.reviewCorrected.textContent = "—";
    elements.reviewRejected.textContent = "—";
    elements.reviewAverageDuration.textContent = "—";
}

async function loadReviewSummary() {
    elements.reviewSummaryStatus.textContent = "Зареждане...";

    try {
        const response =
            await window.documentAuth.authenticatedFetch(
                `${HISTORY_URL}/review-summary`,
                {
                    headers: {
                        Accept: "application/json",
                    },
                },
            );

        const body = await readJson(response);

        if (!response.ok) {
            throw new Error(
                body?.detail || `HTTP ${response.status}`
            );
        }

        elements.reviewTotal.textContent =
            String(body.total_requiring_review);
        elements.reviewPending.textContent =
            String(body.pending);
        elements.reviewApproved.textContent =
            String(body.approved);
        elements.reviewCorrected.textContent =
            String(body.corrected);
        elements.reviewRejected.textContent =
            String(body.rejected);
        elements.reviewAverageDuration.textContent =
            formatDuration(body.average_review_duration_ms);
        elements.reviewSummaryStatus.textContent =
            "Глобални стойности за tenant-а.";
    } catch (error) {
        resetReviewSummary();
        elements.reviewSummaryStatus.textContent =
            `Metrics не са достъпни: ${error.message}`;
    }
}

function resetInvoiceShadowSummary() {
    elements.invoiceShadowTotal.textContent = "—";
    elements.invoiceShadowSucceeded.textContent = "—";
    elements.invoiceShadowFailed.textContent = "—";
    elements.invoiceShadowNotApplicable.textContent = "—";
    elements.invoiceShadowSuccessRate.textContent = "—";
    elements.invoiceShadowSchemaVersions.textContent = "—";
    elements.invoiceShadowFailureReasons.textContent = "—";
}

async function loadInvoiceShadowSummary() {
    elements.invoiceShadowSummaryStatus.textContent = "Зареждане...";

    try {
        const response = await window.documentAuth.authenticatedFetch(
            INVOICE_SHADOW_SUMMARY_URL,
            { headers: { Accept: "application/json" } },
        );
        const body = await readJson(response);
        if (!response.ok) {
            throw new Error(body?.detail || `HTTP ${response.status}`);
        }

        elements.invoiceShadowTotal.textContent = String(body.total);
        elements.invoiceShadowSucceeded.textContent = String(body.succeeded);
        elements.invoiceShadowFailed.textContent = String(body.failed);
        elements.invoiceShadowNotApplicable.textContent =
            String(body.not_applicable);
        elements.invoiceShadowSuccessRate.textContent =
            body.success_rate == null
                ? "—"
                : `${(body.success_rate * 100).toFixed(1)}%`;
        elements.invoiceShadowSchemaVersions.textContent =
            body.schema_versions.length
                ? body.schema_versions
                    .map((item) => `${item.schema_version}: ${item.total}`)
                    .join(", ")
                : "—";
        elements.invoiceShadowFailureReasons.textContent =
            body.failure_reasons.length
                ? body.failure_reasons
                    .map((item) => `${item.reason}: ${item.count}`)
                    .join(", ")
                : "—";
        elements.invoiceShadowSummaryStatus.textContent =
            "Глобални стойности за tenant-а.";
    } catch (error) {
        resetInvoiceShadowSummary();
        elements.invoiceShadowSummaryStatus.textContent =
            `Metrics не са достъпни: ${error.message}`;
    }
}

async function refreshHistoryPage() {
    await Promise.all([
        loadHistory(),
        loadReviewSummary(),
        loadInvoiceShadowSummary(),
    ]);
}

async function loadHistory() {
    clearMessage();
    state.loading = true;
    elements.summary.textContent = "Зареждане...";
    updatePagination();
    try {
        const response = await window.documentAuth.authenticatedFetch(`${HISTORY_URL}?${buildQuery()}`, { headers: { Accept: "application/json" } });
        const body = await readJson(response);
        if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
        state.total = body.total;
        renderRows(body.items);
        const pendingOnPage = body.items.filter(
            (item) => item.review_status === "pending"
        ).length;
        elements.summary.textContent = (
            `Намерени обработки: ${body.total}`
            + ` | Pending на страницата: ${pendingOnPage}`
        );
        setApiStatus(true);
    } catch (error) {
        state.total = 0;
        renderRows([]);
        elements.summary.textContent = "Зареждането е неуспешно.";
        showMessage(`Неуспешно зареждане: ${error.message}`);
        setApiStatus(false);
    } finally {
        state.loading = false;
        updatePagination();
    }
}

function appendDetail(label, value) {
    const wrapper = document.createElement("div");
    wrapper.className = "history-detail-item";
    const heading = document.createElement("strong");
    heading.textContent = label;
    const content = document.createElement("pre");
    content.textContent = typeof value === "object" && value !== null
        ? JSON.stringify(value, null, 2)
        : String(value ?? "—");
    wrapper.append(heading, content);
    elements.dialogBody.appendChild(wrapper);
}

function canSubmitReview() {
    return Boolean(
        window.documentAuth?.isEnabled()
        && window.documentAuth.isAuthenticated()
    );
}

async function submitReview(runId, status, correctedValues, comment) {
    const payload = {
        status,
        comment: comment || null,
    };

    if (status === "corrected") {
        payload.corrected_values = correctedValues;
    }

    const response = await window.documentAuth.authenticatedFetch(
        `${HISTORY_URL}/${encodeURIComponent(runId)}/review`,
        {
            method: "PUT",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        },
    );

    const body = await readJson(response);
    if (!response.ok) {
        throw new Error(body?.detail || `HTTP ${response.status}`);
    }
    return body;
}

function reviewFieldLabel(field) {
    const label = field?.label;
    if (label && typeof label === "object") {
        return label.bg || label.en || field.name;
    }
    return field?.name || "Поле";
}

function reviewFieldDefinitions(processingRun) {
    const configured =
        processingRun.configuration_snapshot?.resolved_fields;

    if (Array.isArray(configured) && configured.length) {
        return configured;
    }

    return Object.keys(processingRun.final_values || {}).map(
        (name) => ({ name }),
    );
}

function serializeReviewValue(value) {
    if (typeof value === "string") return value;
    return JSON.stringify(value);
}

function parseReviewValue(input, originalValue) {
    if (typeof originalValue === "string") {
        return input.value;
    }

    try {
        return JSON.parse(input.value);
    } catch {
        throw new Error(
            `Полето "${input.dataset.fieldName}" `
            + "не съдържа валидна JSON стойност.",
        );
    }
}

function buildFieldReviewEditor(processingRun) {
    const editor = document.createElement("div");
    editor.className = "review-field-editor";

    const inputs = new Map();
    const originalValues = processingRun.final_values || {};
    const validationErrors =
        processingRun.validation?.fields?.errors || {};

    for (const field of reviewFieldDefinitions(processingRun)) {
        const fieldName = field.name;
        if (!fieldName) continue;

        const originalValue = originalValues[fieldName];

        const row = document.createElement("div");
        row.className = "review-field-row";

        const heading = document.createElement("div");
        heading.className = "review-field-heading";

        const label = document.createElement("label");
        label.htmlFor = `reviewField-${fieldName}`;
        label.textContent = reviewFieldLabel(field);

        const technicalName = document.createElement("code");
        technicalName.textContent = fieldName;

        heading.append(label, technicalName);

        const original = document.createElement("pre");
        original.className = "review-field-original";
        original.textContent = serializeReviewValue(originalValue);

        const input = document.createElement("textarea");
        input.id = `reviewField-${fieldName}`;
        input.className = "form-control review-field-input";
        input.dataset.fieldName = fieldName;
        input.rows = 2;
        input.value = serializeReviewValue(originalValue);

        input.addEventListener("input", () => {
            row.classList.toggle(
                "review-field-changed",
                input.value !== serializeReviewValue(originalValue),
            );
        });

        const errors = validationErrors[fieldName];
        if (Array.isArray(errors) && errors.length) {
            const errorList = document.createElement("ul");
            errorList.className = "review-field-errors";

            for (const error of errors) {
                const item = document.createElement("li");
                item.textContent = String(error);
                errorList.appendChild(item);
            }

            row.append(heading, original, input, errorList);
        } else {
            row.append(heading, original, input);
        }

        inputs.set(fieldName, {
            input,
            originalValue,
        });
        editor.appendChild(row);
    }

    return { editor, inputs };
}

function collectCorrectedValues(inputs) {
    const correctedValues = {};

    for (const [fieldName, entry] of inputs) {
        correctedValues[fieldName] = parseReviewValue(
            entry.input,
            entry.originalValue,
        );
    }

    return correctedValues;
}

function appendReviewActions(runId, processingRun) {
    if (processingRun.review_status !== "pending") return;

    const section = document.createElement("section");
    section.className = "review-actions";

    const heading = document.createElement("h3");
    heading.textContent = "Human review";

    if (!canSubmitReview()) {
        const notice = document.createElement("p");
        notice.className = "review-auth-notice";
        notice.textContent =
            "Необходим е удостоверен профил за review решение.";
        section.append(heading, notice);
        elements.dialogBody.appendChild(section);
        return;
    }

    const fieldEditor = buildFieldReviewEditor(processingRun);

    const commentLabel = document.createElement("label");
    commentLabel.htmlFor = "reviewComment";
    commentLabel.textContent = "Review коментар";

    const comment = document.createElement("textarea");
    comment.id = "reviewComment";
    comment.className = "form-control";
    comment.maxLength = 2000;
    comment.rows = 3;

    const buttons = document.createElement("div");
    buttons.className = "review-action-buttons";

    const definitions = [
        ["approved", "Approve", "button-primary"],
        ["corrected", "Correct", "button-secondary"],
        ["rejected", "Reject", "button-danger-outline"],
    ];

    for (const [status, label, buttonClass] of definitions) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `button ${buttonClass}`;
        button.textContent = label;

        button.addEventListener("click", async () => {
            let correctedValues = null;

            if (status === "corrected") {
                try {
                    correctedValues = collectCorrectedValues(
                        fieldEditor.inputs,
                    );
                } catch (error) {
                    showMessage(error.message);
                    return;
                }
            }

            for (const actionButton of buttons.children) {
                actionButton.disabled = true;
            }

            try {
                await submitReview(
                    runId,
                    status,
                    correctedValues,
                    comment.value.trim(),
                );
                elements.dialog.close();
                showMessage(
                    "Review решението е записано.",
                    "success",
                );
                await refreshHistoryPage();
            } catch (error) {
                showMessage(
                    `Review решението не беше записано: ${error.message}`,
                );
            } finally {
                for (const actionButton of buttons.children) {
                    actionButton.disabled = false;
                }
            }
        });

        buttons.appendChild(button);
    }

    section.append(
        heading,
        fieldEditor.editor,
        commentLabel,
        comment,
        buttons,
    );
    elements.dialogBody.appendChild(section);
}


async function loadUniversalInvoice(runId, filename) {
    try {
        const response = await window.documentAuth.authenticatedFetch(
            `${HISTORY_URL}/${encodeURIComponent(runId)}/universal-invoice`,
            { headers: { Accept: "application/json" } },
        );
        const body = await readJson(response);
        if (!response.ok) {
            throw new Error(body?.detail || `HTTP ${response.status}`);
        }

        elements.dialogTitle.textContent = `${filename} · Universal Invoice`;
        elements.dialogBody.replaceChildren();
        appendDetail("Universal Invoice", body);
        elements.dialog.showModal();
    } catch (error) {
        showMessage(
            `Universal Invoice не е достъпен: ${error.message}`,
        );
    }
}


async function loadDetail(runId) {
    try {
        const response = await window.documentAuth.authenticatedFetch(`${HISTORY_URL}/${encodeURIComponent(runId)}`, { headers: { Accept: "application/json" } });
        const body = await readJson(response);
        if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
        elements.dialogTitle.textContent = body.filename;
        elements.dialogBody.replaceChildren();
        appendDetail("Статус", body.processing_status);
        appendDetail("Профил", body.profile);
        appendDetail("Invoice schema version", body.invoice_schema_version);
        appendDetail(
            "Invoice shadow статус",
            body.invoice_shadow_validation_status,
        );
        appendDetail(
            "Invoice shadow причина",
            body.invoice_shadow_validation_reason,
        );
        appendDetail("Общо време", body.duration_ms == null ? null : `${body.duration_ms} ms`);
        appendDetail("Step timings", body.step_timings);
        appendDetail("Качество", body.quality);
        appendDetail("Извлечени стойности", body.final_values);
        appendDetail("Review статус", body.review_status);
        appendDetail("Коригирани стойности", body.corrected_values);
        appendDetail("Review коментар", body.review_comment);
        appendDetail("Проверено на", formatDate(body.reviewed_at));
        appendDetail("Reviewer тип", body.reviewed_by_type);
        appendDetail("Reviewer", body.reviewed_by_subject);
        appendDetail("Колекции", body.collections);
        appendDetail("Валидация", body.validation);
        appendDetail("Грешка", body.error);
        appendReviewActions(runId, body);
        elements.dialog.showModal();
    } catch (error) {
        showMessage(`Неуспешно зареждане на детайлите: ${error.message}`);
    }
}

elements.filters.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!elements.filters.reportValidity()) return;
    state.offset = 0;
    loadHistory();
});
elements.clearFilters.addEventListener("click", () => {
    elements.filters.reset();
    state.offset = 0;
    loadHistory();
});
elements.refresh.addEventListener(
    "click",
    refreshHistoryPage,
);
elements.previous.addEventListener("click", () => {
    state.offset = Math.max(0, state.offset - PAGE_SIZE);
    loadHistory();
});
elements.next.addEventListener("click", () => {
    state.offset += PAGE_SIZE;
    loadHistory();
});
elements.closeDialog.addEventListener("click", () => elements.dialog.close());

window.documentAuth.initialize().then(
    refreshHistoryPage,
);
