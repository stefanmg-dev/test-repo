"use strict";

function createAuthControls() {
    const footer = document.querySelector(".sidebar-footer");
    if (!footer || !window.documentAuth) return;

    const container = document.createElement("div");
    container.id = "authControls";
    container.className = "auth-controls hidden";

    const status = document.createElement("span");
    status.id = "authStatusText";
    status.className = "auth-status-text";

    const button = document.createElement("button");
    button.id = "authActionButton";
    button.type = "button";
    button.className = "button button-small button-secondary";

    container.append(status, button);
    footer.prepend(container);

    return { container, status, button };
}

async function initializeAuthControls() {
    const controls = createAuthControls();
    if (!controls) return;

    try {
        await window.documentAuth.initialize();
        if (!window.documentAuth.isEnabled()) return;

        controls.container.classList.remove("hidden");
        const authenticated = window.documentAuth.isAuthenticated();
        controls.status.textContent = authenticated
            ? "Удостоверен профил"
            : "Не сте влезли";
        controls.button.textContent = authenticated
            ? "Изход"
            : "Вход";
        controls.button.addEventListener("click", async () => {
            controls.button.disabled = true;
            try {
                if (window.documentAuth.isAuthenticated()) {
                    await window.documentAuth.signOut();
                } else {
                    await window.documentAuth.signIn();
                }
            } finally {
                controls.button.disabled = false;
            }
        });
    } catch (error) {
        controls.container.classList.remove("hidden");
        controls.status.textContent = "Грешка при удостоверяване";
        controls.button.textContent = "Опитай отново";
        controls.button.addEventListener("click", () => {
            window.location.reload();
        });
    }
}

initializeAuthControls();
