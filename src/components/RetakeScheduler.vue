<script setup lang="ts">
import { nextTick, ref, watch, computed } from 'vue';
import { Calendar, Clock, Users, CheckCircle, Search, ChevronDown, MapPin, Globe, X, AlertTriangle, Info, Trash2, Pencil } from 'lucide-vue-next';
import { addToast } from '../composables/useToast';
import { BackendApiError, fetchBackendFromBrowser } from '../lib/backend-api';
import { cleanSubjectName } from '../lib/subjectNorm';
import {
  formatGroupValue,
  matchesGroupQuery,
  getNormalizedCursorIndex,
  getFormattedCursorIndex,
} from '../lib/groupFormat';

type GroupHistoryEntry = { subjectName: string; teacherNames: string[] };
type RetakeTeacher = { teacherUuid: string; fullName: string; role: string };
type GroupRetake = { id: string; subjectUuid: string; subjectName: string | null; attemptNumber: number; date: string; timeSlots: number[]; roomUuid: string | null; link: string | null; meetingId: string | null; departmentId: number | null; createdBy: string | null; canDelete: boolean; teachers: RetakeTeacher[] };
type MergedDaySchedule = Record<string, { reason: string; details: { subject: string; type: string; location: string } } | null>;
type RetakeSubjectOption = { uuid: string; name: string };
type RetakeMeeting = { id: string; departmentId: number | null; date: string; link: string | null; title: string | null; retakeCount: number };
type RetakeAttemptRule = { attemptNumber: number; requiresChairman: boolean; minCommissionMembers: number };
type FormContextScope = 'idle' | 'group' | 'subject' | 'teachers' | 'full';
type RetakeFormContext = {
  groupHistory: GroupHistoryEntry[];
  existingRetakes: GroupRetake[];
  availableSubjects: RetakeSubjectOption[];
  subjectBlockedReason: string | null;
  assignedAttempts: number[];
  nextAttemptNumber: number;
  availableMainTeacherUuids: string[];
  availableCommissionTeacherUuids: string[];
  availableChairmanUuids: string[];
  availableMeetings: RetakeMeeting[];
  attemptRules: RetakeAttemptRule[];
  departmentId: number | null;
  mainTeacherLacksDept: boolean;
};

function normalizeRetakeFormContext(raw: any): RetakeFormContext {
  return {
    groupHistory: (raw?.groupHistory ?? raw?.group_history ?? []).map((entry: any) => ({
      subjectName: entry?.subjectName ?? entry?.subject_name ?? '',
      teacherNames: entry?.teacherNames ?? entry?.teacher_names ?? [],
    })),
    existingRetakes: (raw?.existingRetakes ?? raw?.existing_retakes ?? []).map((retake: any) => ({
      id: retake?.id ?? '',
      subjectUuid: retake?.subjectUuid ?? retake?.subject_uuid ?? '',
      subjectName: retake?.subjectName ?? retake?.subject_name ?? null,
      attemptNumber: retake?.attemptNumber ?? retake?.attempt_number ?? 1,
      date: retake?.date ?? '',
      timeSlots: retake?.timeSlots ?? retake?.time_slots ?? [],
      roomUuid: retake?.roomUuid ?? retake?.room_uuid ?? null,
      link: retake?.link ?? null,
      meetingId: retake?.meetingId ?? retake?.meeting_id ?? null,
      departmentId: retake?.departmentId ?? retake?.department_id ?? null,
      createdBy: retake?.createdBy ?? retake?.created_by ?? null,
      canDelete: retake?.canDelete ?? retake?.can_delete ?? false,
      teachers: (retake?.teachers ?? []).map((teacher: any) => ({
        teacherUuid: teacher?.teacherUuid ?? teacher?.teacher_uuid ?? '',
        fullName: teacher?.fullName ?? teacher?.full_name ?? '',
        role: teacher?.role ?? '',
      })),
    })),
    availableSubjects: (raw?.availableSubjects ?? raw?.available_subjects ?? []).map((subject: any) => ({
      uuid: subject?.uuid ?? '',
      name: subject?.name ?? '',
    })),
    subjectBlockedReason: raw?.subjectBlockedReason ?? raw?.subject_blocked_reason ?? null,
    assignedAttempts: raw?.assignedAttempts ?? raw?.assigned_attempts ?? [],
    nextAttemptNumber: raw?.nextAttemptNumber ?? raw?.next_attempt_number ?? 1,
    availableMainTeacherUuids: raw?.availableMainTeacherUuids ?? raw?.available_main_teacher_uuids ?? [],
    availableCommissionTeacherUuids: raw?.availableCommissionTeacherUuids ?? raw?.available_commission_teacher_uuids ?? [],
    availableChairmanUuids: raw?.availableChairmanUuids ?? raw?.available_chairman_uuids ?? [],
    availableMeetings: (raw?.availableMeetings ?? raw?.available_meetings ?? []).map((meeting: any) => ({
      id: meeting?.id ?? '',
      departmentId: meeting?.departmentId ?? meeting?.department_id ?? null,
      date: meeting?.date ?? '',
      link: meeting?.link ?? null,
      title: meeting?.title ?? null,
      retakeCount: meeting?.retakeCount ?? meeting?.retake_count ?? 0,
    })),
    attemptRules: (raw?.attemptRules ?? raw?.attempt_rules ?? []).map((rule: any) => ({
      attemptNumber: rule?.attemptNumber ?? rule?.attempt_number ?? 1,
      requiresChairman: rule?.requiresChairman ?? rule?.requires_chairman ?? false,
      minCommissionMembers: rule?.minCommissionMembers ?? rule?.min_commission_members ?? 0,
    })),
    departmentId: raw?.departmentId ?? raw?.department_id ?? null,
    mainTeacherLacksDept: raw?.mainTeacherLacksDept ?? raw?.main_teacher_lacks_dept ?? false,
  };
}

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
const selectedMeetingId = ref('');
const availableMeetings = ref<RetakeMeeting[]>([]);
const editingMeetingId = ref<string | null>(null);
const editingMeetingLink = ref('');
const editingRetakeId = ref<string | null>(null);
const attemptNumber = ref(1);

const groupSearchQuery = ref('');
const selectedGroupUuid = ref('');
const showGroupDropdown = ref(false);
const showSubjectDropdown = ref(false);
const subjectSearchQuery = ref('');

