"use strict";

import {
    InteractionRequiredAuthError,
    PublicClientApplication,
} from "@azure/msal-browser";

const CONFIG_URL = "/api/v1/auth/config";

let config = null;
let client = null;
let account = null;
let initialized = false;

async function loadConfig() {
    const response = await fetch(CONFIG_URL, {
        headers: { Accept: "application/json" },
    });
    if (!response.ok) {
        throw new Error(`Authentication configuration failed: HTTP ${response.status}`);
    }
    return response.json();
}

async function initialize() {
    if (initialized) return;
    config = await loadConfig();
    initialized = true;
    if (!config.enabled) return;

    client = new PublicClientApplication({
        auth: {
            clientId: config.client_id,
            authority: config.authority,
            redirectUri: `${window.location.origin}${config.redirect_path}`,
            postLogoutRedirectUri: `${window.location.origin}${config.redirect_path}`,
        },
        cache: {
            cacheLocation: "sessionStorage",
        },
    });
    await client.initialize();
    const redirectResult = await client.handleRedirectPromise();
    account = redirectResult?.account || client.getAllAccounts()[0] || null;
    if (account) client.setActiveAccount(account);
}

async function signIn() {
    await initialize();
    if (!config?.enabled) return;
    await client.loginRedirect({ scopes: config.scopes });
}

async function signOut() {
    await initialize();
    if (!config?.enabled || !account) return;
    await client.logoutRedirect({ account });
}

async function accessToken() {
    await initialize();
    if (!config?.enabled) return null;
    account = client.getActiveAccount() || client.getAllAccounts()[0] || null;
    if (!account) {
        await signIn();
        return null;
    }
    try {
        const result = await client.acquireTokenSilent({
            account,
            scopes: config.scopes,
        });
        return result.accessToken;
    } catch (error) {
        if (error instanceof InteractionRequiredAuthError) {
            await client.acquireTokenRedirect({
                account,
                scopes: config.scopes,
            });
            return null;
        }
        throw error;
    }
}

async function authenticatedFetch(input, init = {}) {
    const token = await accessToken();
    const headers = new Headers(init.headers || {});
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(input, { ...init, headers });
}

function isEnabled() {
    return Boolean(config?.enabled);
}

function isAuthenticated() {
    return Boolean(account);
}

window.documentAuth = {
    authenticatedFetch,
    initialize,
    isAuthenticated,
    isEnabled,
    signIn,
    signOut,
};
