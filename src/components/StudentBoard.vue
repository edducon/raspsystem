<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Search, Clock, MapPin, Globe, ChevronDown, Users, Info, Filter, X } from 'lucide-vue-next';
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

const { recentGroups, addRecentGroup, clearRecentGroups } = useRecentGroups();

// Info block state
const infoDismissed = ref(false);
const infoCollapsed = ref(false);
const INFO_KEY = 'poli-rasp:info-dismissed';

onMounted(() => {
  if (localStorage.getItem(INFO_KEY) === '1') infoDismissed.value = true;
});

function dismissInfo() {
  infoDismissed.value = true;
  localStorage.setItem(INFO_KEY, '1');
}

// Commission collapse per retake (mobile)
const openCommissions = ref<Set<number>>(new Set());
function toggleCommission(id: number) {
  const s = new Set(openCommissions.value);
  s.has(id) ? s.delete(id) : s.add(id);
  openCommissions.value = s;
}

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 50);
  const q = groupSearchQuery.value.toLowerCase();
  return props.groups.filter(g => g.number.toLowerCase().includes(q)).slice(0, 50);
});

const selectGroup = (group: { uuid: string; number: string }) => {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
  selectedSubjectFilter.value = '';
  addRecentGroup(group);
};

const sortTeachers = (teachers: any[]) => {
  if (!teachers) return [];
  const roleWeights: Record<string, number> = { 'MAIN': 1, 'CHAIRMAN': 2, 'COMMISSION': 3 };
  return [...teachers].sort((a, b) => (roleWeights[a.role] || 99) - (roleWeights[b.role] || 99));
};

const studentRetakes = computed(() => {
  if (!selectedGroupUuid.value) return [];
  return props.retakes
    .filter(r => r.groupUuid === selectedGroupUuid.value)
    .map(r => ({ ...r, teachers: sortTeachers(r.teachers), dateLabel: getDateLabel(r.date) }))
    .sort((a, b) => {
      const pastA = daysUntil(a.date) < 0 ? 1 : 0;
      const pastB = daysUntil(b.date) < 0 ? 1 : 0;
      if (pastA !== pastB) return pastA - pastB;
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });
});

const availableSubjects = computed(() => {
  const subjects = new Set<string>();
  studentRetakes.value.forEach(r => subjects.add(r.subjectName));
  return Array.from(subjects).sort();
});

const groupedRetakes = computed(() => {
  let filtered = studentRetakes.value;
  if (selectedSubjectFilter.value) {
    filtered = filtered.filter(r => r.subjectName === selectedSubjectFilter.value);
  }
  const grouped: Record<string, any[]> = {};
  filtered.forEach(r => {
    if (!grouped[r.subjectName]) grouped[r.subjectName] = [];
    grouped[r.subjectName].push(r);
  });
  return grouped;
});

const TIME_MAPPING: Record<number, string> = {
  1: '09:00–10:30', 2: '10:40–12:10', 3: '12:20–13:50', 4: '14:30–16:00', 5: '16:10–17:40', 6: '17:50–19:20', 7: '19:30–21:00',
};

const formatDate = (dateStr: string) => {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(dateStr));
};
</script>

