<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Calendar, Clock, Users, CheckCircle, Search, ChevronDown, MapPin, Globe, X, AlertTriangle, Info, Trash2 } from 'lucide-vue-next';
import { addToast } from '../composables/useToast';
import { fetchBackendFromBrowser } from '../lib/backend-api';
import { cleanSubjectName, normalizeForCompare, fuzzyMatch } from '../lib/subjectNorm';

type GroupHistoryEntry = { subjectName: string; teacherNames: string[] };
type GroupRetake = { id: string; subjectUuid: string; attemptNumber: number; date: string; createdBy: string | null; canDelete: boolean };
type MergedDaySchedule = Record<string, { reason: string; details: { subject: string; type: string; location: string } } | null>;

const props = defineProps<{
  backendApiUrl: string;
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
  return props.groups.filter((g) => g.number.toLowerCase().includes(q)).slice(0, 50);
});

const selectGroup = (group: { uuid: string; number: string }) => {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
};

const groupHistory = ref<GroupHistoryEntry[]>([]);
const existingGroupRetakes = ref<GroupRetake[]>([]);

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
  const historyNames = groupHistory.value.map((item) => item.subjectName);
  const cleanedHistoryNames = historyNames.map((name) => normalizeForCompare(name));

  let matched = props.subjects.filter((subject) =>
    cleanedHistoryNames.some((historyName) => historyName === normalizeForCompare(subject.name)),
  );

  if (matched.length === 0) {
    matched = props.subjects.filter((subject) =>
      historyNames.some((historyName) => fuzzyMatch(historyName, subject.name)),
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

const loadGroupContext = async (groupUuid: string) => {
  const group = props.groups.find((item) => item.uuid === groupUuid);
  if (!group) return;

  try {
    const [history, retakes] = await Promise.all([
      fetchBackendFromBrowser<GroupHistoryEntry[]>(
        props.backendApiUrl,
        `/retakes/history/group/${encodeURIComponent(group.number)}`,
      ),
      fetchBackendFromBrowser<GroupRetake[]>(props.backendApiUrl, `/retakes/group/${groupUuid}`),
    ]);

    groupHistory.value = history;
    existingGroupRetakes.value = retakes;
  } catch (error) {
    addToast(error instanceof Error ? error.message : '�� ������� ��������� ������ ������', 'error');
  }
};

watch(selectedGroupUuid, async (newUuid) => {
  selectedSubject.value = '';
  groupHistory.value = [];
  existingGroupRetakes.value = [];
  mainTeachers.value = [];
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
  if (!newUuid) return;
  await loadGroupContext(newUuid);
});

const currentSubjectRetakes = computed(() => {
  if (!selectedSubject.value) return [];
  return existingGroupRetakes.value.filter((retake) => retake.subjectUuid === selectedSubject.value);
});

const assignedAttempts = computed(() => currentSubjectRetakes.value.map((retake) => Number(retake.attemptNumber)));

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

watch(showMainDropdown, (value) => { if (!value) mainSearchQuery.value = ''; });
watch(showChairmanDropdown, (value) => { if (!value) chairmanSearchQuery.value = ''; });
watch(showCommDropdown, (value) => { if (!value) commSearchQuery.value = ''; });

const allTeachersForSelectedSubject = computed(() => {
  if (!selectedSubject.value) return [];
  const subject = props.subjects.find((item) => item.uuid === selectedSubject.value);
  if (!subject) return [];
  const cleanedSubjectName = cleanSubjectName(subject.name);
  const historyRecords = groupHistory.value.filter((item) => cleanSubjectName(item.subjectName) === cleanedSubjectName);
  return historyRecords.flatMap((item) => item.teacherNames);
});

const subjectBelongsToAnotherDept = computed(() => {
  if (props.currentUser.role === 'ADMIN' || !selectedSubject.value) return false;
  const historyNames = allTeachersForSelectedSubject.value;
  if (historyNames.length === 0) return false;
  const teachersInHistory = props.teachers.filter((teacher) => historyNames.includes(teacher.fullName));
  if (teachersInHistory.length === 0) return false;
  const userDepts = props.currentUser.departmentIds || [];
  const sharesDept = teachersInHistory.some((teacher) => {
    const teacherDepts = teacher.departmentIds || [];
    return teacherDepts.some((id) => userDepts.includes(id));
  });
  return !sharesDept;
});

const availableMainTeachers = computed(() => {
  if (!selectedSubject.value || subjectBelongsToAnotherDept.value) return [];
  let filtered = props.teachers;
  const historyNames = allTeachersForSelectedSubject.value;

  if (historyNames.length > 0) {
    filtered = filtered.filter((teacher) => historyNames.includes(teacher.fullName));
  }

  if (props.currentUser.role !== 'ADMIN') {
    const userDepts = props.currentUser.departmentIds || [];
    filtered = filtered.filter((teacher) => {
      const teacherDepts = teacher.departmentIds || [];
      return teacherDepts.some((id) => userDepts.includes(id));
    });
  }

  return filtered;
});

const validCommissionPool = computed(() => {
  if (mainTeachers.value.length === 0) return [];
  const mainTeacher = props.teachers.find((teacher) => teacher.uuid === mainTeachers.value[0]);
  const mainDepts = mainTeacher?.departmentIds || [];
  if (mainDepts.length === 0) return [];
  return props.teachers.filter((teacher) => {
    const teacherDepts = teacher.departmentIds || [];
    return teacherDepts.some((id) => mainDepts.includes(id));
  });
});

const mainTeacherLacksDept = computed(() => {
  if (mainTeachers.value.length === 0) return false;
  const mainTeacher = props.teachers.find((teacher) => teacher.uuid === mainTeachers.value[0]);
  return !mainTeacher?.departmentIds || mainTeacher.departmentIds.length === 0;
});

const availableChairmen = computed(() => {
  return validCommissionPool.value.filter((teacher) => !mainTeachers.value.includes(teacher.uuid) && !commissionTeachers.value.includes(teacher.uuid));
});

const availableCommissionTeachers = computed(() => {
  return validCommissionPool.value.filter((teacher) => !mainTeachers.value.includes(teacher.uuid) && teacher.uuid !== chairmanTeacher.value);
});

const displayMainTeachers = computed(() => {
  const query = mainSearchQuery.value.toLowerCase();
  return query ? availableMainTeachers.value.filter((teacher) => teacher.fullName.toLowerCase().includes(query)) : availableMainTeachers.value;
});

const displayChairmen = computed(() => {
  const query = chairmanSearchQuery.value.toLowerCase();
  return query ? availableChairmen.value.filter((teacher) => teacher.fullName.toLowerCase().includes(query)) : availableChairmen.value;
});

const displayCommTeachers = computed(() => {
  const query = commSearchQuery.value.toLowerCase();
  return query ? availableCommissionTeachers.value.filter((teacher) => teacher.fullName.toLowerCase().includes(query)) : availableCommissionTeachers.value;
});

watch(selectedSubject, () => {
  mainTeachers.value = availableMainTeachers.value.map((teacher) => teacher.uuid);
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
});

const removeMainTeacher = (uuid: string) => {
  mainTeachers.value = mainTeachers.value.filter((id) => id !== uuid);
};

const removeCommTeacher = (uuid: string) => {
  commissionTeachers.value = commissionTeachers.value.filter((id) => id !== uuid);
};

const selectChairman = (uuid: string) => {
  chairmanTeacher.value = uuid;
  showChairmanDropdown.value = false;
};

const TIME_MAPPING: Record<number, string> = {
  1: '09:00-10:30',
  2: '10:40-12:10',
  3: '12:20-13:50',
  4: '14:30-16:00',
  5: '16:10-17:40',
  6: '17:50-19:20',
  7: '19:30-21:00',
};

const isLoadingSlots = ref(false);
const daySchedule = ref<MergedDaySchedule | null>(null);

watch([selectedDate, selectedGroupUuid, mainTeachers, commissionTeachers, chairmanTeacher], async () => {
  selectedSlots.value = [];
  daySchedule.value = null;

  if (selectedDate.value && selectedGroupUuid.value) {
    isLoadingSlots.value = true;
    const group = props.groups.find((item) => item.uuid === selectedGroupUuid.value);
    const allSelectedTeacherUuids = [...mainTeachers.value, ...commissionTeachers.value];
    if (chairmanTeacher.value) allSelectedTeacherUuids.push(chairmanTeacher.value);

    if (group) {
      try {
        daySchedule.value = await fetchBackendFromBrowser<MergedDaySchedule>(
          props.backendApiUrl,
          '/retakes/merged-day',
          {
            method: 'POST',
            body: JSON.stringify({
              groupNumber: group.number,
              groupUuid: group.uuid,
              teacherUuids: allSelectedTeacherUuids,
              date: selectedDate.value,
            }),
          },
        );
      } catch (error) {
        addToast(error instanceof Error ? error.message : '�� ������� ��������� ���������� �� ����', 'error');
      }
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
  if (subjectBelongsToAnotherDept.value) return addToast('��� ������� � ����������!', 'error');
  if (selectedSlots.value.length === 0 || mainTeachers.value.length === 0) return addToast('�������� ����� � �������� �������������!', 'error');
  if (attemptNumber.value > 1 && !chairmanTeacher.value) return addToast('��� 2-� � 3-� ������� ���������� ��������� ������������ ��������!', 'error');
  if (retakeFormat.value === 'offline' && !roomUuid.value) return addToast('������� ��������� ��� ���������� ���������', 'error');
  if (retakeFormat.value === 'online' && !onlineLink.value) return addToast('������� ������ �� �����������', 'error');
  if (assignedAttempts.value.includes(attemptNumber.value)) return addToast('��� ������� ��������� ��� ���������!', 'error');

  isSubmitting.value = true;

  try {
    const group = props.groups.find((item) => item.uuid === selectedGroupUuid.value);
    if (!group) throw new Error('������ �� �������');

    await fetchBackendFromBrowser(
      props.backendApiUrl,
      '/retakes',
      {
        method: 'POST',
        body: JSON.stringify({
          groupNumber: group.number,
          groupUuid: selectedGroupUuid.value,
          subjectUuid: selectedSubject.value,
          date: selectedDate.value,
          timeSlots: selectedSlots.value,
          roomUuid: retakeFormat.value === 'offline' ? roomUuid.value : undefined,
          link: retakeFormat.value === 'online' ? onlineLink.value : undefined,
          attemptNumber: attemptNumber.value,
          mainTeachersUuids: mainTeachers.value,
          commissionTeachersUuids: commissionTeachers.value,
          chairmanUuid: chairmanTeacher.value || undefined,
        }),
      },
    );

    await loadGroupContext(selectedGroupUuid.value);
    selectedSlots.value = [];
    selectedDate.value = '';
    addToast('��������� ������� ���������!', 'success');
    roomUuid.value = '';
    onlineLink.value = '';
    chairmanTeacher.value = null;
    commissionTeachers.value = [];
  } catch (error) {
    addToast(error instanceof Error ? error.message : '�� ������� ������� ���������', 'error');
  } finally {
    isSubmitting.value = false;
  }
};

const deleteRetake = async (id: string) => {
  if (!confirm('�� �������, ��� ������ ������� ��� ���������?')) return;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/retakes/${id}`, { method: 'DELETE' });
    addToast('��������� ��������', 'success');
    existingGroupRetakes.value = existingGroupRetakes.value.filter((item) => item.id !== id);
    selectedDate.value = '';
  } catch (error) {
    addToast(error instanceof Error ? error.message : '�� ������� ������� ���������', 'error');
  }
};
</script>

<template>
  <div class="relative z-10 rounded-[30px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_20px_70px_rgba(15,23,42,0.10)] overflow-hidden transition-colors">
    <!-- Header -->
    <div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-slate-100 dark:border-white/10 flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 via-red-600 to-blue-600 flex items-center justify-center shadow-[0_16px_40px_rgba(239,68,68,0.24)] shrink-0">
        <Calendar class="w-5 h-5 text-white" />
      </div>

      <div>
        <p class="text-[11px] uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold">
          Управление
        </p>
        <h2 class="mt-1 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white">
          Назначение пересдачи
        </h2>
        <p class="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          Заполните шаги для создания новой записи
        </p>
      </div>
    </div>

    <div class="p-5 sm:p-6 lg:p-7">
      <!-- Step 1 -->
      <div class="flex items-center gap-3 mb-4">
        <div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]">
          1
        </div>
        <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white">
          Группа, дисциплина и дата
        </h3>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <!-- Group -->
        <div class="relative">
          <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
            Группа
          </label>

          <div class="relative">
            <input
                v-model="groupSearchQuery"
                @focus="showGroupDropdown = true"
                @input="showGroupDropdown = true; selectedGroupUuid = ''"
                type="text"
                placeholder="Номер группы..."
                class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 pr-10 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all"
            />
            <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>

          <div
              v-if="showGroupDropdown && filteredGroups.length > 0"
              class="absolute z-20 w-full mt-2 max-h-60 overflow-y-auto bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)]"
          >
            <div
                v-for="g in filteredGroups"
                :key="g.uuid"
                @click="selectGroup(g)"
                class="px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer text-sm text-slate-700 dark:text-slate-200 font-semibold transition-colors"
            >
              {{ g.number }}
            </div>
          </div>

          <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
        </div>

        <!-- Subject -->
        <div>
          <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
            Дисциплина
          </label>

          <select
              v-model="selectedSubject"
              :disabled="!selectedGroupUuid || availableSubjects.length === 0"
              class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none disabled:opacity-50 transition-all"
          >
            <option value="" disabled>
              {{ availableSubjects.length === 0 ? 'Сначала выберите группу' : 'Выберите предмет...' }}
            </option>
            <option v-for="s in availableSubjects" :key="s.uuid" :value="s.uuid">
              {{ s.name }}
            </option>
          </select>

          <p
              v-if="subjectBelongsToAnotherDept"
              class="text-xs text-red-500 dark:text-red-400 font-medium mt-2 flex items-start gap-1.5"
          >
            <AlertTriangle class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            Дисциплина другой кафедры. Нет прав назначения.
          </p>
        </div>

        <!-- Date -->
        <div>
          <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
            Дата
          </label>

          <input
              type="date"
              v-model="selectedDate"
              :disabled="!selectedSubject"
              class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none disabled:opacity-50 [color-scheme:light] dark:[color-scheme:dark] transition-all"
          />
        </div>
      </div>

      <!-- Existing retakes -->
      <div
          v-if="currentSubjectRetakes.length > 0"
          class="mb-8 p-4 sm:p-5 rounded-[24px] bg-amber-50/80 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 flex items-start gap-3"
      >
        <Info class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />

        <div class="w-full">
          <h4 class="text-[11px] font-bold text-amber-800 dark:text-amber-400 uppercase tracking-[0.18em] mb-3">
            Уже назначенные пересдачи
          </h4>

          <div class="space-y-2">
            <div
                v-for="r in currentSubjectRetakes"
                :key="r.id"
                class="text-sm text-amber-900 dark:text-amber-100 flex items-center justify-between gap-3 bg-white/60 dark:bg-black/20 p-3 rounded-2xl border border-amber-200/60 dark:border-amber-500/10"
            >
              <div class="flex items-center gap-2 flex-wrap">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                <span>Попытка {{ r.attemptNumber }} — <span class="font-bold">{{ formatDate(r.date) }}</span></span>
              </div>

              <button
                  v-if="r.canDelete"
                  @click="deleteRetake(r.id)"
                  class="text-red-500 hover:text-red-700 dark:hover:text-red-400 p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  title="Удалить"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2 -->
      <div v-if="selectedDate && selectedGroupUuid" class="mb-8">
        <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]">
              2
            </div>
            <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Clock class="w-4 h-4 text-red-500" />
              Расписание на день
            </h3>
          </div>

          <button @click="sectionsCollapsed.slots = !sectionsCollapsed.slots" class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">
            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.slots ? '-rotate-90' : ''" />
          </button>
        </div>

        <div :class="{ 'hidden md:block': sectionsCollapsed.slots }">
          <div v-if="isLoadingSlots" class="flex items-center justify-center p-10 text-slate-500 dark:text-slate-400">
            <div class="w-5 h-5 rounded-full border-2 border-red-500 border-t-transparent animate-spin mr-3"></div>
            Загрузка расписания...
          </div>

          <div v-else-if="daySchedule" class="grid grid-cols-1 gap-3">
            <div
                v-for="slot in 7"
                :key="slot"
                @click="toggleSlot(slot)"
                :class="[
                'p-4 rounded-[22px] border flex flex-col md:flex-row justify-between md:items-center gap-3 transition-all select-none',
                daySchedule[slot.toString()]
                  ? 'bg-slate-50 dark:bg-black/10 border-slate-200 dark:border-white/10 opacity-70 cursor-not-allowed'
                  : selectedSlots.includes(slot)
                    ? 'bg-red-500 border-red-500 text-white shadow-[0_16px_40px_rgba(239,68,68,0.20)] cursor-pointer scale-[1.01]'
                    : 'bg-white dark:bg-white/[0.03] border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15 cursor-pointer hover:shadow-[0_14px_34px_rgba(15,23,42,0.08)]'
              ]"
            >
              <div class="flex items-center gap-4">
                <div
                    :class="[
                    'w-11 h-11 rounded-2xl flex items-center justify-center font-black text-base shrink-0',
                    selectedSlots.includes(slot) && !daySchedule[slot.toString()]
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-100 dark:bg-white/[0.05] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-white/10'
                  ]"
                >
                  {{ slot }}
                </div>

                <div>
                  <div
                      class="font-semibold text-sm"
                      :class="selectedSlots.includes(slot) && !daySchedule[slot.toString()] ? 'text-white' : 'text-slate-900 dark:text-slate-100'"
                  >
                    {{ TIME_MAPPING[slot] }}
                  </div>

                  <div v-if="daySchedule[slot.toString()]" class="mt-0.5 flex flex-col gap-0.5">
                    <div class="text-xs text-red-500 font-semibold flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-red-500 inline-block"></span>
                      {{ daySchedule[slot.toString()].reason }}
                    </div>

                    <div
                        v-if="daySchedule[slot.toString()].details"
                        class="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px] sm:max-w-xs md:max-w-md"
                    >
                      {{ daySchedule[slot.toString()].details.subject }}
                    </div>
                  </div>

                  <div
                      v-else
                      class="text-xs font-semibold mt-0.5 flex items-center gap-1"
                      :class="selectedSlots.includes(slot) ? 'text-red-100' : 'text-emerald-600 dark:text-emerald-500'"
                  >
                    <span class="w-1.5 h-1.5 rounded-full inline-block" :class="selectedSlots.includes(slot) ? 'bg-red-100' : 'bg-emerald-500'"></span>
                    {{ selectedSlots.includes(slot) ? 'Выбрано' : 'Свободно' }}
                  </div>
                </div>
              </div>

              <div v-if="daySchedule[slot.toString()]?.details" class="text-right text-xs">
                <div class="text-slate-500 dark:text-slate-400 font-medium">
                  {{ daySchedule[slot.toString()].details.type }}
                </div>
                <div class="font-medium text-slate-700 dark:text-slate-300 mt-0.5 truncate max-w-[220px]">
                  {{ daySchedule[slot.toString()].details.location }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]">
            3
          </div>
          <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white">
            Формат и попытка
          </h3>
        </div>

        <button @click="sectionsCollapsed.format = !sectionsCollapsed.format" class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">
          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.format ? '-rotate-90' : ''" />
        </button>
      </div>

      <div :class="{ 'hidden md:block': sectionsCollapsed.format }">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 p-5 sm:p-6 bg-slate-50/80 dark:bg-black/10 rounded-[24px] border border-slate-100 dark:border-white/10">
          <!-- Format -->
          <div>
            <h4 class="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-[0.18em]">
              Формат проведения
            </h4>

            <div class="flex gap-2 mb-3">
              <button
                  @click="retakeFormat = 'offline'"
                  :class="retakeFormat === 'offline'
                  ? 'bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]'
                  : 'bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15'"
                  class="flex-1 py-2.5 px-3 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all text-sm border"
              >
                <MapPin class="w-4 h-4" />
                Очно
              </button>

              <button
                  @click="retakeFormat = 'online'"
                  :class="retakeFormat === 'online'
                  ? 'bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]'
                  : 'bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15'"
                  class="flex-1 py-2.5 px-3 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all text-sm border"
              >
                <Globe class="w-4 h-4" />
                Онлайн
              </button>
            </div>

            <input
                v-if="retakeFormat === 'offline'"
                v-model="roomUuid"
                type="text"
                placeholder="Аудитория (А-414)"
                class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all"
            />

            <input
                v-else
                v-model="onlineLink"
                type="url"
                placeholder="Ссылка на подключение"
                class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all"
            />
          </div>

          <!-- Attempt -->
          <div>
            <h4 class="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-[0.18em]">
              Номер попытки
            </h4>

            <div class="flex flex-col gap-2">
              <label
                  v-for="n in 3"
                  :key="n"
                  class="flex items-center gap-3 p-3 rounded-2xl transition-all border"
                  :class="assignedAttempts.includes(n)
                  ? 'opacity-40 cursor-not-allowed border-transparent bg-slate-50 dark:bg-white/[0.03]'
                  : 'cursor-pointer border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] hover:border-slate-300 dark:hover:border-white/15'"
              >
                <input
                    type="radio"
                    v-model="attemptNumber"
                    :value="n"
                    :disabled="assignedAttempts.includes(n)"
                    class="w-4 h-4 text-red-500 disabled:cursor-not-allowed"
                />

                <span
                    class="text-sm font-semibold"
                    :class="[
                    assignedAttempts.includes(n)
                      ? 'text-slate-400 dark:text-slate-500 line-through'
                      : n === 3
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-slate-800 dark:text-slate-200'
                  ]"
                >
                  {{ n }}-я пересдача {{ n > 1 ? '(Комиссия)' : '' }}
                  <span v-if="assignedAttempts.includes(n)" class="text-xs ml-1 font-normal">(Назначена)</span>
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4 -->
      <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

      <div class="flex items-center justify-between mb-4" :class="{ 'opacity-40 pointer-events-none': subjectBelongsToAnotherDept }">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]">
            4
          </div>
          <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Users class="w-4 h-4 text-red-500" />
            Комиссия
          </h3>
        </div>

        <button @click="sectionsCollapsed.commission = !sectionsCollapsed.commission" class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">
          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.commission ? '-rotate-90' : ''" />
        </button>
      </div>

      <div :class="{ 'hidden md:block': sectionsCollapsed.commission }">
        <div class="mb-8" :class="{ 'opacity-40 pointer-events-none': subjectBelongsToAnotherDept }">
          <div
              v-if="mainTeacherLacksDept"
              class="mb-5 text-sm text-amber-800 dark:text-amber-200 bg-amber-50/80 dark:bg-amber-500/10 p-4 rounded-[22px] border border-amber-200 dark:border-amber-500/20 flex items-start gap-3"
          >
            <AlertTriangle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <span class="font-bold block mb-0.5">Кафедра не указана</span>
              Назначьте кафедру ведущему преподавателю в панели администратора для формирования состава комиссии.
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <!-- Main teacher -->
            <div class="relative">
              <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
                Ведущий
                <span v-if="availableMainTeachers.length === 0 && selectedSubject && !subjectBelongsToAnotherDept" class="text-red-500 normal-case tracking-normal">
                  (Нет в истории)
                </span>
              </label>

              <div
                  @click="!selectedSubject ? null : showMainDropdown = !showMainDropdown"
                  :class="[
                  'w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                  !selectedSubject
                    ? 'bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500'
                ]"
              >
                <span v-if="mainTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">
                  Выберите...
                </span>

                <span
                    v-for="uuid in mainTeachers"
                    :key="uuid"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-500/20 text-xs font-semibold"
                >
                  {{ formatShortName(availableMainTeachers.find(t => t.uuid === uuid)?.fullName) }}
                  <X class="w-3 h-3 hover:text-blue-900 dark:hover:text-white cursor-pointer" @click.stop="removeMainTeacher(uuid)" />
                </span>
              </div>

              <div
                  v-if="showMainDropdown"
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="mainSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <label
                      v-for="t in displayMainTeachers"
                      :key="t.uuid"
                      class="flex items-center px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"
                  >
                    <input type="checkbox" :value="t.uuid" v-model="mainTeachers" class="w-4 h-4 text-red-500 rounded border-slate-300 focus:ring-red-500 mr-3">
                    <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
                  </label>

                  <div v-if="displayMainTeachers.length === 0" class="p-4 text-sm text-slate-400 text-center">
                    Ничего не найдено
                  </div>
                </div>
              </div>

              <div v-if="showMainDropdown" @click="showMainDropdown = false" class="fixed inset-0 z-10"></div>
            </div>

            <!-- Chairman -->
            <div class="relative">
              <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
                Председатель
                <span v-if="attemptNumber > 1" class="text-red-500">*</span>
              </label>

              <div
                  @click="availableChairmen.length === 0 ? null : showChairmanDropdown = !showChairmanDropdown"
                  :class="[
                  'w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                  availableChairmen.length === 0
                    ? 'bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500'
                ]"
              >
                <span v-if="!chairmanTeacher" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">
                  Выберите...
                </span>

                <span
                    v-else
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/20 text-xs font-semibold"
                >
                  {{ formatShortName(props.teachers.find(t => t.uuid === chairmanTeacher)?.fullName) }}
                  <X class="w-3 h-3 hover:text-amber-900 dark:hover:text-white cursor-pointer" @click.stop="chairmanTeacher = null" />
                </span>
              </div>

              <div
                  v-if="showChairmanDropdown"
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="chairmanSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <div
                      v-for="t in displayChairmen"
                      :key="t.uuid"
                      @click="selectChairman(t.uuid)"
                      class="px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer text-sm text-slate-700 dark:text-slate-200 transition-colors"
                  >
                    {{ t.fullName }}
                  </div>

                  <div v-if="displayChairmen.length === 0" class="p-4 text-sm text-slate-400 text-center">
                    Ничего не найдено
                  </div>
                </div>
              </div>

              <div v-if="showChairmanDropdown" @click="showChairmanDropdown = false" class="fixed inset-0 z-10"></div>
            </div>

            <!-- Commission members -->
            <div class="relative">
              <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
                Члены комиссии
              </label>

              <div
                  @click="availableCommissionTeachers.length === 0 ? null : showCommDropdown = !showCommDropdown"
                  :class="[
                  'w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                  availableCommissionTeachers.length === 0
                    ? 'bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500'
                ]"
              >
                <span v-if="commissionTeachers.length === 0" class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm">
                  Выберите...
                </span>

                <span
                    v-for="uuid in commissionTeachers"
                    :key="uuid"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-white/[0.05] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-white/10 text-xs font-semibold"
                >
                  {{ formatShortName(availableCommissionTeachers.find(t => t.uuid === uuid)?.fullName) }}
                  <X class="w-3 h-3 hover:text-red-500 cursor-pointer" @click.stop="removeCommTeacher(uuid)" />
                </span>
              </div>

              <div
                  v-if="showCommDropdown"
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="commSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <label
                      v-for="t in displayCommTeachers"
                      :key="t.uuid"
                      class="flex items-center px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"
                  >
                    <input type="checkbox" :value="t.uuid" v-model="commissionTeachers" class="w-4 h-4 text-red-500 rounded border-slate-300 focus:ring-red-500 mr-3">
                    <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
                  </label>

                  <div v-if="displayCommTeachers.length === 0" class="p-4 text-sm text-slate-400 text-center">
                    Ничего не найдено
                  </div>
                </div>
              </div>

              <div v-if="showCommDropdown" @click="showCommDropdown = false" class="fixed inset-0 z-10"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="flex justify-end pt-6 border-t border-slate-100 dark:border-white/10">
        <button
            @click="submitRetake"
            :disabled="isSubmitting || subjectBelongsToAnotherDept"
            class="h-12 px-8 rounded-2xl bg-red-500 hover:bg-red-600 text-white font-black shadow-[0_16px_40px_rgba(239,68,68,0.24)] flex items-center gap-2 transition-all hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0"
        >
          <div v-if="isSubmitting" class="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
          <CheckCircle v-else class="w-5 h-5" />
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>


