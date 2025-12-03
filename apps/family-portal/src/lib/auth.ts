import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

const config = {
    authority: 'https://auth.pesulabs.net/application/o/family-assistant/',
    client_id: 'tw2kzde62QPl0dzYhY6YR9vjEQ4GYHcJ4KIa7fbD',
    redirect_uri: `${window.location.origin}/auth/callback`,
    post_logout_redirect_uri: window.location.origin,
    response_type: 'code',
    scope: 'openid profile email',
    userStore: new WebStorageStateStore({ store: window.localStorage }),
    automaticSilentRenew: true,
    // Enable PKCE for public client (SPA)
    // This is required for browser-based apps as client secrets cannot be kept secure
    loadUserInfo: true,
};

export const userManager = new UserManager(config);

export async function login() {
    await userManager.signinRedirect();
}

export async function logout() {
    await userManager.signoutRedirect();
}

export async function getUser() {
    return await userManager.getUser();
}

export async function handleCallback() {
    return await userManager.signinRedirectCallback();
}
