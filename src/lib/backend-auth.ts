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

export function getPublicBackendApiUrl(): string {
    return stripTrailingSlash(import.meta.env.BACKEND_API_URL ?? "http://localhost:8000/api");
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
