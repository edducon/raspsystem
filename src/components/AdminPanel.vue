<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { BackendApiError, fetchBackendFromBrowser } from '../lib/backend-api';

type UserRole = 'ADMIN' | 'EMPLOYEE' | 'TEACHER';
type StatusKind = 'success' | 'error';
type SnapshotSummary = { id: number; name: string; semesterLabel: string; status: string; sourceType: string; description: string | null; isReferenceForRetakes: boolean; capturedAt: string | null; createdAt: string; dateRangeStart: string | null; dateRangeEnd: string | null; groupCount: number; subjectCount: number; teacherCount: number; scheduleItemCount: number };
type ArchiveItem = { id: string; name: string; semesterLabel: string; sourceLabel: string; kind: 'manual' | 'snapshot'; isReferenceForRetakes: boolean; capturedAt: string | null; createdAt: string | null; dateRangeStart: string | null; dateRangeEnd: string | null; groupCount: number; subjectCount: number; teacherCount: number; scheduleItemCount: number; accentClass: string; badgeText: string | null; deletePath: string | null };
type UserItem = { id: number; username: string; fullName: string; role: UserRole; isActive: boolean; departmentId: number | null; departmentIds: number[]; teacherUuid: string | null };
type DepartmentItem = { id: number; name: string; short_name: string };
type TeacherDirectoryItem = { uuid: string; fullName: string; departmentIds: number[]; positionId: number | null };
type PositionItem = { id: number; name: string; sort_order: number; is_active: boolean };
type TeacherItem = { id: number; full_name: string; department_id: number; position_id: number | null };
type PastSemesterStatus = { isLoaded: boolean; importedRecords: number; uniqueGroups: number; uniqueSubjects: number; dateRangeStart: string | null; dateRangeEnd: string | null };

const props = defineProps<{
  backendApiUrl: string;
  currentUserId: number;
  initialUsers: UserItem[];
  initialDepartments: DepartmentItem[];
  initialTeacherDirectory: TeacherDirectoryItem[];
  initialPositions: PositionItem[];
  initialTeachers: TeacherItem[];
  initialScheduleSnapshots: SnapshotSummary[];
}>();

const users = ref([...props.initialUsers]);
const departments = ref([...props.initialDepartments]);
const teacherDirectory = ref([...props.initialTeacherDirectory]);
const positions = ref([...props.initialPositions]);
const teachers = ref([...props.initialTeachers]);
const scheduleSnapshots = ref([...props.initialScheduleSnapshots]);
const status = ref<{ kind: StatusKind; message: string } | null>(null);
const pastSemesterInfo = ref<{ imported: number; groups: number; subjects: number; dateRangeStart: string | null; dateRangeEnd: string | null } | null>(null);

const activeTab = ref('teachers');
const tabs = [
  { id: 'teachers', label: 'Преподаватели' },
  { id: 'departments', label: 'Кафедры и должности' },
  { id: 'snapshots', label: 'Снимки расписания' },
];

const busy = reactive({
  reload: false,
  flow: false,
  department: false,
  position: false,
  syncTeachers: false,
  importPastSemester: false,
  createAccount: '' as string,
  updateTeacherPosition: '' as string,
});

// --- Teacher search ---
const teacherSearchQuery = ref('');
const teacherPage = ref(0);
const TEACHERS_PER_PAGE = 50;

const filteredTeacherDirectory = computed(() => {
  const q = teacherSearchQuery.value.toLowerCase().trim();
  const list = q
      ? teacherDirectory.value.filter(t => t.fullName.toLowerCase().includes(q))
      : teacherDirectory.value;
  return list;
});

const pagedTeacherDirectory = computed(() => {
  const start = teacherPage.value * TEACHERS_PER_PAGE;
  return filteredTeacherDirectory.value.slice(start, start + TEACHERS_PER_PAGE);
});

const totalTeacherPages = computed(() => Math.ceil(filteredTeacherDirectory.value.length / TEACHERS_PER_PAGE));

// --- Modals ---
const showTeacherModal = ref(false);
const teacherFlowForm = reactive({ full_name: '', department_ids: [] as string[], position_id: '', create_account: false, username: '', password: '' });
const teacherInlineForm = reactive({ uuid: '', fullName: '', department_ids: [] as string[], position_id: '' });
const teacherInlineOriginal = reactive({ uuid: '', department_ids: [] as string[], position_id: '' });
const teacherDepartmentMenuUuid = ref('');
const teacherPositionMenuUuid = ref('');
const departmentForm = reactive({ name: '', short_name: '' });
const positionForm = reactive({ name: '', sort_order: 0, is_active: true });

// Account creation modal for existing teacher
const showAccountModal = ref(false);
const accountTarget = reactive({ uuid: '', fullName: '', username: '', password: '', role: 'TEACHER' as UserRole, department_id: '' });

const pastSemesterFileInput = ref<HTMLInputElement | null>(null);

const errorText = (error: unknown, fallback: string) => error instanceof BackendApiError ? error.detail : error instanceof Error ? error.message : fallback;
const setStatus = (kind: StatusKind, message: string) => { status.value = { kind, message }; setTimeout(() => status.value = null, 8000); };

