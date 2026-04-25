<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import {
  Search,
  Clock,
  MapPin,
  Globe,
  CalendarDays,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next';
import { getDateLabel, daysUntil } from '../lib/dateUtils';
import { useRecentGroups } from '../composables/useRecentGroups';
import {
  formatGroupValue,
  matchesGroupQuery,
  getNormalizedCursorIndex,
  getFormattedCursorIndex,
} from '../lib/groupFormat';

const props = defineProps<{
  groups: { uuid: string; number: string }[];
  retakes: any[];
  today?: string;
}>();

const groupSearchQuery = ref('');
const selectedGroupUuid = ref('');
const showGroupDropdown = ref(false);
const selectedDateFilter = ref('');
const activeAttemptBySubject = ref<Record<string, string | number>>({});

const { recentGroups, addRecentGroup, clearRecentGroups } = useRecentGroups();

const baseDate = props.today ? new Date(props.today) : new Date();
const openMonth = ref(new Date(baseDate.getFullYear(), baseDate.getMonth(), 1));

const TIME_MAPPING: Record<number, string> = {
  1: '09:00-10:30',
  2: '10:40-12:10',
  3: '12:20-13:50',
  4: '14:30-16:00',
  5: '16:10-17:40',
  6: '17:50-19:20',
  7: '19:30-21:00',
};

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 20);

  return props.groups
      .filter((group) => matchesGroupQuery(group.number, groupSearchQuery.value))
      .slice(0, 20);
});

const studentRetakes = computed(() => {
  if (!selectedGroupUuid.value) return [];

  return props.retakes
      .filter((retake) => retake.groupUuid === selectedGroupUuid.value)
      .map((retake) => ({
        ...retake,
        dateLabel: getDateLabel(retake.date),
        daysDelta: daysUntil(retake.date),
      }))
      .filter((retake) => retake.daysDelta >= 0)
      .sort((a, b) => {
        const dateDiff = new Date(a.date).getTime() - new Date(b.date).getTime();
        if (dateDiff !== 0) return dateDiff;

        return (a.attemptNumber || 1) - (b.attemptNumber || 1);
      });
});

const availableDateSet = computed(() => new Set(studentRetakes.value.map((retake) => retake.date)));

const filteredRetakes = computed(() =>
    studentRetakes.value.filter((retake) => {
      const dateOk = !selectedDateFilter.value || retake.date === selectedDateFilter.value;
      return dateOk;
    }),
);

const retakesBySubject = computed(() => {
  const map = new Map<string, any[]>();

  filteredRetakes.value.forEach((retake) => {
    const subjectName = retake.subjectName || 'Без названия';

    if (!map.has(subjectName)) {
      map.set(subjectName, []);
    }

    map.get(subjectName)?.push(retake);
  });

  return Array.from(map.entries()).map(([subjectName, retakes]) => ({
    subjectName,
    retakes: retakes
        .slice()
        .sort((a, b) => (a.attemptNumber || 1) - (b.attemptNumber || 1))
        .slice(0, 3),
  }));
});

const nearestUpcomingRetake = computed(() => filteredRetakes.value.find((retake) => retake.daysDelta >= 0) ?? null);

const monthLabel = computed(() =>
    new Intl.DateTimeFormat('ru-RU', {
      month: 'long',
      year: 'numeric',
    }).format(openMonth.value),
);

const calendarDays = computed(() => {
  const year = openMonth.value.getFullYear();
  const month = openMonth.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const firstWeekday = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const days: Array<{
    key: string;
    label: number | '';
    iso: string | '';
    inMonth: boolean;
    isAvailable: boolean;
    isSelected: boolean;
    isToday: boolean;
  }> = [];

  for (let i = 0; i < firstWeekday; i += 1) {
    days.push({
      key: `empty-start-${i}`,
      label: '',
      iso: '',
      inMonth: false,
      isAvailable: false,
      isSelected: false,
      isToday: false,
    });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(year, month, day);
    const iso = toIsoDate(date);

    days.push({
      key: iso,
      label: day,
      iso,
      inMonth: true,
      isAvailable: !!selectedGroupUuid.value && availableDateSet.value.has(iso),
      isSelected: selectedDateFilter.value === iso,
      isToday: iso === toIsoDate(baseDate),
    });
  }

  while (days.length % 7 !== 0) {
    const idx = days.length;

    days.push({
      key: `empty-end-${idx}`,
      label: '',
      iso: '',
      inMonth: false,
      isAvailable: false,
      isSelected: false,
      isToday: false,
    });
  }

  return days;
});

