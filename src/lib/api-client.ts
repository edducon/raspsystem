// Типизация ответа расписания
export interface PairData {
    group: string;
    subject: string;
    teachers: string[];
    start_date: string;
    end_date: string;
    rooms: string[];
    location: string;
    type: string;
    link: string | null;
}

export type DaySchedule = {
    [slot in "1" | "2" | "3" | "4" | "5" | "6" | "7"]: PairData[] | null;
};

export interface ScheduleApiResponse {
    status: string;
    response: Record<string, DaySchedule>;
}

const API_BASE_URL = "https://zefixed.ru/raspyx/api/v2";
const AUTH_URL = "https://zefixed.ru/auth/api/v1/login";

// Переменная для хранения токена в памяти сервера Astro
let cachedAccessToken: string | null = null;

/**
 * Функция получения JWT токена
 */
async function getAccessToken(): Promise<string> {
    if (cachedAccessToken) return cachedAccessToken;

    console.log("Получение нового JWT токена...");
    const response = await fetch(AUTH_URL, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: "accesstoapi",
            password: "YWNjZXNzdG9hcGk="
        })
    });

    if (!response.ok) {
        throw new Error(`Ошибка авторизации в API: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.result?.access_token) {
        cachedAccessToken = data.result.access_token;
        return cachedAccessToken;
    }
    else if (data.status === "OK" && data.response?.token) {
        cachedAccessToken = data.response.token;
        return cachedAccessToken;
    }

    throw new Error("Неверный формат ответа при авторизации");
}

/**
 * Базовая функция для fetch-запросов с автоматической подстановкой JWT
 */
async function apiFetch<T>(endpoint: string, options: RequestInit = {}, retryCount = 1): Promise<T> {
    const token = await getAccessToken();
    const url = `${API_BASE_URL}${endpoint}`;

    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("Content-Type", "application/json");
    headers.set("Accept", "application/json");

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 && retryCount > 0) {
        console.log("Токен истек, обновляем...");
        cachedAccessToken = null;
        return apiFetch<T>(endpoint, options, retryCount - 1);
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API Error ${response.status}: ${JSON.stringify(errorData)}`);
    }

    return response.json() as Promise<T>;
}

// --- МЕТОДЫ ДЛЯ РАБОТЫ С API ---
export const RaspyxAPI = {
    getGroups: async () => {
        return apiFetch<any>("/groups");
    },

    getGroupSchedule: async (groupNumber: string, isSession: boolean = false): Promise<ScheduleApiResponse> => {
        return apiFetch<ScheduleApiResponse>(`/schedule/group_number/${encodeURIComponent(groupNumber)}?is_session=${isSession}`);
    },

    getTeacherSchedule: async (teacherFio: string, isSession: boolean = false): Promise<ScheduleApiResponse> => {
        return apiFetch<ScheduleApiResponse>(`/schedule/teacher_fio/${encodeURIComponent(teacherFio)}?is_session=${isSession}`);
    },

    getTeachers: async () => {
        return apiFetch<any>("/teachers");
    },

    getSubjects: async () => {
        return apiFetch<any>("/subjects");
    },
};