<script setup lang="ts">
import { toasts } from '../composables/useToast';
import { CheckCircle2, AlertTriangle } from 'lucide-vue-next';
</script>

<template>
  <div class="fixed bottom-5 right-5 sm:bottom-6 sm:right-6 z-[80] flex flex-col gap-3 pointer-events-none">
    <TransitionGroup name="toast">
      <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
          'pointer-events-auto min-w-[280px] max-w-[360px] rounded-[22px] border backdrop-blur-2xl shadow-[0_20px_60px_rgba(15,23,42,0.18)] px-4 py-4 flex items-start gap-3.5 text-sm',
          toast.type === 'success'
            ? 'bg-white/90 dark:bg-[#12161d]/92 border-slate-200/80 dark:border-emerald-500/20 text-slate-800 dark:text-emerald-50'
            : 'bg-white/90 dark:bg-[#181116]/92 border-slate-200/80 dark:border-red-500/20 text-slate-800 dark:text-red-50'
        ]"
      >
        <div
            :class="[
            'shrink-0 mt-0.5 w-9 h-9 rounded-2xl flex items-center justify-center border',
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-600 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400'
              : 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-400'
          ]"
        >
          <CheckCircle2 v-if="toast.type === 'success'" class="w-[18px] h-[18px]" />
          <AlertTriangle v-else class="w-[18px] h-[18px]" />
        </div>

        <div class="min-w-0 flex-1">
          <div
              :class="[
              'text-[11px] uppercase tracking-[0.18em] font-bold mb-1',
              toast.type === 'success'
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-red-600 dark:text-red-400'
            ]"
          >
            {{ toast.type === 'success' ? 'Успешно' : 'Ошибка' }}
          </div>

          <div class="leading-6 font-medium text-slate-700 dark:text-slate-200 break-words">
            {{ toast.message }}
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.35s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}
</style>