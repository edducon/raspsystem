<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Calendar, Clock, Users, CheckCircle, Search, ChevronDown, MapPin, Globe, X, AlertTriangle, Info, Trash2 } from 'lucide-vue-next';
import { actions } from 'astro:actions';
import { addToast } from '../composables/useToast';
import { cleanSubjectName, normalizeForCompare, fuzzyMatch } from '../lib/subjectNorm';

const props = defineProps<{
  groups: { uuid: string; number: string }[];
  subjects: { uuid: string; name: string }[];
  teachers: { uuid: string; fullName: string; departmentIds: number[] | null }[];
  currentUser: { id: string; role: string; departmentIds: number[] | null };
}>();

const selectedDate = ref('');
const selectedSubject = ref('');
const selectedSlots = ref<number[]>([]);
const mainTeachers = ref<string[]>([]);
const commissionTeachers = ref<string[]>([]);
const chairmanTeacher = ref<string | null>(null);
const isSubmitting = ref(false);

const retakeFormat = ref<'offline' | 'online'>('offline');
const roomUuid = ref('');
const onlineLink = ref('');
const attemptNumber = ref(1);

const groupSearchQuery = ref('');
const selectedGroupUuid = ref('');
const showGroupDropdown = ref(false);

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 50);
  const q = groupSearchQuery.value.toLowerCase();
  return props.groups.filter(g => g.number.toLowerCase().includes(q)).slice(0, 50);
});

const selectGroup = (group: { uuid: string; number: string }) => {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
};

const groupHistory = ref<{ subjectName: string; teacherNames: string[] }[]>([]);
const existingGroupRetakes = ref<{id: number, subjectUuid: string, attemptNumber: number, date: string, createdBy: string}[]>([]);

const sectionsCollapsed = ref({ slots: false, format: false, commission: false });

const formatShortName = (fullName?: string) => {
  if (!fullName) return '';
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 1) return parts[0];
  if (parts.length === 2) return `${parts[0]} ${parts[1][0]}.`;
  return `${parts[0]} ${parts[1][0]}.${parts[2][0]}.`;
};

const availableSubjects = computed(() => {
  if (groupHistory.value.length === 0) return [];
  const historyNames = groupHistory.value.map(h => h.subjectName);
  const cleanedHistoryNames = historyNames.map(n => normalizeForCompare(n));

  let matched = props.subjects.filter(s =>
    cleanedHistoryNames.some(h => h === normalizeForCompare(s.name))
  );

  if (matched.length === 0) {
    matched = props.subjects.filter(s =>
      historyNames.some(h => fuzzyMatch(h, s.name))
    );
  }

  const uniqueSubjects: { uuid: string; name: string }[] = [];
  const seenNames = new Set<string>();
  for (const subject of matched) {
    const cleaned = cleanSubjectName(subject.name);
    if (!seenNames.has(cleaned)) {
      seenNames.add(cleaned);
      uniqueSubjects.push({ uuid: subject.uuid, name: cleaned });
    }
  }
  return uniqueSubjects.sort((a, b) => a.name.localeCompare(b.name, 'ru'));
});

watch(selectedGroupUuid, async (newUuid) => {
  selectedSubject.value = '';
  groupHistory.value = [];
  existingGroupRetakes.value = [];
  mainTeachers.value = [];
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
  if (!newUuid) return;
  const group = props.groups.find(g => g.uuid === newUuid);
  if (group) {
    const { data: hData } = await actions.scheduleOptions.getGroupHistory({ groupName: group.number });
    if (hData) groupHistory.value = hData;
    const { data: rData } = await actions.scheduleOptions.getGroupRetakes({ groupUuid: newUuid });
    if (rData) existingGroupRetakes.value = rData;
  }
});

const currentSubjectRetakes = computed(() => {
  if (!selectedSubject.value) return [];
  return existingGroupRetakes.value.filter(r => r.subjectUuid === selectedSubject.value);
});

const assignedAttempts = computed(() => {
  return currentSubjectRetakes.value.map(r => Number(r.attemptNumber));
});

watch(assignedAttempts, (assigned) => {
  if (!assigned.includes(1)) attemptNumber.value = 1;
  else if (!assigned.includes(2)) attemptNumber.value = 2;
  else if (!assigned.includes(3)) attemptNumber.value = 3;
}, { immediate: true });

const formatDate = (dateStr: string) => {
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(dateStr));
};

