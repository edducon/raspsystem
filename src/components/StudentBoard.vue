<script setup lang="ts">
import { ref, computed } from 'vue';
import { Search, Clock, MapPin, Globe, ChevronDown, Users, Info, Filter } from 'lucide-vue-next';

const props = defineProps<{
  groups: { uuid: string; number: string }[];
  retakes: any[];
}>();

const groupSearchQuery = ref('');
const selectedGroupUuid = ref('');
const showGroupDropdown = ref(false);
const selectedSubjectFilter = ref('');

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
};

const sortTeachers = (teachers: any[]) => {
  if (!teachers) return [];
  const roleWeights: Record<string, number> = { 'MAIN': 1, 'CHAIRMAN': 2, 'COMMISSION': 3 };
  return [...teachers].sort((a, b) => (roleWeights[a.role] || 99) - (roleWeights[b.role] || 99));
};

const studentRetakes = computed(() => {
  if (!selectedGroupUuid.value) return [];
  let rawRetakes = props.retakes
      .filter(r => r.groupUuid === selectedGroupUuid.value)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return rawRetakes.map(r => ({ ...r, teachers: sortTeachers(r.teachers) }));
});

const availableSubjects = computed(() => {
  const subjects = new Set<string>();
  studentRetakes.value.forEach(r => subjects.add(r.subjectName));
  return Array.from(subjects).sort();
});

// Группировка по предметам (и применение фильтра)
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
  1: '09:00-10:30', 2: '10:40-12:10', 3: '12:20-13:50', 4: '14:30-16:00', 5: '16:10-17:40', 6: '17:50-19:20', 7: '19:30-21:00',
};

const formatDate = (dateStr: string) => {
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(dateStr));
};
</script>

