<script setup lang="ts">
import { toasts } from '../composables/useToast';
import { CheckCircle, AlertCircle } from 'lucide-vue-next';
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
    <TransitionGroup name="toast">
      <div
          v-for="toast in toasts" :key="toast.id"
          :class="[
          'px-5 py-3.5 rounded-xl shadow-lg flex items-center gap-3 font-medium min-w-[280px] text-sm pointer-events-auto',
          toast.type === 'success'
            ? 'bg-slate-900 text-white dark:bg-emerald-950 dark:text-emerald-100 border border-slate-800 dark:border-emerald-800/50'
            : 'bg-red-600 text-white dark:bg-red-950 dark:text-red-100 border border-red-700 dark:border-red-800/50'
        ]"
      >
        <CheckCircle v-if="toast.type === 'success'" class="w-5 h-5 opacity-80" />
        <AlertCircle v-else class="w-5 h-5 opacity-80" />
        {{ toast.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateY(20px) scale(0.95); }
.toast-leave-to { opacity: 0; transform: scale(0.95); }
</style>