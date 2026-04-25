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
  Users,
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
const selectedSubjectFilter = ref('');
const selectedDateFilter = ref('');
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
  return props.groups.filter((group) => matchesGroupQuery(group.number, groupSearchQuery.value)).slice(0, 20);
});

const studentRetakes = computed(() => {
  if (!selectedGroupUuid.value) return [];

  return props.retakes
      .filter((retake) => retake.groupUuid === selectedGroupUuid.value)
      .map((retake) => ({
        ...retake,
        teachers: sortTeachers(retake.teachers || []),
        dateLabel: getDateLabel(retake.date),
        daysDelta: daysUntil(retake.date),
      }))
      .sort((a, b) => {
        const pastA = daysUntil(a.date) < 0 ? 1 : 0;
        const pastB = daysUntil(b.date) < 0 ? 1 : 0;

        if (pastA !== pastB) return pastA - pastB;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });
});

const availableSubjects = computed(() => {
  const subjects = new Set<string>();
  studentRetakes.value.forEach((retake) => subjects.add(retake.subjectName));
  return Array.from(subjects).sort();
});

const availableDateSet = computed(() => new Set(studentRetakes.value.map((retake) => retake.date)));

const filteredRetakes = computed(() =>
    studentRetakes.value.filter((retake) => {
      const subjectOk = !selectedSubjectFilter.value || retake.subjectName === selectedSubjectFilter.value;
      const dateOk = !selectedDateFilter.value || retake.date === selectedDateFilter.value;
      return subjectOk && dateOk;
    }),
);

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
  selectedSubjectFilter.value = '';
  selectedDateFilter.value = '';
  showGroupDropdown.value = true;

  nextTick(() => {
    const cursorIndex = getFormattedCursorIndex(formatted, normalizedCursorIndex);
    input.setSelectionRange(cursorIndex, cursorIndex);
  });
}

function sortTeachers(teachers: any[]) {
  if (!teachers) return [];

  const roleWeights: Record<string, number> = {
    MAIN: 1,
    CHAIRMAN: 2,
    COMMISSION: 3,
  };

  return [...teachers].sort((a, b) => (roleWeights[a.role] || 99) - (roleWeights[b.role] || 99));
}

function selectGroup(group: { uuid: string; number: string }) {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
  selectedSubjectFilter.value = '';
  selectedDateFilter.value = '';
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
  selectedSubjectFilter.value = '';
  selectedDateFilter.value = '';
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
}

function getTeacherName(teacher: any) {
  return teacher?.name || teacher?.fullName || teacher?.fio || teacher?.teacherName || teacher?.displayName || 'Преподаватель';
}

function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(dateStr));
}

function formatShortDate(dateStr: string) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
  }).format(new Date(dateStr));
}

function getRoleName(role: string) {
  if (role === 'MAIN') return 'Ведущий';
  if (role === 'CHAIRMAN') return 'Председатель';
  return 'Комиссия';
}

function getRoleTone(role: string) {
  if (role === 'MAIN') return 'text-[var(--accent-strong)] bg-[var(--accent-soft)]';
  if (role === 'CHAIRMAN') return 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-500/10';
  return 'text-slate-600 dark:text-slate-300 bg-[var(--panel-muted)]';
}

function getAttemptTone(attempt: number) {
  if (attempt === 1) return 'bg-[var(--accent-soft)] text-[var(--accent-strong)]';
  if (attempt === 2) return 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300';
  return 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300';
}

function getStatusText(daysDelta: number) {
  if (daysDelta < 0) return 'Архив';
  if (daysDelta === 0) return 'Сегодня';
  if (daysDelta <= 3) return 'Скоро';
  return 'Запланировано';
}

