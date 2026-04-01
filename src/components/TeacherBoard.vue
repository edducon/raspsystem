<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { CalendarDays, ChevronLeft, ChevronRight, Clock, MapPin, Globe, AlertTriangle, Users } from 'lucide-vue-next';

const props = defineProps<{
  teacherFullName: string;
  retakes: any[];
  baseSchedule: Record<string, any> | null;
}>();

const currentDate = ref(new Date());

const setToday = () => { currentDate.value = new Date(); };
const nextWeek = () => { const d = new Date(currentDate.value); d.setDate(d.getDate() + 7); currentDate.value = d; };
const prevWeek = () => { const d = new Date(currentDate.value); d.setDate(d.getDate() - 7); currentDate.value = d; };

const currentWeekStart = computed(() => {
  const d = new Date(currentDate.value);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const start = new Date(d.setDate(diff));
  start.setHours(0, 0, 0, 0);
  return start;
});

const daysOfWeekNames = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
const shortDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

const weekDays = computed(() => {
  return daysOfWeekNames.map((dayName, idx) => {
    const date = new Date(currentWeekStart.value);
    date.setDate(date.getDate() + idx);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return { id: dayName, date, dateStr: `${year}-${month}-${day}`, label: `${shortDays[idx]}, ${day}.${month}` };
  });
});

const weekDateRange = computed(() => {
  const start = weekDays.value[0].date;
  const end = weekDays.value[5].date;
  const format = (d: Date) => d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
  if (start.getMonth() !== end.getMonth()) {
    return `${format(start).split(' ')[0]} ${format(start).split(' ')[1].slice(0, 3)} — ${format(end)}`;
  }
  return `${start.getDate()} — ${format(end)}`;
});

const activeTab = ref('monday');

watch(currentDate, (val) => {
  const d = val.getDay();
  if (d >= 1 && d <= 6) activeTab.value = daysOfWeekNames[d - 1];
  else activeTab.value = 'monday';
}, { immediate: true });

const TIME_MAPPING: Record<number, string> = {
  1: '09:00-10:30',
  2: '10:40-12:10',
  3: '12:20-13:50',
  4: '14:30-16:00',
  5: '16:10-17:40',
  6: '17:50-19:20',
  7: '19:30-21:00',
};

const parseDateString = (ds: string) => {
  if (!ds) return 0;
  const [y, m, d] = ds.split('-');
  return new Date(Number(y), Number(m) - 1, Number(d)).getTime();
};

const mergedDaySchedule = computed(() => {
  const activeDay = weekDays.value.find(d => d.id === activeTab.value);
  if (!activeDay) return [];

  const targetTime = parseDateString(activeDay.dateStr);
  const items: any[] = [];
  const processedRetakeIds = new Set<number>();

  const todaysRetakes = props.retakes.filter(r => r.date === activeDay.dateStr);

  todaysRetakes.forEach(retake => {
    if (!processedRetakeIds.has(retake.id)) {
      processedRetakeIds.add(retake.id);
      let hasConflict = false;

      retake.timeSlots.forEach((slot: number) => {
        if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
          const conflictingPair = props.baseSchedule[activeDay.id][slot].find((p: any) => {
            if (!p.start_date || !p.end_date) return true;
            return targetTime >= parseDateString(p.start_date) && targetTime <= parseDateString(p.end_date);
          });
          if (conflictingPair) hasConflict = true;
        }
      });

      items.push({ type: 'retake', startSlot: Math.min(...retake.timeSlots), data: retake, hasConflict });
    }
  });

  for (let slot = 1; slot <= 7; slot++) {
    if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
      const pairsInSlot = props.baseSchedule[activeDay.id][slot];
      const regularPair = pairsInSlot.find((p: any) => {
        if (!p.start_date || !p.end_date) return true;
        const start = parseDateString(p.start_date);
        const end = parseDateString(p.end_date);
        return targetTime >= start && targetTime <= end;
      });

      if (regularPair) {
        const isRetakeInThisSlot = todaysRetakes.some(r => r.timeSlots.includes(slot));
        if (!isRetakeInThisSlot) {
          items.push({ type: 'regular', startSlot: slot, data: regularPair });
        }
      }
    }
  }

  return items.sort((a, b) => a.startSlot - b.startSlot);
});

const getRoleBadge = (role: string) => {
  if (role === 'CHAIRMAN') {
    return {
      text: 'Председатель',
      class: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20'
    };
  }
  if (role === 'MAIN') {
    return {
      text: 'Ведущий',
      class: 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
    };
  }
  return {
    text: 'Комиссия',
    class: 'bg-slate-50 text-slate-600 border border-slate-200 dark:bg-white/[0.04] dark:text-slate-400 dark:border-white/10'
  };
};
</script>