<template>
  <div class="max-w-5xl mx-auto w-full relative z-10">

    <!-- Search card -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm mb-5 flex flex-col md:flex-row md:items-center gap-5 justify-between transition-colors">
      <div>
        <h2 class="text-base font-bold text-slate-900 dark:text-white">Поиск расписания</h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Выберите академическую группу для просмотра пересдач</p>
      </div>

      <div class="relative w-full md:w-80">
        <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
        <input
          v-model="groupSearchQuery"
          @focus="showGroupDropdown = true"
          @input="showGroupDropdown = true; selectedGroupUuid = ''"
          type="text"
          placeholder="Номер группы"
          class="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-300 dark:border-slate-700 rounded-xl focus:border-indigo-500 dark:focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 bg-transparent dark:text-white outline-none transition-colors"
        />
        <div v-if="showGroupDropdown && (filteredGroups.length > 0 || (recentGroups.length > 0 && !groupSearchQuery))" class="absolute z-30 w-full mt-2 max-h-72 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg">
          <!-- Recent groups -->
          <div v-if="recentGroups.length > 0 && !groupSearchQuery" class="border-b border-slate-100 dark:border-slate-700">
            <div class="px-4 py-2 flex items-center justify-between">
              <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Недавние</span>
              <button @click.stop="clearRecentGroups" class="text-xs text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors">Очистить</button>
            </div>
            <div v-for="g in recentGroups" :key="'r-' + g.uuid" @click="selectGroup(g)" class="px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer text-slate-700 dark:text-slate-200 flex items-center gap-2 transition-colors">
              <Clock class="w-3.5 h-3.5 text-slate-400 shrink-0" />
              {{ g.number }}
            </div>
          </div>
          <!-- All groups -->
          <div v-for="g in filteredGroups" :key="g.uuid" @click="selectGroup(g)" class="px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer text-slate-700 dark:text-slate-200 transition-colors">{{ g.number }}</div>
        </div>
        <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
      </div>
    </div>

    <!-- Info block (dismissible) -->
    <div v-if="!infoDismissed" class="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30 p-5 rounded-2xl mb-7 transition-colors">
      <div class="flex items-center gap-3 mb-3">
        <div class="bg-blue-100 dark:bg-blue-900/50 p-2 rounded-xl text-blue-600 dark:text-blue-400 shrink-0"><Info class="w-4 h-4" /></div>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white flex-grow">Информация о порядке проведения пересдач</h3>
        <div class="flex items-center gap-1 shrink-0">
          <button @click="infoCollapsed = !infoCollapsed" class="p-1.5 rounded-lg hover:bg-blue-100/60 dark:hover:bg-blue-800/30 transition-colors text-blue-500 dark:text-blue-400">
            <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="infoCollapsed ? '-rotate-90' : 'rotate-0'" />
          </button>
          <button @click="dismissInfo" class="p-1.5 rounded-lg hover:bg-blue-100/60 dark:hover:bg-blue-800/30 transition-colors text-blue-400 dark:text-blue-500">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
      <div v-show="!infoCollapsed" class="space-y-2.5 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
        <p>Всего предусмотрено <span class="font-semibold text-slate-800 dark:text-slate-200">3 повторные промежуточные аттестации</span>. <span class="font-semibold text-slate-800 dark:text-slate-200">Последняя (3-я) повторная аттестация</span> назначается для обучающихся, пропустивших первую и/или вторую аттестации по уважительным причинам, или ввиду удовлетворения апелляции.</p>
        <p>Третья дата назначается <span class="font-semibold text-slate-800 dark:text-slate-200">только по заявлению обучающегося</span> (подается в течение 3 рабочих дней со дня пропуска пересдачи) и при предоставлении подтверждающих документов.</p>
        <div class="mt-3 pt-3 border-t border-blue-200/50 dark:border-blue-800/30"><span class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">* Заявление на апелляцию подается в день проведения пересдачи.</span></div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="selectedGroupUuid">
      <!-- Empty state -->
      <div v-if="studentRetakes.length === 0" class="p-10 text-center border border-dashed border-slate-300 dark:border-slate-700 rounded-2xl transition-colors bg-white/50 dark:bg-slate-900/50">
        <div class="w-14 h-14 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <Search class="w-7 h-7 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 class="text-base font-semibold text-slate-700 dark:text-slate-300 mb-1">Пересдачи не назначены</h3>
        <p class="text-sm text-slate-400 dark:text-slate-500 max-w-xs mx-auto">
          Для группы <span class="font-medium">{{ groupSearchQuery }}</span> пересдачи ещё не запланированы. Если у вас есть задолженности, обратитесь на кафедру.
        </p>
      </div>

      <div v-else>
        <!-- Subject filter -->
        <div v-if="availableSubjects.length > 1" class="mb-7 flex flex-wrap items-center gap-2">
          <div class="text-xs font-medium text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1.5"><Filter class="w-3.5 h-3.5" /> Дисциплины:</div>
          <button @click="selectedSubjectFilter = ''" :class="selectedSubjectFilter === '' ? 'bg-slate-900 dark:bg-indigo-600 text-white shadow-sm' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'" class="px-3 py-1.5 rounded-full text-xs font-medium transition-colors">Все</button>
          <button v-for="sub in availableSubjects" :key="sub" @click="selectedSubjectFilter = sub" :class="selectedSubjectFilter === sub ? 'bg-slate-900 dark:bg-indigo-600 text-white shadow-sm' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'" class="px-3 py-1.5 rounded-full text-xs font-medium transition-colors">{{ sub }}</button>
        </div>

        <!-- Subject groups -->
        <div v-for="(retakesList, subjectName) in groupedRetakes" :key="subjectName" class="mb-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-sm transition-colors">
          <div class="bg-slate-50 dark:bg-slate-800/50 px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
            <div class="w-1.5 h-5 bg-indigo-500 rounded-full shrink-0"></div>
            <h3 class="text-base font-bold text-slate-800 dark:text-slate-100">{{ subjectName }}</h3>
          </div>

          <div class="p-5 space-y-5">
            <div v-for="retake in retakesList" :key="retake.id" class="pb-5 border-b border-slate-100 dark:border-slate-800/50 last:border-0 last:pb-0">

              <!-- Top: attempt + date badge -->
              <div class="flex flex-wrap items-center gap-2 mb-3">
                <span class="px-2.5 py-1 text-xs font-bold rounded-lg uppercase tracking-wider text-white" :class="retake.attemptNumber === 1 ? 'bg-indigo-600' : retake.attemptNumber === 2 ? 'bg-amber-500' : 'bg-red-600'">Попытка {{ retake.attemptNumber || 1 }}</span>
                <span class="px-2.5 py-1 text-xs font-semibold rounded-lg" :class="retake.dateLabel.colorClass">{{ retake.dateLabel.text }}</span>
              </div>

              <!-- Content: date/time/place + commission -->
              <div class="flex flex-col md:flex-row gap-5">
                <!-- Left: date/time/place -->
                <div class="md:w-1/3 shrink-0">
                  <div class="font-mono text-slate-900 dark:text-white font-bold text-base">{{ formatDate(retake.date) }}</div>
                  <div class="text-sm text-slate-500 dark:text-slate-400 mt-1.5 flex flex-col gap-1">
                    <div class="flex items-center gap-1.5"><Clock class="w-3.5 h-3.5 shrink-0 opacity-70" /> <span>{{ retake.timeSlots.map((s: number) => TIME_MAPPING[s]).join(', ') }}</span></div>
                    <div><span class="inline-block text-xs font-medium bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">{{ retake.timeSlots.join(', ') }} пара</span></div>
                  </div>
                  <div class="text-sm font-medium mt-2.5 flex items-center gap-1.5" :class="retake.link ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-600 dark:text-slate-300'">
                    <template v-if="retake.link"><Globe class="w-3.5 h-3.5 opacity-80" /> <a :href="retake.link" target="_blank" class="hover:underline">Онлайн-подключение</a></template>
                    <template v-else><MapPin class="w-3.5 h-3.5 opacity-80" /> {{ retake.room || 'Аудитория уточняется' }}</template>
                  </div>
                </div>

                <div class="hidden md:block w-px bg-slate-200 dark:bg-slate-800 shrink-0"></div>

                <!-- Right: commission -->
                <div class="md:w-2/3">
                  <!-- Mobile toggle -->
                  <button @click="toggleCommission(retake.id)" class="md:hidden w-full flex items-center justify-between py-2 text-xs font-medium text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800/50 mt-1 mb-1">
                    <span class="flex items-center gap-1.5"><Users class="w-3.5 h-3.5" /> Состав комиссии ({{ retake.teachers.length }})</span>
                    <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="openCommissions.has(retake.id) ? 'rotate-180' : ''" />
                  </button>
                  <!-- Commission content -->
                  <div :class="{ 'hidden md:block': !openCommissions.has(retake.id), 'block': openCommissions.has(retake.id) }">
                    <div class="text-xs text-slate-400 dark:text-slate-500 font-medium tracking-wider mb-2.5 hidden md:flex items-center gap-1.5"><Users class="w-3.5 h-3.5" /> СОСТАВ КОМИССИИ</div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      <div v-for="t in retake.teachers" :key="t.name" class="flex flex-col gap-0.5 p-3 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-100 dark:border-slate-800">
                        <span class="text-xs font-bold uppercase tracking-wider" :class="t.role === 'CHAIRMAN' ? 'text-amber-600 dark:text-amber-500' : t.role === 'MAIN' ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
                          {{ t.role === 'MAIN' ? 'Ведущий преподаватель' : t.role === 'CHAIRMAN' ? 'Председатель комиссии' : 'Член комиссии' }}
                        </span>
                        <span class="font-medium text-slate-800 dark:text-slate-200 text-sm">{{ t.name }}</span>
                      </div>
                    </div>
                    <div v-if="!retake.teachers || retake.teachers.length === 0" class="text-sm text-slate-400">Преподаватели не назначены</div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
