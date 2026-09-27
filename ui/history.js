"use strict";

const HISTORY_URL = "/api/v1/processing-runs";
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
    clearFilters: byId("clearHistoryFiltersButton"),
    refresh: byId("refreshHistoryButton"),
    rows: byId("historyRows"),
    summary: byId("historySummary"),
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
        cell.colSpan = 7;
        cell.className = "history-empty";
        row.appendChild(cell);
        elements.rows.appendChild(row);
        return;
    }
    for (const item of items) {
        const row = document.createElement("tr");
        row.appendChild(createCell(formatDate(item.created_at)));
        row.appendChild(createCell(item.filename));
        row.appendChild(createCell(item.document_type));
        row.appendChild(createCell(item.profile || "—"));
        const statusCell = document.createElement("td");
        statusCell.appendChild(statusBadge(item.processing_status));
        row.appendChild(statusCell);
        row.appendChild(createCell(item.duration_ms == null ? "—" : `${item.duration_ms} ms`));
        const actionCell = document.createElement("td");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button-small button-secondary";
        button.textContent = "Отвори";
        button.addEventListener("click", () => loadDetail(item.id));
        actionCell.appendChild(button);
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
        elements.summary.textContent = `Намерени обработки: ${body.total}`;
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

    const comment = document.createElement("textarea");
    comment.id = "reviewComment";
    comment.className = "form-control";
    comment.maxLength = 2000;
    comment.rows = 3;

    const correctedValues = document.createElement("textarea");
    correctedValues.id = "reviewCorrectedValues";
    correctedValues.className =
        "form-control review-json-editor";
    correctedValues.rows = 10;
    correctedValues.value = JSON.stringify(
        processingRun.final_values || {},
        null,
        2,
    );

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
            let parsedValues = null;

            if (status === "corrected") {
                try {
                    parsedValues = JSON.parse(
                        correctedValues.value,
                    );
                } catch {
                    showMessage(
                        "Коригираните стойности не са валиден JSON.",
                    );
                    return;
                }

                if (
                    parsedValues === null
                    || Array.isArray(parsedValues)
                    || typeof parsedValues !== "object"
                ) {
                    showMessage(
                        "Корекциите трябва да са JSON object.",
                    );
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
                    parsedValues,
                    comment.value.trim(),
                );
                elements.dialog.close();
                showMessage(
                    "Review решението е записано.",
                    "success",
                );
                await loadHistory();
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

    section.append(heading, comment, correctedValues, buttons);
    elements.dialogBody.appendChild(section);
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
elements.refresh.addEventListener("click", loadHistory);
elements.previous.addEventListener("click", () => {
    state.offset = Math.max(0, state.offset - PAGE_SIZE);
    loadHistory();
});
elements.next.addEventListener("click", () => {
    state.offset += PAGE_SIZE;
    loadHistory();
});
elements.closeDialog.addEventListener("click", () => elements.dialog.close());

window.documentAuth.initialize().then(loadHistory);