const getDepartmentName = (id: number | null | string) => {
  if (!id) return '—';
  const dept = departments.value.find(d => String(d.id) === String(id));
  return dept ? dept.short_name : `ID:${id}`;
};

const getDepartmentNames = (ids: number[]) => {
  if (!ids || ids.length === 0) return '—';
  return ids.map(id => getDepartmentName(id)).join(', ');
};

const getPositionName = (id: number | null) => {
  if (!id) return '—';
  const position = positions.value.find(item => item.id === id);
  return position?.name ?? '—';
};

const getAccountForTeacherUuid = (uuid: string) => users.value.find(u => u.teacherUuid === uuid);

const normalizeDepartmentIds = (ids: string[]) => [...new Set(ids)].sort((a, b) => Number(a) - Number(b));

function resetTeacherInlineForm() {
  teacherInlineForm.uuid = '';
  teacherInlineForm.fullName = '';
  teacherInlineForm.department_ids = [];
  teacherInlineForm.position_id = '';
  teacherInlineOriginal.uuid = '';
  teacherInlineOriginal.department_ids = [];
  teacherInlineOriginal.position_id = '';
  teacherDepartmentMenuUuid.value = '';
  teacherPositionMenuUuid.value = '';
}

function toggleDepartmentSelection(target: string[], departmentId: number) {
  const normalizedId = String(departmentId);
  const index = target.indexOf(normalizedId);
  if (index >= 0) target.splice(index, 1);
  else target.push(normalizedId);
}

function toggleTeacherInlineDepartment(departmentId: number) {
  toggleDepartmentSelection(teacherInlineForm.department_ids, departmentId);
}

function toggleTeacherFlowDepartment(departmentId: number) {
  toggleDepartmentSelection(teacherFlowForm.department_ids, departmentId);
}

function hasTeacherInlineDepartment(departmentId: number) {
  return teacherInlineForm.department_ids.includes(String(departmentId));
}

function hasTeacherFlowDepartment(departmentId: number) {
  return teacherFlowForm.department_ids.includes(String(departmentId));
}

function isTeacherInlineActive(uuid: string) {
  return teacherInlineForm.uuid === uuid;
}

function activateTeacherInline(teacher: TeacherDirectoryItem) {
  if (teacherInlineForm.uuid === teacher.uuid) {
    return;
  }

  teacherInlineForm.uuid = teacher.uuid;
  teacherInlineForm.fullName = teacher.fullName;
  teacherInlineForm.department_ids = teacher.departmentIds.map(String);
  teacherInlineForm.position_id = teacher.positionId ? String(teacher.positionId) : '';
  teacherInlineOriginal.uuid = teacher.uuid;
  teacherInlineOriginal.department_ids = teacher.departmentIds.map(String);
  teacherInlineOriginal.position_id = teacher.positionId ? String(teacher.positionId) : '';
}

function toggleTeacherDepartmentMenu(teacher: TeacherDirectoryItem) {
  activateTeacherInline(teacher);
  teacherDepartmentMenuUuid.value = teacherDepartmentMenuUuid.value === teacher.uuid ? '' : teacher.uuid;
  if (teacherDepartmentMenuUuid.value) {
    teacherPositionMenuUuid.value = '';
  }
}

function toggleTeacherPositionMenu(teacher: TeacherDirectoryItem) {
  activateTeacherInline(teacher);
  teacherPositionMenuUuid.value = teacherPositionMenuUuid.value === teacher.uuid ? '' : teacher.uuid;
  if (teacherPositionMenuUuid.value) {
    teacherDepartmentMenuUuid.value = '';
  }
}

function closeTeacherInlineMenus() {
  teacherDepartmentMenuUuid.value = '';
  teacherPositionMenuUuid.value = '';
}

function cancelTeacherInlineEdit() {
  resetTeacherInlineForm();
}

function hasTeacherInlineChanges(uuid: string) {
  if (teacherInlineForm.uuid !== uuid || teacherInlineOriginal.uuid !== uuid) {
    return false;
  }

  const currentDepartmentIds = normalizeDepartmentIds(teacherInlineForm.department_ids);
  const originalDepartmentIds = normalizeDepartmentIds(teacherInlineOriginal.department_ids);
  return currentDepartmentIds.join(',') !== originalDepartmentIds.join(',')
    || teacherInlineForm.position_id !== teacherInlineOriginal.position_id;
}

function getTeacherDepartmentsForDisplay(teacher: TeacherDirectoryItem) {
  const ids = isTeacherInlineActive(teacher.uuid)
    ? teacherInlineForm.department_ids
    : teacher.departmentIds.map(String);
  const names = ids.map((id) => getDepartmentName(id)).filter((name) => name !== '—');
  return names;
}

function getTeacherPositionForDisplay(teacher: TeacherDirectoryItem) {
  if (isTeacherInlineActive(teacher.uuid)) {
    return teacherInlineForm.position_id ? getPositionName(Number(teacherInlineForm.position_id)) : 'Не указана';
  }
  return getPositionName(teacher.positionId);
}

// --- Auto-generate login/password ---
function transliterate(text: string): string {
  const map: Record<string, string> = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i',
    'й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y',
    'ь':'','э':'e','ю':'yu','я':'ya',
  };
  return text.toLowerCase().split('').map(c => map[c] ?? c).join('');
}

