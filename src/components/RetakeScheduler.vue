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

// Collapse state for form sections (2–4) on mobile
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

  // Strict match first
  let matched = props.subjects.filter(s =>
    cleanedHistoryNames.some(h => h === normalizeForCompare(s.name))
  );

  // Fuzzy fallback if strict yields nothing
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
  <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-5 md:p-8 relative z-10 transition-colors">
    <div class="bg-indigo-50/60 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800/40 rounded-xl px-5 py-4 mb-7">
      <h2 class="text-lg md:text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
        <Calendar class="w-5 h-5 text-indigo-600 dark:text-indigo-400 shrink-0" />
        Назначение пересдачи
      </h2>
    </div>

    <!-- Step 1 -->
    <div class="flex items-center gap-3 mb-4">
      <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shrink-0">1</div>
      <h3 class="text-base font-bold text-slate-800 dark:text-white">Группа, дисциплина и дата</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="relative">
        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Учебная группа</label>
        <div class="relative">
          <input v-model="groupSearchQuery" @focus="showGroupDropdown = true" @input="showGroupDropdown = true; selectedGroupUuid = ''" type="text" placeholder="Введите номер..." class="w-full box-border m-0 rounded-lg border-slate-300 dark:border-slate-600 focus:border-indigo-500 focus:ring-indigo-500 p-2.5 border bg-slate-50 dark:bg-slate-900 dark:text-white outline-none pr-10 transition-colors" />
          <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
        </div>
        <div v-if="showGroupDropdown && filteredGroups.length > 0" class="absolute z-20 w-full mt-1 max-h-60 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg shadow-xl">
          <div v-for="g in filteredGroups" :key="g.uuid" @click="selectGroup(g)" class="px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer text-slate-700 dark:text-slate-200 transition-colors">{{ g.number }}</div>
        </div>
        <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Дисциплина</label>
        <select v-model="selectedSubject" :disabled="!selectedGroupUuid || availableSubjects.length === 0" class="w-full box-border m-0 rounded-lg border-slate-300 dark:border-slate-600 focus:border-indigo-500 focus:ring-indigo-500 p-2.5 border bg-slate-50 dark:bg-slate-900 dark:text-white outline-none disabled:opacity-50 transition-colors">
          <option value="" disabled>{{ availableSubjects.length === 0 ? 'Сначала выберите группу' : 'Выберите предмет...' }}</option>
          <option v-for="s in availableSubjects" :key="s.uuid" :value="s.uuid">{{ s.name }}</option>
        </select>

        <p v-if="subjectBelongsToAnotherDept" class="text-sm text-red-500 dark:text-red-400 font-medium mt-2 flex items-start gap-1.5">
          <AlertTriangle class="w-4 h-4 mt-0.5 shrink-0" />
          Эта дисциплина относится к другой кафедре. У вас нет прав доступа для назначения пересдачи.
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Дата пересдачи</label>
        <input type="date" v-model="selectedDate" :disabled="!selectedSubject" class="w-full box-border m-0 rounded-lg border-slate-300 dark:border-slate-600 focus:border-indigo-500 focus:ring-indigo-500 p-2.5 border bg-slate-50 dark:bg-slate-900 dark:text-white outline-none disabled:opacity-50 [color-scheme:light] dark:[color-scheme:dark] transition-colors" />
      </div>
    </div>

    <div v-if="currentSubjectRetakes.length > 0" class="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl flex items-start gap-3 transition-colors">
      <Info class="w-6 h-6 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
      <div class="w-full">
        <h4 class="text-sm font-bold text-amber-900 dark:text-amber-400 mb-2">Назначенные пересдачи:</h4>
        <ul class="space-y-2">
          <li v-for="r in currentSubjectRetakes" :key="r.id" class="text-sm text-amber-900 dark:text-amber-200 flex items-center justify-between bg-white/50 dark:bg-black/20 p-2 rounded-lg border border-amber-200/50 dark:border-amber-700/50">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Попытка {{ r.attemptNumber }} — <span class="font-bold">{{ formatDate(r.date) }}</span>
            </div>
            <button v-if="props.currentUser.role === 'ADMIN' || props.currentUser.id === r.createdBy" @click="deleteRetake(r.id)" class="text-red-500 hover:text-red-700 dark:hover:text-red-400 p-1.5 rounded-md hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors" title="Удалить пересдачу">
              <Trash2 class="w-4 h-4" />
            </button>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="selectedDate && selectedGroupUuid" class="mb-8">
      <hr class="border-slate-100 dark:border-slate-700/50 mb-6" />
      <!-- Step 2 header with mobile collapse -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shrink-0">2</div>
          <h3 class="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2"><Clock class="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Расписание на выбранный день</h3>
        </div>
        <button @click="sectionsCollapsed.slots = !sectionsCollapsed.slots" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.slots ? '-rotate-90' : ''" />
        </button>
      </div>
      <div :class="{ 'hidden md:block': sectionsCollapsed.slots }">
      <div v-if="isLoadingSlots" class="text-slate-500 dark:text-slate-400 flex items-center justify-center p-8 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-700">
        <div class="w-5 h-5 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin mr-3"></div> Синхронизация с базой...
      </div>
      <div v-else-if="daySchedule" class="grid grid-cols-1 gap-3">
        <div v-for="slot in 7" :key="slot" @click="toggleSlot(slot)" :class="['p-4 rounded-xl border flex flex-col md:flex-row justify-between md:items-center gap-3 transition-all select-none', daySchedule[slot.toString()] ? 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-700/50 opacity-80 cursor-not-allowed' : selectedSlots.includes(slot) ? 'bg-slate-900 dark:bg-indigo-600 border-slate-900 dark:border-indigo-600 text-white shadow-md cursor-pointer transform scale-[1.01]' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-400 cursor-pointer hover:shadow-sm']">
          <div class="flex items-center gap-4">
            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shrink-0 transition-colors', selectedSlots.includes(slot) && !daySchedule[slot.toString()] ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300']">{{ slot }}</div>
            <div>
              <div class="font-semibold" :class="selectedSlots.includes(slot) && !daySchedule[slot.toString()] ? 'text-white' : 'text-slate-900 dark:text-slate-100'">{{ TIME_MAPPING[slot] }}</div>
              <div v-if="daySchedule[slot.toString()]" class="mt-1 flex flex-col gap-0.5"><div class="text-xs text-red-500 font-medium flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500 inline-block shrink-0"></span> {{ daySchedule[slot.toString()].reason }}</div><div v-if="daySchedule[slot.toString()].details" class="text-xs text-slate-500 dark:text-slate-400 max-w-[200px] sm:max-w-xs md:max-w-md truncate">{{ daySchedule[slot.toString()].details.subject }}</div></div>
              <div v-else class="text-xs font-medium mt-1 flex items-center gap-1" :class="selectedSlots.includes(slot) ? 'text-indigo-100' : 'text-emerald-600 dark:text-emerald-500'"><span class="w-2 h-2 rounded-full inline-block" :class="selectedSlots.includes(slot) ? 'bg-indigo-100' : 'bg-emerald-500'"></span> {{ selectedSlots.includes(slot) ? 'Выбрано для пересдачи' : 'Окно свободно' }}</div>
            </div>
          </div>
          <div v-if="daySchedule[slot.toString()] && daySchedule[slot.toString()].details" class="text-left md:text-right text-sm"><div class="text-slate-500 dark:text-slate-400 font-medium">{{ daySchedule[slot.toString()].details.type }}</div><div class="font-medium text-slate-800 dark:text-slate-200 mt-0.5 max-w-[200px] truncate">{{ daySchedule[slot.toString()].details.location }}</div></div>
        </div>
      </div>
      </div> <!-- end collapsible slots wrapper -->
    </div>

    <hr class="border-slate-100 dark:border-slate-700/50 mb-6" />
    <!-- Step 3 header with mobile collapse -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shrink-0">3</div>
        <h3 class="text-base font-bold text-slate-800 dark:text-white">Формат и номер попытки</h3>
      </div>
      <button @click="sectionsCollapsed.format = !sectionsCollapsed.format" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
        <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.format ? '-rotate-90' : ''" />
      </button>
    </div>
    <div :class="{ 'hidden md:block': sectionsCollapsed.format }">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 p-5 bg-slate-50 dark:bg-slate-900/30 rounded-xl border border-slate-200 dark:border-slate-700/50">
      <div>
        <h3 class="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider">Формат</h3>
        <div class="flex gap-3 mb-4">
          <button @click="retakeFormat = 'offline'" :class="['flex-1 py-2 px-3 rounded-lg border font-medium flex items-center justify-center gap-2 transition-colors text-sm', retakeFormat === 'offline' ? 'bg-slate-900 dark:bg-indigo-600 text-white border-slate-900 dark:border-indigo-600' : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700']"><MapPin class="w-4 h-4" /> Очно</button>
          <button @click="retakeFormat = 'online'" :class="['flex-1 py-2 px-3 rounded-lg border font-medium flex items-center justify-center gap-2 transition-colors text-sm', retakeFormat === 'online' ? 'bg-slate-900 dark:bg-indigo-600 text-white border-slate-900 dark:border-indigo-600' : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700']"><Globe class="w-4 h-4" /> Онлайн</button>
        </div>
        <div v-if="retakeFormat === 'offline'">
          <input v-model="roomUuid" type="text" placeholder="Укажите кабинет (А-414)" class="w-full box-border m-0 rounded-lg border-slate-300 dark:border-slate-600 focus:border-indigo-500 p-2.5 text-sm border bg-white dark:bg-slate-900 dark:text-white outline-none transition-colors" />
        </div>
        <div v-else>
          <input v-model="onlineLink" type="url" placeholder="Ссылка на подключение" class="w-full box-border m-0 rounded-lg border-slate-300 dark:border-slate-600 focus:border-indigo-500 p-2.5 text-sm border bg-white dark:bg-slate-900 dark:text-white outline-none transition-colors" />
        </div>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider">Номер попытки</h3>
        <div class="flex flex-col gap-3">
          <label class="flex items-center gap-3 p-2 rounded-lg transition-colors border border-transparent"
                 :class="assignedAttempts.includes(1) ? 'opacity-50 cursor-not-allowed grayscale' : 'cursor-pointer hover:bg-white dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-700'">
            <input type="radio" v-model="attemptNumber" :value="1" :disabled="assignedAttempts.includes(1)" class="w-4 h-4 text-indigo-600 disabled:cursor-not-allowed">
            <span class="text-sm font-medium" :class="assignedAttempts.includes(1) ? 'text-slate-400 dark:text-slate-500 line-through' : 'text-slate-800 dark:text-slate-200'">
              1-я пересдача <span v-if="assignedAttempts.includes(1)" class="text-xs ml-1">(Уже назначена)</span>
            </span>
          </label>

          <label class="flex items-center gap-3 p-2 rounded-lg transition-colors border border-transparent"
                 :class="assignedAttempts.includes(2) ? 'opacity-50 cursor-not-allowed grayscale' : 'cursor-pointer hover:bg-white dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-700'">
            <input type="radio" v-model="attemptNumber" :value="2" :disabled="assignedAttempts.includes(2)" class="w-4 h-4 text-indigo-600 disabled:cursor-not-allowed">
            <span class="text-sm font-medium" :class="assignedAttempts.includes(2) ? 'text-slate-400 dark:text-slate-500 line-through' : 'text-slate-800 dark:text-slate-200'">
              2-я пересдача (Комиссия) <span v-if="assignedAttempts.includes(2)" class="text-xs ml-1">(Уже назначена)</span>
            </span>
          </label>

          <label class="flex items-center gap-3 p-2 rounded-lg transition-colors border border-transparent"
                 :class="assignedAttempts.includes(3) ? 'opacity-50 cursor-not-allowed grayscale' : 'cursor-pointer hover:bg-white dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-700'">
            <input type="radio" v-model="attemptNumber" :value="3" :disabled="assignedAttempts.includes(3)" class="w-4 h-4 text-indigo-600 disabled:cursor-not-allowed">
            <span class="text-sm font-bold" :class="assignedAttempts.includes(3) ? 'text-slate-400 dark:text-slate-500 line-through' : 'text-red-600 dark:text-red-400'">
              3-я пересдача (Комиссия) <span v-if="assignedAttempts.includes(3)" class="text-xs ml-1 font-medium text-slate-400 dark:text-slate-500">(Уже назначена)</span>
            </span>
          </label>
        </div>
      </div>
    </div>
    </div> <!-- end collapsible format wrapper -->

    <hr class="border-slate-100 dark:border-slate-700/50 my-6" />
    <!-- Step 4 header with mobile collapse -->
    <div class="flex items-center justify-between mb-4" :class="{'opacity-50 pointer-events-none': subjectBelongsToAnotherDept}">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shrink-0">4</div>
        <h3 class="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <Users class="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Состав комиссии
        </h3>
      </div>
      <button @click="sectionsCollapsed.commission = !sectionsCollapsed.commission" class="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
        <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.commission ? '-rotate-90' : ''" />
      </button>
    </div>
    <div :class="{ 'hidden md:block': sectionsCollapsed.commission }">
    <div class="mb-8" :class="{'opacity-50 pointer-events-none': subjectBelongsToAnotherDept}">

      <div v-if="mainTeacherLacksDept" class="mb-5 text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-900/20 p-4 rounded-xl border border-amber-200 dark:border-amber-800/50 flex items-start gap-3 transition-colors">
        <AlertTriangle class="w-5 h-5 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
        <div>
          <span class="font-bold block mb-0.5">Внимание: Кафедра не указана</span>
          У выбранного ведущего преподавателя не указана кафедра в системе. Назначьте её в панели администратора, чтобы система смогла сформировать список возможных председателей и членов комиссии.
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

        <div class="relative">
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Ведущий преподаватель <span v-if="availableMainTeachers.length === 0 && selectedSubject && !subjectBelongsToAnotherDept" class="text-red-500 text-xs ml-2">(Нет в истории)</span></label>
          <div @click="!selectedSubject ? null : showMainDropdown = !showMainDropdown" :class="['w-full min-h-[46px] rounded-lg border p-2 flex flex-wrap gap-1.5 items-center transition-colors', !selectedSubject ? 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 opacity-60 cursor-not-allowed' : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 cursor-pointer']">
            <span v-if="mainTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-1 text-sm">Выберите...</span>
            <span v-for="uuid in mainTeachers" :key="uuid" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-100 dark:bg-indigo-900/50 text-indigo-800 dark:text-indigo-300 text-sm font-medium">
              {{ formatShortName(availableMainTeachers.find(t => t.uuid === uuid)?.fullName) }}
              <X class="w-3.5 h-3.5 hover:text-indigo-900 dark:hover:text-white" @click.stop="removeMainTeacher(uuid)" />
            </span>
          </div>

          <div v-if="showMainDropdown" class="absolute z-20 w-full mt-1 max-h-64 flex flex-col bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-xl">
            <div class="p-2 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input type="text" v-model="mainSearchQuery" @click.stop placeholder="Поиск преподавателя..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:border-indigo-500 dark:text-white transition-colors" />
              </div>
            </div>
            <div class="overflow-y-auto flex-1">
              <label v-for="t in displayMainTeachers" :key="t.uuid" class="flex items-center px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b last:border-0 border-slate-100 dark:border-slate-700">
                <input type="checkbox" :value="t.uuid" v-model="mainTeachers" class="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 mr-3">
                <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
              </label>
              <div v-if="displayMainTeachers.length === 0" class="p-4 text-sm text-slate-500 text-center">Ничего не найдено</div>
            </div>
          </div>
          <div v-if="showMainDropdown" @click="showMainDropdown = false" class="fixed inset-0 z-10"></div>
        </div>

        <div class="relative">
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Председатель <span v-if="attemptNumber > 1" class="text-red-600 font-bold">*</span></label>
          <div @click="availableChairmen.length === 0 ? null : showChairmanDropdown = !showChairmanDropdown" :class="['w-full min-h-[46px] rounded-lg border p-2 flex flex-wrap gap-1.5 items-center transition-colors', availableChairmen.length === 0 ? 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 opacity-60 cursor-not-allowed' : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 cursor-pointer']">
            <span v-if="!chairmanTeacher" class="text-slate-400 dark:text-slate-500 pl-1 text-sm">Выберите...</span>
            <span v-else class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 text-sm font-medium border border-slate-300 dark:border-slate-600">
              {{ formatShortName(props.teachers.find(t => t.uuid === chairmanTeacher)?.fullName) }}
              <X class="w-3.5 h-3.5 hover:text-slate-900 dark:hover:text-white" @click.stop="chairmanTeacher = null" />
            </span>
          </div>

          <div v-if="showChairmanDropdown" class="absolute z-20 w-full mt-1 max-h-64 flex flex-col bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-xl">
            <div class="p-2 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input type="text" v-model="chairmanSearchQuery" @click.stop placeholder="Поиск председателя..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:border-indigo-500 dark:text-white transition-colors" />
              </div>
            </div>
            <div class="overflow-y-auto flex-1">
              <div v-for="t in displayChairmen" :key="t.uuid" @click="selectChairman(t.uuid)" class="flex items-center px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b last:border-0 border-slate-100 dark:border-slate-700">
                <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
              </div>
              <div v-if="displayChairmen.length === 0" class="p-4 text-sm text-slate-500 text-center">Ничего не найдено</div>
            </div>
          </div>
          <div v-if="showChairmanDropdown" @click="showChairmanDropdown = false" class="fixed inset-0 z-10"></div>
        </div>

        <div class="relative">
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Члены комиссии</label>
          <div @click="availableCommissionTeachers.length === 0 ? null : showCommDropdown = !showCommDropdown" :class="['w-full min-h-[46px] rounded-lg border p-2 flex flex-wrap gap-1.5 items-center transition-colors', availableCommissionTeachers.length === 0 ? 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 opacity-60 cursor-not-allowed' : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 cursor-pointer']">
            <span v-if="commissionTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-1 text-sm">Выберите...</span>
            <span v-for="uuid in commissionTeachers" :key="uuid" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-medium border border-slate-200 dark:border-slate-700">
              {{ formatShortName(availableCommissionTeachers.find(t => t.uuid === uuid)?.fullName) }}
              <X class="w-3.5 h-3.5 hover:text-red-600 dark:hover:text-red-400" @click.stop="removeCommTeacher(uuid)" />
            </span>
          </div>

          <div v-if="showCommDropdown" class="absolute z-20 w-full mt-1 max-h-64 flex flex-col bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-xl">
            <div class="p-2 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input type="text" v-model="commSearchQuery" @click.stop placeholder="Поиск по комиссии..." class="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:border-indigo-500 dark:text-white transition-colors" />
              </div>
            </div>
            <div class="overflow-y-auto flex-1">
              <label v-for="t in displayCommTeachers" :key="t.uuid" class="flex items-center px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b last:border-0 border-slate-100 dark:border-slate-700">
                <input type="checkbox" :value="t.uuid" v-model="commissionTeachers" class="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 mr-3">
                <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
              </label>
              <div v-if="displayCommTeachers.length === 0" class="p-4 text-sm text-slate-500 text-center">Ничего не найдено</div>
            </div>
          </div>
          <div v-if="showCommDropdown" @click="showCommDropdown = false" class="fixed inset-0 z-10"></div>
        </div>

      </div>
    </div>

    </div> <!-- end collapsible commission wrapper -->

    <div class="flex justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
      <button @click="submitRetake" :disabled="isSubmitting || subjectBelongsToAnotherDept" class="bg-slate-900 hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white font-medium py-3 px-8 rounded-xl shadow-sm flex items-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed">
        <div v-if="isSubmitting" class="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
        <CheckCircle v-else class="w-5 h-5" />
        Сохранить расписание
      </button>
    </div>
  </div>
</template>