function getStatusTone(daysDelta: number) {
  if (daysDelta < 0) return 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300';
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
  <div class="w-full space-y-5">
    <section class="rounded-[28px] border border-[var(--panel-border)] bg-[var(--panel-bg)] shadow-[var(--panel-shadow)]">
      <div class="px-5 pb-5 pt-6 lg:px-6 lg:pt-7">
        <div class="mb-5 flex flex-col gap-2">
          <h2 class="text-2xl font-black tracking-tight text-slate-950 dark:text-white lg:text-3xl">
            Найдите пересдачи своей группы
          </h2>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            Введите номер группы и выберите дату справа, если нужно отфильтровать результаты.
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

        <div
            v-if="selectedGroupUuid"
            class="mt-4 flex flex-wrap items-center gap-2 rounded-[20px] border border-[var(--panel-border)] bg-[var(--panel-muted)] p-3"
        >
          <div class="inline-flex items-center gap-2 rounded-full border border-[var(--panel-border)] bg-[var(--panel-bg)] px-3 py-1.5 text-sm font-semibold text-slate-700 dark:text-slate-200">
            Группа: {{ groupSearchQuery }}
          </div>

          <button
              v-if="availableSubjects.length > 1"
              @click="selectedSubjectFilter = ''"
              :class="selectedSubjectFilter === ''
              ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
              : 'border-[var(--panel-border)] bg-[var(--panel-bg)] text-slate-600 dark:text-slate-300'"
              class="rounded-full border px-3 py-1.5 text-sm font-semibold"
          >
            Все предметы
          </button>

          <button
              v-for="subject in availableSubjects"
              :key="subject"
              @click="selectedSubjectFilter = subject"
              :class="selectedSubjectFilter === subject
              ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
              : 'border-[var(--panel-border)] bg-[var(--panel-bg)] text-slate-600 dark:text-slate-300'"
              class="rounded-full border px-3 py-1.5 text-sm font-semibold"
          >
            {{ subject }}
          </button>

          <button
              v-if="selectedDateFilter"
              @click="clearDateFilter"
              class="rounded-full border border-[var(--panel-border)] bg-[var(--panel-bg)] px-3 py-1.5 text-sm font-semibold text-slate-600 dark:text-slate-300"
          >
            Сбросить дату
          </button>

          <button
              @click="clearSelectedGroup"
              class="ml-auto inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
          >
            <X class="h-4 w-4" />
            Сменить группу
          </button>
        </div>
      </div>

      <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-20"></div>
    </section>

    <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div class="space-y-4">
        <section
            v-if="!selectedGroupUuid"
            class="rounded-[28px] border border-dashed border-[var(--panel-border)] bg-[var(--panel-bg)] px-6 py-16 text-center"
        >
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
            <Search class="h-6 w-6 text-slate-400 dark:text-slate-500" />
          </div>
          <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">Введите номер группы</h3>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
            После выбора группы здесь появятся все назначенные пересдачи.
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
            Для группы <span class="font-semibold text-slate-700 dark:text-slate-300">{{ groupSearchQuery }}</span> записей пока нет.
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
            Попробуйте сбросить фильтр по дате или предмету.
          </p>
        </section>

        <section v-else class="space-y-4">
          <article
              v-for="retake in filteredRetakes"
              :key="retake.id"
              class="rounded-[28px] border border-[var(--panel-border)] bg-[var(--panel-bg)] p-5 shadow-[var(--panel-shadow)]"
          >
            <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div class="min-w-0 flex-1 space-y-4">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]" :class="getStatusTone(retake.daysDelta)">
                    {{ getStatusText(retake.daysDelta) }}
                  </span>

                  <span class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]" :class="getAttemptTone(retake.attemptNumber || 1)">
                    Попытка {{ retake.attemptNumber || 1 }}
                  </span>

                  <span
                      v-if="retake.id === nearestUpcomingRetake?.id"
                      class="rounded-full bg-slate-900 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-white dark:bg-white dark:text-slate-900"
                  >
                    Ближайшая
                  </span>
                </div>

                <div>
                  <h3 class="text-2xl font-black tracking-tight text-slate-950 dark:text-white">
                    {{ retake.subjectName }}
                  </h3>
                  <p class="mt-1 text-sm font-medium" :class="retake.dateLabel.colorClass">
                    {{ retake.dateLabel.text }}
                  </p>
                </div>

                <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-3">
                    <div class="mb-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Дата</div>
                    <div class="text-base font-bold text-slate-900 dark:text-white">{{ formatShortDate(retake.date) }}</div>
                    <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ formatDate(retake.date) }}</div>
                  </div>

                  <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-3">
                    <div class="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      <Clock class="h-3.5 w-3.5" />
                      Время
                    </div>
                    <div class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      {{ retake.timeSlots.map((slot: number) => TIME_MAPPING[slot]).join(', ') }}
                    </div>
                  </div>

                  <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-3">
                    <div class="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      <component :is="retake.link ? Globe : MapPin" class="h-3.5 w-3.5" />
                      Формат
                    </div>

                    <a
                        v-if="retake.link"
                        :href="retake.link"
                        target="_blank"
                        class="text-sm font-semibold text-[var(--accent-strong)] hover:underline"
                    >
                      Открыть ссылку
                    </a>

                    <div v-else class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      {{ retake.room || 'Аудитория уточняется' }}
                    </div>
                  </div>

                  <div class="rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 py-3">
                    <div class="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                      <Users class="h-3.5 w-3.5" />
                      Комиссия
                    </div>
                    <div class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      {{ retake.teachers?.length ? `${retake.teachers.length} чел.` : 'Не назначена' }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="w-full xl:max-w-[360px]">
                <div class="rounded-[22px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] p-4">
                  <div class="mb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                    Преподаватели
                  </div>

                  <div
                      v-if="retake.teachers && retake.teachers.length > 0"
                      class="space-y-2"
                  >
                    <div
                        v-for="teacher in retake.teachers"
                        :key="`${retake.id}-${getTeacherName(teacher)}-${teacher.role}`"
                        class="flex items-center justify-between gap-3 rounded-[16px] border border-[var(--panel-border)] bg-[var(--panel-bg)] px-3 py-2.5"
                    >
                      <div class="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {{ getTeacherName(teacher) }}
                      </div>
                      <span class="shrink-0 rounded-full px-2 py-1 text-[11px] font-bold" :class="getRoleTone(teacher.role)">
                        {{ getRoleName(teacher.role) }}
                      </span>
                    </div>
                  </div>

                  <div v-else class="text-sm italic text-slate-400">
                    Преподаватели не назначены
                  </div>
                </div>
              </div>
            </div>
          </article>
        </section>
      </div>

      <aside class="xl:sticky xl:top-24 xl:self-start">
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

          <div class="mt-4 rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] p-3">
            <div v-if="!selectedGroupUuid" class="text-sm text-slate-500 dark:text-slate-400">
            </div>

            <div v-else class="space-y-2 text-sm text-slate-500 dark:text-slate-400">
              <button
                  v-if="selectedDateFilter"
                  @click="clearDateFilter"
                  class="font-semibold text-[var(--accent-strong)] hover:underline"
              >
                Сбросить выбранную дату
              </button>
            </div>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>
