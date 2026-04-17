<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { CalendarDays, ChevronLeft, ChevronRight, MapPin, Globe, AlertTriangle, Users } from 'lucide-vue-next';

const props = defineProps<{
  teacherFullName: string;
  retakes: any[];
  baseSchedule: Record<string, any> | null;
}>();

const currentDate = ref(new Date());
const activeTab = ref('monday');

const daysOfWeekNames = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
const shortDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

const TIME_MAPPING: Record<number, string> = {
  1: '09:00-10:30',
  2: '10:40-12:10',
  3: '12:20-13:50',
  4: '14:30-16:00',
  5: '16:10-17:40',
  6: '17:50-19:20',
  7: '19:30-21:00',
};

const currentWeekStart = computed(() => {
  const date = new Date(currentDate.value);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  const start = new Date(date.setDate(diff));
  start.setHours(0, 0, 0, 0);
  return start;
});

const weekDays = computed(() => daysOfWeekNames.map((dayName, idx) => {
  const date = new Date(currentWeekStart.value);
  date.setDate(date.getDate() + idx);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return {
    id: dayName,
    date,
    dateStr: `${year}-${month}-${day}`,
    label: `${shortDays[idx]}, ${day}.${month}`,
  };
}));

const weekDateRange = computed(() => {
  const start = weekDays.value[0].date;
  const end = weekDays.value[5].date;
  const format = (date: Date) => date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });

  if (start.getMonth() !== end.getMonth()) {
    return `${format(start).split(' ')[0]} ${format(start).split(' ')[1].slice(0, 3)} — ${format(end)}`;
  }

  return `${start.getDate()} — ${format(end)}`;
});

const parseDateString = (value: string) => {
  if (!value) return 0;
  const [year, month, day] = value.split('-');
  return new Date(Number(year), Number(month) - 1, Number(day)).getTime();
};

const mergedDaySchedule = computed(() => {
  const activeDay = weekDays.value.find((day) => day.id === activeTab.value);
  if (!activeDay) return [];

  const targetTime = parseDateString(activeDay.dateStr);
  const items: any[] = [];
  const processedRetakeIds = new Set<string>();
  const todaysRetakes = props.retakes.filter((retake) => retake.date === activeDay.dateStr);

  todaysRetakes.forEach((retake) => {
    if (processedRetakeIds.has(retake.id)) return;

    processedRetakeIds.add(retake.id);
    let hasConflict = false;

    retake.timeSlots.forEach((slot: number) => {
      if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
        const conflictingPair = props.baseSchedule[activeDay.id][slot].find((pair: any) => {
          if (!pair.start_date || !pair.end_date) return true;
          return targetTime >= parseDateString(pair.start_date) && targetTime <= parseDateString(pair.end_date);
        });

        if (conflictingPair) hasConflict = true;
      }
    });

    items.push({ type: 'retake', startSlot: Math.min(...retake.timeSlots), data: retake, hasConflict });
  });

  for (let slot = 1; slot <= 7; slot += 1) {
    if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
      const pairsInSlot = props.baseSchedule[activeDay.id][slot];
      const regularPair = pairsInSlot.find((pair: any) => {
        if (!pair.start_date || !pair.end_date) return true;
        const start = parseDateString(pair.start_date);
        const end = parseDateString(pair.end_date);
        return targetTime >= start && targetTime <= end;
      });

      if (regularPair) {
        const isRetakeInThisSlot = todaysRetakes.some((retake) => retake.timeSlots.includes(slot));
        if (!isRetakeInThisSlot) {
          items.push({ type: 'regular', startSlot: slot, data: regularPair });
        }
      }
    }
  }

  return items.sort((a, b) => a.startSlot - b.startSlot);
});

watch(currentDate, (value) => {
  const day = value.getDay();
  if (day >= 1 && day <= 6) {
    activeTab.value = daysOfWeekNames[day - 1];
    return;
  }

  activeTab.value = 'monday';
}, { immediate: true });