const showMainDropdown = ref(false);
const showCommDropdown = ref(false);
const showChairmanDropdown = ref(false);

const mainSearchQuery = ref('');
const chairmanSearchQuery = ref('');
const commSearchQuery = ref('');

watch(showMainDropdown, (val) => { if(!val) mainSearchQuery.value = ''; });
watch(showChairmanDropdown, (val) => { if(!val) chairmanSearchQuery.value = ''; });
watch(showCommDropdown, (val) => { if(!val) commSearchQuery.value = ''; });

const allTeachersForSelectedSubject = computed(() => {
  if (!selectedSubject.value) return [];
  const subject = props.subjects.find(s => s.uuid === selectedSubject.value);
  if (!subject) return [];
  const cleanedSubjectName = cleanSubjectName(subject.name);
  const historyRecords = groupHistory.value.filter(h => cleanSubjectName(h.subjectName) === cleanedSubjectName);
  return historyRecords.flatMap(h => h.teacherNames);
});

const subjectBelongsToAnotherDept = computed(() => {
  if (props.currentUser.role === 'ADMIN' || !selectedSubject.value) return false;
  const historyNames = allTeachersForSelectedSubject.value;
  if (historyNames.length === 0) return false;
  const teachersInHistory = props.teachers.filter(t => historyNames.includes(t.fullName));
  if (teachersInHistory.length === 0) return false;
  const userDepts = props.currentUser.departmentIds || [];
  const sharesDept = teachersInHistory.some(t => {
    const tDepts = t.departmentIds || [];
    return tDepts.some(id => userDepts.includes(id));
  });
  return !sharesDept;
});

const availableMainTeachers = computed(() => {
  if (!selectedSubject.value || subjectBelongsToAnotherDept.value) return [];
  let filtered = props.teachers;
  const historyNames = allTeachersForSelectedSubject.value;
  if (historyNames.length > 0) {
    filtered = filtered.filter(t => historyNames.includes(t.fullName));
  }
  if (props.currentUser.role !== 'ADMIN') {
    const userDepts = props.currentUser.departmentIds || [];
    filtered = filtered.filter(t => {
      const tDepts = t.departmentIds || [];
      return tDepts.some(id => userDepts.includes(id));
    });
  }
  return filtered;
});

const validCommissionPool = computed(() => {
  if (mainTeachers.value.length === 0) return [];
  const mainTeacher = props.teachers.find(t => t.uuid === mainTeachers.value[0]);
  const mainDepts = mainTeacher?.departmentIds || [];
  if (mainDepts.length === 0) return [];
  return props.teachers.filter(t => {
    const tDepts = t.departmentIds || [];
    return tDepts.some(id => mainDepts.includes(id));
  });
});

const mainTeacherLacksDept = computed(() => {
  if (mainTeachers.value.length === 0) return false;
  const mainTeacher = props.teachers.find(t => t.uuid === mainTeachers.value[0]);
  return !mainTeacher?.departmentIds || mainTeacher.departmentIds.length === 0;
});

const availableChairmen = computed(() => {
  return validCommissionPool.value.filter(t => !mainTeachers.value.includes(t.uuid) && !commissionTeachers.value.includes(t.uuid));
});

const availableCommissionTeachers = computed(() => {
  return validCommissionPool.value.filter(t => !mainTeachers.value.includes(t.uuid) && t.uuid !== chairmanTeacher.value);
});

const displayMainTeachers = computed(() => {
  const q = mainSearchQuery.value.toLowerCase();
  return q ? availableMainTeachers.value.filter(t => t.fullName.toLowerCase().includes(q)) : availableMainTeachers.value;
});

const displayChairmen = computed(() => {
  const q = chairmanSearchQuery.value.toLowerCase();
  return q ? availableChairmen.value.filter(t => t.fullName.toLowerCase().includes(q)) : availableChairmen.value;
});

const displayCommTeachers = computed(() => {
  const q = commSearchQuery.value.toLowerCase();
  return q ? availableCommissionTeachers.value.filter(t => t.fullName.toLowerCase().includes(q)) : availableCommissionTeachers.value;
});

watch(selectedSubject, () => {
  mainTeachers.value = availableMainTeachers.value.map(t => t.uuid);
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
});

