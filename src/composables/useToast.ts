import { ref } from 'vue';

export interface Toast {
    id: number;
    message: string;
    type: 'success' | 'error';
}

export const toasts = ref<Toast[]>([]);

export const addToast = (message: string, type: 'success' | 'error' = 'success') => {
    const id = Date.now();
    toasts.value.push({ id, message, type });

    setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id);
    }, 4000);
};