function handleGroupInput(event: Event) {
  const input = event.target as HTMLInputElement;
  const normalizedCursorIndex = getNormalizedCursorIndex(input.value, input.selectionStart);
  const formatted = formatGroupValue(input.value);

  groupSearchQuery.value = formatted;
  selectedGroupUuid.value = '';
  selectedDateFilter.value = '';
  activeAttemptBySubject.value = {};
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
  selectedDateFilter.value = '';
  activeAttemptBySubject.value = {};
  addRecentGroup(group);

  const firstDate = studentRetakes.value[0]?.date;

  if (firstDate) {
    const date = new Date(firstDate);
    openMonth.value = new Date(date.getFullYear(), date.getMonth(), 1);
  } else {
    openMonth.value = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
  }
}

function clearSelectedGroup() {
  selectedGroupUuid.value = '';
  groupSearchQuery.value = '';
  selectedDateFilter.value = '';
  activeAttemptBySubject.value = {};
  showGroupDropdown.value = false;
  openMonth.value = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
}

function clearDateFilter() {
  selectedDateFilter.value = '';
}

function prevMonth() {
  openMonth.value = new Date(openMonth.value.getFullYear(), openMonth.value.getMonth() - 1, 1);
}

function nextMonth() {
  openMonth.value = new Date(openMonth.value.getFullYear(), openMonth.value.getMonth() + 1, 1);
}

function pickDate(iso: string, isAvailable: boolean) {
  if (!iso || !isAvailable) return;
  selectedDateFilter.value = selectedDateFilter.value === iso ? '' : iso;
  activeAttemptBySubject.value = {};
}

function getActiveAttempt(subjectName: string, retakes: any[]) {
  return activeAttemptBySubject.value[subjectName] ?? retakes[0]?.id;
}

function setActiveAttempt(subjectName: string, retakeId: number | string) {
  activeAttemptBySubject.value = {
    ...activeAttemptBySubject.value,
    [subjectName]: retakeId,
  };
}

function isActiveAttempt(subjectName: string, retakes: any[], retake: any) {
  if (retakes.length === 1) return true;
  return getActiveAttempt(subjectName, retakes) === retake.id;
}

function getPanelClass(subjectName: string, retakes: any[], retake: any) {
  if (retakes.length === 1) {
    return 'min-h-[220px] flex-1 p-5 cursor-default';
  }

  if (isActiveAttempt(subjectName, retakes, retake)) {
    return 'min-h-[240px] flex-[3.2] p-5';
  }

  return 'min-h-[96px] flex-[0.78] p-4 md:min-h-[240px]';
}

function getDateParts(dateStr: string) {
  const date = new Date(dateStr);

  return {
    day: new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
    }).format(date),
    month: new Intl.DateTimeFormat('ru-RU', {
      month: 'short',
    })
        .format(date)
        .replace('.', ''),
    year: new Intl.DateTimeFormat('ru-RU', {
      year: 'numeric',
    }).format(date),
  };
}

function formatTimeSlots(slots: number[]) {
  if (!Array.isArray(slots) || slots.length === 0) return 'Время уточняется';
  return slots.map((slot) => TIME_MAPPING[slot] || `Пара ${slot}`).join(', ');
}

function getAttemptTone(attempt: number) {
  if (attempt === 1) return 'bg-[var(--accent-soft)] text-[var(--accent-strong)]';
  if (attempt === 2) return 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300';
  return 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300';
}