const createEmptyFormContext = (): RetakeFormContext => ({
  groupHistory: [],
  existingRetakes: [],
  availableSubjects: [],
  subjectBlockedReason: null,
  assignedAttempts: [],
  nextAttemptNumber: 1,
  availableMainTeacherUuids: [],
  availableCommissionTeacherUuids: [],
  availableChairmanUuids: [],
  availableMeetings: [],
  attemptRules: [
    { attemptNumber: 1, requiresChairman: false, minCommissionMembers: 1 },
    { attemptNumber: 2, requiresChairman: true, minCommissionMembers: 0 },
    { attemptNumber: 3, requiresChairman: true, minCommissionMembers: 0 },
  ],
  departmentId: null,
  mainTeacherLacksDept: false,
});

const formContext = ref<RetakeFormContext>(createEmptyFormContext());
const isLoadingFormContext = ref(false);
const formContextError = ref<string | null>(null);
const hasLoadedFormContext = ref(false);
const formContextLoadScope = ref<FormContextScope>('idle');
const autoMainTeacherMessage = ref<string | null>(null);
let formContextRequestId = 0;
let suppressFormContextReload = false;

const filteredGroups = computed(() => {
  if (!groupSearchQuery.value) return props.groups.slice(0, 50);
  return props.groups.filter((group) => matchesGroupQuery(group.number, groupSearchQuery.value)).slice(0, 50);
});

const selectGroup = (group: { uuid: string; number: string }) => {
  selectedGroupUuid.value = group.uuid;
  groupSearchQuery.value = group.number;
  showGroupDropdown.value = false;
};

const handleGroupInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const normalizedCursorIndex = getNormalizedCursorIndex(input.value, input.selectionStart);
  const formatted = formatGroupValue(input.value);

  groupSearchQuery.value = formatted;
  selectedGroupUuid.value = '';
  showGroupDropdown.value = true;

  nextTick(() => {
    const cursorIndex = getFormattedCursorIndex(formatted, normalizedCursorIndex);
    input.setSelectionRange(cursorIndex, cursorIndex);
  });
};

const selectSubject = (subject: RetakeSubjectOption) => {
  if (editingRetakeId.value && subject.uuid !== selectedSubject.value) {
    addToast('Сначала отмените редактирование текущей пересдачи.', 'error');
    return;
  }
  selectedSubject.value = subject.uuid;
  showSubjectDropdown.value = false;
};

const groupHistory = computed(() => formContext.value.groupHistory);
const existingGroupRetakes = computed(() => formContext.value.existingRetakes);
const editingRetake = computed(() => existingGroupRetakes.value.find((retake) => retake.id === editingRetakeId.value) ?? null);
const isAttemptUnavailable = (attempt: number) => (
  assignedAttempts.value.includes(attempt) && editingRetake.value?.attemptNumber !== attempt
);

const sectionsCollapsed = ref({ slots: false, format: false, commission: false });

const formatShortName = (fullName?: string) => {
  if (!fullName) return '';
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 1) return parts[0];
  if (parts.length === 2) return `${parts[0]} ${parts[1][0]}.`;
  return `${parts[0]} ${parts[1][0]}.${parts[2][0]}.`;
};

const availableSubjects = computed(() =>
  [...formContext.value.availableSubjects]
    .map((subject) => ({ ...subject, name: cleanSubjectName(subject.name) }))
    .sort((a, b) => a.name.localeCompare(b.name, 'ru')),
);

const teachersByNormalizedName = computed(() => {
  const map = new Map<string, string[]>();
  props.teachers.forEach((teacher) => {
    const key = teacher.fullName.trim().toLowerCase();
    if (!key) return;
    const existing = map.get(key) ?? [];
    existing.push(teacher.uuid);
    map.set(key, existing);
  });
  return map;
});

const selectedSubjectOption = computed(() =>
  availableSubjects.value.find((subject) => subject.uuid === selectedSubject.value) ?? null,
);

const filteredAvailableSubjects = computed(() => {
  const query = subjectSearchQuery.value.toLowerCase().trim();
  if (!query) return availableSubjects.value;
  return availableSubjects.value.filter((subject) => subject.name.toLowerCase().includes(query));
});

const currentSubjectRetakes = computed(() => {
  if (!selectedSubject.value) return [];
  const selectedName = selectedSubjectOption.value?.name ? cleanSubjectName(selectedSubjectOption.value.name).toLowerCase() : '';
  if (!selectedName) {
    return existingGroupRetakes.value.filter((retake) => retake.subjectUuid === selectedSubject.value);
  }
  return existingGroupRetakes.value.filter((retake) => {
    const retakeName = retake.subjectName ? cleanSubjectName(retake.subjectName).toLowerCase() : '';
    return retakeName ? retakeName === selectedName : retake.subjectUuid === selectedSubject.value;
  });
});

const assignedAttempts = computed(() => formContext.value.assignedAttempts);