const removeMainTeacher = (uuid: string) => { mainTeachers.value = mainTeachers.value.filter(id => id !== uuid); };
const removeCommTeacher = (uuid: string) => { commissionTeachers.value = commissionTeachers.value.filter(id => id !== uuid); };
const selectChairman = (uuid: string) => {
  chairmanTeacher.value = uuid;
  showChairmanDropdown.value = false;
};

const TIME_MAPPING: Record<number, string> = {
  1: '09:00-10:30', 2: '10:40-12:10', 3: '12:20-13:50', 4: '14:30-16:00', 5: '16:10-17:40', 6: '17:50-19:20', 7: '19:30-21:00',
};

const isLoadingSlots = ref(false);
const daySchedule = ref<Record<string, any> | null>(null);

watch([selectedDate, selectedGroupUuid, mainTeachers, commissionTeachers, chairmanTeacher], async () => {
  selectedSlots.value = [];
  daySchedule.value = null;
  if (selectedDate.value && selectedGroupUuid.value) {
    isLoadingSlots.value = true;
    const group = props.groups.find(g => g.uuid === selectedGroupUuid.value);
    const allSelectedTeacherUuids = [...mainTeachers.value, ...commissionTeachers.value];
    if (chairmanTeacher.value) allSelectedTeacherUuids.push(chairmanTeacher.value);
    const teacherNames = allSelectedTeacherUuids.map(uuid => props.teachers.find(t => t.uuid === uuid)?.fullName).filter(Boolean) as string[];

    if (group) {
      const { data, error } = await actions.scheduleOptions.getMergedDaySchedule({
        groupNumber: group.number, groupUuid: group.uuid, teacherUuids: allSelectedTeacherUuids, teacherNames: teacherNames, date: selectedDate.value
      });
      if (!error && data) daySchedule.value = data;
    }
    isLoadingSlots.value = false;
  }
});

const toggleSlot = (slot: number) => {
  if (daySchedule.value && daySchedule.value[slot.toString()] !== null) return;
  const index = selectedSlots.value.indexOf(slot);
  if (index === -1) selectedSlots.value.push(slot);
  else selectedSlots.value.splice(index, 1);
  selectedSlots.value.sort();
};

const submitRetake = async () => {
  if (subjectBelongsToAnotherDept.value) return addToast('Нет доступа к дисциплине!', 'error');
  if (selectedSlots.value.length === 0 || mainTeachers.value.length === 0) return addToast('Выберите слоты и ведущего преподавателя!', 'error');
  if (attemptNumber.value > 1 && !chairmanTeacher.value) return addToast('Для 2-й и 3-й попытки необходимо назначить председателя комиссии!', 'error');
  if (retakeFormat.value === 'offline' && !roomUuid.value) return addToast('Укажите аудиторию для проведения пересдачи', 'error');
  if (retakeFormat.value === 'online' && !onlineLink.value) return addToast('Укажите ссылку на подключение', 'error');
  if (assignedAttempts.value.includes(attemptNumber.value)) return addToast('Эта попытка пересдачи уже назначена!', 'error');

  isSubmitting.value = true;
  const { error } = await actions.scheduleOptions.createRetake({
    groupUuid: selectedGroupUuid.value, subjectUuid: selectedSubject.value, date: selectedDate.value, timeSlots: selectedSlots.value,
    roomUuid: retakeFormat.value === 'offline' ? roomUuid.value : undefined, link: retakeFormat.value === 'online' ? onlineLink.value : undefined,
    attemptNumber: attemptNumber.value, mainTeachersUuids: mainTeachers.value, commissionTeachersUuids: commissionTeachers.value, chairmanUuid: chairmanTeacher.value || undefined,
  });
  isSubmitting.value = false;

  if (error) {
    addToast(error.message, 'error');
  } else {
    addToast('Пересдача успешно назначена!', 'success');
    const { data: rData } = await actions.scheduleOptions.getGroupRetakes({ groupUuid: selectedGroupUuid.value });
    if (rData) existingGroupRetakes.value = rData;
    selectedSlots.value = []; selectedDate.value = ''; roomUuid.value = ''; onlineLink.value = '';
    chairmanTeacher.value = null; commissionTeachers.value = [];
  }
};

