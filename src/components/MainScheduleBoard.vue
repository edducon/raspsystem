<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { CalendarDays, ChevronLeft, ChevronRight, Search } from 'lucide-vue-next';
import {
  formatGroupValue,
  matchesGroupQuery,
  getNormalizedCursorIndex,
  getFormattedCursorIndex,
} from '../lib/groupFormat';

const props = defineProps<{
  groups: { uuid: string; number: string }[];
}>();

const selectedGroupUuid = ref('');
const groupSearchQuery = ref('');
const showGroupDropdown = ref(false);
const currentDate = ref(new Date());
const activeDay = ref(0);

const dayLabels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const timeSlots = ['09:00', '10:40', '12:20', '14:30', '16:10', '17:50'];

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 20);
  return props.groups.filter((group) => matchesGroupQuery(group.number, groupSearchQuery.value)).slice(0, 20);
});

const currentWeekStart = computed(() => {
  const date = new Date(currentDate.value);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  const start = new Date(date.setDate(diff));
  start.setHours(0, 0, 0, 0);
  return start;
});

const weekDays = computed(() => dayLabels.map((label, index) => {
  const date = new Date(currentWeekStart.value);
  date.setDate(date.getDate() + index);
  return {
    label,
    shortDate: new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit' }).format(date),
  };
}));

const weekLabel = computed(() => {
  const start = weekDays.value[0]?.shortDate;
  const end = weekDays.value[5]?.shortDate;
  return start && end ? `${start} — ${end}` : '';
});

function handleGroupInput(event: Event) {
  const input = event.target as HTMLInputElement;
  const normalizedCursorIndex = getNormalizedCursorIndex(input.value, input.selectionStart);
  const formatted = formatGroupValue(input.value);

  groupSearchQuery.value = formatted;
  selectedGroupUuid.value = '';
  showGroupDropdown.value = true;

  nextTick(() => {
    const cursorIndex = getFormattedCursorIndex(formatted, normalizedCursorIndex);
    input.setSelectionRange(cursorIndex, cursorIndex);
  });
}

function selectGroup(group: { uuid: string; number: string }) {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
}

function clearGroup() {
  selectedGroupUuid.value = '';
  groupSearchQuery.value = '';
  showGroupDropdown.value = false;
}

function shiftWeek(direction: -1 | 1) {
  const date = new Date(currentDate.value);
  date.setDate(date.getDate() + direction * 7);
  currentDate.value = date;
}
</script>

<template>
  <section class="overflow-hidden rounded-[24px] border border-[var(--panel-border)] bg-[var(--panel-bg)] shadow-[var(--panel-shadow)]">
    <div class="border-b border-[var(--panel-border)] px-5 py-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="academic-kicker">Основное расписание</p>
          <h1 class="mt-2 text-3xl font-black tracking-tight text-slate-950 dark:text-white">Учебная неделя</h1>
        </div>

        <div class="grid gap-3 sm:grid-cols-[minmax(0,18rem)_auto]">
          <div class="relative">
            <Search class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              :value="groupSearchQuery"
              @focus="showGroupDropdown = true"
              @input="handleGroupInput"
              type="text"
              placeholder="Номер группы"
              class="h-[52px] w-full rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] pl-12 pr-4 text-sm font-semibold text-slate-900 outline-none focus:border-[var(--accent)] dark:text-white"
            />

            <div
              v-if="showGroupDropdown && filteredGroups.length > 0"
              class="absolute left-0 right-0 z-30 mt-2 max-h-72 overflow-y-auto rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] shadow-[var(--panel-shadow)]"
            >
              <button
                v-for="group in filteredGroups"
                :key="group.uuid"
                type="button"
                @click="selectGroup(group)"
                class="block w-full px-4 py-3 text-left text-sm font-semibold text-slate-700 transition-colors hover:bg-[var(--panel-muted)] dark:text-slate-200"
              >
                {{ group.number }}
              </button>
            </div>
          </div>

          <button
            @click="clearGroup"
            class="h-[52px] rounded-[18px] border border-slate-900 bg-slate-900 px-5 text-sm font-bold text-white dark:border-white dark:bg-white dark:text-slate-900"
          >
            Сбросить
          </button>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-3">
        <div class="inline-flex items-center rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] p-1">
          <button @click="shiftWeek(-1)" class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 dark:text-slate-400">
            <ChevronLeft class="h-4 w-4" />
          </button>
          <div class="min-w-[140px] px-3 text-center text-sm font-black text-slate-900 dark:text-white">
            {{ weekLabel }}
          </div>
          <button @click="shiftWeek(1)" class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 dark:text-slate-400">
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>

        <div v-if="selectedGroupUuid" class="inline-flex items-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)] px-3 py-1.5 text-sm font-semibold text-slate-700 dark:text-slate-200">
          {{ groupSearchQuery }}
        </div>
      </div>
    </div>

    <div class="border-b border-[var(--panel-border)] bg-[var(--panel-muted)] px-3 py-3">
      <div class="grid grid-cols-3 gap-2 sm:grid-cols-6">
        <button
          v-for="(day, index) in weekDays"
          :key="`${day.label}-${day.shortDate}`"
          @click="activeDay = index"
          :class="activeDay === index
            ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
            : 'border-transparent bg-transparent text-slate-500 dark:text-slate-400'"
          class="rounded-[16px] border px-3 py-3 text-center text-sm"
        >
          <div class="font-black">{{ day.label }}</div>
          <div class="mt-0.5 text-[10px] opacity-70">{{ day.shortDate }}</div>
        </button>
      </div>
    </div>

    <div v-if="!selectedGroupUuid" class="px-5 py-16 text-center">
      <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
        <CalendarDays class="h-7 w-7 text-slate-400 dark:text-slate-500" />
      </div>
      <div class="text-lg font-black tracking-tight text-slate-900 dark:text-white">Выберите группу</div>
    </div>

    <div v-else class="p-5">
      <div class="grid gap-3 lg:grid-cols-[7rem_repeat(3,minmax(0,1fr))]">
        <div
          v-for="time in timeSlots"
          :key="`time-${time}`"
          class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-4 text-sm font-semibold text-slate-600 dark:text-slate-300"
        >
          {{ time }}
        </div>
      </div>

      <div class="mt-4 rounded-[18px] border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-5 py-10 text-center">
        <div class="text-lg font-black tracking-tight text-slate-900 dark:text-white">Основное расписание подключается</div>
        <div class="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Для группы {{ groupSearchQuery }} здесь будет выводиться обычная учебная неделя. Раздел пересдач расположен ниже.
        </div>
      </div>
    </div>

    <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-20"></div>
  </section>
</template>