function getStatusText(daysDelta: number) {
  if (daysDelta === 0) return 'Сегодня';
}

function getStatusTone(daysDelta: number) {
  if (daysDelta === 0) return 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-300';
  if (daysDelta <= 3) return 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300';
  return 'bg-[var(--accent-soft)] text-[var(--accent-strong)]';
}

function pad(value: number) {
  return String(value).padStart(2, '0');
}

function toIsoDate(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}
</script>

<template>
  <div class="w-full">
    <div class="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px] 2xl:grid-cols-[minmax(0,1fr)_390px]">
      <div class="max-w-[980px] space-y-5">
        <section class="rounded-[28px] border border-[var(--panel-border)] bg-[var(--panel-bg)] shadow-[var(--panel-shadow)]">
          <div class="px-5 pb-5 pt-6 lg:px-6 lg:pt-7">
            <div class="mb-5 flex flex-col gap-2">
              <h2 class="text-2xl font-black tracking-tight text-slate-950 dark:text-white lg:text-3xl">
                Найдите пересдачи своей группы
              </h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">
                Введите номер группы.
              </p>
            </div>

            <div class="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
              <div class="relative">
                <Search class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                    :value="groupSearchQuery"
                    @focus="showGroupDropdown = true"
                    @input="handleGroupInput"
                    type="text"
                    placeholder="Например: 241-321"
                    class="h-[58px] w-full rounded-[20px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] pl-12 pr-4 text-base font-semibold text-slate-900 outline-none focus:border-[var(--accent)] dark:text-white"
                />
              </div>

              <button
                  @click="clearSelectedGroup"
                  class="h-[58px] rounded-[20px] border border-slate-900 bg-slate-900 px-5 text-sm font-bold text-white dark:border-white dark:bg-white dark:text-slate-900"
              >
                Сбросить
              </button>
            </div>

            <div
                v-if="showGroupDropdown && (filteredGroups.length > 0 || (recentGroups.length > 0 && !groupSearchQuery))"
                class="relative z-30 mt-3 max-h-80 overflow-y-auto rounded-[22px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] shadow-[var(--panel-shadow)]"
            >
              <div v-if="recentGroups.length > 0 && !groupSearchQuery" class="border-b border-[var(--panel-border)]">
                <div class="flex items-center justify-between px-4 py-3">
                  <span class="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">Недавние группы</span>
                  <button
                      @click.stop="clearRecentGroups"
                      class="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400 hover:text-[var(--accent-strong)]"
                  >
                    Очистить
                  </button>
                </div>

                <div
                    v-for="group in recentGroups"
                    :key="`recent-${group.uuid}`"
                    @click="selectGroup(group)"
                    class="flex cursor-pointer items-center gap-3 px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-[var(--panel-muted)] dark:text-slate-200"
                >
                  <Clock class="h-4 w-4 shrink-0 text-slate-400" />
                  <span>{{ group.number }}</span>
                </div>
              </div>

              <div
                  v-for="group in filteredGroups"
                  :key="group.uuid"
                  @click="selectGroup(group)"
                  class="cursor-pointer px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-[var(--panel-muted)] dark:text-slate-200"
              >
                {{ group.number }}
              </div>
            </div>

            <div v-if="selectedGroupUuid" class="mt-4 flex items-center justify-end">
              <button
                  @click="clearSelectedGroup"
                  class="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
              >
                <X class="h-4 w-4" />
                Сменить группу
              </button>
            </div>
          </div>

          <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-20"></div>
        </section>

        <section
            v-if="!selectedGroupUuid"
            class="rounded-[28px] border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg)] px-6 py-16 text-center"
        >
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
            <Search class="h-6 w-6 text-slate-400 dark:text-slate-500" />
          </div>
          <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">Введите номер группы</h3>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
            После выбора группы здесь появятся назначенные пересдачи.
          </p>
        </section>

        <section
            v-else-if="studentRetakes.length === 0"
            class="rounded-[28px] border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg)] px-6 py-16 text-center"
        >
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
            <CalendarDays class="h-6 w-6 text-slate-400 dark:text-slate-500" />
          </div>
          <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">Пересдачи не назначены</h3>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Для группы <span class="font-semibold text-slate-700 dark:text-slate-300">{{ groupSearchQuery }}</span> актуальных пересдач нет.
          </p>
        </section>

        <section
            v-else-if="filteredRetakes.length === 0"
            class="rounded-[28px] border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg)] px-6 py-16 text-center"
        >
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
            <Search class="h-6 w-6 text-slate-400 dark:text-slate-500" />
          </div>
          <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">Ничего не найдено</h3>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Попробуйте сбросить выбранную дату.
          </p>

          <button
              v-if="selectedDateFilter"
              @click="clearDateFilter"
              class="mt-4 rounded-full border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-2 text-sm font-semibold text-[var(--accent-strong)]"
          >
            Сбросить дату
          </button>
        </section>

        <section v-else class="space-y-4">
          <article
              v-for="subjectGroup in retakesBySubject"
              :key="subjectGroup.subjectName"
              class="overflow-hidden rounded-[30px] border border-[var(--panel-border)] bg-[var(--panel-bg)] p-2 shadow-[var(--panel-shadow)]"
          >
            <div class="flex h-[270px] flex-col gap-2 md:flex-row">
              <button
                  v-for="retake in subjectGroup.retakes"
                  :key="retake.id"
                  type="button"
                  @click="subjectGroup.retakes.length > 1 && setActiveAttempt(subjectGroup.subjectName, retake.id)"
                  class="group relative overflow-hidden rounded-[24px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] text-left transition-[width,background-color,border-color,box-shadow] duration-500 ease-in-out"
                  :class="getPanelClass(subjectGroup.subjectName, subjectGroup.retakes, retake)"
              >
                <div class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100 bg-[radial-gradient(circle_at_top_right,rgba(90,122,165,0.16),transparent_45%)]"></div>

                <div
                    v-if="subjectGroup.retakes.length > 1 && !isActiveAttempt(subjectGroup.subjectName, subjectGroup.retakes, retake)"
                    class="relative flex h-full flex-col items-start justify-between"
                >
                  <div
                      class="inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]"
                      :class="getAttemptTone(retake.attemptNumber || 1)"
                  >
                    Попытка {{ retake.attemptNumber || 1 }}
                  </div>

                  <div class="space-y-1">
                    <div class="text-3xl font-black leading-none tracking-tight text-slate-950 dark:text-white">
                      {{ getDateParts(retake.date).day }}
                    </div>
                    <div class="text-sm font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
                      {{ getDateParts(retake.date).month }}
                    </div>
                    <div class="text-xs font-semibold text-slate-400">
                      {{ getDateParts(retake.date).year }}
                    </div>
                  </div>
                </div>

                <div v-else class="relative flex h-full flex-col justify-between gap-5">
                  <div>
                    <div class="mb-4 flex flex-wrap items-center gap-2">
                      <span
                          class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]"
                          :class="getStatusTone(retake.daysDelta)"
                      >
                        {{ getStatusText(retake.daysDelta) }}
                      </span>

                      <span
                          class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]"
                          :class="getAttemptTone(retake.attemptNumber || 1)"
                      >
                        Попытка {{ retake.attemptNumber || 1 }}
                      </span>

                      <span
                          v-if="retake.id === nearestUpcomingRetake?.id"
                          class="rounded-full bg-slate-900 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-white dark:bg-white dark:text-slate-900"
                      >
                        Ближайшая
                      </span>
                    </div>

                    <h3 class="max-w-2xl text-2xl font-black leading-tight tracking-tight text-slate-950 dark:text-white">
                      {{ subjectGroup.subjectName }}
                    </h3>
                  </div>

                  <div class="grid gap-3 sm:grid-cols-3">
                    <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg)] px-4 py-3 text-center">
                      <div class="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                        Дата
                      </div>
                      <div class="text-3xl font-black leading-none text-slate-900 dark:text-white">
                        {{ getDateParts(retake.date).day }}
                      </div>
                      <div class="mt-1 text-sm font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
                        {{ getDateParts(retake.date).month }}
                      </div>
                      <div class="mt-0.5 text-xs font-semibold text-slate-400">
                        {{ getDateParts(retake.date).year }}
                      </div>
                    </div>

                    <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg)] px-4 py-3">
                      <div class="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                        <Clock class="h-3.5 w-3.5" />
                        Время
                      </div>
                      <div class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {{ formatTimeSlots(retake.timeSlots) }}
                      </div>
                    </div>

                    <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg)] px-4 py-3">
                      <div class="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                        <component :is="retake.link ? Globe : MapPin" class="h-3.5 w-3.5" />
                        Формат
                      </div>

                      <div v-if="retake.link" class="space-y-1">
                        <div class="text-sm font-bold text-slate-900 dark:text-white">
                          Онлайн
                        </div>
                        <a
                            :href="retake.link"
                            target="_blank"
                            @click.stop
                            class="text-sm font-semibold text-[var(--accent-strong)] hover:underline"
                        >
                          Ссылка
                        </a>
                      </div>

                      <div v-else class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {{ retake.room || 'Аудитория уточняется' }}
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </article>
        </section>
      </div>

      <aside class="xl:sticky xl:top-24 xl:self-start xl:pl-2 2xl:pl-4">
        <section class="rounded-[28px] border border-[var(--panel-border)] bg-[var(--panel-bg)] p-4 shadow-[var(--panel-shadow)]">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
                Календарь
              </div>
              <div class="mt-1 text-lg font-black capitalize tracking-tight text-slate-950 dark:text-white">
                {{ monthLabel }}
              </div>
            </div>

            <div class="flex items-center gap-2">
              <button
                  type="button"
                  @click="prevMonth"
                  class="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--panel-border)] bg-[var(--panel-bg-strong)]"
              >
                <ChevronLeft class="h-4 w-4 text-slate-500" />
              </button>

              <button
                  type="button"
                  @click="nextMonth"
                  class="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--panel-border)] bg-[var(--panel-bg-strong)]"
              >
                <ChevronRight class="h-4 w-4 text-slate-500" />
              </button>
            </div>
          </div>

          <div class="mb-2 grid grid-cols-7 gap-2 text-center text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">
            <div>Пн</div>
            <div>Вт</div>
            <div>Ср</div>
            <div>Чт</div>
            <div>Пт</div>
            <div>Сб</div>
            <div>Вс</div>
          </div>

          <div class="grid grid-cols-7 gap-2">
            <button
                v-for="day in calendarDays"
                :key="day.key"
                type="button"
                :disabled="!day.isAvailable"
                @click="pickDate(day.iso, day.isAvailable)"
                class="h-10 rounded-xl text-sm font-semibold transition"
                :class="[
                !day.inMonth
                  ? 'pointer-events-none opacity-0'
                  : day.isSelected
                    ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
                    : day.isAvailable
                      ? 'border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] text-slate-900 hover:border-[var(--accent)] dark:text-white'
                      : selectedGroupUuid
                        ? 'cursor-not-allowed bg-[var(--panel-muted)] text-slate-300 dark:text-slate-600'
                        : 'cursor-not-allowed bg-[var(--panel-muted)] text-slate-300 opacity-60 dark:text-slate-600',
                day.isToday && !day.isSelected && day.isAvailable ? 'ring-1 ring-[var(--accent)]' : '',
              ]"
            >
              {{ day.label }}
            </button>
          </div>

          <div v-if="selectedDateFilter" class="mt-4 rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] p-3">
            <button
                @click="clearDateFilter"
                class="font-semibold text-[var(--accent-strong)] hover:underline"
            >
              Сбросить выбранную дату
            </button>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>