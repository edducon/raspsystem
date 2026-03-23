<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Search, Clock, MapPin, Globe, ChevronDown, Users, Info, X } from 'lucide-vue-next';
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

const getRoleName = (role: string) => {
  if (role === 'MAIN') return 'Ведущий';
  if (role === 'CHAIRMAN') return 'Председатель';
  return 'Комиссия';
};

const getRoleColor = (role: string) => {
  if (role === 'MAIN') return 'text-blue-600 dark:text-blue-400';
  if (role === 'CHAIRMAN') return 'text-amber-600 dark:text-amber-400';
  return 'text-slate-500 dark:text-slate-400';
};
</script>

<template>
  <div class="w-full relative z-10">

    <!-- Search -->
    <div class="relative mb-6">
      <div class="relative">
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
        <input
          v-model="groupSearchQuery"
          @focus="showGroupDropdown = true"
          @input="showGroupDropdown = true; selectedGroupUuid = ''"
          type="text"
          placeholder="Введите номер группы для поиска пересдач..."
          class="w-full h-14 pl-12 pr-4 text-base rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm focus:shadow-lg focus:border-blue-500 dark:focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none"
        />
      </div>

      <!-- Dropdown -->
      <div v-if="showGroupDropdown && (filteredGroups.length > 0 || (recentGroups.length > 0 && !groupSearchQuery))"
           class="absolute z-30 w-full mt-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl shadow-slate-200/60 dark:shadow-none overflow-hidden max-h-80 overflow-y-auto">
        <!-- Recent groups -->
        <div v-if="recentGroups.length > 0 && !groupSearchQuery" class="border-b border-slate-100 dark:border-slate-800">
          <div class="px-4 py-2.5 flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Недавние</span>
            <button @click.stop="clearRecentGroups" class="text-[10px] font-semibold text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 transition-colors uppercase tracking-wider">Очистить</button>
          </div>
          <div v-for="g in recentGroups" :key="'r-' + g.uuid" @click="selectGroup(g)"
               class="px-4 py-3 text-sm hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer text-slate-700 dark:text-slate-200 flex items-center gap-2.5 transition-colors">
            <Clock class="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span class="font-medium">{{ g.number }}</span>
          </div>
        </div>
        <!-- All groups -->
        <div v-for="g in filteredGroups" :key="g.uuid" @click="selectGroup(g)"
             class="px-4 py-3 text-sm hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer text-slate-700 dark:text-slate-200 font-medium transition-colors">
          {{ g.number }}
        </div>
      </div>
      <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-20"></div>
    </div>

    <!-- Info block -->
    <div v-if="!infoDismissed" class="mb-6 bg-white dark:bg-slate-900 rounded-2xl border border-blue-200/60 dark:border-blue-800/30 overflow-hidden shadow-sm">
      <div class="flex items-center gap-3 px-5 py-3.5 bg-blue-50/60 dark:bg-blue-950/20">
        <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900/50 rounded-xl flex items-center justify-center shrink-0">
          <Info class="w-4 h-4 text-blue-600 dark:text-blue-400" />
        </div>
        <h3 class="text-sm font-bold text-slate-900 dark:text-white flex-grow">Порядок проведения пересдач</h3>
        <button @click="infoCollapsed = !infoCollapsed" class="p-1.5 rounded-lg hover:bg-blue-100/60 dark:hover:bg-blue-800/30 transition-colors text-slate-400">
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="infoCollapsed ? '-rotate-90' : 'rotate-0'" />
        </button>
        <button @click="dismissInfo" class="p-1.5 rounded-lg hover:bg-blue-100/60 dark:hover:bg-blue-800/30 transition-colors text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X class="w-4 h-4" />
        </button>
      </div>
      <div v-show="!infoCollapsed" class="px-5 py-4 space-y-2.5 text-sm text-slate-600 dark:text-slate-300 leading-relaxed border-t border-blue-100/60 dark:border-blue-800/20">
        <p>Всего предусмотрено <span class="font-semibold text-slate-800 dark:text-slate-200">3 повторные промежуточные аттестации</span>. <span class="font-semibold text-slate-800 dark:text-slate-200">Последняя (3-я) повторная аттестация</span> назначается для обучающихся, пропустивших первую и/или вторую аттестации по уважительным причинам, или ввиду удовлетворения апелляции.</p>
        <p>Третья дата назначается <span class="font-semibold text-slate-800 dark:text-slate-200">только по заявлению обучающегося</span> (подается в течение 3 рабочих дней со дня пропуска пересдачи) и при предоставлении подтверждающих документов.</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800/50">* Заявление на апелляцию подается в день проведения пересдачи.</p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="selectedGroupUuid">
      <!-- Empty state -->
      <div v-if="studentRetakes.length === 0" class="py-16 text-center">
        <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-5">
          <Search class="w-7 h-7 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 class="text-lg font-bold text-slate-700 dark:text-slate-300 mb-1.5">Пересдачи не назначены</h3>
        <p class="text-sm text-slate-400 dark:text-slate-500 max-w-xs mx-auto leading-relaxed">
          Для группы <span class="font-semibold text-slate-500 dark:text-slate-400">{{ groupSearchQuery }}</span> пересдачи ещё не запланированы. Обратитесь на кафедру.
        </p>
      </div>

      <div v-else>
        <!-- Subject filter pills -->
        <div v-if="availableSubjects.length > 1" class="mb-6 flex flex-wrap items-center gap-2 overflow-x-auto hide-scrollbar pb-1">
          <button @click="selectedSubjectFilter = ''"
            :class="selectedSubjectFilter === '' ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-md shadow-blue-600/20' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'"
            class="px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap">
            Все
          </button>
          <button v-for="sub in availableSubjects" :key="sub" @click="selectedSubjectFilter = sub"
            :class="selectedSubjectFilter === sub ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-md shadow-blue-600/20' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'"
            class="px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap">
            {{ sub }}
          </button>
        </div>

        <!-- Subject groups -->
        <div v-for="(retakesList, subjectName) in groupedRetakes" :key="subjectName" class="mb-8">
          <!-- Subject header -->
          <div class="flex items-center gap-3 mb-3">
            <div class="w-1 h-5 rounded-full bg-gradient-to-b from-blue-500 to-violet-500"></div>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">{{ subjectName }}</h3>
            <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">{{ retakesList.length }}</span>
          </div>

          <!-- Retake cards -->
          <div class="space-y-3">
            <div v-for="retake in retakesList" :key="retake.id"
                 class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-md hover:border-slate-300 dark:hover:border-slate-700 transition-all"
                 :class="{ 'opacity-50': daysUntil(retake.date) < 0 }">

              <!-- Badges row -->
              <div class="flex flex-wrap items-center gap-2 mb-3">
                <span class="px-2.5 py-1 text-[10px] font-extrabold rounded-lg uppercase tracking-wider text-white"
                      :class="retake.attemptNumber === 1 ? 'bg-blue-600' : retake.attemptNumber === 2 ? 'bg-amber-500' : 'bg-rose-500'">
                  Попытка {{ retake.attemptNumber || 1 }}
                </span>
                <span class="px-2.5 py-1 text-[10px] font-bold rounded-lg" :class="retake.dateLabel.colorClass">
                  {{ retake.dateLabel.text }}
                </span>
              </div>

              <!-- Main content -->
              <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <div class="text-lg font-bold text-slate-900 dark:text-white">{{ formatDate(retake.date) }}</div>
                  <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-sm text-slate-500 dark:text-slate-400">
                    <span class="flex items-center gap-1.5">
                      <Clock class="w-3.5 h-3.5 shrink-0 opacity-60" />
                      {{ retake.timeSlots.map((s: number) => TIME_MAPPING[s]).join(', ') }}
                    </span>
                    <span class="flex items-center gap-1.5" :class="retake.link ? 'text-blue-600 dark:text-blue-400' : ''">
                      <template v-if="retake.link">
                        <Globe class="w-3.5 h-3.5 opacity-80" />
                        <a :href="retake.link" target="_blank" class="hover:underline font-medium">Онлайн</a>
                      </template>
                      <template v-else>
                        <MapPin class="w-3.5 h-3.5 opacity-60" />
                        {{ retake.room || 'Аудитория уточняется' }}
                      </template>
                    </span>
                  </div>
                </div>
                <div class="text-xs font-semibold text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-lg whitespace-nowrap self-start md:self-center">
                  {{ retake.timeSlots.join(', ') }} пара
                </div>
              </div>

              <!-- Commission -->
              <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/50">
                <!-- Mobile toggle -->
                <button @click="toggleCommission(retake.id)"
                        class="md:hidden w-full flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
                  <span class="flex items-center gap-1.5"><Users class="w-3.5 h-3.5" /> Комиссия ({{ retake.teachers.length }})</span>
                  <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="openCommissions.has(retake.id) ? 'rotate-180' : ''" />
                </button>

                <div :class="{ 'hidden md:block': !openCommissions.has(retake.id), 'block': openCommissions.has(retake.id) }">
                  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    <div v-for="t in retake.teachers" :key="t.name"
                         class="flex items-center gap-3 p-2.5 bg-slate-50 dark:bg-slate-800/30 rounded-xl">
                      <div class="w-1.5 h-1.5 rounded-full shrink-0"
                           :class="t.role === 'MAIN' ? 'bg-blue-500' : t.role === 'CHAIRMAN' ? 'bg-amber-500' : 'bg-slate-400'"></div>
                      <div class="min-w-0">
                        <div class="text-[10px] font-bold uppercase tracking-wider" :class="getRoleColor(t.role)">{{ getRoleName(t.role) }}</div>
                        <div class="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{{ t.name }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-if="!retake.teachers || retake.teachers.length === 0" class="text-sm text-slate-400 italic">Преподаватели не назначены</div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
