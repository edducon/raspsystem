<script setup lang="ts">
import { ref, computed } from 'vue';
import { Search, Clock, MapPin, Globe, CalendarDays, X, ChevronLeft, ChevronRight } from 'lucide-vue-next';
import { getDateLabel, daysUntil } from '../lib/dateUtils';
import { useRecentGroups } from '../composables/useRecentGroups';

const props = defineProps<{
  groups: { uuid: string; number: string }[];
  retakes: any[];
  today?: string;
}>();

const groupSearchQuery = ref('');
const selectedGroupUuid = ref('');
const showGroupDropdown = ref(false);
const selectedSubjectFilter = ref('');
const showDatePicker = ref(false);
const selectedDateFilter = ref('');
const { recentGroups, addRecentGroup, clearRecentGroups } = useRecentGroups();
const openMonth = ref(() => {
  const base = props.today ? new Date(props.today) : new Date();
  return new Date(base.getFullYear(), base.getMonth(), 1);
}) as any;
if (typeof openMonth.value === 'function') {
  const base = props.today ? new Date(props.today) : new Date();
  openMonth.value = new Date(base.getFullYear(), base.getMonth(), 1);
}

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 20);
  const q = groupSearchQuery.value.toLowerCase().trim();
  return props.groups.filter((g) => g.number.toLowerCase().includes(q)).slice(0, 20);
});

function selectGroup(group: { uuid: string; number: string }) {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
  selectedSubjectFilter.value = '';
  selectedDateFilter.value = '';
  showDatePicker.value = false;
  addRecentGroup(group);
  const firstDate = studentRetakes.value[0]?.date;
  if (firstDate) {
    const d = new Date(firstDate);
    openMonth.value = new Date(d.getFullYear(), d.getMonth(), 1);
  }
}

function clearSelectedGroup() {
  selectedGroupUuid.value = '';
  groupSearchQuery.value = '';
  selectedSubjectFilter.value = '';
  selectedDateFilter.value = '';
  showGroupDropdown.value = false;
  showDatePicker.value = false;
}

