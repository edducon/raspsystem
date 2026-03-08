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

  // 1. Ищем пересдачи (слияние)
  const todaysRetakes = props.retakes.filter(r => r.date === activeDay.dateStr);
  todaysRetakes.forEach(retake => {
    if (!processedRetakeIds.has(retake.id)) {
      processedRetakeIds.add(retake.id);

      // Проверяем накладки с обычным расписанием
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

      items.push({
        type: 'retake',
        startSlot: Math.min(...retake.timeSlots),
        data: retake,
        hasConflict
      });
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
          items.push({
            type: 'regular',
            startSlot: slot,
            data: regularPair
          });
        }
      }
    }
  }

  return items.sort((a, b) => a.startSlot - b.startSlot);
});

const getRoleBadge = (role: string) => {
  if (role === 'CHAIRMAN') return { text: 'Председатель', class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400' };
  if (role === 'MAIN') return { text: 'Ведущий', class: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-400' };
  return { text: 'Комиссия', class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' };
};
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden relative z-10 transition-colors">

    <div class="p-6 md:p-8 border-b border-slate-200 dark:border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-slate-50/50 dark:bg-slate-900/50">
      <div>
        <h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <CalendarDays class="text-indigo-600 dark:text-indigo-400 w-6 h-6" />
          Моё расписание
        </h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">{{ teacherFullName }}</p>
      </div>

      <div class="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
        <button @click="setToday" class="px-4 py-2 w-full sm:w-auto text-sm font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl shadow-sm transition-colors">Сегодня</button>
        <div class="flex items-center justify-between w-full sm:w-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1.5 rounded-xl shadow-sm">
          <button @click="prevWeek" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 transition-colors"><ChevronLeft class="w-5 h-5" /></button>
          <div class="px-4 text-center text-sm font-bold text-slate-800 dark:text-white min-w-[140px]">{{ weekDateRange }}</div>
          <button @click="nextWeek" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300 transition-colors"><ChevronRight class="w-5 h-5" /></button>
        </div>
      </div>
    </div>

    <div class="flex overflow-x-auto border-b border-slate-200 dark:border-slate-800 hide-scrollbar">
      <button
          v-for="day in weekDays" :key="day.id"
          @click="activeTab = day.id"
          :class="['flex-1 min-w-[100px] py-4 text-center text-sm font-semibold transition-colors outline-none border-b-2', activeTab === day.id ? 'text-indigo-600 dark:text-indigo-400 border-indigo-600 dark:border-indigo-400 bg-indigo-50/30 dark:bg-indigo-900/10' : 'text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50']"
      >
        <div class="mb-0.5">{{ day.label.split(',')[0] }}</div>
        <div class="text-xs font-normal opacity-70">{{ day.label.split(',')[1] }}</div>
      </button>
    </div>

    <div class="p-6 md:p-8 min-h-[400px] bg-slate-50/30 dark:bg-slate-950">

      <div v-if="mergedDaySchedule.length === 0" class="flex flex-col items-center justify-center py-16 text-slate-400 dark:text-slate-500 text-center">
        <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4"><CalendarDays class="w-8 h-8 opacity-50" /></div>
        <h3 class="text-lg font-medium text-slate-700 dark:text-slate-300">На этот день пар нет</h3>
        <p class="text-sm mt-1">Отличный повод заняться научной работой!</p>
      </div>

      <div v-else class="space-y-4">
        <div v-for="(item, idx) in mergedDaySchedule" :key="idx" class="flex flex-col md:flex-row gap-4">

          <div class="md:w-28 shrink-0 flex flex-row md:flex-col items-center md:items-start gap-3 md:gap-1 pt-2">
            <div class="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg flex items-center justify-center font-bold text-slate-700 dark:text-slate-300 text-sm whitespace-nowrap">
              {{ item.type === 'retake' ? item.data.timeSlots.join(', ') : item.startSlot }} пара
            </div>
            <div class="text-xs font-semibold text-slate-500 dark:text-slate-400 font-mono mt-1">
              <template v-if="item.type === 'retake'">
                {{ TIME_MAPPING[item.data.timeSlots[0]].split('-')[0] }} - {{ TIME_MAPPING[item.data.timeSlots[item.data.timeSlots.length - 1]].split('-')[1] }}
              </template>
              <template v-else>
                {{ TIME_MAPPING[item.startSlot] }}
              </template>
            </div>
          </div>

          <div class="flex-1 space-y-3">

            <div v-if="item.type === 'regular'" class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between gap-4 mb-2">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold rounded uppercase tracking-wider">По расписанию</span>
                  <span class="text-sm font-semibold text-slate-700 dark:text-slate-200"><Users class="w-3.5 h-3.5 inline mr-1 opacity-70"/>{{ item.data.group.number }}</span>
                </div>
                <div class="text-xs text-slate-500 dark:text-slate-400 font-medium bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">{{ item.data.subject_type.type }}</div>
              </div>
              <h4 class="font-bold text-slate-900 dark:text-white text-lg mb-3">{{ item.data.subject.name }}</h4>
              <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm font-medium" :class="item.data.link ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-600 dark:text-slate-400'">
                <template v-if="item.data.link"><a :href="item.data.link" target="_blank" class="flex items-center gap-1.5 hover:underline"><Globe class="w-4 h-4 opacity-80" /> Подключение (Онлайн)</a></template>
                <template v-else>
                  <div class="flex items-center gap-1.5"><MapPin class="w-4 h-4 opacity-80" /><span>{{ item.data.location.name }} <span v-if="item.data.rooms && item.data.rooms[0]" class="font-semibold text-slate-800 dark:text-slate-200">({{ item.data.rooms[0].number }})</span></span></div>
                </template>
              </div>
            </div>

            <div v-if="item.type === 'retake'" :class="['border rounded-xl p-5 shadow-sm transition-shadow relative overflow-hidden', item.hasConflict ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800' : 'bg-indigo-50 dark:bg-indigo-900/10 border-indigo-200 dark:border-indigo-800']">
              <div class="absolute left-0 top-0 bottom-0 w-1.5" :class="item.hasConflict ? 'bg-red-500' : 'bg-indigo-500'"></div>

              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 pl-3">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2 py-0.5 text-white text-xs font-bold rounded uppercase tracking-wider" :class="item.hasConflict ? 'bg-red-600' : 'bg-indigo-600'">Пересдача</span>
                  <span class="px-2 py-0.5 bg-white/50 dark:bg-black/20 text-xs font-bold rounded" :class="item.hasConflict ? 'text-red-700 dark:text-red-400' : 'text-indigo-700 dark:text-indigo-400'">Попытка {{ item.data.attemptNumber }}</span>
                  <span class="text-sm font-semibold flex items-center gap-1.5" :class="item.hasConflict ? 'text-red-800 dark:text-red-300' : 'text-indigo-800 dark:text-indigo-300'"><Users class="w-3.5 h-3.5"/>{{ item.data.groupName }}</span>
                </div>
                <div v-if="item.hasConflict" class="flex items-center gap-1 text-red-600 dark:text-red-400 text-xs font-bold bg-white dark:bg-red-950 px-2 py-1 rounded-lg border border-red-200 dark:border-red-800 self-start sm:self-auto"><AlertTriangle class="w-3.5 h-3.5" /> Накладка с парами</div>
              </div>

              <h4 class="font-bold text-lg mb-3 pl-3" :class="item.hasConflict ? 'text-red-900 dark:text-red-100' : 'text-indigo-900 dark:text-indigo-100'">{{ item.data.subjectName }}</h4>

              <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm pl-3 font-medium" :class="item.hasConflict ? 'text-red-700 dark:text-red-300' : 'text-indigo-700 dark:text-indigo-300'">
                <template v-if="item.data.link"><a :href="item.data.link" target="_blank" class="flex items-center gap-1.5 hover:underline"><Globe class="w-4 h-4 opacity-80" /> Онлайн-подключение</a></template>
                <template v-else><div class="flex items-center gap-1.5"><MapPin class="w-4 h-4 opacity-80" /> {{ item.data.room || 'Аудитория уточняется' }}</div></template>
                <span class="opacity-60 hidden sm:inline">•</span>
                <span class="flex items-center gap-1.5 opacity-90"><span class="px-2 py-0.5 rounded text-xs uppercase tracking-wider" :class="getRoleBadge(item.data.myRole).class">{{ getRoleBadge(item.data.myRole).text }}</span></span>
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