<template>
  <div class="max-w-5xl mx-auto w-full relative z-10">

    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 rounded-2xl shadow-sm mb-6 flex flex-col md:flex-row md:items-center gap-6 justify-between transition-colors">
      <div>
        <h2 class="text-lg font-bold text-slate-900 dark:text-white">Поиск расписания</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Выберите академическую группу для просмотра пересдач</p>
      </div>

      <div class="relative w-full md:w-80">
        <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
        <input v-model="groupSearchQuery" @focus="showGroupDropdown = true" @input="showGroupDropdown = true; selectedGroupUuid = ''" type="text" placeholder="Номер группы" class="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-300 dark:border-slate-700 rounded-xl focus:border-slate-900 dark:focus:border-slate-400 focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-400 bg-transparent dark:text-white outline-none transition-colors" />
        <div v-if="showGroupDropdown && filteredGroups.length > 0" class="absolute z-30 w-full mt-2 max-h-60 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg">
          <div v-for="g in filteredGroups" :key="g.uuid" @click="selectGroup(g)" class="px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer text-slate-700 dark:text-slate-200 transition-colors">{{ g.number }}</div>
        </div>
        <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
      </div>
    </div>

    <div class="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30 p-6 rounded-2xl mb-8 transition-colors">
      <div class="flex items-center gap-3 mb-4">
        <div class="bg-blue-100 dark:bg-blue-900/50 p-2 rounded-xl text-blue-600 dark:text-blue-400"><Info class="w-5 h-5" /></div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Информация о порядке проведения пересдач</h3>
      </div>
      <div class="space-y-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
        <p>Всего предусмотрено <span class="font-semibold text-slate-800 dark:text-slate-200">3 повторные промежуточные аттестации</span>. <span class="font-semibold text-slate-800 dark:text-slate-200">Последняя (3-я) повторная аттестация</span> назначается для обучающихся, пропустивших первую и/или вторую аттестации по уважительным причинам, или ввиду удовлетворения апелляции.</p>
        <p>Третья дата назначается <span class="font-semibold text-slate-800 dark:text-slate-200">только по заявлению обучающегося</span> (подается в течение 3 рабочих дней со дня пропуска пересдачи) и при предоставлении подтверждающих документов.</p>
        <div class="mt-4 pt-3 border-t border-blue-200/50 dark:border-blue-800/30"><span class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">* Заявление на апелляцию подается в день проведения пересдачи.</span></div>
      </div>
    </div>

    <div v-if="selectedGroupUuid">
      <div v-if="studentRetakes.length === 0" class="p-10 text-center border border-dashed border-slate-300 dark:border-slate-700 rounded-2xl text-slate-500 dark:text-slate-400 transition-colors bg-white/50 dark:bg-slate-900/50">
        Пересдачи для выбранной группы не назначены.
      </div>

      <div v-else>
        <div v-if="availableSubjects.length > 1" class="mb-8 flex flex-wrap items-center gap-2">
          <div class="text-sm font-medium text-slate-500 dark:text-slate-400 mr-2 flex items-center gap-1.5"><Filter class="w-4 h-4" /> Дисциплины:</div>
          <button @click="selectedSubjectFilter = ''" :class="selectedSubjectFilter === '' ? 'bg-slate-900 dark:bg-indigo-600 text-white shadow-sm' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'" class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors">Все</button>
          <button v-for="sub in availableSubjects" :key="sub" @click="selectedSubjectFilter = sub" :class="selectedSubjectFilter === sub ? 'bg-slate-900 dark:bg-indigo-600 text-white shadow-sm' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'" class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors">{{ sub }}</button>
        </div>

        <div v-for="(retakesList, subjectName) in groupedRetakes" :key="subjectName" class="mb-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-sm transition-colors">

          <div class="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
            <div class="w-1.5 h-6 bg-indigo-500 rounded-full"></div>
            <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">{{ subjectName }}</h3>
          </div>

          <div class="p-6 space-y-6">
            <div v-for="retake in retakesList" :key="retake.id" class="flex flex-col md:flex-row gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/50 last:border-0 last:pb-0">

              <div class="md:w-1/3 shrink-0 pt-0.5">
                <div class="flex items-center gap-2 mb-3">
                  <span class="px-2.5 py-1 text-xs font-bold rounded-lg uppercase tracking-wider text-white" :class="retake.attemptNumber === 1 ? 'bg-indigo-600' : retake.attemptNumber === 2 ? 'bg-amber-500' : 'bg-red-600'">Попытка {{ retake.attemptNumber || 1 }}</span>
                </div>
                <div class="font-mono text-slate-900 dark:text-white font-bold text-lg">{{ formatDate(retake.date) }}</div>
                <div class="text-sm text-slate-500 dark:text-slate-400 mt-2 flex flex-col gap-1.5">
                  <div class="flex items-center gap-1.5"><Clock class="w-4 h-4 shrink-0 opacity-70" /> <span>{{ retake.timeSlots.map(s => TIME_MAPPING[s]).join(', ') }}</span></div>
                  <div><span class="inline-block text-xs font-medium bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">{{ retake.timeSlots.join(', ') }} пара</span></div>
                </div>
                <div class="text-sm font-medium mt-3 flex items-center gap-1.5" :class="retake.link ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-600 dark:text-slate-300'">
                  <template v-if="retake.link"><Globe class="w-4 h-4 opacity-80" /> <a :href="retake.link" target="_blank" class="hover:underline">Онлайн-подключение</a></template>
                  <template v-else><MapPin class="w-4 h-4 opacity-80" /> {{ retake.room || 'Аудитория уточняется' }}</template>
                </div>
              </div>

              <div class="hidden md:block w-px bg-slate-200 dark:bg-slate-800"></div>

              <div class="md:w-2/3 pt-0.5">
                <div class="text-xs text-slate-400 dark:text-slate-500 font-medium tracking-wider mb-3 flex items-center gap-1.5"><Users class="w-3.5 h-3.5"/> СОСТАВ КОМИССИИ</div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div v-for="t in retake.teachers" :key="t.name" class="flex flex-col gap-1 p-3 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-100 dark:border-slate-800">
                    <span class="text-xs font-bold uppercase tracking-wider" :class="t.role === 'CHAIRMAN' ? 'text-amber-600 dark:text-amber-500' : t.role === 'MAIN' ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'">
                      {{ t.role === 'MAIN' ? 'Ведущий преподаватель' : t.role === 'CHAIRMAN' ? 'Председатель комиссии' : 'Член комиссии' }}
                    </span>
                    <span class="font-medium text-slate-800 dark:text-slate-200">{{ t.name }}</span>
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
</template>