<template>
  <div class="relative z-10 rounded-[30px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_20px_70px_rgba(15,23,42,0.10)] overflow-hidden transition-colors">
    <!-- Header -->
    <div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-slate-100 dark:border-white/10 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 via-red-600 to-blue-600 flex items-center justify-center shadow-[0_16px_40px_rgba(239,68,68,0.24)] shrink-0">
          <CalendarDays class="w-5 h-5 text-white" />
        </div>

        <div>
          <p class="text-[11px] uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold">
            Кабинет преподавателя
          </p>
          <h2 class="mt-1 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white">
            Моё расписание
          </h2>
          <p class="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            {{ teacherFullName }}
          </p>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 w-full lg:w-auto">
        <button
            @click="setToday"
            class="h-11 px-4 rounded-2xl text-sm font-semibold text-slate-700 dark:text-slate-200 bg-white/90 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/[0.07] hover:-translate-y-0.5 transition-all"
        >
          Сегодня
        </button>

        <div class="flex items-center justify-between sm:justify-start bg-white/90 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 p-1 rounded-2xl">
          <button
              @click="prevWeek"
              class="w-10 h-10 flex items-center justify-center rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.07] transition-colors"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>

          <div class="px-3 text-center text-sm font-black tracking-tight text-slate-900 dark:text-white min-w-[150px]">
            {{ weekDateRange }}
          </div>

          <button
              @click="nextWeek"
              class="w-10 h-10 flex items-center justify-center rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.07] transition-colors"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Day tabs -->
    <div class="flex overflow-x-auto border-b border-slate-100 dark:border-white/10 hide-scrollbar bg-slate-50/70 dark:bg-black/10 px-2 sm:px-3 py-2">
      <button
          v-for="day in weekDays"
          :key="day.id"
          @click="activeTab = day.id"
          :class="[
          'flex-1 min-w-[92px] rounded-2xl py-3 text-center text-sm transition-all outline-none border',
          activeTab === day.id
            ? 'text-white bg-red-500 border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]'
            : 'text-slate-500 dark:text-slate-400 border-transparent hover:border-slate-200 dark:hover:border-white/10 hover:bg-white dark:hover:bg-white/[0.04]'
        ]"
      >
        <div class="text-xs font-black tracking-tight">
          {{ day.label.split(',')[0] }}
        </div>
        <div
            class="text-[10px] mt-0.5"
            :class="activeTab === day.id ? 'text-white/70' : 'opacity-70'"
        >
          {{ day.label.split(',')[1] }}
        </div>
      </button>
    </div>

    <!-- Content -->
    <div class="p-5 sm:p-6 min-h-[380px]">
      <!-- Empty -->
      <div v-if="mergedDaySchedule.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
        <div class="w-16 h-16 rounded-full flex items-center justify-center mb-5 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10">
          <CalendarDays class="w-7 h-7 text-slate-300 dark:text-slate-600" />
        </div>

        <h3 class="text-lg font-black tracking-tight text-slate-700 dark:text-slate-200">
          Пар нет
        </h3>

        <p class="text-sm text-slate-400 dark:text-slate-500 mt-2 max-w-xs leading-6">
          На этот день занятия не запланированы
        </p>
      </div>

      <!-- Schedule items -->
      <div v-else class="space-y-4">
        <div
            v-for="(item, idx) in mergedDaySchedule"
            :key="idx"
            class="flex flex-col lg:flex-row gap-3 lg:gap-4"
        >
          <!-- Time badge -->
          <div class="lg:w-28 shrink-0 flex lg:flex-col items-center lg:items-start gap-2 lg:gap-1 lg:pt-3">
            <div class="px-3.5 py-2 rounded-2xl font-bold text-slate-600 dark:text-slate-300 text-xs whitespace-nowrap bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10">
              {{ item.type === 'retake' ? item.data.timeSlots.join(', ') : item.startSlot }} пара
            </div>

            <div class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 font-mono lg:mt-1">
              <template v-if="item.type === 'retake'">
                {{ TIME_MAPPING[item.data.timeSlots[0]].split('-')[0] }} - {{ TIME_MAPPING[item.data.timeSlots[item.data.timeSlots.length - 1]].split('-')[1] }}
              </template>
              <template v-else>
                {{ TIME_MAPPING[item.startSlot] }}
              </template>
            </div>
          </div>

          <!-- Regular class -->
          <div v-if="item.type === 'regular'" class="flex-1">
            <div class="rounded-[24px] border border-slate-200/80 dark:border-white/10 bg-white/90 dark:bg-white/[0.04] backdrop-blur-xl p-4 sm:p-5 hover:-translate-y-1 hover:shadow-[0_20px_60px_rgba(15,23,42,0.10)] transition-all duration-300">
              <div class="flex flex-wrap items-center gap-2 mb-3">
                <span class="px-2.5 py-1 text-[10px] font-black rounded-xl uppercase tracking-[0.16em] bg-slate-100 dark:bg-white/[0.05] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10">
                  Расписание
                </span>

                <span class="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                  <Users class="w-3.5 h-3.5 opacity-60" />
                  {{ item.data.group.number }}
                </span>

                <span class="text-[10px] text-slate-400 dark:text-slate-500 font-semibold bg-slate-50 dark:bg-white/[0.04] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-white/10">
                  {{ item.data.subject_type.type }}
                </span>
              </div>

              <h4 class="font-black tracking-tight text-slate-950 dark:text-white text-lg sm:text-xl mb-3">
                {{ item.data.subject.name }}
              </h4>

              <div
                  class="flex flex-wrap items-center gap-3 text-sm font-medium"
                  :class="item.data.link ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400'"
              >
                <template v-if="item.data.link">
                  <a :href="item.data.link" target="_blank" class="flex items-center gap-2 hover:underline">
                    <Globe class="w-4 h-4" />
                    Онлайн
                  </a>
                </template>

                <template v-else>
                  <span class="flex items-center gap-2">
                    <MapPin class="w-4 h-4" />
                    {{ item.data.location.name }}
                    <span
                        v-if="item.data.rooms && item.data.rooms[0]"
                        class="font-bold text-slate-700 dark:text-slate-200"
                    >
                      ({{ item.data.rooms[0].number }})
                    </span>
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- Retake -->
          <div v-if="item.type === 'retake'" class="flex-1">
            <div
                :class="[
                'rounded-[24px] border p-4 sm:p-5 relative overflow-hidden backdrop-blur-xl hover:-translate-y-1 transition-all duration-300',
                item.hasConflict
                  ? 'bg-red-50/90 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 hover:shadow-[0_20px_60px_rgba(239,68,68,0.14)]'
                  : 'bg-white/90 dark:bg-white/[0.04] border-slate-200/80 dark:border-white/10 hover:shadow-[0_20px_60px_rgba(15,23,42,0.10)]'
              ]"
            >
              <div
                  class="absolute left-0 top-0 bottom-0 w-1.5"
                  :class="item.hasConflict ? 'bg-red-500' : 'bg-gradient-to-b from-red-500 to-blue-600'"
              ></div>

              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 pl-3">
                <div class="flex flex-wrap items-center gap-2">
                  <span
                      class="px-3 py-1.5 text-white text-[10px] font-black rounded-xl uppercase tracking-[0.16em]"
                      :class="item.hasConflict ? 'bg-red-500' : 'bg-gradient-to-r from-red-500 to-blue-600'"
                  >
                    Пересдача
                  </span>

                  <span
                      class="px-3 py-1.5 text-[10px] font-bold rounded-xl border"
                      :class="item.hasConflict
                      ? 'bg-white/70 dark:bg-black/20 text-red-700 dark:text-red-300 border-red-200 dark:border-red-500/20'
                      : 'bg-slate-50 dark:bg-white/[0.04] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-white/10'"
                  >
                    Попытка {{ item.data.attemptNumber }}
                  </span>

                  <span
                      class="text-xs font-semibold flex items-center gap-1.5"
                      :class="item.hasConflict ? 'text-red-700 dark:text-red-300' : 'text-slate-600 dark:text-slate-300'"
                  >
                    <Users class="w-3.5 h-3.5" />
                    {{ item.data.groupName }}
                  </span>
                </div>

                <div
                    v-if="item.hasConflict"
                    class="flex items-center gap-1.5 text-red-600 dark:text-red-400 text-[10px] font-black bg-white dark:bg-red-950/40 px-2.5 py-1.5 rounded-xl border border-red-200 dark:border-red-500/20 self-start"
                >
                  <AlertTriangle class="w-3 h-3" />
                  Накладка
                </div>
              </div>

              <h4
                  class="font-black tracking-tight text-lg sm:text-xl mb-3 pl-3"
                  :class="item.hasConflict ? 'text-red-950 dark:text-red-50' : 'text-slate-950 dark:text-white'"
              >
                {{ item.data.subjectName }}
              </h4>

              <div
                  class="flex flex-wrap items-center gap-3 text-sm pl-3 font-medium"
                  :class="item.hasConflict ? 'text-red-700 dark:text-red-300' : 'text-slate-500 dark:text-slate-400'"
              >
                <template v-if="item.data.link">
                  <a :href="item.data.link" target="_blank" class="flex items-center gap-2 hover:underline">
                    <Globe class="w-4 h-4" />
                    Онлайн
                  </a>
                </template>

                <template v-else>
                  <span class="flex items-center gap-2">
                    <MapPin class="w-4 h-4" />
                    {{ item.data.room || 'Аудитория уточняется' }}
                  </span>
                </template>

                <span
                    class="px-2.5 py-1 rounded-xl text-[10px] font-black uppercase tracking-[0.14em]"
                    :class="getRoleBadge(item.data.myRole).class"
                >
                  {{ getRoleBadge(item.data.myRole).text }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
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