function generateUsername(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length >= 3) {
    // Фамилия + И.О. → ivanov.i.i
    return transliterate(parts[0]) + '.' + transliterate(parts[1][0]) + '.' + transliterate(parts[2][0]);
  }
  if (parts.length === 2) {
    return transliterate(parts[0]) + '.' + transliterate(parts[1][0]);
  }
  return transliterate(parts[0]);
}

function generatePassword(): string {
  const chars = 'abcdefghijkmnpqrstuvwxyz23456789';
  let pwd = '';
  for (let i = 0; i < 8; i++) pwd += chars[Math.floor(Math.random() * chars.length)];
  return pwd;
}

function openAccountModal(teacher: TeacherDirectoryItem) {
  accountTarget.uuid = teacher.uuid;
  accountTarget.fullName = teacher.fullName;
  accountTarget.username = generateUsername(teacher.fullName);
  accountTarget.password = generatePassword();
  accountTarget.role = 'TEACHER';
  accountTarget.department_id = teacher.departmentIds.length > 0 ? String(teacher.departmentIds[0]) : '';
  showAccountModal.value = true;
}

// --- API calls ---
async function reloadAll() {
  busy.reload = true;
  resetTeacherInlineForm();
  try {
    const [u, d, td, p, t, s] = await Promise.all([
      fetchBackendFromBrowser<UserItem[]>(props.backendApiUrl, '/users/'),
      fetchBackendFromBrowser<DepartmentItem[]>(props.backendApiUrl, '/departments/'),
      fetchBackendFromBrowser<TeacherDirectoryItem[]>(props.backendApiUrl, '/teacher-directory/'),
      fetchBackendFromBrowser<PositionItem[]>(props.backendApiUrl, '/positions/'),
      fetchBackendFromBrowser<TeacherItem[]>(props.backendApiUrl, '/teachers/'),
      fetchBackendFromBrowser<SnapshotSummary[]>(props.backendApiUrl, '/schedule-snapshots/'),
    ]);
    users.value = u; departments.value = d; teacherDirectory.value = td; positions.value = p; teachers.value = t; scheduleSnapshots.value = s;
    await loadPastSemesterStatus(true);
  } catch (error) { setStatus('error', errorText(error, 'Ошибка обновления данных.')); }
  finally { busy.reload = false; }
}

async function loadPastSemesterStatus(silent = false) {
  try {
    const result = await fetchBackendFromBrowser<PastSemesterStatus>(props.backendApiUrl, '/retakes/admin/past-semester/status');
    pastSemesterInfo.value = result.isLoaded
      ? {
        imported: result.importedRecords,
        groups: result.uniqueGroups,
        subjects: result.uniqueSubjects,
        dateRangeStart: result.dateRangeStart ?? null,
        dateRangeEnd: result.dateRangeEnd ?? null,
      }
      : null;
  } catch (error) {
    if (!silent) setStatus('error', errorText(error, 'Не удалось загрузить статус прошлого семестра.'));
  }
}

async function submitDepartment() {
  busy.department = true;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, '/departments/', {
      method: 'POST',
      body: JSON.stringify({ name: departmentForm.name.trim(), short_name: departmentForm.short_name.trim() })
    });
    setStatus('success', 'Кафедра создана.');
    departmentForm.name = ''; departmentForm.short_name = '';
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Не удалось создать кафедру.')); }
  finally { busy.department = false; }
}

async function submitPosition() {
  busy.position = true;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, '/positions/', {
      method: 'POST',
      body: JSON.stringify({ name: positionForm.name.trim(), sort_order: Number(positionForm.sort_order), is_active: positionForm.is_active })
    });
    setStatus('success', 'Должность создана.');
    positionForm.name = ''; positionForm.sort_order = 0;
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Не удалось создать должность.')); }
  finally { busy.position = false; }
}