watch(assignedAttempts, (assigned) => {
  if (!assigned.includes(attemptNumber.value) || editingRetake.value?.attemptNumber === attemptNumber.value) return;
  attemptNumber.value = formContext.value.nextAttemptNumber;
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
watch(showSubjectDropdown, (value) => { if (!value) subjectSearchQuery.value = ''; });

const teachersByUuids = (uuids: string[]) => {
  const allowed = new Set(uuids);
  return props.teachers.filter((teacher) => allowed.has(teacher.uuid));
};

const subjectBelongsToAnotherDept = computed(() => !!formContext.value.subjectBlockedReason);
const availableMainTeachers = computed(() => teachersByUuids(formContext.value.availableMainTeacherUuids));
const availableChairmen = computed(() => teachersByUuids(formContext.value.availableChairmanUuids));
const availableCommissionTeachers = computed(() => teachersByUuids(formContext.value.availableCommissionTeacherUuids));
const mainTeacherLacksDept = computed(() => formContext.value.mainTeacherLacksDept);
const meetingOptions = computed(() => availableMeetings.value.length > 0 ? availableMeetings.value : formContext.value.availableMeetings);
const currentAttemptRule = computed(() => (
  formContext.value.attemptRules.find((rule) => rule.attemptNumber === attemptNumber.value)
  ?? { attemptNumber: attemptNumber.value, requiresChairman: attemptNumber.value > 1, minCommissionMembers: attemptNumber.value === 1 ? 1 : 0 }
));

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

const loadMeetingCandidates = async () => {
  if (retakeFormat.value !== 'online' || !selectedDate.value) {
    availableMeetings.value = [];
    selectedMeetingId.value = '';
    return;
  }

  const params = new URLSearchParams({ date: selectedDate.value });
  if (formContext.value.departmentId !== null) {
    params.set('department_id', String(formContext.value.departmentId));
  }

  try {
    availableMeetings.value = await fetchBackendFromBrowser<RetakeMeeting[]>(
      props.backendApiUrl,
      `/retakes/meetings?${params.toString()}`,
    );
  } catch {
    availableMeetings.value = [];
  }
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

const currentGroup = computed(() => props.groups.find((item) => item.uuid === selectedGroupUuid.value) ?? null);

const resetFormContext = () => {
  formContext.value = createEmptyFormContext();
};

const resetSubjectContext = () => {
  formContext.value = {
    ...formContext.value,
    subjectBlockedReason: null,
    assignedAttempts: [],
    nextAttemptNumber: 1,
    availableMainTeacherUuids: [],
    availableCommissionTeacherUuids: [],
    availableChairmanUuids: [],
    availableMeetings: [],
    attemptRules: formContext.value.attemptRules,
    departmentId: null,
    mainTeacherLacksDept: false,
  };
};

const mergeFormContext = (scope: FormContextScope, nextContext: RetakeFormContext) => {
  if (scope === 'group') {
    formContext.value = {
      ...formContext.value,
      groupHistory: nextContext.groupHistory,
      existingRetakes: nextContext.existingRetakes,
      availableSubjects: nextContext.availableSubjects,
    };
    return;
  }

  if (scope === 'subject') {
    formContext.value = {
      ...formContext.value,
      subjectBlockedReason: nextContext.subjectBlockedReason,
      assignedAttempts: nextContext.assignedAttempts,
      nextAttemptNumber: nextContext.nextAttemptNumber,
      availableMainTeacherUuids: nextContext.availableMainTeacherUuids,
      availableCommissionTeacherUuids: [],
      availableChairmanUuids: [],
      availableMeetings: [],
      attemptRules: nextContext.attemptRules,
      departmentId: null,
      mainTeacherLacksDept: false,
    };
    return;
  }

  if (scope === 'teachers') {
    formContext.value = {
      ...formContext.value,
      availableCommissionTeacherUuids: nextContext.availableCommissionTeacherUuids,
      availableChairmanUuids: nextContext.availableChairmanUuids,
      availableMeetings: nextContext.availableMeetings,
      attemptRules: nextContext.attemptRules,
      departmentId: nextContext.departmentId,
      mainTeacherLacksDept: nextContext.mainTeacherLacksDept,
    };
    return;
  }

  formContext.value = nextContext;
};

const formContextErrorText = (error: unknown) => (
  error instanceof BackendApiError
    ? error.detail
    : error instanceof Error
      ? error.message
      : 'Не удалось загрузить данные для формы пересдачи.'
);

const normalizeSelectedTeacherState = (context: RetakeFormContext) => {
  const allowedMain = new Set(context.availableMainTeacherUuids);
  const nextMain = mainTeachers.value.filter((uuid) => allowedMain.has(uuid));
  if (nextMain.length !== mainTeachers.value.length) {
    mainTeachers.value = nextMain;
    return true;
  }

  const allowedCommission = new Set(context.availableCommissionTeacherUuids);
  const nextCommission = commissionTeachers.value.filter((uuid) => allowedCommission.has(uuid));
  if (nextCommission.length !== commissionTeachers.value.length) {
    commissionTeachers.value = nextCommission;
    return true;
  }

  if (chairmanTeacher.value && !context.availableChairmanUuids.includes(chairmanTeacher.value)) {
    chairmanTeacher.value = null;
    return true;
  }

  return false;
};

const selectedSubjectKey = computed(() => {
  const subjectName = selectedSubjectOption.value?.name ?? '';
  return cleanSubjectName(subjectName).trim().toLowerCase();
});

const autoMainTeacherCandidateNames = (context: RetakeFormContext): string[] => {
  if (!selectedSubjectKey.value) {
    return [];
  }

  return [
    ...new Set(
      context.groupHistory
        .filter((entry) => cleanSubjectName(entry.subjectName).trim().toLowerCase() === selectedSubjectKey.value)
        .flatMap((entry) => entry.teacherNames.map((teacherName) => teacherName.trim()).filter(Boolean)),
    ),
  ];
};

const applyAutoMainTeachers = (context: RetakeFormContext, force = false) => {
  if (!selectedSubject.value || subjectBelongsToAnotherDept.value) {
    autoMainTeacherMessage.value = null;
    return;
  }

  const candidateNames = autoMainTeacherCandidateNames(context);
  if (candidateNames.length === 0) {
    autoMainTeacherMessage.value = 'Автоподстановка ведущего недоступна: в прошлом семестре для этой дисциплины преподаватель не найден.';
    if (force) {
      mainTeachers.value = [];
    }
    return;
  }

  const matchedTeacherUuids = [
    ...new Set(
      candidateNames.flatMap((teacherName) => teachersByNormalizedName.value.get(teacherName.toLowerCase()) ?? []),
    ),
  ];
  if (matchedTeacherUuids.length === 0) {
    autoMainTeacherMessage.value = 'Автоподстановка ведущего недоступна: преподаватель из прошлого семестра не найден в локальном справочнике.';
    if (force) {
      mainTeachers.value = [];
    }
    return;
  }

  const allowedMainTeachers = new Set(context.availableMainTeacherUuids);
  const suggestedTeacherUuids = matchedTeacherUuids.filter((uuid) => allowedMainTeachers.has(uuid));
  if (suggestedTeacherUuids.length === 0) {
    autoMainTeacherMessage.value = 'Автоподстановка ведущего недоступна: найденные преподаватели сейчас недоступны для выбора по текущим ограничениям.';
    if (force) {
      mainTeachers.value = [];
    }
    return;
  }

  if (force || mainTeachers.value.length === 0) {
    mainTeachers.value = suggestedTeacherUuids;
  }
  autoMainTeacherMessage.value = suggestedTeacherUuids.length === 1
    ? 'Ведущий преподаватель подставлен автоматически по данным прошлого семестра.'
    : 'Ведущие преподаватели подставлены автоматически по данным прошлого семестра.';
};

const loadFormContext = async (scope: FormContextScope = 'full') => {
  if (!currentGroup.value) {
    resetFormContext();
    formContextError.value = null;
    hasLoadedFormContext.value = false;
    isLoadingFormContext.value = false;
    formContextLoadScope.value = 'idle';
    return;
  }

  const requestId = ++formContextRequestId;
  isLoadingFormContext.value = true;
  formContextLoadScope.value = scope;
  formContextError.value = null;

  try {
    const rawContext = await fetchBackendFromBrowser<any>(
      props.backendApiUrl,
      '/retakes/form-context',
      {
        method: 'POST',
        body: JSON.stringify({
          groupUuid: currentGroup.value.uuid,
          groupNumber: currentGroup.value.number,
          subjectUuid: selectedSubject.value || undefined,
          mainTeacherUuids: mainTeachers.value,
          commissionTeacherUuids: commissionTeachers.value,
          chairmanUuid: chairmanTeacher.value || undefined,
          includeGroupData: scope === 'group' || scope === 'full',
          includeSubjectData: scope === 'subject' || scope === 'full',
          includeTeacherData: scope === 'teachers' || scope === 'full',
        }),
      },
    );

    if (requestId !== formContextRequestId) {
      return;
    }

    const nextContext = normalizeRetakeFormContext(rawContext);

    mergeFormContext(scope, nextContext);
    hasLoadedFormContext.value = true;

    if ((scope === 'teachers' || scope === 'full') && !editingRetakeId.value) {
      normalizeSelectedTeacherState(formContext.value);
    }

    if ((scope === 'subject' || scope === 'full') && selectedSubject.value && !editingRetakeId.value) {
      applyAutoMainTeachers(formContext.value, scope === 'subject');
    }

    if (
      (scope === 'subject' || scope === 'full')
      && (isAttemptUnavailable(attemptNumber.value) || attemptNumber.value < 1 || attemptNumber.value > 3)
    ) {
      attemptNumber.value = formContext.value.nextAttemptNumber;
    }
  } catch (error) {
    if (requestId !== formContextRequestId) {
      return;
    }

    formContextError.value = formContextErrorText(error);
    hasLoadedFormContext.value = false;
    addToast(formContextError.value, 'error');
  } finally {
    if (requestId === formContextRequestId) {
      isLoadingFormContext.value = false;
      formContextLoadScope.value = 'idle';
    }
  }
};

watch(selectedGroupUuid, async (newUuid, oldUuid) => {
  if (!newUuid) {
    showSubjectDropdown.value = false;
    resetFormContext();
    formContextError.value = null;
    hasLoadedFormContext.value = false;
    isLoadingFormContext.value = false;
    return;
  }

  if (newUuid === oldUuid) {
    return;
  }

  suppressFormContextReload = true;
  showSubjectDropdown.value = false;
  showMainDropdown.value = false;
  showCommDropdown.value = false;
  showChairmanDropdown.value = false;
  selectedSubject.value = '';
  mainTeachers.value = [];
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
  selectedSlots.value = [];
  daySchedule.value = null;
  autoMainTeacherMessage.value = null;
  editingRetakeId.value = null;
  resetFormContext();
  formContextError.value = null;
  hasLoadedFormContext.value = false;

  try {
    await loadFormContext('group');
  } finally {
    suppressFormContextReload = false;
  }
});

watch(selectedSubject, async () => {
  if (suppressFormContextReload || !selectedGroupUuid.value) return;

  showMainDropdown.value = false;
  showCommDropdown.value = false;
  showChairmanDropdown.value = false;
  mainTeachers.value = [];
  commissionTeachers.value = [];
  chairmanTeacher.value = null;
  selectedSlots.value = [];
  daySchedule.value = null;
  autoMainTeacherMessage.value = null;
  resetSubjectContext();

  if (!selectedSubject.value) {
    return;
  }

  await loadFormContext('subject');
});

watch(
  [
    () => mainTeachers.value.join(','),
    () => commissionTeachers.value.join(','),
    chairmanTeacher,
  ],
  async () => {
    if (suppressFormContextReload || !selectedGroupUuid.value || !selectedSubject.value) return;
    await loadFormContext('teachers');
  },
);

watch([selectedDate, selectedGroupUuid, () => mainTeachers.value.join(','), () => commissionTeachers.value.join(','), chairmanTeacher, editingRetakeId], async () => {
  selectedSlots.value = [];
  daySchedule.value = null;

  if (selectedDate.value && selectedGroupUuid.value) {
    isLoadingSlots.value = true;
    const group = props.groups.find((item) => item.uuid === selectedGroupUuid.value);
    const allSelectedTeacherUuids = [...commissionTeachers.value];
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
              excludeRetakeId: editingRetakeId.value || undefined,
            }),
          },
        );
      } catch (error) {
        addToast(error instanceof Error ? error.message : 'Не удалось загрузить занятость на день.', 'error');
      }
    }

    isLoadingSlots.value = false;
  }
});