function clearDateFilter() {
  selectedDateFilter.value = '';
  showDatePicker.value = false;
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

function getTeacherName(t: any) {
  return t?.name || t?.fullName || t?.fio || t?.teacherName || t?.displayName || 'Преподаватель';
}

const studentRetakes = computed(() => {
  if (!selectedGroupUuid.value) return [];
  return props.retakes
      .filter((r) => r.groupUuid === selectedGroupUuid.value)
      .map((r) => ({
        ...r,
        teachers: sortTeachers(r.teachers || []),
        dateLabel: getDateLabel(r.date),
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
  studentRetakes.value.forEach((r) => subjects.add(r.subjectName));
  return Array.from(subjects).sort();
});
const availableDateSet = computed(() => {
  return new Set(studentRetakes.value.map((r) => r.date));
});
const availableDates = computed(() => {
  return Array.from(availableDateSet.value).sort();
});
const filteredRetakes = computed(() => {
  return studentRetakes.value.filter((r) => {
    const subjectOk =
        !selectedSubjectFilter.value || r.subjectName === selectedSubjectFilter.value;
    const dateOk =
        !selectedDateFilter.value || r.date === selectedDateFilter.value;

    return subjectOk && dateOk;
  });
});

const TIME_MAPPING: Record<number, string> = {
  1: '09:00–10:30',
  2: '10:40–12:10',
  3: '12:20–13:50',
  4: '14:30–16:00',
  5: '16:10–17:40',
  6: '17:50–19:20',
  7: '19:30–21:00',
};

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

function getRoleColor(role: string) {
  if (role === 'MAIN') return 'text-blue-600 dark:text-blue-400';
  if (role === 'CHAIRMAN') return 'text-amber-600 dark:text-amber-400';
  return 'text-slate-500 dark:text-slate-400';
}

function pad(n: number) {
  return String(n).padStart(2, '0');
}

function toIsoDate(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const monthLabel = computed(() => {
  return new Intl.DateTimeFormat('ru-RU', {
    month: 'long',
    year: 'numeric',
  }).format(openMonth.value);
});

const calendarDays = computed(() => {
  const year = openMonth.value.getFullYear();
  const month = openMonth.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const firstWeekday = (firstDay.getDay() + 6) % 7; // пн = 0
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const days: Array<{
    key: string;
    label: number | '';
    iso: string | '';
    inMonth: boolean;
    isAvailable: boolean;
    isSelected: boolean;
  }> = [];

  for (let i = 0; i < firstWeekday; i++) {
    days.push({
      key: `empty-start-${i}`,
      label: '',
      iso: '',
      inMonth: false,
      isAvailable: false,
      isSelected: false,
    });
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const iso = toIsoDate(date);
    const isAvailable = availableDateSet.value.has(iso);

    days.push({
      key: iso,
      label: day,
      iso,
      inMonth: true,
      isAvailable,
      isSelected: selectedDateFilter.value === iso,
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
    });
  }

  return days;
});

function prevMonth() {
  const y = openMonth.value.getFullYear();
  const m = openMonth.value.getMonth();
  openMonth.value = new Date(y, m - 1, 1);
}

function nextMonth() {
  const y = openMonth.value.getFullYear();
  const m = openMonth.value.getMonth();
  openMonth.value = new Date(y, m + 1, 1);
}

function pickDate(iso: string, isAvailable: boolean) {
  if (!iso || !isAvailable) return;
  selectedDateFilter.value = iso;
  showDatePicker.value = false;
}

function jumpToMonthOfSelected() {
  if (!selectedDateFilter.value) return;
  const d = new Date(selectedDateFilter.value);
  openMonth.value = new Date(d.getFullYear(), d.getMonth(), 1);
}
</script>

<template>
  <div class="w-full">
    <div class="rounded-[28px] border border-slate-200 bg-[#f8f8fb] p-5 sm:p-6 lg:p-8 dark:border-white/15 dark:bg-[#1a1d24]">
      <div class="mb-6">
        <h2 class="text-2xl sm:text-4xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">
          Актуальное расписание
        </h2>
      </div>

      <div class="relative">
        <div class="flex flex-col xl:flex-row gap-3">
          <div class="relative flex-[1.5]">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
            <input
                v-model="groupSearchQuery"
                @focus="showGroupDropdown = true"
                @input="showGroupDropdown = true; selectedGroupUuid = ''"
                type="text"
                placeholder="Введите номер группы..."
                class="w-full h-14 pl-12 pr-4 rounded-2xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:border-red-400 focus:ring-4 focus:ring-red-500/10 outline-none transition dark:border-white/15 dark:bg-white/[0.04] dark:text-white"
            />
          </div>

          <div class="relative w-full xl:w-[260px]">
            <button
                type="button"
                @click="selectedGroupUuid && (showDatePicker = !showDatePicker, jumpToMonthOfSelected())"
                class="w-full h-14 px-4 rounded-2xl border border-slate-200 bg-white text-slate-700 outline-none text-left flex items-center justify-between focus:border-red-400 dark:bg-white/[0.04] dark:border-white/15 dark:text-slate-300"
                :class="{ 'opacity-60 cursor-not-allowed': !selectedGroupUuid }"
            >
              <span>
                {{ selectedDateFilter ? formatShortDate(selectedDateFilter) : 'Все даты' }}
              </span>
              <span class="text-slate-400 mr-1">▼</span>
            </button>

            <div
                v-if="showDatePicker && selectedGroupUuid"
                class="absolute right-0 mt-3 z-40 w-[320px] rounded-[24px] border border-slate-200 bg-white p-4 shadow-[0_24px_60px_rgba(15,23,42,0.12)] dark:border-white/15 dark:bg-[#14171d]"
            >
              <div class="flex items-center justify-between mb-4">
                <button
                    type="button"
                    @click="prevMonth"
                    class="w-9 h-9 rounded-xl border border-slate-200 bg-white flex items-center justify-center hover:bg-slate-50 dark:border-white/15 dark:bg-white/[0.04] dark:hover:bg-white/[0.08]"
                >
                  <ChevronLeft class="w-4 h-4 text-slate-500" />
                </button>

                <div class="text-sm font-bold text-slate-900 dark:text-white capitalize">
                  {{ monthLabel }}
                </div>

                <button
                    type="button"
                    @click="nextMonth"
                    class="w-9 h-9 rounded-xl border border-slate-200 bg-white flex items-center justify-center hover:bg-slate-50 dark:border-white/15 dark:bg-white/[0.04] dark:hover:bg-white/[0.08]"
                >
                  <ChevronRight class="w-4 h-4 text-slate-500" />
                </button>
              </div>

              <div class="grid grid-cols-7 gap-2 mb-2 text-center text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">
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
                      ? 'opacity-0 pointer-events-none'
                      : day.isSelected
                        ? 'bg-red-500 text-white shadow-[0_8px_18px_rgba(239,68,68,0.22)]'
                        : day.isAvailable
                          ? 'bg-white border border-slate-200 text-slate-900 hover:bg-red-50 hover:border-red-200 dark:bg-white/[0.04] dark:border-white/15 dark:text-white dark:hover:bg-white/[0.08]'
                          : 'bg-slate-50 text-slate-300 cursor-not-allowed dark:bg-[#1a1d24] dark:text-slate-600'
                  ]"
                >
                  {{ day.label }}
                </button>
              </div>

              <div class="mt-4 flex items-center justify-between gap-3">
                <button
                    type="button"
                    @click="clearDateFilter"
                    class="text-sm font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
                >
                  Сбросить дату
                </button>
              </div>
            </div>
          </div>

          <button
              data-arc-trigger
              @click="clearSelectedGroup"
              class="h-14 px-6 rounded-2xl bg-red-500 text-white font-bold hover:bg-red-600 transition"
          >
            Сбросить
          </button>
        </div>

        <div
            v-if="showGroupDropdown && (filteredGroups.length > 0 || (recentGroups.length > 0 && !groupSearchQuery))"
            class="absolute z-30 w-full mt-3 rounded-[24px] border border-slate-200 bg-white shadow-[0_24px_60px_rgba(15,23,42,0.12)] overflow-hidden max-h-80 overflow-y-auto dark:border-white/15 dark:bg-[#14171d]"
        >
          <div
              v-if="recentGroups.length > 0 && !groupSearchQuery"
              class="border-b border-slate-100 dark:border-white/15"
          >
            <div class="px-4 py-3 flex items-center justify-between">
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-[0.22em]">
                Недавние
              </span>
              <button
                  @click.stop="clearRecentGroups"
                  class="text-[10px] font-semibold text-slate-400 hover:text-red-500 transition-colors uppercase tracking-[0.16em]"
              >
                Очистить
              </button>
            </div>

            <div
                v-for="g in recentGroups"
                :key="'r-' + g.uuid"
                @click="selectGroup(g)"
                class="px-4 py-3 text-sm cursor-pointer text-slate-700 dark:text-slate-200 flex items-center gap-3 hover:bg-slate-50 dark:hover:bg-white/[0.04] transition-colors"
            >
              <Clock class="w-4 h-4 text-slate-400 shrink-0" />
              <span class="font-semibold">{{ g.number }}</span>
            </div>
          </div>

          <div
              v-for="g in filteredGroups"
              :key="g.uuid"
              @click="selectGroup(g)"
              class="px-4 py-3 text-sm cursor-pointer text-slate-700 dark:text-slate-200 font-semibold hover:bg-slate-50 dark:hover:bg-white/[0.04] transition-colors"
          >
            {{ g.number }}
          </div>
        </div>

        <div
            v-if="showGroupDropdown"
            @click="showGroupDropdown = false"
            class="fixed inset-0 z-20"
        ></div>

        <div
            v-if="showDatePicker"
            @click="showDatePicker = false"
            class="fixed inset-0 z-30"
        ></div>
      </div>
    </div>

    <div v-if="selectedGroupUuid" class="mt-7 flex items-center justify-between gap-3 flex-wrap">
      <div class="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 dark:border-white/15 dark:bg-white/[0.04] dark:text-slate-200">
        <span>{{ groupSearchQuery }}</span>
      </div>

      <button
          @click="clearSelectedGroup"
          class="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white transition"
      >
        <X class="w-4 h-4" />
        Сбросить выбор
      </button>
    </div>

    <div
        v-if="selectedGroupUuid && availableSubjects.length > 1"
        class="mt-5 flex flex-wrap gap-2"
    >
      <button
          @click="selectedSubjectFilter = ''"
          :class="selectedSubjectFilter === ''
          ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white'
          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-white/[0.04] dark:text-slate-300 dark:border-white/15 dark:hover:bg-white/[0.08]'"
          class="px-4 py-2.5 rounded-2xl text-sm font-semibold border transition"
      >
        Все
      </button>

      <button
          v-for="sub in availableSubjects"
          :key="sub"
          @click="selectedSubjectFilter = sub"
          :class="selectedSubjectFilter === sub
          ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white'
          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-white/[0.04] dark:text-slate-300 dark:border-white/15 dark:hover:bg-white/[0.08]'"
          class="px-4 py-2.5 rounded-2xl text-sm font-semibold border transition"
      >
        {{ sub }}
      </button>
    </div>

    <div v-if="!selectedGroupUuid" class="py-14 sm:py-16 text-center">
      <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/15">
        <Search class="w-6 h-6 text-slate-400 dark:text-slate-500" />
      </div>

      <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">
        Сначала выберите группу
      </h3>

      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-7">
        После выбора группы здесь сразу появится список пересдач.
      </p>
    </div>

    <div v-else-if="studentRetakes.length === 0" class="py-14 sm:py-16 text-center">
      <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/15">
        <CalendarDays class="w-6 h-6 text-slate-400 dark:text-slate-500" />
      </div>

      <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">
        Пересдачи не назначены
      </h3>

      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-7">
        Для группы
        <span class="font-semibold text-slate-700 dark:text-slate-300">{{ groupSearchQuery }}</span>
        сейчас нет записей.
      </p>
    </div>

    <div v-else class="mt-7">
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div
            v-for="retake in filteredRetakes"
            :key="retake.id"
            class="rounded-[28px] border border-slate-200 bg-white p-5 sm:p-6 shadow-sm dark:border-white/15 dark:bg-white/[0.03]"
            :class="{ 'opacity-60': daysUntil(retake.date) < 0 }"
        >
          <div class="flex flex-wrap items-center gap-2 mb-5">
            <span
                class="px-3 py-1.5 text-[10px] font-extrabold rounded-xl uppercase tracking-[0.16em] text-white"
                :class="retake.attemptNumber === 1 ? 'bg-blue-600' : retake.attemptNumber === 2 ? 'bg-amber-500' : 'bg-red-500'"
            >
              Попытка {{ retake.attemptNumber || 1 }}
            </span>

            <span
                class="px-3 py-1.5 text-[10px] font-bold rounded-xl border border-slate-200 dark:border-white/15 bg-slate-50 dark:bg-white/[0.04]"
                :class="retake.dateLabel.colorClass"
            >
              {{ retake.dateLabel.text }}
            </span>
          </div>

          <div class="space-y-5">
            <div>
              <div class="text-2xl font-black tracking-tight text-slate-950 dark:text-white">
                {{ formatDate(retake.date) }}
              </div>
              <div class="mt-2 text-2xl sm:text-[32px] leading-tight font-black tracking-[-0.04em] text-slate-950 dark:text-white">
                {{ retake.subjectName }}
              </div>
            </div>

            <div class="flex flex-wrap gap-3 text-sm">
              <div class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-slate-500 dark:bg-white/[0.05] dark:text-slate-400">
                <Clock class="w-4 h-4" />
                {{ retake.timeSlots.map((s: number) => TIME_MAPPING[s]).join(', ') }}
              </div>

              <div
                  v-if="retake.link"
                  class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-blue-600 dark:bg-white/[0.05] dark:text-blue-400"
              >
                <Globe class="w-4 h-4" />
                <a :href="retake.link" target="_blank" class="hover:underline font-semibold">
                  Онлайн
                </a>
              </div>

              <div
                  v-else
                  class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-slate-500 dark:bg-white/[0.05] dark:text-slate-400"
              >
                <MapPin class="w-4 h-4" />
                {{ retake.room || 'Аудитория уточняется' }}
              </div>
            </div>

            <div class="rounded-2xl bg-[#f8f8fb] border border-slate-200 p-4 dark:bg-white/[0.04] dark:border-white/15">
              <div class="text-xs font-bold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
                Комиссия
              </div>

              <div
                  v-if="retake.teachers && retake.teachers.length > 0"
                  class="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3"
              >
                <div
                    v-for="t in retake.teachers"
                    :key="`${retake.id}-${getTeacherName(t)}-${t.role}`"
                    class="flex items-center gap-3 p-3 rounded-2xl bg-white border border-slate-200 dark:bg-white/[0.03] dark:border-white/15"
                >
                  <div
                      class="w-2 h-2 rounded-full shrink-0"
                      :class="t.role === 'MAIN' ? 'bg-blue-500' : t.role === 'CHAIRMAN' ? 'bg-amber-500' : 'bg-slate-400'"
                  ></div>

                  <div class="min-w-0">
                    <div class="text-[10px] font-bold uppercase tracking-[0.18em]" :class="getRoleColor(t.role)">
                      {{ getRoleName(t.role) }}
                    </div>
                    <div class="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
                      {{ getTeacherName(t) }}
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="mt-3 text-sm text-slate-400 italic">
                Преподаватели не назначены
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredRetakes.length === 0" class="py-14 text-center">
        <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/15">
          <Search class="w-6 h-6 text-slate-400 dark:text-slate-500" />
        </div>

        <h3 class="text-xl font-black tracking-tight text-slate-900 dark:text-white">
          Ничего не найдено
        </h3>

        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-7">
          Попробуйте сбросить фильтр по дате или предмету.
        </p>
      </div>
    </div>
  </div>
</template>