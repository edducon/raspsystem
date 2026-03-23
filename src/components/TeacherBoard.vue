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
    return `${format(start).split(' ')[0]} ${format(start).split(' ')[1].slice(0,3)} — ${format(end)}`;
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
  1: '09:00-10:30', 2: '10:40-12:10', 3: '12:20-13:50', 4: '14:30-16:00', 5: '16:10-17:40', 6: '17:50-19:20', 7: '19:30-21:00',
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
  if (role === 'CHAIRMAN') return { text: 'Председатель', class: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' };
  if (role === 'MAIN') return { text: 'Ведущий', class: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' };
  return { text: 'Комиссия', class: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' };
};
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden relative z-10 transition-colors">

    <!-- Header -->
    <div class="p-5 md:p-6 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-600/20 shrink-0">
          <CalendarDays class="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Моё расписание</h2>
          <p class="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{{ teacherFullName }}</p>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row items-center gap-2.5 w-full sm:w-auto">
        <button @click="setToday" class="px-4 py-2 w-full sm:w-auto text-sm font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl transition-all">Сегодня</button>
        <div class="flex items-center w-full sm:w-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 rounded-xl">
          <button @click="prevWeek" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-500 dark:text-slate-400 transition-colors"><ChevronLeft class="w-4 h-4" /></button>
          <div class="px-3 text-center text-sm font-bold text-slate-800 dark:text-white min-w-[130px]">{{ weekDateRange }}</div>
          <button @click="nextWeek" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-500 dark:text-slate-400 transition-colors"><ChevronRight class="w-4 h-4" /></button>
        </div>
      </div>
    </div>

    <!-- Day tabs -->
    <div class="flex overflow-x-auto border-b border-slate-100 dark:border-slate-800 hide-scrollbar bg-slate-50/50 dark:bg-slate-950/50">
      <button
        v-for="day in weekDays" :key="day.id"
        @click="activeTab = day.id"
        :class="['flex-1 min-w-[90px] py-3.5 text-center text-sm font-semibold transition-all outline-none border-b-2',
          activeTab === day.id
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 bg-white dark:bg-slate-900'
            : 'text-slate-400 dark:text-slate-500 border-transparent hover:text-slate-700 dark:hover:text-slate-300 hover:bg-white dark:hover:bg-slate-900']"
      >
        <div class="text-xs font-bold">{{ day.label.split(',')[0] }}</div>
        <div class="text-[10px] font-normal opacity-60 mt-0.5">{{ day.label.split(',')[1] }}</div>
      </button>
    </div>

    <!-- Content -->
    <div class="p-5 md:p-6 min-h-[350px]">
      <!-- Empty -->
      <div v-if="mergedDaySchedule.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <CalendarDays class="w-7 h-7 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 class="text-base font-bold text-slate-600 dark:text-slate-300">Пар нет</h3>
        <p class="text-sm text-slate-400 dark:text-slate-500 mt-1">На этот день занятия не запланированы</p>
      </div>

      <!-- Schedule items -->
      <div v-else class="space-y-3">
        <div v-for="(item, idx) in mergedDaySchedule" :key="idx" class="flex flex-col md:flex-row gap-3">

          <!-- Time badge -->
          <div class="md:w-24 shrink-0 flex md:flex-col items-center md:items-start gap-2 md:gap-0.5 md:pt-3">
            <div class="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg font-bold text-slate-600 dark:text-slate-300 text-xs whitespace-nowrap">
              {{ item.type === 'retake' ? item.data.timeSlots.join(', ') : item.startSlot }} пара
            </div>
            <div class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 font-mono md:mt-1">
              <template v-if="item.type === 'retake'">{{ TIME_MAPPING[item.data.timeSlots[0]].split('-')[0] }} - {{ TIME_MAPPING[item.data.timeSlots[item.data.timeSlots.length - 1]].split('-')[1] }}</template>
              <template v-else>{{ TIME_MAPPING[item.startSlot] }}</template>
            </div>
          </div>

          <!-- Card -->
          <div class="flex-1">
            <!-- Regular class -->
            <div v-if="item.type === 'regular'" class="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl p-4 hover:shadow-sm transition-all">
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span class="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px] font-bold rounded-md uppercase tracking-wider">Расписание</span>
                <span class="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1"><Users class="w-3 h-3 opacity-60"/>{{ item.data.group.number }}</span>
                <span class="text-[10px] text-slate-400 dark:text-slate-500 font-medium bg-slate-50 dark:bg-slate-900 px-2 py-0.5 rounded">{{ item.data.subject_type.type }}</span>
              </div>
              <h4 class="font-bold text-slate-900 dark:text-white text-base mb-2">{{ item.data.subject.name }}</h4>
              <div class="flex flex-wrap items-center gap-3 text-sm font-medium" :class="item.data.link ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400'">
                <template v-if="item.data.link"><a :href="item.data.link" target="_blank" class="flex items-center gap-1.5 hover:underline"><Globe class="w-3.5 h-3.5" /> Онлайн</a></template>
                <template v-else><span class="flex items-center gap-1.5"><MapPin class="w-3.5 h-3.5" />{{ item.data.location.name }} <span v-if="item.data.rooms && item.data.rooms[0]" class="font-bold text-slate-700 dark:text-slate-200">({{ item.data.rooms[0].number }})</span></span></template>
              </div>
            </div>

            <!-- Retake -->
            <div v-if="item.type === 'retake'"
              :class="['border rounded-xl p-4 relative overflow-hidden transition-all',
                item.hasConflict
                  ? 'bg-rose-50 dark:bg-rose-950/10 border-rose-200 dark:border-rose-800'
                  : 'bg-blue-50 dark:bg-blue-950/10 border-blue-200 dark:border-blue-800']">
              <div class="absolute left-0 top-0 bottom-0 w-1" :class="item.hasConflict ? 'bg-rose-500' : 'bg-gradient-to-b from-blue-500 to-violet-500'"></div>

              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2 pl-3">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2 py-0.5 text-white text-[10px] font-bold rounded-md uppercase tracking-wider" :class="item.hasConflict ? 'bg-rose-500' : 'bg-gradient-to-r from-blue-600 to-violet-600'">Пересдача</span>
                  <span class="px-2 py-0.5 bg-white/60 dark:bg-black/20 text-[10px] font-bold rounded-md" :class="item.hasConflict ? 'text-rose-700 dark:text-rose-400' : 'text-blue-700 dark:text-blue-400'">Попытка {{ item.data.attemptNumber }}</span>
                  <span class="text-xs font-semibold flex items-center gap-1" :class="item.hasConflict ? 'text-rose-700 dark:text-rose-300' : 'text-blue-700 dark:text-blue-300'"><Users class="w-3 h-3"/>{{ item.data.groupName }}</span>
                </div>
                <div v-if="item.hasConflict" class="flex items-center gap-1 text-rose-600 dark:text-rose-400 text-[10px] font-bold bg-white dark:bg-rose-950 px-2 py-1 rounded-lg border border-rose-200 dark:border-rose-800 self-start"><AlertTriangle class="w-3 h-3" /> Накладка</div>
              </div>

              <h4 class="font-bold text-base mb-2 pl-3" :class="item.hasConflict ? 'text-rose-900 dark:text-rose-100' : 'text-blue-900 dark:text-blue-100'">{{ item.data.subjectName }}</h4>

              <div class="flex flex-wrap items-center gap-3 text-sm pl-3 font-medium" :class="item.hasConflict ? 'text-rose-600 dark:text-rose-300' : 'text-blue-600 dark:text-blue-300'">
                <template v-if="item.data.link"><a :href="item.data.link" target="_blank" class="flex items-center gap-1.5 hover:underline"><Globe class="w-3.5 h-3.5" /> Онлайн</a></template>
                <template v-else><span class="flex items-center gap-1.5"><MapPin class="w-3.5 h-3.5" /> {{ item.data.room || 'Аудитория уточняется' }}</span></template>
                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase" :class="getRoleBadge(item.data.myRole).class">{{ getRoleBadge(item.data.myRole).text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