watch([selectedDate, retakeFormat, () => formContext.value.departmentId], loadMeetingCandidates);

watch(selectedMeetingId, (value) => {
  if (value) onlineLink.value = '';
});

const toggleSlot = (slot: number) => {
  if (daySchedule.value && daySchedule.value[slot.toString()] !== null && !selectedSlots.value.includes(slot)) return;
  const index = selectedSlots.value.indexOf(slot);
  if (index === -1) selectedSlots.value.push(slot);
  else selectedSlots.value.splice(index, 1);
  selectedSlots.value.sort();
};

const resetRetakeDraft = () => {
  selectedSlots.value = [];
  selectedDate.value = '';
  roomUuid.value = '';
  onlineLink.value = '';
  selectedMeetingId.value = '';
  chairmanTeacher.value = null;
  commissionTeachers.value = [];
};

const cancelRetakeEdit = () => {
  editingRetakeId.value = null;
  resetRetakeDraft();
  attemptNumber.value = formContext.value.nextAttemptNumber;
};

const startEditRetake = async (retake: GroupRetake) => {
  if (!retake.canDelete) return;

  suppressFormContextReload = true;
  editingRetakeId.value = retake.id;
  selectedSubject.value = retake.subjectUuid;
  selectedDate.value = retake.date;
  selectedSlots.value = [...retake.timeSlots].sort();
  attemptNumber.value = retake.attemptNumber;
  mainTeachers.value = retake.teachers.filter((teacher) => teacher.role === 'MAIN').map((teacher) => teacher.teacherUuid);
  commissionTeachers.value = retake.teachers.filter((teacher) => teacher.role === 'COMMISSION').map((teacher) => teacher.teacherUuid);
  chairmanTeacher.value = retake.teachers.find((teacher) => teacher.role === 'CHAIRMAN')?.teacherUuid ?? null;
  retakeFormat.value = retake.roomUuid ? 'offline' : 'online';
  roomUuid.value = retake.roomUuid ?? '';
  selectedMeetingId.value = retake.meetingId ?? '';
  onlineLink.value = retake.meetingId ? '' : retake.link ?? '';
  autoMainTeacherMessage.value = null;

  try {
    await loadFormContext('full');
    await loadMeetingCandidates();
  } finally {
    suppressFormContextReload = false;
    selectedSlots.value = [...retake.timeSlots].sort();
  }
};