const setToday = () => { currentDate.value = new Date(); };
const nextWeek = () => {
  const date = new Date(currentDate.value);
  date.setDate(date.getDate() + 7);
  currentDate.value = date;
};
const prevWeek = () => {
  const date = new Date(currentDate.value);
  date.setDate(date.getDate() - 7);
  currentDate.value = date;
};

const getRoleBadge = (role: string) => {
  if (role === 'CHAIRMAN') {
    return {
      text: 'Председатель',
      class: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/20',
    };
  }

  if (role === 'MAIN') {
    return {
      text: 'Ведущий',
      class: 'bg-[var(--accent-soft)] text-[var(--accent-strong)] border border-[var(--panel-border)]',
    };
  }

  return {
    text: 'Комиссия',
    class: 'bg-[var(--panel-muted)] text-slate-600 border border-[var(--panel-border)] dark:text-slate-300',
  };
};
</script>

<template>
  <div class="overflow-hidden rounded-[24px] border border-[var(--panel-border)] bg-[var(--panel-bg)] shadow-[var(--panel-shadow)]">
    <div class="flex flex-col gap-4 border-b border-[var(--panel-border)] px-4 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-5">
      <div>
        <div class="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Преподаватель</div>
        <h2 class="mt-1 text-2xl font-black tracking-tight text-slate-950 dark:text-white">Моё расписание</h2>
        <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ teacherFullName }}</div>
      </div>

      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <button
          @click="setToday"
          class="h-11 rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 text-sm font-semibold text-slate-700 dark:text-slate-200"
        >
          Сегодня
        </button>

        <div class="flex items-center rounded-[18px] border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] p-1">
          <button
            @click="prevWeek"
            class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 dark:text-slate-400"
          >
            <ChevronLeft class="h-4 w-4" />
          </button>

          <div class="min-w-[170px] px-3 text-center text-sm font-black tracking-tight text-slate-900 dark:text-white">
            {{ weekDateRange }}
          </div>

          <button
            @click="nextWeek"
            class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 dark:text-slate-400"
          >
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <div class="hide-scrollbar flex overflow-x-auto border-b border-[var(--panel-border)] bg-[var(--panel-muted)] px-2 py-2 sm:px-3">
      <button
        v-for="day in weekDays"
        :key="day.id"
        @click="activeTab = day.id"
        :class="[
          'min-w-[98px] flex-1 rounded-[16px] border py-3 text-center text-sm',
          activeTab === day.id
            ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
            : 'border-transparent text-slate-500 dark:text-slate-400',
        ]"
      >
        <div class="text-xs font-black tracking-tight">{{ day.label.split(',')[0] }}</div>
        <div class="mt-0.5 text-[10px]" :class="activeTab === day.id ? 'text-white/70 dark:text-slate-500' : 'opacity-70'">
          {{ day.label.split(',')[1] }}
        </div>
      </button>
    </div>

    <div v-if="mergedDaySchedule.length === 0" class="px-5 py-20 text-center">
      <div class="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)]">
        <CalendarDays class="h-7 w-7 text-slate-300 dark:text-slate-600" />
      </div>
      <h3 class="text-lg font-black tracking-tight text-slate-700 dark:text-slate-200">Пар нет</h3>
    </div>

    <div v-else class="divide-y divide-[var(--panel-border)]">
      <article
        v-for="(item, idx) in mergedDaySchedule"
        :key="idx"
        class="grid gap-4 px-5 py-5 lg:grid-cols-[8rem_minmax(0,1fr)]"
        :class="item.type === 'retake' && item.hasConflict ? 'bg-red-50/70 dark:bg-red-500/10' : ''"
      >
        <div class="space-y-1 lg:border-r lg:border-[var(--panel-border)] lg:pr-4">
          <div class="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            {{ item.type === 'retake' ? 'Пересдача' : 'Пара' }}
          </div>
          <div class="text-2xl font-black text-slate-950 dark:text-white tnum">
            {{ item.type === 'retake' ? item.data.timeSlots.join(', ') : item.startSlot }}
          </div>
          <div class="text-sm text-slate-500 dark:text-slate-400 tnum">
            <template v-if="item.type === 'retake'">
              {{ TIME_MAPPING[item.data.timeSlots[0]].split('-')[0] }} - {{ TIME_MAPPING[item.data.timeSlots[item.data.timeSlots.length - 1]].split('-')[1] }}
            </template>
            <template v-else>
              {{ TIME_MAPPING[item.startSlot] }}
            </template>
          </div>
        </div>

        <div v-if="item.type === 'regular'" class="space-y-3">
          <div class="flex flex-wrap items-center gap-2">
            <span class="rounded-full bg-[var(--panel-muted)] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600 dark:text-slate-300">
              Расписание
            </span>
            <span class="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 dark:text-slate-300">
              <Users class="h-3.5 w-3.5 opacity-60" />
              {{ item.data.group.number }}
            </span>
            <span class="rounded-full border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-2.5 py-1 text-[10px] font-semibold text-slate-500 dark:text-slate-400">
              {{ item.data.subject_type.type }}
            </span>
          </div>

          <h4 class="text-xl font-black tracking-tight text-slate-950 dark:text-white">
            {{ item.data.subject.name }}
          </h4>

          <div class="flex flex-wrap items-center gap-3 text-sm font-medium" :class="item.data.link ? 'text-[var(--accent-strong)]' : 'text-slate-500 dark:text-slate-400'">
            <template v-if="item.data.link">
              <a :href="item.data.link" target="_blank" class="flex items-center gap-2 hover:underline">
                <Globe class="h-4 w-4" />
                Онлайн
              </a>
            </template>

            <template v-else>
              <span class="flex items-center gap-2">
                <MapPin class="h-4 w-4" />
                {{ item.data.location.name }}
                <span v-if="item.data.rooms && item.data.rooms[0]" class="font-bold text-slate-700 dark:text-slate-200">
                  ({{ item.data.rooms[0].number }})
                </span>
              </span>
            </template>
          </div>
        </div>

        <div v-else class="space-y-3">
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]"
              :class="item.hasConflict ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300' : 'bg-[var(--accent-soft)] text-[var(--accent-strong)]'"
            >
              Пересдача
            </span>
            <span class="rounded-full border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-2.5 py-1 text-[10px] font-bold text-slate-700 dark:text-slate-300">
              Попытка {{ item.data.attemptNumber }}
            </span>
            <span class="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 dark:text-slate-300">
              <Users class="h-3.5 w-3.5" />
              {{ item.data.groupName }}
            </span>
            <span
              class="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]"
              :class="getRoleBadge(item.data.myRole).class"
            >
              {{ getRoleBadge(item.data.myRole).text }}
            </span>
          </div>

          <h4 class="text-xl font-black tracking-tight text-slate-950 dark:text-white">
            {{ item.data.subjectName }}
          </h4>

          <div class="flex flex-wrap items-center gap-3 text-sm font-medium" :class="item.hasConflict ? 'text-red-700 dark:text-red-300' : 'text-slate-500 dark:text-slate-400'">
            <template v-if="item.data.link">
              <a :href="item.data.link" target="_blank" class="flex items-center gap-2 hover:underline">
                <Globe class="h-4 w-4" />
                Онлайн
              </a>
            </template>

            <template v-else>
              <span class="flex items-center gap-2">
                <MapPin class="h-4 w-4" />
                {{ item.data.room || 'Аудитория уточняется' }}
              </span>
            </template>

            <span v-if="item.hasConflict" class="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-red-700 dark:bg-red-950/40 dark:text-red-300">
              <AlertTriangle class="h-3 w-3" />
              Накладка
            </span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