async function submitTeacherFlow() {
  busy.flow = true;
  try {
    const teacherDepartmentIds = teacherFlowForm.department_ids.map(Number);
    const directoryRes = await fetchBackendFromBrowser<{ uuid: string }>(props.backendApiUrl, '/teacher-directory/', {
      method: 'POST', body: JSON.stringify({
        full_name: teacherFlowForm.full_name,
        department_ids: teacherDepartmentIds,
        position_id: teacherFlowForm.position_id ? Number(teacherFlowForm.position_id) : null,
      })
    });

    if (teacherFlowForm.create_account) {
      const primaryDepartmentId = teacherDepartmentIds[0] ?? null;
      await fetchBackendFromBrowser(props.backendApiUrl, '/users/', {
        method: 'POST', body: JSON.stringify({
          username: teacherFlowForm.username, password: teacherFlowForm.password,
          full_name: teacherFlowForm.full_name, role: 'TEACHER', is_active: true,
          department_id: primaryDepartmentId,
          department_ids: teacherDepartmentIds,
          teacher_uuid: directoryRes.uuid
        })
      });
    }

    setStatus('success', 'Преподаватель добавлен в справочник!');
    showTeacherModal.value = false;
    Object.assign(teacherFlowForm, { full_name: '', department_ids: [], position_id: '', create_account: false, username: '', password: '' });
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Ошибка при добавлении преподавателя.')); }
  finally { busy.flow = false; }
}

async function saveTeacherSettings() {
  if (!teacherInlineForm.uuid) return;
  busy.updateTeacherPosition = teacherInlineForm.uuid;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/teacher-directory/${teacherInlineForm.uuid}`, {
      method: 'PUT',
      body: JSON.stringify({
        full_name: teacherInlineForm.fullName,
        department_ids: teacherInlineForm.department_ids.map(Number),
        position_id: teacherInlineForm.position_id ? Number(teacherInlineForm.position_id) : null,
      }),
    });
    setStatus('success', `Настройки преподавателя обновлены: ${teacherInlineForm.fullName}.`);
    resetTeacherInlineForm();
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Не удалось обновить настройки преподавателя.'));
  } finally {
    busy.updateTeacherPosition = '';
  }
}

async function createAccountForTeacher() {
  busy.createAccount = accountTarget.uuid;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, '/users/', {
      method: 'POST', body: JSON.stringify({
        username: accountTarget.username,
        password: accountTarget.password,
        full_name: accountTarget.fullName,
        role: accountTarget.role,
        is_active: true,
        department_id: accountTarget.department_id ? Number(accountTarget.department_id) : null,
        department_ids: accountTarget.department_id ? [Number(accountTarget.department_id)] : [],
        teacher_uuid: accountTarget.uuid,
      })
    });
    setStatus('success', `Аккаунт создан: ${accountTarget.username} / ${accountTarget.password}`);
    showAccountModal.value = false;
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Ошибка создания аккаунта.')); }
  finally { busy.createAccount = ''; }
}

async function syncTeachersFromApi() {
  busy.syncTeachers = true;
  try {
    const result = await fetchBackendFromBrowser<any>(props.backendApiUrl, '/retakes/admin/sync-teachers', { method: 'POST' });
    setStatus('success', result.message || 'Синхронизация завершена.');
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Ошибка синхронизации.')); }
  finally { busy.syncTeachers = false; }
}

function triggerPastSemesterUpload() { pastSemesterFileInput.value?.click(); }

async function handlePastSemesterFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  busy.importPastSemester = true;
  try {
    const text = await file.text();
    let json: any;
    try { json = JSON.parse(text); } catch { setStatus('error', 'Некорректный JSON.'); return; }

    const result = await fetchBackendFromBrowser<any>(props.backendApiUrl, '/retakes/admin/past-semester/import-json', {
      method: 'POST', body: JSON.stringify(json),
    });

    pastSemesterInfo.value = {
      imported: result.importedRecords ?? result.imported_records ?? 0,
      groups: result.uniqueGroups ?? result.unique_groups ?? 0,
      subjects: result.uniqueSubjects ?? result.unique_subjects ?? 0,
      dateRangeStart: result.dateRangeStart ?? result.date_range_start ?? null,
      dateRangeEnd: result.dateRangeEnd ?? result.date_range_end ?? null,
    };
    setStatus('success', result.message || 'Импорт завершён.');
    await loadPastSemesterStatus(true);
  } catch (error) { setStatus('error', errorText(error, 'Ошибка импорта.')); }
  finally { busy.importPastSemester = false; input.value = ''; }
}

const archiveItems = computed<ArchiveItem[]>(() => {
  const items: ArchiveItem[] = [];

  if (pastSemesterInfo.value) {
    items.push({
      id: 'past-semester-manual',
      name: 'Предыдущий семестр',
      semesterLabel: 'Ручной импорт прошлого семестра',
      sourceLabel: 'Источник: schedules.json',
      kind: 'manual',
      isReferenceForRetakes: false,
      capturedAt: null,
      createdAt: null,
      dateRangeStart: pastSemesterInfo.value.dateRangeStart,
      dateRangeEnd: pastSemesterInfo.value.dateRangeEnd,
      groupCount: pastSemesterInfo.value.groups,
      subjectCount: pastSemesterInfo.value.subjects,
      teacherCount: 0,
      scheduleItemCount: pastSemesterInfo.value.imported,
      accentClass: 'border-amber-300 bg-amber-50/80 dark:bg-amber-900/10 dark:border-amber-700/40',
      badgeText: 'Ручная загрузка',
      deletePath: null,
    });
  }

  scheduleSnapshots.value.forEach((item) => {
    items.push({
      id: `snapshot-${item.id}`,
      name: item.name,
      semesterLabel: item.semesterLabel,
      sourceLabel: item.sourceType === 'manual' ? 'Источник: ручной snapshot' : `Источник: ${item.sourceType}`,
      kind: 'snapshot',
      isReferenceForRetakes: item.isReferenceForRetakes,
      capturedAt: item.capturedAt,
      createdAt: item.createdAt,
      dateRangeStart: item.dateRangeStart,
      dateRangeEnd: item.dateRangeEnd,
      groupCount: item.groupCount,
      subjectCount: item.subjectCount,
      teacherCount: item.teacherCount,
      scheduleItemCount: item.scheduleItemCount,
      accentClass: item.isReferenceForRetakes ? 'border-green-400 bg-green-50 dark:bg-green-900/10 dark:border-green-600' : 'border-slate-200 dark:border-white/10 bg-white dark:bg-white/5',
      badgeText: item.isReferenceForRetakes ? 'Текущий эталон' : null,
      deletePath: `/schedule-snapshots/${item.id}`,
    });
  });

  return items;
});

async function deleteEntity(path: string, msg: string) {
  if (!window.confirm('Вы уверены?')) return;
  try { await fetchBackendFromBrowser(props.backendApiUrl, path, { method: 'DELETE' }); setStatus('success', msg); await reloadAll(); }
  catch (error) { setStatus('error', errorText(error, 'Ошибка при удалении.')); }
}

function formatDateTime(value: string | null) {
  return value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—';
}

function formatDateOnly(value: string | null) {
  return value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short' }).format(new Date(value)) : '—';
}

onMounted(() => {
  loadPastSemesterStatus(true);
});
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-6 relative">
    <!-- Header -->
    <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 mb-6">
      <div class="flex justify-between items-end">
        <div>
          <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Администрирование</p>
          <h1 class="text-3xl font-black text-slate-900 dark:text-white mt-2">Панель администратора</h1>
        </div>
        <button @click="reloadAll" :disabled="busy.reload" class="px-5 py-2.5 bg-white dark:bg-white/10 border border-slate-300 dark:border-white/10 rounded-2xl text-sm font-bold shadow-sm hover:bg-slate-50 dark:hover:bg-white/20 transition-colors disabled:opacity-50">
          {{ busy.reload ? 'Обновление...' : 'Обновить данные' }}
        </button>
      </div>
      <div v-if="status" class="mt-4 p-4 rounded-xl text-sm font-medium border" :class="status.kind === 'error' ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800/30 dark:text-red-300' : 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800/30 dark:text-green-300'">
        {{ status.message }}
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex space-x-6 border-b border-slate-200 dark:border-white/10 overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
              :class="['pb-4 text-sm font-bold transition-colors whitespace-nowrap', activeTab === tab.id ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300']">
        {{ tab.label }}
      </button>
    </div>

    <!-- ==================== TEACHERS TAB ==================== -->
    <div v-if="activeTab === 'teachers'" class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <div class="flex flex-wrap justify-between items-center mb-4 gap-4">
        <div>
          <h2 class="text-xl font-black text-slate-900 dark:text-white">Справочник преподавателей</h2>
          <p class="text-xs text-slate-500 mt-1">Всего: {{ teacherDirectory.length }} | С аккаунтом: {{ users.filter(u => u.teacherUuid).length }}</p>
        </div>
        <div class="flex gap-2">
          <button @click="syncTeachersFromApi" :disabled="busy.syncTeachers" class="px-4 py-2 border border-slate-300 dark:border-white/20 rounded-xl text-sm font-bold hover:bg-slate-50 dark:hover:bg-white/10 disabled:opacity-50 transition-colors">
            {{ busy.syncTeachers ? '⏳ Загрузка...' : '🔄 Подтянуть из API' }}
          </button>
          <button @click="showTeacherModal = true" class="px-5 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all">+ Добавить</button>
        </div>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <input v-model="teacherSearchQuery" @input="teacherPage = 0" type="text" placeholder="Поиск по ФИО..."
               class="w-full sm:w-80 h-10 px-4 rounded-xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm dark:text-white outline-none focus:border-blue-400 transition-colors" />
      </div>

      <!-- Table -->
      <div class="overflow-x-auto rounded-2xl border border-slate-100 dark:border-white/5">
        <table class="w-full text-sm text-left">
          <thead class="bg-slate-50 dark:bg-black/20 text-slate-600 dark:text-slate-400">
          <tr>
            <th class="px-5 py-3 font-bold">ФИО</th>
            <th class="px-5 py-3 font-bold">Кафедры</th>
            <th class="px-5 py-3 font-bold">Должность</th>
            <th class="px-5 py-3 font-bold">Аккаунт</th>
            <th class="px-5 py-3 font-bold text-right">Действия</th>
          </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-white/5">
          <template v-for="t in pagedTeacherDirectory" :key="t.uuid">
            <tr class="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors align-top">
              <td class="px-5 py-3 font-semibold text-slate-900 dark:text-white">
                <div>
                  <div>{{ t.fullName }}</div>
                  <div class="text-[11px] font-medium text-slate-400 mt-0.5">
                    {{ isTeacherInlineActive(t.uuid) ? 'Редактирование в строке' : 'Кафедры и должность меняются прямо в таблице' }}
                  </div>
                </div>
              </td>
              <td class="px-5 py-3 text-slate-600 dark:text-slate-300 text-xs">
                <div class="relative">
                  <button
                    type="button"
                    @click.stop="toggleTeacherDepartmentMenu(t)"
                    class="w-full rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] px-3 py-2 text-left hover:border-blue-300 dark:hover:border-blue-500/40 transition-colors"
                    :class="teacherDepartmentMenuUuid === t.uuid ? 'border-blue-400 dark:border-blue-500/50 shadow-sm' : ''"
                  >
                    <div v-if="getTeacherDepartmentsForDisplay(t).length > 0" class="flex flex-wrap gap-1.5">
                      <span
                        v-for="name in getTeacherDepartmentsForDisplay(t)"
                        :key="`${t.uuid}-${name}`"
                        class="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300 border border-blue-100 dark:border-blue-800/40"
                      >
                        {{ name }}
                      </span>
                    </div>
                    <span v-else class="text-slate-400">Не выбраны</span>
                  </button>

                  <div
                    v-if="teacherDepartmentMenuUuid === t.uuid"
                    class="absolute left-0 top-full z-20 mt-2 w-[22rem] max-w-[calc(100vw-4rem)] rounded-2xl border border-slate-200 dark:border-white/10 bg-white/95 dark:bg-slate-900/95 p-3 shadow-2xl backdrop-blur"
                  >
                    <div class="mb-2 flex items-center justify-between gap-3">
                      <p class="text-xs font-bold text-slate-500">Кафедры</p>
                      <button type="button" @click.stop="closeTeacherInlineMenus" class="text-[11px] font-bold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">Закрыть</button>
                    </div>
                    <div class="grid gap-2 max-h-64 overflow-y-auto">
                      <label
                        v-for="d in departments"
                        :key="d.id"
                        class="flex items-start gap-3 rounded-2xl border px-3 py-3 cursor-pointer transition-colors"
                        :class="hasTeacherInlineDepartment(d.id)
                          ? 'border-blue-300 bg-blue-50/80 text-blue-900 dark:border-blue-700 dark:bg-blue-900/20 dark:text-blue-100'
                          : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 dark:border-white/10 dark:bg-slate-900/60 dark:text-slate-200 dark:hover:border-white/20'"
                      >
                        <input
                          type="checkbox"
                          :checked="hasTeacherInlineDepartment(d.id)"
                          @change="toggleTeacherInlineDepartment(d.id)"
                          class="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span class="flex flex-col gap-0.5">
                          <span class="text-sm font-semibold">{{ d.short_name }}</span>
                          <span class="text-[11px] text-slate-500 dark:text-slate-400">{{ d.name }}</span>
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-5 py-3 text-slate-600 dark:text-slate-300 text-xs">
                <div class="relative">
                  <button
                    type="button"
                    @click.stop="toggleTeacherPositionMenu(t)"
                    class="inline-flex min-w-[12rem] items-center justify-between gap-3 rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] px-3 py-2 text-left hover:border-blue-300 dark:hover:border-blue-500/40 transition-colors"
                    :class="teacherPositionMenuUuid === t.uuid ? 'border-blue-400 dark:border-blue-500/50 shadow-sm' : ''"
                  >
                    <span :class="getTeacherPositionForDisplay(t) === 'Не указана' ? 'text-slate-400' : 'text-slate-700 dark:text-slate-200'">
                      {{ getTeacherPositionForDisplay(t) }}
                    </span>
                    <span class="text-slate-400">▾</span>
                  </button>

                  <div
                    v-if="teacherPositionMenuUuid === t.uuid"
                    class="absolute left-0 top-full z-20 mt-2 w-72 max-w-[calc(100vw-4rem)] rounded-2xl border border-slate-200 dark:border-white/10 bg-white/95 dark:bg-slate-900/95 p-2 shadow-2xl backdrop-blur"
                  >
                    <button
                      type="button"
                      @click.stop="teacherInlineForm.position_id = ''; closeTeacherInlineMenus()"
                      class="w-full rounded-xl px-3 py-2 text-left text-sm transition-colors hover:bg-slate-100 dark:hover:bg-white/10"
                    >
                      Не указана
                    </button>
                    <button
                      v-for="item in positions"
                      :key="item.id"
                      type="button"
                      @click.stop="teacherInlineForm.position_id = String(item.id); closeTeacherInlineMenus()"
                      class="w-full rounded-xl px-3 py-2 text-left text-sm transition-colors hover:bg-slate-100 dark:hover:bg-white/10"
                    >
                      {{ item.name }}
                    </button>
                  </div>
                </div>
              </td>
              <td class="px-5 py-3">
                <template v-if="getAccountForTeacherUuid(t.uuid)">
                    <span class="px-2.5 py-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 rounded-lg text-xs font-bold">
                      {{ getAccountForTeacherUuid(t.uuid)?.username }}
                    </span>
                </template>
                <template v-else>
                  <button @click.stop="openAccountModal(t)" class="px-2.5 py-1 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300 rounded-lg text-xs font-bold hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
                    Создать аккаунт
                  </button>
                </template>
              </td>
              <td class="px-5 py-3 text-right">
                <div class="flex flex-col items-end gap-2">
                  <div v-if="busy.updateTeacherPosition === t.uuid" class="text-[11px] text-slate-400">Сохранение...</div>
                  <template v-else-if="isTeacherInlineActive(t.uuid)">
                    <button
                      @click.stop="saveTeacherSettings"
                      :disabled="!hasTeacherInlineChanges(t.uuid)"
                      class="inline-flex items-center justify-center rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600"
                    >
                      Сохранить
                    </button>
                    <button @click.stop="cancelTeacherInlineEdit" class="text-slate-500 font-bold hover:text-slate-700 dark:hover:text-slate-200 text-xs">Отмена</button>
                  </template>
                  <div v-else class="text-[11px] text-slate-400">Без раскрытия строки</div>
                  <button @click.stop="deleteEntity(`/teacher-directory/${t.uuid}`, 'Удалён из справочника')" class="text-red-500 font-bold hover:text-red-700 text-xs">Удалить</button>
                </div>
                <div v-if="teacherDepartmentMenuUuid === t.uuid || teacherPositionMenuUuid === t.uuid" @click="closeTeacherInlineMenus" class="fixed inset-0 z-10"></div>
              </td>
            </tr>
          </template>
          <tr v-if="pagedTeacherDirectory.length === 0">
            <td colspan="5" class="px-5 py-8 text-center text-slate-400">
              {{ teacherSearchQuery ? 'Ничего не найдено' : 'Справочник пуст. Нажмите «Подтянуть из API».' }}
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalTeacherPages > 1" class="flex items-center justify-between mt-4">
        <span class="text-xs text-slate-500">Стр. {{ teacherPage + 1 }} из {{ totalTeacherPages }} ({{ filteredTeacherDirectory.length }} записей)</span>
        <div class="flex gap-2">
          <button @click="teacherPage = Math.max(0, teacherPage - 1)" :disabled="teacherPage === 0" class="px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-300 dark:border-white/10 disabled:opacity-30 hover:bg-slate-50 dark:hover:bg-white/10 transition-colors">← Назад</button>
          <button @click="teacherPage = Math.min(totalTeacherPages - 1, teacherPage + 1)" :disabled="teacherPage >= totalTeacherPages - 1" class="px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-300 dark:border-white/10 disabled:opacity-30 hover:bg-slate-50 dark:hover:bg-white/10 transition-colors">Далее →</button>
        </div>
      </div>
    </div>

    <!-- ==================== ADD TEACHER MODAL ==================== -->
    <div v-if="showTeacherModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div class="bg-white dark:bg-slate-900 rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-200 dark:border-slate-700">
        <h3 class="text-2xl font-black mb-6 dark:text-white">Новый преподаватель</h3>
        <form @submit.prevent="submitTeacherFlow" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">ФИО (Полностью)</label>
            <input v-model="teacherFlowForm.full_name" required type="text" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm" />
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">Кафедра</label>
            <div class="grid gap-2 sm:grid-cols-2">
              <label
                v-for="d in departments"
                :key="d.id"
                class="flex items-start gap-3 rounded-2xl border px-3 py-3 cursor-pointer transition-colors"
                :class="hasTeacherFlowDepartment(d.id)
                  ? 'border-blue-300 bg-blue-50/80 text-blue-900 dark:border-blue-700 dark:bg-blue-900/20 dark:text-blue-100'
                  : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-500'"
              >
                <input
                  type="checkbox"
                  :checked="hasTeacherFlowDepartment(d.id)"
                  @change="toggleTeacherFlowDepartment(d.id)"
                  class="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="flex flex-col gap-0.5">
                  <span class="text-sm font-semibold">{{ d.short_name }}</span>
                  <span class="text-[11px] text-slate-500 dark:text-slate-400">{{ d.name }}</span>
                </span>
              </label>
            </div>
            <p class="mt-1 text-xs text-slate-500">Можно выбрать несколько кафедр.</p>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">Должность</label>
            <select v-model="teacherFlowForm.position_id" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm">
              <option value="">Не указана</option>
              <option v-for="item in positions" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div class="pt-4 border-t border-slate-100 dark:border-slate-700">
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="teacherFlowForm.create_account" type="checkbox" class="w-5 h-5 rounded" />
              <span class="text-sm font-bold dark:text-slate-300">Сразу создать аккаунт</span>
            </label>
          </div>
          <div v-if="teacherFlowForm.create_account" class="space-y-3 bg-blue-50/50 dark:bg-blue-900/10 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/30">
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Логин</label>
              <input v-model="teacherFlowForm.username" required type="text" class="w-full h-10 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Пароль</label>
              <input v-model="teacherFlowForm.password" required type="text" class="w-full h-10 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 dark:text-white text-sm font-mono" />
            </div>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="submit" :disabled="busy.flow" class="flex-1 h-12 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50">Создать</button>
            <button type="button" @click="showTeacherModal = false" class="px-6 h-12 bg-slate-100 dark:bg-slate-800 dark:text-white rounded-xl font-bold hover:bg-slate-200 dark:hover:bg-slate-700">Отмена</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== CREATE ACCOUNT MODAL ==================== -->
    <div v-if="showAccountModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div class="bg-white dark:bg-slate-900 rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-200 dark:border-slate-700">
        <h3 class="text-xl font-black mb-2 dark:text-white">Создание аккаунта</h3>
        <p class="text-sm text-slate-500 mb-6">{{ accountTarget.fullName }}</p>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">Логин</label>
            <input v-model="accountTarget.username" type="text" class="w-full h-10 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm" />
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">Пароль</label>
            <div class="flex gap-2">
              <input v-model="accountTarget.password" type="text" class="flex-1 h-10 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm font-mono" />
              <button @click="accountTarget.password = generatePassword()" type="button" class="px-3 h-10 rounded-xl border border-slate-300 dark:border-white/10 text-xs font-bold hover:bg-slate-50 dark:hover:bg-white/10">🔄</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Роль</label>
              <select v-model="accountTarget.role" class="w-full h-10 px-3 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm">
                <option value="TEACHER">Преподаватель</option>
                <option value="EMPLOYEE">Сотрудник</option>
                <option value="ADMIN">Администратор</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Кафедра</label>
              <select v-model="accountTarget.department_id" class="w-full h-10 px-3 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm">
                <option value="">—</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.short_name }}</option>
              </select>
            </div>
          </div>
          <div class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 p-3 rounded-xl text-xs text-amber-800 dark:text-amber-300">
            Запишите данные перед созданием — пароль нельзя будет посмотреть позже.
          </div>
          <div class="flex gap-3 pt-2">
            <button @click="createAccountForTeacher" :disabled="!!busy.createAccount" class="flex-1 h-11 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 disabled:opacity-50">Создать аккаунт</button>
            <button @click="showAccountModal = false" class="px-6 h-11 bg-slate-100 dark:bg-slate-800 dark:text-white rounded-xl font-bold hover:bg-slate-200 dark:hover:bg-slate-700">Отмена</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== DEPARTMENTS TAB ==================== -->
    <div v-if="activeTab === 'departments'" class="grid gap-6 md:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Кафедры</h2>
        <form class="grid gap-3" @submit.prevent="submitDepartment">
          <input v-model="departmentForm.name" type="text" required placeholder="Полное название кафедры" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm dark:text-white" />
          <input v-model="departmentForm.short_name" type="text" required placeholder="Аббревиатура" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm dark:text-white" />
          <button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.department">{{ busy.department ? 'Создание...' : 'Добавить кафедру' }}</button>
        </form>
        <div class="space-y-2 mt-4">
          <div v-for="item in departments" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm flex justify-between items-center bg-white dark:bg-black/20">
            <span class="dark:text-white"><b>{{ item.short_name }}</b> <span class="text-slate-500">({{ item.name }})</span></span>
            <button @click="deleteEntity(`/departments/${item.id}`, 'Удалено')" class="text-red-500 font-bold text-xs">Удалить</button>
          </div>
        </div>
      </div>
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Должности</h2>
        <form class="grid gap-3" @submit.prevent="submitPosition">
          <input v-model="positionForm.name" type="text" required placeholder="Название должности" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm dark:text-white" />
          <input v-model.number="positionForm.sort_order" type="number" placeholder="Порядок сортировки" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm dark:text-white" />
          <button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.position">{{ busy.position ? 'Создание...' : 'Добавить должность' }}</button>
        </form>
        <div class="space-y-2 mt-4">
          <div v-for="item in positions" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm flex justify-between items-center bg-white dark:bg-black/20">
            <span class="dark:text-white">{{ item.name }}</span>
            <button @click="deleteEntity(`/positions/${item.id}`, 'Удалено')" class="text-red-500 font-bold text-xs">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== SNAPSHOTS TAB ==================== -->
    <div v-if="activeTab === 'snapshots'" class="space-y-6">
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
        <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-xl font-black dark:text-white">Архив семестров</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400 mt-2">
              Здесь хранятся прошлые семестры. Первый прошлый семестр загружается вручную через <code class="bg-slate-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono">schedules.json</code>, а снимки дальше пополняют архив для следующих циклов.
            </p>
          </div>
          <div>
            <input ref="pastSemesterFileInput" type="file" accept=".json" class="hidden" @change="handlePastSemesterFile" />
            <button @click="triggerPastSemesterUpload" :disabled="busy.importPastSemester" class="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl text-sm disabled:opacity-50 transition-colors">
              {{ busy.importPastSemester ? '⏳ Импорт...' : '📂 Загрузить schedules.json' }}
            </button>
          </div>
        </div>

        <div v-if="archiveItems.length === 0" class="text-center py-10 text-slate-400 dark:text-slate-500">
          <p class="text-sm">Архив семестров пока пуст.</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="item in archiveItems" :key="item.id" class="p-5 border rounded-3xl" :class="item.accentClass">
            <span v-if="item.badgeText" class="px-2.5 py-1 text-white text-[10px] uppercase font-black rounded-lg mb-2 inline-block" :class="item.kind === 'manual' ? 'bg-amber-600' : 'bg-green-500'">{{ item.badgeText }}</span>
            <div class="font-bold text-lg dark:text-white">{{ item.name }}</div>
            <div class="text-sm text-slate-600 dark:text-slate-300">Семестр: {{ item.semesterLabel }}</div>
            <div class="text-sm text-slate-500 dark:text-slate-400 mt-1">{{ item.sourceLabel }}</div>
            <div class="text-xs text-slate-500 mt-3 space-y-1">
              <p>Групп: {{ item.groupCount }} | Предметов: {{ item.subjectCount }} | Преподавателей: {{ item.teacherCount }} | Записей: {{ item.scheduleItemCount }}</p>
              <p>Период: {{ item.dateRangeStart && item.dateRangeEnd ? `${formatDateOnly(item.dateRangeStart)} - ${formatDateOnly(item.dateRangeEnd)}` : 'Диапазон дат не найден в данных расписания' }}</p>
              <p v-if="item.kind === 'snapshot'">Фиксация: {{ formatDateTime(item.capturedAt) }} | Создан: {{ formatDateTime(item.createdAt) }}</p>
            </div>
            <button v-if="item.deletePath" @click="deleteEntity(item.deletePath, 'Снимок удалён')" class="mt-3 text-red-500 font-bold text-xs hover:text-red-700">Удалить</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