const submitRetake = async () => {
  if (subjectBelongsToAnotherDept.value) return addToast(formContext.value.subjectBlockedReason || 'Нет прав назначения.', 'error');
  if (selectedSlots.value.length === 0 || mainTeachers.value.length === 0) return addToast('Выберите пары и ведущих преподавателей.', 'error');
  if (currentAttemptRule.value.requiresChairman && !chairmanTeacher.value) return addToast('Для выбранной попытки нужно выбрать председателя комиссии.', 'error');
  if (commissionTeachers.value.length < currentAttemptRule.value.minCommissionMembers) {
    return addToast(`Для выбранной попытки нужно выбрать членов комиссии: минимум ${currentAttemptRule.value.minCommissionMembers}.`, 'error');
  }
  if (retakeFormat.value === 'offline' && !roomUuid.value) return addToast('Укажите аудиторию для очного формата.', 'error');
  if (isAttemptUnavailable(attemptNumber.value)) return addToast('Эта попытка пересдачи уже назначена.', 'error');

  isSubmitting.value = true;

  try {
    const group = props.groups.find((item) => item.uuid === selectedGroupUuid.value);
    if (!group) throw new Error('Группа не найдена.');

    const isEditing = !!editingRetakeId.value;
    await fetchBackendFromBrowser(
      props.backendApiUrl,
      isEditing ? `/retakes/${editingRetakeId.value}` : '/retakes',
      {
        method: isEditing ? 'PATCH' : 'POST',
        body: JSON.stringify({
          groupNumber: group.number,
          groupUuid: selectedGroupUuid.value,
          subjectUuid: selectedSubject.value,
          date: selectedDate.value,
          timeSlots: selectedSlots.value,
          roomUuid: retakeFormat.value === 'offline' ? roomUuid.value : undefined,
          link: retakeFormat.value === 'online' && !selectedMeetingId.value ? onlineLink.value || undefined : undefined,
          meetingId: retakeFormat.value === 'online' && selectedMeetingId.value ? selectedMeetingId.value : undefined,
          isOnline: retakeFormat.value === 'online',
          attemptNumber: attemptNumber.value,
          mainTeacherUuids: mainTeachers.value,
          commissionTeacherUuids: commissionTeachers.value,
          chairmanUuid: chairmanTeacher.value || undefined,
        }),
      },
    );

    const successMessage = isEditing
      ? 'Пересдача успешно обновлена.'
      : 'Пересдача успешно назначена.';
    editingRetakeId.value = null;
    await loadFormContext('full');
    resetRetakeDraft();
    addToast(successMessage, 'success');
  } catch (error) {
    addToast(error instanceof Error ? error.message : 'Не удалось сохранить пересдачу.', 'error');
  } finally {
    isSubmitting.value = false;
  }
};

