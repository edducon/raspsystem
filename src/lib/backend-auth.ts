export interface BackendAuthUser {
    id: number;
    username: string;
    fullName: string;
    role: "ADMIN" | "EMPLOYEE" | "TEACHER";
    isActive: boolean;
    mustChangePassword: boolean;
    departmentId: number | null;
    departmentIds: number[];
    teacherUuid: string | null;
}

export interface BackendSessionState {
    user: BackendAuthUser;
    csrfToken: string;
}

const stripTrailingSlash = (value: string) => value.replace(/\/+$/, '');

function getDefaultPublicBackendApiUrl(): string {
    return import.meta.env.APP_ENV === "production" ? "/api" : "http://localhost:8000/api";
}

export function getPublicBackendApiUrl(): string {
    const configuredUrl = stripTrailingSlash(import.meta.env.BACKEND_API_URL ?? getDefaultPublicBackendApiUrl());
    if (/\/raspyx\/api(?:\/|$)/i.test(configuredUrl)) {
        console.warn("BACKEND_API_URL points to Raspyx; falling back to the application backend API.");
        return getDefaultPublicBackendApiUrl();
    }
    return configuredUrl;
}

export function getServerBackendApiUrl(): string {
    return stripTrailingSlash(import.meta.env.BACKEND_INTERNAL_API_URL ?? getPublicBackendApiUrl());
}

export async function fetchCurrentSession(request: Request): Promise<BackendSessionState | null> {
    const cookie = request.headers.get("cookie");
    if (!cookie) {
        return null;
    }

    const response = await fetch(`${getServerBackendApiUrl()}/auth/me`, {
        headers: {
            Accept: "application/json",
            Cookie: cookie,
        },
    });

    if (!response.ok) {
        return null;
    }

    return (await response.json()) as BackendSessionState;
}
