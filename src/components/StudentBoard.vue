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

const openCommissions = ref<Set<string>>(new Set());
function toggleCommission(id: string) {
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
  const roleWeights: Record<string, number> = { MAIN: 1, CHAIRMAN: 2, COMMISSION: 3 };
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
  1: '09:00–10:30',
  2: '10:40–12:10',
  3: '12:20–13:50',
  4: '14:30–16:00',
  5: '16:10–17:40',
  6: '17:50–19:20',
  7: '19:30–21:00'
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
    <div class="mb-8">
      <div class="mb-3">
        <p class="text-[11px] uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500 font-bold">
          Поиск
        </p>
        <h3 class="mt-2 text-2xl sm:text-3xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">
          Найдите свою группу
        </h3>
        <p class="mt-2 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-2xl leading-7">
          Введите номер группы, чтобы быстро получить актуальное расписание пересдач.
        </p>
      </div>

      <div class="relative mt-5">
        <div class="relative group">
          <Search class="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-slate-500 pointer-events-none transition-colors group-focus-within:text-red-500" />
          <input
              v-model="groupSearchQuery"
              @focus="showGroupDropdown = true"
              @input="showGroupDropdown = true; selectedGroupUuid = ''"
              type="text"
              placeholder="Введите номер группы для поиска пересдач..."
              class="w-full h-16 pl-14 pr-5 text-base rounded-[22px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-xl shadow-[0_10px_30px_rgba(15,23,42,0.06)] dark:shadow-none focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 outline-none transition-all text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
        </div>

        <div
            v-if="showGroupDropdown && (filteredGroups.length > 0 || (recentGroups.length > 0 && !groupSearchQuery))"
            class="absolute z-30 w-full mt-3 rounded-[24px] border border-slate-200/80 dark:border-white/10 bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl shadow-[0_24px_80px_rgba(15,23,42,0.18)] overflow-hidden max-h-80 overflow-y-auto"
        >
          <div
              v-if="recentGroups.length > 0 && !groupSearchQuery"
              class="border-b border-slate-100 dark:border-white/10"
          >
            <div class="px-5 py-3 flex items-center justify-between">
              <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.22em]">Недавние</span>
              <button
                  @click.stop="clearRecentGroups"
                  class="text-[10px] font-semibold text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors uppercase tracking-[0.16em]"
              >
                Очистить
              </button>
            </div>

            <div
                v-for="g in recentGroups"
                :key="'r-' + g.uuid"
                @click="selectGroup(g)"
                class="px-5 py-3.5 text-sm cursor-pointer text-slate-700 dark:text-slate-200 flex items-center gap-3 hover:bg-red-50 dark:hover:bg-white/[0.04] transition-colors"
            >
              <Clock class="w-4 h-4 text-slate-400 shrink-0" />
              <span class="font-semibold">{{ g.number }}</span>
            </div>
          </div>

          <div
              v-for="g in filteredGroups"
              :key="g.uuid"
              @click="selectGroup(g)"
              class="px-5 py-3.5 text-sm cursor-pointer text-slate-700 dark:text-slate-200 font-semibold hover:bg-red-50 dark:hover:bg-white/[0.04] transition-colors"
          >
            {{ g.number }}
          </div>
        </div>

        <div
            v-if="showGroupDropdown"
            @click="showGroupDropdown = false"
            class="fixed inset-0 z-20"
        ></div>
      </div>
    </div>

    <div
        v-if="!infoDismissed"
        class="mb-8 rounded-[26px] overflow-hidden border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_12px_40px_rgba(15,23,42,0.08)]"
    >
      <div class="flex items-center gap-3 px-5 sm:px-6 py-4 bg-red-50/70 dark:bg-red-500/10">
        <div class="w-10 h-10 rounded-2xl bg-red-100 dark:bg-red-500/15 flex items-center justify-center shrink-0">
          <Info class="w-4 h-4 text-red-600 dark:text-red-400" />
        </div>

        <h3 class="text-sm sm:text-[15px] font-extrabold text-slate-900 dark:text-white flex-grow tracking-tight">
          Порядок проведения пересдач
        </h3>

        <button
            @click="infoCollapsed = !infoCollapsed"
            class="p-2 rounded-xl hover:bg-red-100/70 dark:hover:bg-red-500/10 transition-colors text-slate-400"
        >
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="infoCollapsed ? '-rotate-90' : 'rotate-0'" />
        </button>

        <button
            @click="dismissInfo"
            class="p-2 rounded-xl hover:bg-red-100/70 dark:hover:bg-red-500/10 transition-colors text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div
          v-show="!infoCollapsed"
          class="px-5 sm:px-6 py-5 space-y-3 text-sm text-slate-600 dark:text-slate-300 leading-7 border-t border-slate-100 dark:border-white/10"
      >
        <p>
          Всего предусмотрено
          <span class="font-bold text-slate-900 dark:text-white">3 повторные промежуточные аттестации</span>.
          <span class="font-bold text-slate-900 dark:text-white">Последняя (3-я) повторная аттестация</span>
          назначается для обучающихся, пропустивших первую и/или вторую аттестации по уважительным причинам,
          или ввиду удовлетворения апелляции.
        </p>

        <p>
          Третья дата назначается
          <span class="font-bold text-slate-900 dark:text-white">только по заявлению обучающегося</span>
          и при предоставлении подтверждающих документов.
        </p>

        <p class="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-white/10">
          * Заявление на апелляцию подается в день проведения пересдачи.
        </p>
      </div>
    </div>

    <div v-if="selectedGroupUuid">
      <div v-if="studentRetakes.length === 0" class="py-20 text-center">
        <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10">
          <Search class="w-8 h-8 text-slate-300 dark:text-slate-600" />
        </div>

        <h3 class="text-xl font-black tracking-tight text-slate-800 dark:text-slate-200 mb-2">
          Пересдачи не назначены
        </h3>

        <p class="text-sm text-slate-400 dark:text-slate-500 max-w-sm mx-auto leading-7">
          Для группы
          <span class="font-semibold text-slate-500 dark:text-slate-400">{{ groupSearchQuery }}</span>
          пересдачи ещё не запланированы.
        </p>
      </div>

      <div v-else>
        <div
            v-if="availableSubjects.length > 1"
            class="mb-8 flex flex-wrap items-center gap-2 overflow-x-auto hide-scrollbar pb-1"
        >
          <button
              @click="selectedSubjectFilter = ''"
              :class="selectedSubjectFilter === ''
              ? 'bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.2)]'
              : 'bg-white/90 dark:bg-white/[0.04] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15'"
              class="px-4 py-2.5 rounded-2xl text-xs font-bold border transition-all whitespace-nowrap hover:-translate-y-0.5"
          >
            Все
          </button>

          <button
              v-for="sub in availableSubjects"
              :key="sub"
              @click="selectedSubjectFilter = sub"
              :class="selectedSubjectFilter === sub
              ? 'bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.2)]'
              : 'bg-white/90 dark:bg-white/[0.04] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15'"
              class="px-4 py-2.5 rounded-2xl text-xs font-bold border transition-all whitespace-nowrap hover:-translate-y-0.5"
          >
            {{ sub }}
          </button>
        </div>

        <div
            v-for="(retakesList, subjectName) in groupedRetakes"
            :key="subjectName"
            class="mb-10"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-1.5 h-6 rounded-full bg-red-500"></div>
            <h3 class="text-base sm:text-lg font-black tracking-tight text-slate-950 dark:text-white">
              {{ subjectName }}
            </h3>
            <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-white/[0.05] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-white/10">
              {{ retakesList.length }}
            </span>
          </div>

          <div class="space-y-4">
            <div
                v-for="retake in retakesList"
                :key="retake.id"
                class="rounded-[26px] border border-slate-200/80 dark:border-white/10 bg-white/88 dark:bg-white/[0.04] backdrop-blur-xl p-5 sm:p-6 shadow-[0_14px_40px_rgba(15,23,42,0.07)] hover:shadow-[0_22px_60px_rgba(15,23,42,0.12)] hover:-translate-y-1 transition-all duration-300"
                :class="{ 'opacity-55': daysUntil(retake.date) < 0 }"
            >
              <div class="flex flex-wrap items-center gap-2 mb-4">
                <span
                    class="px-3 py-1.5 text-[10px] font-extrabold rounded-xl uppercase tracking-[0.16em] text-white"
                    :class="retake.attemptNumber === 1 ? 'bg-blue-600' : retake.attemptNumber === 2 ? 'bg-amber-500' : 'bg-red-500'"
                >
                  Попытка {{ retake.attemptNumber || 1 }}
                </span>

                <span
                    class="px-3 py-1.5 text-[10px] font-bold rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-white/[0.04]"
                    :class="retake.dateLabel.colorClass"
                >
                  {{ retake.dateLabel.text }}
                </span>
              </div>

              <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div>
                  <div class="text-xl sm:text-2xl font-black tracking-tight text-slate-950 dark:text-white">
                    {{ formatDate(retake.date) }}
                  </div>

                  <div class="flex flex-wrap items-center gap-x-5 gap-y-2 mt-2.5 text-sm text-slate-500 dark:text-slate-400">
                    <span class="flex items-center gap-2">
                      <Clock class="w-4 h-4 shrink-0 opacity-70" />
                      {{ retake.timeSlots.map((s: number) => TIME_MAPPING[s]).join(', ') }}
                    </span>

                    <span class="flex items-center gap-2" :class="retake.link ? 'text-blue-600 dark:text-blue-400' : ''">
                      <template v-if="retake.link">
                        <Globe class="w-4 h-4 opacity-90" />
                        <a :href="retake.link" target="_blank" class="hover:underline font-semibold">
                          Онлайн
                        </a>
                      </template>
                      <template v-else>
                        <MapPin class="w-4 h-4 opacity-70" />
                        {{ retake.room || 'Аудитория уточняется' }}
                      </template>
                    </span>
                  </div>
                </div>

                <div class="self-start lg:self-center">
                  <div class="px-4 py-2 rounded-2xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs font-bold text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {{ retake.timeSlots.join(', ') }} пара
                  </div>
                </div>
              </div>

              <div class="mt-5 pt-5 border-t border-slate-100 dark:border-white/10">
                <button
                    @click="toggleCommission(retake.id)"
                    class="md:hidden w-full flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3"
                >
                  <span class="flex items-center gap-2">
                    <Users class="w-4 h-4" />
                    Комиссия ({{ retake.teachers.length }})
                  </span>
                  <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="openCommissions.has(retake.id) ? 'rotate-180' : ''" />
                </button>

                <div :class="{ 'hidden md:block': !openCommissions.has(retake.id), 'block': openCommissions.has(retake.id) }">
                  <div
                      v-if="retake.teachers && retake.teachers.length > 0"
                      class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3"
                  >
                    <div
                        v-for="t in retake.teachers"
                        :key="t.name"
                        class="flex items-center gap-3 p-3 rounded-2xl bg-slate-50/90 dark:bg-white/[0.04] border border-slate-200/70 dark:border-white/10"
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
                          {{ t.name }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div
                      v-else
                      class="text-sm text-slate-400 italic"
                  >
                    Преподаватели не назначены
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