const deleteRetake = async (id: string) => {
  if (!confirm('Вы уверены, что хотите удалить эту пересдачу?')) return;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/retakes/${id}`, { method: 'DELETE' });
    addToast('Пересдача удалена.', 'success');
    if (editingRetakeId.value === id) {
      editingRetakeId.value = null;
      resetRetakeDraft();
    }
    await loadFormContext('full');
    selectedDate.value = '';
  } catch (error) {
    addToast(error instanceof Error ? error.message : 'Не удалось удалить пересдачу.', 'error');
  }
};

const startEditMeetingLink = (retake: GroupRetake) => {
  if (!retake.meetingId) return;
  editingMeetingId.value = retake.meetingId;
  editingMeetingLink.value = retake.link ?? '';
};

const saveMeetingLink = async () => {
  if (!editingMeetingId.value) return;
  try {
    await fetchBackendFromBrowser(
      props.backendApiUrl,
      `/retakes/meetings/${editingMeetingId.value}`,
      {
        method: 'PATCH',
        body: JSON.stringify({ link: editingMeetingLink.value || null }),
      },
    );
    addToast('Ссылка обновлена для всех пересдач этой встречи.', 'success');
    editingMeetingId.value = null;
    editingMeetingLink.value = '';
    await loadFormContext('full');
    await loadMeetingCandidates();
  } catch (error) {
    addToast(error instanceof Error ? error.message : 'Не удалось обновить ссылку.', 'error');
  }
};
</script>

<template>
  <div class="relative z-10 rounded-[24px] border border-[var(--panel-border)] bg-[var(--panel-bg)] shadow-[var(--panel-shadow)] overflow-hidden transition-colors">
    <!-- Header -->
    <div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-[var(--panel-border)] flex items-center gap-4">
      <div class="w-12 h-12 rounded-[16px] bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] flex items-center justify-center shrink-0">
        <Calendar class="w-5 h-5 text-[var(--accent-strong)]" />
      </div>

      <div>
        <p class="academic-kicker">
          Управление
        </p>
        <h2 class="mt-1 text-xl sm:text-2xl academic-title text-slate-950 dark:text-white">
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
        <div class="w-8 h-8 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center text-xs font-black shrink-0">
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
                :value="groupSearchQuery"
                @focus="showGroupDropdown = true"
                @input="handleGroupInput"
                type="text"
                placeholder="Номер группы..."
                class="w-full h-12 rounded-2xl border border-[var(--panel-border)] focus:border-[var(--accent)] px-4 pr-10 text-sm font-semibold bg-[var(--panel-bg-strong)] dark:text-white outline-none transition-all"
            />
            <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>

          <div
              v-if="showGroupDropdown && filteredGroups.length > 0"
              class="absolute z-20 w-full mt-2 max-h-60 overflow-y-auto bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] rounded-[20px] shadow-[var(--panel-shadow)]"
          >
            <div
                v-for="g in filteredGroups"
                :key="g.uuid"
                @click="selectGroup(g)"
                class="px-4 py-3 hover:bg-[var(--panel-muted)] cursor-pointer text-sm text-slate-700 dark:text-slate-200 font-semibold transition-colors"
            >
              {{ g.number }}
            </div>
          </div>

          <div v-if="showGroupDropdown" @click="showGroupDropdown = false" class="fixed inset-0 z-10"></div>
        </div>

        <!-- Subject -->
        <div class="relative">
          <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
            Дисциплина
          </label>

          <button
              type="button"
              :disabled="!selectedGroupUuid || isLoadingFormContext"
              @click="(!selectedGroupUuid || isLoadingFormContext) ? null : showSubjectDropdown = !showSubjectDropdown"
              class="w-full h-12 rounded-2xl border border-[var(--panel-border)] focus:border-[var(--accent)] px-4 text-sm bg-[var(--panel-bg-strong)] dark:text-white outline-none disabled:opacity-50 transition-all flex items-center justify-between gap-3 text-left"
          >
            <span
                class="truncate"
                :class="selectedSubjectOption ? 'text-slate-900 dark:text-white font-medium' : 'text-slate-400 dark:text-slate-500'"
            >
              {{
                selectedSubjectOption?.name
                  ?? (isLoadingFormContext
                    ? 'Загружаем дисциплины...'
                    : (!selectedGroupUuid ? 'Сначала выберите группу' : 'Выберите дисциплину'))
              }}
            </span>
            <div class="flex items-center gap-2 shrink-0">
              <div
                  v-if="isLoadingFormContext"
                  class="w-4 h-4 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin"
              ></div>
              <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="showSubjectDropdown ? 'rotate-180' : ''" />
            </div>
          </button>

          <div
              v-if="showSubjectDropdown"
                  class="absolute z-20 w-full mt-2 max-h-72 flex flex-col bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] rounded-[20px] shadow-[var(--panel-shadow)] overflow-hidden"
          >
            <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                    v-model="subjectSearchQuery"
                    type="text"
                    @click.stop
                    placeholder="Поиск дисциплины..."
                    class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-[var(--accent)] dark:text-white transition-colors"
                />
              </div>
            </div>

            <div class="overflow-y-auto flex-1">
              <button
                  v-for="subject in filteredAvailableSubjects"
                  :key="subject.uuid"
                  type="button"
                  @click="selectSubject(subject)"
                  class="w-full px-4 py-3 text-left hover:bg-[var(--panel-muted)] transition-colors flex items-center justify-between gap-3"
              >
                <span class="text-sm text-slate-700 dark:text-slate-200">{{ subject.name }}</span>
                <CheckCircle v-if="selectedSubject === subject.uuid" class="w-4 h-4 text-[var(--accent-strong)] shrink-0" />
              </button>

              <div v-if="filteredAvailableSubjects.length === 0" class="p-4 text-sm text-slate-400 text-center">
                {{ isLoadingFormContext ? 'Загружаем дисциплины...' : 'По вашему запросу ничего не найдено.' }}
              </div>
            </div>
          </div>

          <div v-if="showSubjectDropdown" @click="showSubjectDropdown = false" class="fixed inset-0 z-10"></div>

          <p
              v-if="subjectBelongsToAnotherDept"
              class="text-xs text-red-500 dark:text-red-400 font-medium mt-2 flex items-start gap-1.5"
          >
            <AlertTriangle class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {{ formContext.subjectBlockedReason }}
          </p>
          <p
              v-else-if="selectedGroupUuid && isLoadingFormContext && formContextLoadScope === 'group'"
              class="text-xs text-slate-500 dark:text-slate-400 font-medium mt-2 flex items-start gap-1.5"
          >
            <Info class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            Загружаем дисциплины и историю группы...
          </p>
          <p
              v-else-if="selectedSubject && isLoadingFormContext && formContextLoadScope === 'subject'"
              class="text-xs text-slate-500 dark:text-slate-400 font-medium mt-2 flex items-start gap-1.5"
          >
            <Info class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            Проверяем попытки и ведущего по данным прошлого семестра...
          </p>
          <p
              v-else-if="formContextError"
              class="text-xs text-red-500 dark:text-red-400 font-medium mt-2 flex items-start gap-1.5"
          >
            <AlertTriangle class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {{ formContextError }}
          </p>
          <p
              v-else-if="selectedGroupUuid && hasLoadedFormContext && availableSubjects.length === 0"
              class="text-xs text-amber-600 dark:text-amber-300 font-medium mt-2 flex items-start gap-1.5"
          >
            <Info class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {{ groupHistory.length === 0
              ? 'Для выбранной группы нет данных прошлого семестра. Загрузите schedules.json или проверьте локальный архив прошлого семестра.'
              : 'Для выбранной группы есть данные прошлого семестра, но дисциплины не удалось сопоставить с доступными сущностями. Список должен строиться из прошлого семестра, поэтому проверьте сопоставление дисциплин без подмены источника на live API.' }}
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
              class="w-full h-12 rounded-2xl border border-[var(--panel-border)] focus:border-[var(--accent)] px-4 text-sm bg-[var(--panel-bg-strong)] dark:text-white outline-none disabled:opacity-50 [color-scheme:light] dark:[color-scheme:dark] transition-all"
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
                <span v-if="r.link" class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">ссылка указана</span>
                <span v-else-if="r.meetingId" class="text-xs font-semibold text-amber-700 dark:text-amber-300">ссылка не указана</span>
              </div>

              <div class="flex items-center gap-2">
                <button
                    v-if="r.canDelete"
                    @click="startEditRetake(r)"
                    class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white p-2 rounded-xl hover:bg-white/70 dark:hover:bg-white/10 transition-colors"
                    title="Редактировать"
                >
                  <Pencil class="w-4 h-4" />
                </button>
                <button
                    v-if="r.meetingId"
                    @click="startEditMeetingLink(r)"
                    class="text-[var(--accent-strong)] hover:underline text-xs font-bold"
                >
                  Ссылка
                </button>
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

          <div
              v-if="editingMeetingId"
              class="mt-3 flex flex-col gap-2 rounded-2xl border border-amber-200/70 bg-white/70 p-3 dark:border-amber-500/10 dark:bg-black/20 sm:flex-row"
          >
            <input
                v-model="editingMeetingLink"
                type="url"
                placeholder="Ссылка на подключение"
                class="min-w-0 flex-1 rounded-xl border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)] dark:text-white"
            />
            <button
                @click="saveMeetingLink"
                class="rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>

      <div class="scheduler-flow">
      <!-- Step 2 -->
      <div v-if="selectedDate && selectedGroupUuid" class="mb-8 scheduler-step scheduler-step-slots">
        <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center text-xs font-black shrink-0">
              3
            </div>
            <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Clock class="w-4 h-4 text-[var(--accent-strong)]" />
              Расписание на день
            </h3>
          </div>

          <button @click="sectionsCollapsed.slots = !sectionsCollapsed.slots" class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">
            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" :class="sectionsCollapsed.slots ? '-rotate-90' : ''" />
          </button>
        </div>

        <div :class="{ 'hidden md:block': sectionsCollapsed.slots }">
          <div v-if="isLoadingSlots" class="flex items-center justify-center p-10 text-slate-500 dark:text-slate-400">
            <div class="w-5 h-5 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin mr-3"></div>
            Загрузка расписания...
          </div>

          <div v-else-if="daySchedule" class="grid grid-cols-1 gap-3">
            <div
                v-for="slot in 7"
                :key="slot"
                @click="toggleSlot(slot)"
                :class="[
                'p-4 rounded-[22px] border flex flex-col md:flex-row justify-between md:items-center gap-3 transition-all select-none',
                selectedSlots.includes(slot)
                  ? 'bg-slate-900 border-slate-900 text-white dark:bg-white dark:border-white dark:text-slate-900 cursor-pointer'
                  : daySchedule[slot.toString()]
                  ? 'bg-slate-50 dark:bg-black/10 border-slate-200 dark:border-white/10 opacity-70 cursor-not-allowed'
                  : 'bg-white dark:bg-white/[0.03] border-slate-200 dark:border-white/10 hover:border-[var(--panel-border-strong)] cursor-pointer'
              ]"
            >
              <div class="flex items-center gap-4">
                <div
                    :class="[
                    'w-11 h-11 rounded-2xl flex items-center justify-center font-black text-base shrink-0',
                    selectedSlots.includes(slot)
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-100 dark:bg-white/[0.05] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-white/10'
                  ]"
                >
                  {{ slot }}
                </div>

                <div>
                  <div
                      class="font-semibold text-sm"
                      :class="selectedSlots.includes(slot) ? 'text-white dark:text-slate-900' : 'text-slate-900 dark:text-slate-100'"
                  >
                    {{ TIME_MAPPING[slot] }}
                  </div>

                  <div v-if="daySchedule[slot.toString()]" class="mt-0.5 flex flex-col gap-0.5">
                    <div class="text-xs text-[var(--danger)] font-semibold flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-[var(--danger)] inline-block"></span>
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
                      :class="selectedSlots.includes(slot) ? 'text-white/80 dark:text-slate-700' : 'text-emerald-600 dark:text-emerald-500'"
                  >
                    <span class="w-1.5 h-1.5 rounded-full inline-block" :class="selectedSlots.includes(slot) ? 'bg-white/80 dark:bg-slate-700' : 'bg-emerald-500'"></span>
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

      <div class="scheduler-step scheduler-step-format">
      <!-- Step 3 -->
      <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center text-xs font-black shrink-0">
            4
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
                  ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white'
                  : 'bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-[var(--panel-border-strong)]'"
                  class="flex-1 py-2.5 px-3 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all text-sm border"
              >
                <MapPin class="w-4 h-4" />
                Очно
              </button>

              <button
                  @click="retakeFormat = 'online'"
                  :class="retakeFormat === 'online'
                  ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 dark:border-white'
                  : 'bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-[var(--panel-border-strong)]'"
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
                class="w-full h-12 rounded-2xl border border-[var(--panel-border)] focus:border-[var(--accent)] px-4 text-sm bg-[var(--panel-bg-strong)] dark:text-white outline-none transition-all"
            />

            <input
                v-else
                v-model="onlineLink"
                :disabled="!!selectedMeetingId"
                type="url"
                placeholder="Ссылка на подключение (можно добавить позже)"
                class="w-full h-12 rounded-2xl border border-[var(--panel-border)] focus:border-[var(--accent)] px-4 text-sm bg-[var(--panel-bg-strong)] dark:text-white outline-none transition-all"
            />

            <div v-if="retakeFormat === 'online' && meetingOptions.length > 0" class="mt-3">
              <label class="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                Общая ссылка
              </label>
              <select
                  v-model="selectedMeetingId"
                  class="h-12 w-full rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] px-4 text-sm outline-none focus:border-[var(--accent)] dark:text-white"
              >
                <option value="">Создать отдельную встречу</option>
                <option v-for="meeting in meetingOptions" :key="meeting.id" :value="meeting.id">
                  {{ meeting.link || 'Ссылка будет добавлена позже' }} · {{ meeting.retakeCount }} пересд.
                </option>
              </select>
            </div>
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
                  :class="isAttemptUnavailable(n)
                  ? 'opacity-40 cursor-not-allowed border-transparent bg-slate-50 dark:bg-white/[0.03]'
                  : 'cursor-pointer border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] hover:border-slate-300 dark:hover:border-white/15'"
              >
                <input
                    type="radio"
                    v-model="attemptNumber"
                    :value="n"
                    :disabled="isAttemptUnavailable(n)"
                    class="w-4 h-4 text-[var(--accent)] disabled:cursor-not-allowed"
                />

                <span
                    class="text-sm font-semibold"
                    :class="[
                    isAttemptUnavailable(n)
                      ? 'text-slate-400 dark:text-slate-500 line-through'
                      : n === 3
                        ? 'text-[var(--accent-strong)]'
                        : 'text-slate-800 dark:text-slate-200'
                  ]"
                >
                  {{ n }}-я пересдача {{ (formContext.attemptRules.find(rule => rule.attemptNumber === n)?.requiresChairman || (formContext.attemptRules.find(rule => rule.attemptNumber === n)?.minCommissionMembers ?? 0) > 0) ? '(Комиссия)' : '' }}
                  <span v-if="isAttemptUnavailable(n)" class="text-xs ml-1 font-normal">(Назначена)</span>
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      </div>

      <div class="scheduler-step scheduler-step-commission">
      <!-- Step 4 -->
      <div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div>

      <div class="flex items-center justify-between mb-4" :class="{ 'opacity-40 pointer-events-none': subjectBelongsToAnotherDept }">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center text-xs font-black shrink-0">
            2
          </div>
          <h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Users class="w-4 h-4 text-[var(--accent-strong)]" />
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
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-[var(--panel-border-strong)]'
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
                  {{ formatShortName(availableMainTeachers.find(t => t.uuid === uuid)?.fullName ?? props.teachers.find(t => t.uuid === uuid)?.fullName) }}
                  <X class="w-3 h-3 hover:text-blue-900 dark:hover:text-white cursor-pointer" @click.stop="removeMainTeacher(uuid)" />
                </span>
              </div>

              <div
                  v-if="showMainDropdown"
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] rounded-[20px] shadow-[var(--panel-shadow)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="mainSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-[var(--accent)] dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <label
                      v-for="t in displayMainTeachers"
                      :key="t.uuid"
                      class="flex items-center px-4 py-3 hover:bg-[var(--panel-muted)] cursor-pointer transition-colors"
                  >
                    <input type="checkbox" :value="t.uuid" v-model="mainTeachers" class="w-4 h-4 text-[var(--accent)] rounded border-slate-300 focus:ring-[var(--accent)] mr-3">
                    <span class="text-sm text-slate-700 dark:text-slate-200">{{ t.fullName }}</span>
                  </label>

                  <div v-if="displayMainTeachers.length === 0" class="p-4 text-sm text-slate-400 text-center">
                    Ничего не найдено
                  </div>
                </div>
              </div>

              <div v-if="showMainDropdown" @click="showMainDropdown = false" class="fixed inset-0 z-10"></div>
              <p
                  v-if="selectedSubject && autoMainTeacherMessage"
                  class="mt-2 text-xs font-medium flex items-start gap-1.5"
                  :class="mainTeachers.length > 0 ? 'text-emerald-600 dark:text-emerald-300' : 'text-amber-600 dark:text-amber-300'"
              >
                <Info class="w-3.5 h-3.5 mt-0.5 shrink-0" />
                {{ autoMainTeacherMessage }}
              </p>
            </div>

            <!-- Chairman -->
            <div class="relative">
              <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
                Председатель
                <span v-if="currentAttemptRule.requiresChairman" class="text-red-500">*</span>
              </label>

              <div
                  @click="availableChairmen.length === 0 ? null : showChairmanDropdown = !showChairmanDropdown"
                  :class="[
                  'w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                  availableChairmen.length === 0
                    ? 'bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-[var(--panel-border-strong)]'
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
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] rounded-[20px] shadow-[var(--panel-shadow)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="chairmanSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-[var(--accent)] dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <div
                      v-for="t in displayChairmen"
                      :key="t.uuid"
                      @click="selectChairman(t.uuid)"
                      class="px-4 py-3 hover:bg-[var(--panel-muted)] cursor-pointer text-sm text-slate-700 dark:text-slate-200 transition-colors"
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
                <span v-if="currentAttemptRule.minCommissionMembers > 0" class="text-red-500">*</span>
              </label>

              <div
                  @click="availableCommissionTeachers.length === 0 ? null : showCommDropdown = !showCommDropdown"
                  :class="[
                  'w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all',
                  availableCommissionTeachers.length === 0
                    ? 'bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed'
                    : 'bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-[var(--panel-border-strong)]'
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
                  {{ formatShortName(availableCommissionTeachers.find(t => t.uuid === uuid)?.fullName ?? props.teachers.find(t => t.uuid === uuid)?.fullName) }}
                  <X class="w-3 h-3 hover:text-red-500 cursor-pointer" @click.stop="removeCommTeacher(uuid)" />
                </span>
              </div>

              <div
                  v-if="showCommDropdown"
                  class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-[var(--panel-bg-strong)] border border-[var(--panel-border)] rounded-[20px] shadow-[var(--panel-shadow)] overflow-hidden"
              >
                <div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0">
                  <div class="relative">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        v-model="commSearchQuery"
                        @click.stop
                        placeholder="Поиск..."
                        class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-[var(--accent)] dark:text-white transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto flex-1">
                  <label
                      v-for="t in displayCommTeachers"
                      :key="t.uuid"
                      class="flex items-center px-4 py-3 hover:bg-[var(--panel-muted)] cursor-pointer transition-colors"
                  >
                    <input type="checkbox" :value="t.uuid" v-model="commissionTeachers" class="w-4 h-4 text-[var(--accent)] rounded border-slate-300 focus:ring-[var(--accent)] mr-3">
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
      </div>
      </div>

      <!-- Submit -->
      <div class="flex flex-col sm:flex-row justify-end gap-3 pt-6 border-t border-[var(--panel-border)]">
        <button
            v-if="editingRetakeId"
            @click="cancelRetakeEdit"
            class="h-12 px-6 rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-bg-strong)] text-sm font-bold text-slate-700 hover:border-[var(--panel-border-strong)] dark:text-slate-200 transition-all"
        >
          Отменить
        </button>
        <button
            @click="submitRetake"
            :disabled="isSubmitting || subjectBelongsToAnotherDept"
            class="h-12 px-8 rounded-2xl bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-200 text-white dark:text-slate-900 font-black shadow-[var(--panel-shadow)] flex items-center gap-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <div v-if="isSubmitting" class="w-5 h-5 rounded-full border-2 border-white dark:border-slate-900 border-t-transparent animate-spin"></div>
          <CheckCircle v-else class="w-5 h-5" />
          {{ editingRetakeId ? 'Сохранить изменения' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scheduler-flow {
  display: flex;
  flex-direction: column;
}

.scheduler-step-slots {
  order: 2;
}

.scheduler-step-format {
  order: 3;
}

.scheduler-step-commission {
  order: 1;
}
</style>