const deleteRetake = async (id: number) => {
  if (!confirm('Вы уверены, что хотите удалить эту пересдачу?')) return;
  const { error } = await actions.scheduleOptions.deleteRetake({ id });
  if (error) {
    addToast(error.message, 'error');
  } else {
    addToast('Пересдача отменена', 'success');
    existingGroupRetakes.value = existingGroupRetakes.value.filter(r => r.id !== id);
    selectedDate.value = '';
  }
};
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5 md:p-8 relative z-10 transition-colors">

    <!-- Header -->
    <div class="flex items-center gap-3 mb-7">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-600/20 shrink-0">
        <Calendar class="w-5 h-5 text-white" />
      </div>
      <div>
        <h2 class="text-lg font-bold text-slate-900 dark:text-white">Назначение пересдачи</h2>
        <p class="text-xs text-slate-400 dark:text-slate-500">Заполните все шаги для создания</p>
      </div>
    </div>

    <!-- Step 1 -->
    <div class="flex items-center gap-3 mb-4">
      <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-md shadow-blue-600/20">1</div>
      <h3 class="text-sm font-bold text-slate-800 dark:text-white">Группа, дисциплина и дата</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
      <!-- Group -->
      <div class="relative">
        <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Группа</label>
        <div class="relative">
          <input v-model="groupSearchQuery" @focus="showGroupDropdown = true" @input="showGroupDropdown = true; selectedGroupUuid = ''" type="text" placeholder="Номер группы..."
            class="w-full rounded-xl border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 p-3 text-sm bg-white dark:bg-slate-950 dark:text-white outline-none pr-10 transition-all" />
          <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
        <div v-if="showGroupDropdown && filteredGroups.length > 0" class="absolute z-20 w-full mt-1.5 max-h-60 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl">
          <div v-for="g in filteredGroups" :key="g.uuid" @click="selectGroup(g)" class="px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer text-sm text-slate-700 dark:text-slate-200 font-medium transition-colors">{{ g.number }}</div>
        </div>
        <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
      </div>

      <!-- Subject -->
      <div>
        <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Дисциплина</label>
        <select v-model="selectedSubject" :disabled="!selectedGroupUuid || availableSubjects.length === 0"
          class="w-full rounded-xl border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 p-3 text-sm bg-white dark:bg-slate-950 dark:text-white outline-none disabled:opacity-50 transition-all">
          <option value="" disabled>{{ availableSubjects.length === 0 ? 'Сначала выберите группу' : 'Выберите предмет...' }}</option>
          <option v-for="s in availableSubjects" :key="s.uuid" :value="s.uuid">{{ s.name }}</option>
        </select>
        <p v-if="subjectBelongsToAnotherDept" class="text-xs text-rose-500 dark:text-rose-400 font-medium mt-2 flex items-start gap-1.5">
          <AlertTriangle class="w-3.5 h-3.5 mt-0.5 shrink-0" />
          Дисциплина другой кафедры. Нет прав назначения.
        </p>
      </div>

      <!-- Date -->
      <div>
        <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Дата</label>
        <input type="date" v-model="selectedDate" :disabled="!selectedSubject"
          class="w-full rounded-xl border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 p-3 text-sm bg-white dark:bg-slate-950 dark:text-white outline-none disabled:opacity-50 [color-scheme:light] dark:[color-scheme:dark] transition-all" />
      </div>
    </div>

    <!-- Existing retakes warning -->
    <div v-if="currentSubjectRetakes.length > 0" class="mb-6 p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/50 rounded-xl flex items-start gap-3 transition-colors">
      <Info class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
      <div class="w-full">
        <h4 class="text-xs font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider mb-2">Назначенные пересдачи</h4>
        <div class="space-y-1.5">
          <div v-for="r in currentSubjectRetakes" :key="r.id" class="text-sm text-amber-800 dark:text-amber-200 flex items-center justify-between bg-white/50 dark:bg-black/20 p-2.5 rounded-lg">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Попытка {{ r.attemptNumber }} — <span class="font-bold">{{ formatDate(r.date) }}</span>
            </div>
            <button v-if="props.currentUser.role === 'ADMIN' || props.currentUser.id === r.createdBy" @click="deleteRetake(r.id)" class="text-rose-500 hover:text-rose-700 dark:hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/30 transition-colors" title="Удалить"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 2: Schedule -->
    <div v-if="selectedDate && selectedGroupUuid" class="mb-8">
      <div class="h-px bg-slate-100 dark:bg-slate-800 mb-6"></div>
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-md shadow-blue-600/20">2</div>
          <h3 class="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2"><Clock class="w-4 h-4 text-blue-500" /> Расписание на день</h3>
        </div>
        <button @click="sectionsCollapsed.slots = !sectionsCollapsed.slots" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.slots ? '-rotate-90' : ''" />
        </button>
      </div>
      <div :class="{ 'hidden md:block': sectionsCollapsed.slots }">
        <div v-if="isLoadingSlots" class="flex items-center justify-center p-10 text-slate-500 dark:text-slate-400">
          <div class="w-5 h-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin mr-3"></div> Загрузка расписания...
        </div>
        <div v-else-if="daySchedule" class="grid grid-cols-1 gap-2.5">
          <div v-for="slot in 7" :key="slot" @click="toggleSlot(slot)"
            :class="[
              'p-4 rounded-xl border flex flex-col md:flex-row justify-between md:items-center gap-3 transition-all select-none',
              daySchedule[slot.toString()]
                ? 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 opacity-70 cursor-not-allowed'
                : selectedSlots.includes(slot)
                  ? 'bg-gradient-to-r from-blue-600 to-violet-600 border-transparent text-white shadow-lg shadow-blue-600/20 cursor-pointer scale-[1.01]'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer hover:shadow-sm'
            ]">
            <div class="flex items-center gap-4">
              <div :class="['w-11 h-11 rounded-xl flex items-center justify-center font-bold text-base shrink-0',
                selectedSlots.includes(slot) && !daySchedule[slot.toString()] ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400']">
                {{ slot }}
              </div>
              <div>
                <div class="font-semibold text-sm" :class="selectedSlots.includes(slot) && !daySchedule[slot.toString()] ? 'text-white' : 'text-slate-900 dark:text-slate-100'">{{ TIME_MAPPING[slot] }}</div>
                <div v-if="daySchedule[slot.toString()]" class="mt-0.5 flex flex-col gap-0.5">
                  <div class="text-xs text-rose-500 font-semibold flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-rose-500 inline-block"></span> {{ daySchedule[slot.toString()].reason }}</div>
                  <div v-if="daySchedule[slot.toString()].details" class="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px] sm:max-w-xs md:max-w-md">{{ daySchedule[slot.toString()].details.subject }}</div>
                </div>
                <div v-else class="text-xs font-semibold mt-0.5 flex items-center gap-1"
                  :class="selectedSlots.includes(slot) ? 'text-blue-100' : 'text-emerald-600 dark:text-emerald-500'">
                  <span class="w-1.5 h-1.5 rounded-full inline-block" :class="selectedSlots.includes(slot) ? 'bg-blue-100' : 'bg-emerald-500'"></span>
                  {{ selectedSlots.includes(slot) ? 'Выбрано' : 'Свободно' }}
                </div>
              </div>
            </div>
            <div v-if="daySchedule[slot.toString()]?.details" class="text-right text-xs">
              <div class="text-slate-500 dark:text-slate-400 font-medium">{{ daySchedule[slot.toString()].details.type }}</div>
              <div class="font-medium text-slate-700 dark:text-slate-300 mt-0.5 truncate max-w-[200px]">{{ daySchedule[slot.toString()].details.location }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 3: Format & attempt -->
    <div class="h-px bg-slate-100 dark:bg-slate-800 mb-6"></div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-md shadow-blue-600/20">3</div>
        <h3 class="text-sm font-bold text-slate-800 dark:text-white">Формат и попытка</h3>
      </div>
      <button @click="sectionsCollapsed.format = !sectionsCollapsed.format" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
        <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.format ? '-rotate-90' : ''" />
      </button>
    </div>
    <div :class="{ 'hidden md:block': sectionsCollapsed.format }">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 p-5 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800">
        <!-- Format -->
        <div>
          <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider">Формат проведения</h4>
          <div class="flex gap-2 mb-3">
            <button @click="retakeFormat = 'offline'"
              :class="retakeFormat === 'offline' ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-md shadow-blue-600/20' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'"
              class="flex-1 py-2.5 px-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all text-sm">
              <MapPin class="w-4 h-4" /> Очно
            </button>
            <button @click="retakeFormat = 'online'"
              :class="retakeFormat === 'online' ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-md shadow-blue-600/20' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'"
              class="flex-1 py-2.5 px-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all text-sm">
              <Globe class="w-4 h-4" /> Онлайн
            </button>
          </div>
          <input v-if="retakeFormat === 'offline'" v-model="roomUuid" type="text" placeholder="Аудитория (А-414)"
            class="w-full rounded-xl border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 p-3 text-sm bg-white dark:bg-slate-950 dark:text-white outline-none transition-all" />
          <input v-else v-model="onlineLink" type="url" placeholder="Ссылка на подключение"
            class="w-full rounded-xl border border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 p-3 text-sm bg-white dark:bg-slate-950 dark:text-white outline-none transition-all" />
        </div>
        <!-- Attempt -->
        <div>
          <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider">Номер попытки</h4>
          <div class="flex flex-col gap-2">
            <label v-for="n in 3" :key="n"
              class="flex items-center gap-3 p-3 rounded-xl transition-all border"
              :class="assignedAttempts.includes(n) ? 'opacity-40 cursor-not-allowed border-transparent bg-slate-50 dark:bg-slate-900' : 'cursor-pointer border-transparent hover:bg-white dark:hover:bg-slate-900 hover:border-slate-200 dark:hover:border-slate-700'">
              <input type="radio" v-model="attemptNumber" :value="n" :disabled="assignedAttempts.includes(n)" class="w-4 h-4 text-blue-600 disabled:cursor-not-allowed">
              <span class="text-sm font-semibold" :class="[
                assignedAttempts.includes(n) ? 'text-slate-400 dark:text-slate-500 line-through' : n === 3 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-800 dark:text-slate-200'
              ]">
                {{ n }}-я пересдача {{ n > 1 ? '(Комиссия)' : '' }}
                <span v-if="assignedAttempts.includes(n)" class="text-xs ml-1 font-normal">(Назначена)</span>
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 4: Commission -->
    <div class="h-px bg-slate-100 dark:bg-slate-800 mb-6"></div>
    <div class="flex items-center justify-between mb-4" :class="{'opacity-40 pointer-events-none': subjectBelongsToAnotherDept}">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-violet-600 text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-md shadow-blue-600/20">4</div>
        <h3 class="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2"><Users class="w-4 h-4 text-blue-500" /> Комиссия</h3>
      </div>
      <button @click="sectionsCollapsed.commission = !sectionsCollapsed.commission" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
        <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.commission ? '-rotate-90' : ''" />
      </button>
    </div>
    <div :class="{ 'hidden md:block': sectionsCollapsed.commission }">
      <div class="mb-8" :class="{'opacity-40 pointer-events-none': subjectBelongsToAnotherDept}">

        <div v-if="mainTeacherLacksDept" class="mb-5 text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/20 p-4 rounded-xl border border-amber-200 dark:border-amber-800/50 flex items-start gap-3">
          <AlertTriangle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <span class="font-bold block mb-0.5">Кафедра не указана</span>
            Назначьте кафедру ведущему преподавателю в панели администратора для формирования состава комиссии.
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <!-- Main teacher -->
          <div class="relative">
            <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Ведущий <span v-if="availableMainTeachers.length === 0 && selectedSubject && !subjectBelongsToAnotherDept" class="text-rose-500 normal-case tracking-normal">(Нет в истории)</span></label>
            <div @click="!selectedSubject ? null : showMainDropdown = !showMainDropdown"
              :class="['w-full min-h-[46px] rounded-xl border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                !selectedSubject ? 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 opacity-50 cursor-not-allowed' : 'bg-white dark:bg-slate-950 border-slate-300 dark:border-slate-700 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600']">
              <span v-if="mainTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">Выберите...</span>
              <span v-for="uuid in mainTeachers" :key="uuid" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-semibold">
                {{ formatShortName(availableMainTeachers.find(t => t.uuid === uuid)?.fullName) }}
                <X class="w-3 h-3 hover:text-blue-900 dark:hover:text-white cursor-pointer" @click.stop="removeMainTeacher(uuid)" />
              </span>
            </div>
            <div v-if="showMainDropdown" class="absolute z-20 w-full mt-1.5 max-h-64 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden">
              <div class="p-2 border-b border-slate-100 dark:border-slate-800 shrink-0">
                <div class="relative">
                  <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" v-model="mainSearchQuery" @click.stop placeholder="Поиск..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg outline-none focus:border-blue-500 dark:text-white transition-colors" />
                </div>
              </div>
              <div class="overflow-y-auto flex-1">
                <label v-for="t in displayMainTeachers" :key="t.uuid" class="flex items-center px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
                  <input type="checkbox" :value="t.uuid" v-model="mainTeachers" class="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mr-3">
                  <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
                </label>
                <div v-if="displayMainTeachers.length === 0" class="p-4 text-sm text-slate-400 text-center">Ничего не найдено</div>
              </div>
            </div>
            <div v-if="showMainDropdown" @click="showMainDropdown = false" class="fixed inset-0 z-10"></div>
          </div>

          <!-- Chairman -->
          <div class="relative">
            <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Председатель <span v-if="attemptNumber > 1" class="text-rose-500">*</span></label>
            <div @click="availableChairmen.length === 0 ? null : showChairmanDropdown = !showChairmanDropdown"
              :class="['w-full min-h-[46px] rounded-xl border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                availableChairmen.length === 0 ? 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 opacity-50 cursor-not-allowed' : 'bg-white dark:bg-slate-950 border-slate-300 dark:border-slate-700 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600']">
              <span v-if="!chairmanTeacher" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">Выберите...</span>
              <span v-else class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-xs font-semibold">
                {{ formatShortName(props.teachers.find(t => t.uuid === chairmanTeacher)?.fullName) }}
                <X class="w-3 h-3 hover:text-amber-900 dark:hover:text-white cursor-pointer" @click.stop="chairmanTeacher = null" />
              </span>
            </div>
            <div v-if="showChairmanDropdown" class="absolute z-20 w-full mt-1.5 max-h-64 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden">
              <div class="p-2 border-b border-slate-100 dark:border-slate-800 shrink-0">
                <div class="relative">
                  <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" v-model="chairmanSearchQuery" @click.stop placeholder="Поиск..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg outline-none focus:border-blue-500 dark:text-white transition-colors" />
                </div>
              </div>
              <div class="overflow-y-auto flex-1">
                <div v-for="t in displayChairmen" :key="t.uuid" @click="selectChairman(t.uuid)" class="px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer text-sm text-slate-700 dark:text-slate-200 transition-colors">{{ t.fullName }}</div>
                <div v-if="displayChairmen.length === 0" class="p-4 text-sm text-slate-400 text-center">Ничего не найдено</div>
              </div>
            </div>
            <div v-if="showChairmanDropdown" @click="showChairmanDropdown = false" class="fixed inset-0 z-10"></div>
          </div>

          <!-- Commission members -->
          <div class="relative">
            <label class="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Члены комиссии</label>
            <div @click="availableCommissionTeachers.length === 0 ? null : showCommDropdown = !showCommDropdown"
              :class="['w-full min-h-[46px] rounded-xl border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                availableCommissionTeachers.length === 0 ? 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 opacity-50 cursor-not-allowed' : 'bg-white dark:bg-slate-950 border-slate-300 dark:border-slate-700 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600']">
              <span v-if="commissionTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">Выберите...</span>
              <span v-for="uuid in commissionTeachers" :key="uuid" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold">
                {{ formatShortName(availableCommissionTeachers.find(t => t.uuid === uuid)?.fullName) }}
                <X class="w-3 h-3 hover:text-rose-500 cursor-pointer" @click.stop="removeCommTeacher(uuid)" />
              </span>
            </div>
            <div v-if="showCommDropdown" class="absolute z-20 w-full mt-1.5 max-h-64 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden">
              <div class="p-2 border-b border-slate-100 dark:border-slate-800 shrink-0">
                <div class="relative">
                  <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" v-model="commSearchQuery" @click.stop placeholder="Поиск..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg outline-none focus:border-blue-500 dark:text-white transition-colors" />
                </div>
              </div>
              <div class="overflow-y-auto flex-1">
                <label v-for="t in displayCommTeachers" :key="t.uuid" class="flex items-center px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
                  <input type="checkbox" :value="t.uuid" v-model="commissionTeachers" class="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mr-3">
                  <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
                </label>
                <div v-if="displayCommTeachers.length === 0" class="p-4 text-sm text-slate-400 text-center">Ничего не найдено</div>
              </div>
            </div>
            <div v-if="showCommDropdown" @click="showCommDropdown = false" class="fixed inset-0 z-10"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Submit -->
    <div class="flex justify-end pt-5 border-t border-slate-100 dark:border-slate-800">
      <button @click="submitRetake" :disabled="isSubmitting || subjectBelongsToAnotherDept"
        class="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg shadow-blue-600/20 flex items-center gap-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed">
        <div v-if="isSubmitting" class="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
        <CheckCircle v-else class="w-5 h-5" />
        Сохранить
      </button>
    </div>
  </div>
</template>
