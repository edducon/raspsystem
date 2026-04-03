<script setup lang="ts">
import { reactive, ref } from 'vue';
import { BackendApiError, fetchBackendFromBrowser } from '../lib/backend-api';

type UserRole = 'ADMIN' | 'EMPLOYEE' | 'TEACHER';
type StatusKind = 'success' | 'error';
type SnapshotSummary = { id: number; name: string; semesterLabel: string; status: string; sourceType: string; description: string | null; isReferenceForRetakes: boolean; capturedAt: string | null; createdAt: string; groupCount: number; subjectCount: number; teacherCount: number; scheduleItemCount: number };
type SnapshotDetail = SnapshotSummary & { groups: unknown[]; subjects: unknown[]; teachers: unknown[]; scheduleItems: unknown[] };
type UserItem = { id: number; username: string; fullName: string; role: UserRole; isActive: boolean; departmentId: number | null; departmentIds: number[]; teacherUuid: string | null };
type DepartmentItem = { id: number; name: string; short_name: string };
type TeacherDirectoryItem = { uuid: string; fullName: string; departmentIds: number[] };
type PositionItem = { id: number; name: string; sort_order: number; is_active: boolean };
type TeacherItem = { id: number; full_name: string; department_id: number; position_id: number | null };

const props = defineProps<{
  backendApiUrl: string;
  currentUserId: number;
  initialUsers: UserItem[];
  initialDepartments: DepartmentItem[];
  initialTeacherDirectory: TeacherDirectoryItem[];
  initialPositions: PositionItem[];
  initialTeachers: TeacherItem[];
  initialScheduleSnapshots: SnapshotSummary[];
  initialLoadError?: string;
}>();

const users = ref([...props.initialUsers]);
const departments = ref([...props.initialDepartments]);
const teacherDirectory = ref([...props.initialTeacherDirectory]);
const positions = ref([...props.initialPositions]);
const teachers = ref([...props.initialTeachers]);
const scheduleSnapshots = ref([...props.initialScheduleSnapshots]);
const loadError = ref(props.initialLoadError ?? '');
const status = ref<{ kind: StatusKind; message: string } | null>(null);
const busy = reactive({ reload: false, user: false, department: false, teacherDirectory: false, position: false, teacher: false, snapshot: false, snapshotLoad: false, maintenance: false });
const editing = reactive({ userId: null as number | null, departmentId: null as number | null, teacherDirectoryUuid: null as string | null, positionId: null as number | null, teacherId: null as number | null, snapshotId: null as number | null });
const userForm = reactive({ username: '', full_name: '', role: 'EMPLOYEE' as UserRole, is_active: true, department_id: '', department_ids: [] as number[], teacher_uuid: '', password: '' });
const departmentForm = reactive({ name: '', short_name: '' });
const teacherDirectoryForm = reactive({ full_name: '', department_ids: [] as number[] });
const positionForm = reactive({ name: '', sort_order: 0, is_active: true });
const teacherForm = reactive({ full_name: '', department_id: '', position_id: '' });
const snapshotForm = reactive({ name: '', semester_label: '', status: 'draft', source_type: 'manual', description: '', is_reference_for_retakes: false, captured_at: '', groups_json: '[]', subjects_json: '[]', teachers_json: '[]', schedule_items_json: '[]' });

const errorText = (error: unknown, fallback: string) => error instanceof BackendApiError ? error.detail : error instanceof Error ? error.message : fallback;
const setStatus = (kind: StatusKind, message: string) => { status.value = { kind, message }; };
const clearStatus = () => { status.value = null; };
const uniq = (values: number[]) => [...new Set(values)];
const checkboxChecked = (event: Event) => event.target instanceof HTMLInputElement ? event.target.checked : false;
const toggleSelection = (target: number[], value: number, checked: boolean) => checked ? uniq([...target, value]) : target.filter((item) => item !== value);
const normalizeDeptIds = (primaryId: string, ids: number[]) => primaryId ? uniq([...ids, Number(primaryId)]) : uniq(ids);
const formatDateTime = (value: string | null) => value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : 'Не указано';
const toLocalDateTime = (value: string | null) => value ? new Date(value).toISOString().slice(0, 16) : '';
const fromLocalDateTime = (value: string) => value ? new Date(value).toISOString() : null;
const parseJsonArray = (value: string, label: string) => {
  const parsed = JSON.parse(value.trim() || '[]');
  if (!Array.isArray(parsed)) throw new Error(`Поле «${label}» должно содержать JSON-массив.`);
  return parsed;
};
const scopeLabel = (ids: number[]) => ids.length ? ids.map((id) => {
  const department = departments.value.find((item) => item.id === id);
  return department ? `${department.short_name} (${department.name})` : `#${id}`;
}).join(', ') : 'Не выбрано';
const departmentLabel = (id: number | null) => {
  if (id === null) return 'Не выбрана';
  const department = departments.value.find((item) => item.id === id);
  return department ? `${department.short_name} (${department.name})` : `#${id}`;
};
const positionLabel = (id: number | null) => {
  if (id === null) return 'Не указана';
  const position = positions.value.find((item) => item.id === id);
  return position ? position.name : `#${id}`;
};
const teacherDirectoryLabel = (uuid: string | null) => {
  if (!uuid) return 'Не привязан';
  const teacher = teacherDirectory.value.find((item) => item.uuid === uuid);
  return teacher ? `${teacher.fullName} (${teacher.uuid})` : uuid;
};

const resetUserForm = () => { Object.assign(userForm, { username: '', full_name: '', role: 'EMPLOYEE', is_active: true, department_id: '', department_ids: [], teacher_uuid: '', password: '' }); editing.userId = null; };
const resetDepartmentForm = () => { Object.assign(departmentForm, { name: '', short_name: '' }); editing.departmentId = null; };
const resetTeacherDirectoryForm = () => { Object.assign(teacherDirectoryForm, { full_name: '', department_ids: [] }); editing.teacherDirectoryUuid = null; };
const resetPositionForm = () => { Object.assign(positionForm, { name: '', sort_order: 0, is_active: true }); editing.positionId = null; };
const resetTeacherForm = () => { Object.assign(teacherForm, { full_name: '', department_id: '', position_id: '' }); editing.teacherId = null; };
const resetSnapshotForm = () => { Object.assign(snapshotForm, { name: '', semester_label: '', status: 'draft', source_type: 'manual', description: '', is_reference_for_retakes: false, captured_at: '', groups_json: '[]', subjects_json: '[]', teachers_json: '[]', schedule_items_json: '[]' }); editing.snapshotId = null; };

async function reloadAll() {
  busy.reload = true;
  try {
    const [nextUsers, nextDepartments, nextTeacherDirectory, nextPositions, nextTeachers, nextSnapshots] = await Promise.all([
      fetchBackendFromBrowser<UserItem[]>(props.backendApiUrl, '/users/'),
      fetchBackendFromBrowser<DepartmentItem[]>(props.backendApiUrl, '/departments/'),
      fetchBackendFromBrowser<TeacherDirectoryItem[]>(props.backendApiUrl, '/teacher-directory/'),
      fetchBackendFromBrowser<PositionItem[]>(props.backendApiUrl, '/positions/'),
      fetchBackendFromBrowser<TeacherItem[]>(props.backendApiUrl, '/teachers/'),
      fetchBackendFromBrowser<SnapshotSummary[]>(props.backendApiUrl, '/schedule-snapshots/'),
    ]);
    users.value = nextUsers; departments.value = nextDepartments; teacherDirectory.value = nextTeacherDirectory; positions.value = nextPositions; teachers.value = nextTeachers; scheduleSnapshots.value = nextSnapshots; loadError.value = '';
  } catch (error) {
    const message = errorText(error, 'Не удалось обновить данные админ-панели.');
    loadError.value = message; setStatus('error', message);
  } finally { busy.reload = false; }
}
async function submitEntity(kind: 'user' | 'department' | 'teacherDirectory' | 'position' | 'teacher' | 'snapshot') {
  clearStatus();
  try {
    if (kind === 'user') {
      busy.user = true;
      if (editing.userId === null && !userForm.password.trim()) throw new Error('Для нового пользователя нужно указать пароль.');
      const isCreate = editing.userId === null;
      const payload: Record<string, unknown> = { username: userForm.username.trim(), full_name: userForm.full_name.trim(), role: userForm.role, is_active: userForm.is_active, department_id: userForm.department_id ? Number(userForm.department_id) : null, department_ids: normalizeDeptIds(userForm.department_id, userForm.department_ids), teacher_uuid: userForm.teacher_uuid || null };
      if (userForm.password.trim()) payload.password = userForm.password.trim();
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/users/' : `/users/${editing.userId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify(payload) });
      resetUserForm(); setStatus('success', isCreate ? 'Пользователь создан.' : 'Пользователь обновлён.');
    }
    if (kind === 'department') {
      busy.department = true;
      const isCreate = editing.departmentId === null;
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/departments/' : `/departments/${editing.departmentId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ name: departmentForm.name.trim(), short_name: departmentForm.short_name.trim() }) });
      resetDepartmentForm(); setStatus('success', isCreate ? 'Кафедра создана.' : 'Кафедра обновлена.');
    }
    if (kind === 'teacherDirectory') {
      busy.teacherDirectory = true;
      const isCreate = editing.teacherDirectoryUuid === null;
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/teacher-directory/' : `/teacher-directory/${editing.teacherDirectoryUuid}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ full_name: teacherDirectoryForm.full_name.trim(), department_ids: uniq(teacherDirectoryForm.department_ids) }) });
      resetTeacherDirectoryForm(); setStatus('success', isCreate ? 'Преподаватель справочника создан.' : 'Преподаватель справочника обновлён.');
    }
    if (kind === 'position') {
      busy.position = true;
      const isCreate = editing.positionId === null;
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/positions/' : `/positions/${editing.positionId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ name: positionForm.name.trim(), sort_order: Number(positionForm.sort_order), is_active: positionForm.is_active }) });
      resetPositionForm(); setStatus('success', isCreate ? 'Должность создана.' : 'Должность обновлена.');
    }
    if (kind === 'teacher') {
      busy.teacher = true;
      if (!teacherForm.department_id) throw new Error('Для преподавателя нужно выбрать кафедру.');
      const isCreate = editing.teacherId === null;
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/teachers/' : `/teachers/${editing.teacherId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ full_name: teacherForm.full_name.trim(), department_id: Number(teacherForm.department_id), position_id: teacherForm.position_id ? Number(teacherForm.position_id) : null }) });
      resetTeacherForm(); setStatus('success', isCreate ? 'Преподаватель создан.' : 'Преподаватель обновлён.');
    }
    if (kind === 'snapshot') {
      busy.snapshot = true;
      const isCreate = editing.snapshotId === null;
      const payload = { name: snapshotForm.name.trim(), semesterLabel: snapshotForm.semester_label.trim(), status: snapshotForm.status, sourceType: snapshotForm.source_type.trim(), description: snapshotForm.description.trim() || null, isReferenceForRetakes: snapshotForm.is_reference_for_retakes, capturedAt: fromLocalDateTime(snapshotForm.captured_at), groups: parseJsonArray(snapshotForm.groups_json, 'Группы'), subjects: parseJsonArray(snapshotForm.subjects_json, 'Дисциплины'), teachers: parseJsonArray(snapshotForm.teachers_json, 'Преподаватели'), scheduleItems: parseJsonArray(snapshotForm.schedule_items_json, 'Элементы расписания') };
      await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/schedule-snapshots/' : `/schedule-snapshots/${editing.snapshotId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify(payload) });
      resetSnapshotForm(); setStatus('success', isCreate ? 'Snapshot создан.' : 'Snapshot обновлён.');
    }
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Не удалось сохранить данные.'));
  } finally {
    busy.user = false; busy.department = false; busy.teacherDirectory = false; busy.position = false; busy.teacher = false; busy.snapshot = false;
  }
}

const editUser = (item: UserItem) => { clearStatus(); editing.userId = item.id; Object.assign(userForm, { username: item.username, full_name: item.fullName, role: item.role, is_active: item.isActive, department_id: item.departmentId === null ? '' : String(item.departmentId), department_ids: [...item.departmentIds], teacher_uuid: item.teacherUuid ?? '', password: '' }); };
const editDepartment = (item: DepartmentItem) => { clearStatus(); editing.departmentId = item.id; Object.assign(departmentForm, { name: item.name, short_name: item.short_name }); };
const editTeacherDirectory = (item: TeacherDirectoryItem) => { clearStatus(); editing.teacherDirectoryUuid = item.uuid; Object.assign(teacherDirectoryForm, { full_name: item.fullName, department_ids: [...item.departmentIds] }); };
const editPosition = (item: PositionItem) => { clearStatus(); editing.positionId = item.id; Object.assign(positionForm, { name: item.name, sort_order: item.sort_order, is_active: item.is_active }); };
const editTeacher = (item: TeacherItem) => { clearStatus(); editing.teacherId = item.id; Object.assign(teacherForm, { full_name: item.full_name, department_id: String(item.department_id), position_id: item.position_id === null ? '' : String(item.position_id) }); };
async function editSnapshot(item: SnapshotSummary) {
  clearStatus(); busy.snapshotLoad = true;
  try {
    const detail = await fetchBackendFromBrowser<SnapshotDetail>(props.backendApiUrl, `/schedule-snapshots/${item.id}`);
    editing.snapshotId = item.id;
    Object.assign(snapshotForm, { name: detail.name, semester_label: detail.semesterLabel, status: detail.status, source_type: detail.sourceType, description: detail.description ?? '', is_reference_for_retakes: detail.isReferenceForRetakes, captured_at: toLocalDateTime(detail.capturedAt), groups_json: JSON.stringify(detail.groups, null, 2), subjects_json: JSON.stringify(detail.subjects, null, 2), teachers_json: JSON.stringify(detail.teachers, null, 2), schedule_items_json: JSON.stringify(detail.scheduleItems, null, 2) });
  } catch (error) {
    setStatus('error', errorText(error, 'Не удалось загрузить snapshot.'));
  } finally { busy.snapshotLoad = false; }
}

async function deleteEntity(path: string, successMessage: string) {
  clearStatus();
  try { await fetchBackendFromBrowser(props.backendApiUrl, path, { method: 'DELETE' }); setStatus('success', successMessage); await reloadAll(); }
  catch (error) { setStatus('error', errorText(error, 'Не удалось удалить запись.')); }
}

async function importPastSemester() {
  busy.maintenance = true;
  try {
    const payload = await fetchBackendFromBrowser<{ message: string; sourcePath?: string }>(props.backendApiUrl, '/retakes/admin/past-semester/import', { method: 'POST', body: JSON.stringify({}) });
    setStatus('success', `${payload.message} Источник: ${payload.sourcePath ?? 'не указан'}.`);
  } catch (error) { setStatus('error', errorText(error, 'Не удалось импортировать данные за прошлый семестр.')); }
  finally { busy.maintenance = false; }
}
async function resetRetakes() {
  if (!window.confirm('Удалить все пересдачи и связи с преподавателями?')) return;
  busy.maintenance = true;
  try {
    const payload = await fetchBackendFromBrowser<{ message: string; deletedRetakes: number; deletedTeacherLinks: number }>(props.backendApiUrl, '/retakes/admin/reset', { method: 'POST' });
    setStatus('success', `${payload.message} Пересдач: ${payload.deletedRetakes}, связей: ${payload.deletedTeacherLinks}.`);
  } catch (error) { setStatus('error', errorText(error, 'Не удалось сбросить пересдачи.')); }
  finally { busy.maintenance = false; }
}
</script>
<template>
  <section class="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-6">
    <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
      <div class="flex flex-col gap-4 lg:flex-row lg:justify-between lg:items-end"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Администрирование</p><h1 class="mt-2 text-3xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">Панель администратора</h1><p class="mt-3 text-sm text-slate-500 dark:text-slate-400 max-w-3xl leading-7">Все CRUD-операции выполняются через backend API. Фронтенд остаётся thin client без локальной бизнес-логики.</p></div><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold disabled:opacity-60" :disabled="busy.reload" @click="reloadAll">{{ busy.reload ? 'Обновляем...' : 'Обновить данные' }}</button></div>
      <div v-if="status" class="rounded-2xl px-4 py-3 text-sm border" :class="status.kind === 'error' ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300' : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300'">{{ status.message }}</div>
      <div v-if="loadError" class="rounded-2xl px-4 py-3 text-sm border border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">{{ loadError }}</div>
      <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3 text-sm"><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Пользователи: <b>{{ users.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Кафедры: <b>{{ departments.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Справочник: <b>{{ teacherDirectory.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Должности: <b>{{ positions.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Преподаватели: <b>{{ teachers.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Snapshots: <b>{{ scheduleSnapshots.length }}</b></div><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4">Элементы: <b>{{ scheduleSnapshots.reduce((acc, item) => acc + item.scheduleItemCount, 0) }}</b></div></div>
    </div>

    <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 flex flex-wrap gap-3"><button type="button" class="h-11 px-5 rounded-2xl bg-blue-600 text-white text-sm font-black disabled:opacity-60" :disabled="busy.maintenance" @click="importPastSemester">{{ busy.maintenance ? 'Выполняем...' : 'Импортировать прошлый семестр' }}</button><button type="button" class="h-11 px-5 rounded-2xl bg-red-500 text-white text-sm font-black disabled:opacity-60" :disabled="busy.maintenance" @click="resetRetakes">{{ busy.maintenance ? 'Выполняем...' : 'Сбросить пересдачи' }}</button></div>

    <div class="grid gap-6 xl:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Пользователи</h2>
        <form class="grid gap-3" @submit.prevent="submitEntity('user')"><input v-model="userForm.username" type="text" required placeholder="Логин" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><input v-model="userForm.full_name" type="text" required placeholder="ФИО" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><div class="grid grid-cols-2 gap-3"><select v-model="userForm.role" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="ADMIN">ADMIN</option><option value="EMPLOYEE">EMPLOYEE</option><option value="TEACHER">TEACHER</option></select><select v-model="userForm.department_id" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="">Основная кафедра</option><option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.short_name }} ({{ department.name }})</option></select></div><select v-model="userForm.teacher_uuid" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="">Связанный преподаватель</option><option v-for="teacher in teacherDirectory" :key="teacher.uuid" :value="teacher.uuid">{{ teacher.fullName }} ({{ teacher.uuid }})</option></select><input v-model="userForm.password" :required="editing.userId === null" type="password" :placeholder="editing.userId === null ? 'Пароль' : 'Новый пароль (необязательно)'" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><label class="flex items-center gap-3 text-sm"><input v-model="userForm.is_active" type="checkbox" /> Активный пользователь</label><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Кафедры доступа</p><label v-for="department in departments" :key="department.id" class="flex items-center gap-3 text-sm"><input type="checkbox" :checked="userForm.department_ids.includes(department.id)" @change="userForm.department_ids = toggleSelection(userForm.department_ids, department.id, checkboxChecked($event))" /> {{ department.short_name }} ({{ department.name }})</label></div><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.user">{{ busy.user ? 'Сохраняем...' : editing.userId === null ? 'Создать' : 'Сохранить' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetUserForm">Сбросить</button></div></form>
        <div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10"><table class="w-full text-sm"><thead class="bg-slate-50 dark:bg-black/10"><tr><th class="px-3 py-2 text-left">Логин</th><th class="px-3 py-2 text-left">ФИО</th><th class="px-3 py-2 text-left">Кафедры</th><th class="px-3 py-2 text-left">Преподаватель</th><th class="px-3 py-2 text-left">Действия</th></tr></thead><tbody><tr v-for="item in users" :key="item.id" class="border-t border-slate-100 dark:border-white/10"><td class="px-3 py-2">{{ item.username }}<div class="text-xs text-slate-500">{{ item.role }} / {{ item.isActive ? 'активен' : 'деактивирован' }}</div></td><td class="px-3 py-2">{{ item.fullName }}</td><td class="px-3 py-2">{{ departmentLabel(item.departmentId) }}<div class="text-xs text-slate-500">{{ scopeLabel(item.departmentIds) }}</div></td><td class="px-3 py-2">{{ teacherDirectoryLabel(item.teacherUuid) }}</td><td class="px-3 py-2 flex gap-2"><button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold" @click="editUser(item)">Редактировать</button><button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold disabled:opacity-50" :disabled="item.id === props.currentUserId" @click="item.id === props.currentUserId ? setStatus('error', 'Нельзя удалить собственную учётную запись.') : deleteEntity(`/users/${item.id}`, 'Пользователь удалён.')">Удалить</button></td></tr></tbody></table></div>
      </div>
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Кафедры и должности</h2>
        <div class="grid gap-6 md:grid-cols-2">
          <form class="grid gap-3" @submit.prevent="submitEntity('department')"><input v-model="departmentForm.name" type="text" required placeholder="Название кафедры" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><input v-model="departmentForm.short_name" type="text" required placeholder="Сокращение" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.department">{{ busy.department ? 'Сохраняем...' : 'Сохранить кафедру' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetDepartmentForm">Сбросить</button></div><div class="space-y-2"><div v-for="item in departments" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm flex justify-between gap-3"><span>{{ item.short_name }} ({{ item.name }})</span><span class="flex gap-2"><button type="button" class="text-xs font-semibold" @click="editDepartment(item)">Редактировать</button><button type="button" class="text-xs font-semibold text-red-600 dark:text-red-300" @click="deleteEntity(`/departments/${item.id}`, 'Кафедра удалена.')">Удалить</button></span></div></div></form>
          <form class="grid gap-3" @submit.prevent="submitEntity('position')"><input v-model="positionForm.name" type="text" required placeholder="Название должности" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><input v-model.number="positionForm.sort_order" type="number" placeholder="Порядок сортировки" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><label class="flex items-center gap-3 text-sm"><input v-model="positionForm.is_active" type="checkbox" /> Активная должность</label><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.position">{{ busy.position ? 'Сохраняем...' : 'Сохранить должность' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetPositionForm">Сбросить</button></div><div class="space-y-2"><div v-for="item in positions" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm flex justify-between gap-3"><span>{{ item.name }}<span class="text-xs text-slate-500"> • {{ item.sort_order }} • {{ item.is_active ? 'активна' : 'неактивна' }}</span></span><span class="flex gap-2"><button type="button" class="text-xs font-semibold" @click="editPosition(item)">Редактировать</button><button type="button" class="text-xs font-semibold text-red-600 dark:text-red-300" @click="deleteEntity(`/positions/${item.id}`, 'Должность удалена.')">Удалить</button></span></div></div></form>
        </div>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Справочник преподавателей и преподаватели</h2>
        <div class="grid gap-6 md:grid-cols-2">
          <form class="grid gap-3" @submit.prevent="submitEntity('teacherDirectory')"><input v-model="teacherDirectoryForm.full_name" type="text" required placeholder="ФИО преподавателя в справочнике" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2"><label v-for="department in departments" :key="department.id" class="flex items-center gap-3 text-sm"><input type="checkbox" :checked="teacherDirectoryForm.department_ids.includes(department.id)" @change="teacherDirectoryForm.department_ids = toggleSelection(teacherDirectoryForm.department_ids, department.id, checkboxChecked($event))" /> {{ department.short_name }} ({{ department.name }})</label></div><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.teacherDirectory">{{ busy.teacherDirectory ? 'Сохраняем...' : 'Сохранить запись' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetTeacherDirectoryForm">Сбросить</button></div><div class="space-y-2"><div v-for="item in teacherDirectory" :key="item.uuid" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm"><div class="font-semibold">{{ item.fullName }}</div><div class="text-xs text-slate-500">{{ item.uuid }}</div><div class="text-xs text-slate-500 mt-1">{{ scopeLabel(item.departmentIds) }}</div><div class="mt-2 flex gap-2"><button type="button" class="text-xs font-semibold" @click="editTeacherDirectory(item)">Редактировать</button><button type="button" class="text-xs font-semibold text-red-600 dark:text-red-300" @click="deleteEntity(`/teacher-directory/${item.uuid}`, 'Преподаватель справочника удалён.')">Удалить</button></div></div></div></form>
          <form class="grid gap-3" @submit.prevent="submitEntity('teacher')"><input v-model="teacherForm.full_name" type="text" required placeholder="ФИО преподавателя" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><select v-model="teacherForm.department_id" required class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="">Кафедра</option><option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.short_name }} ({{ department.name }})</option></select><select v-model="teacherForm.position_id" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="">Должность не указана</option><option v-for="position in positions" :key="position.id" :value="String(position.id)">{{ position.name }}</option></select><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.teacher">{{ busy.teacher ? 'Сохраняем...' : 'Сохранить запись' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetTeacherForm">Сбросить</button></div><div class="space-y-2"><div v-for="item in teachers" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm"><div class="font-semibold">{{ item.full_name }}</div><div class="text-xs text-slate-500">{{ departmentLabel(item.department_id) }} • {{ positionLabel(item.position_id) }}</div><div class="mt-2 flex gap-2"><button type="button" class="text-xs font-semibold" @click="editTeacher(item)">Редактировать</button><button type="button" class="text-xs font-semibold text-red-600 dark:text-red-300" @click="deleteEntity(`/teachers/${item.id}`, 'Преподаватель удалён.')">Удалить</button></div></div></div></form>
        </div>
      </div>
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Schedule snapshots</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 leading-7">Snapshot хранит не только metadata, но и содержимое: `groups`, `subjects`, `teachers`, `scheduleItems`. Backend валидирует связи между ними.</p>
        <form class="grid gap-3" @submit.prevent="submitEntity('snapshot')"><input v-model="snapshotForm.name" type="text" required placeholder="Название snapshot" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><input v-model="snapshotForm.semester_label" type="text" required placeholder="Метка семестра" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /><div class="grid grid-cols-2 gap-3"><select v-model="snapshotForm.status" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="draft">draft</option><option value="published">published</option><option value="archived">archived</option></select><input v-model="snapshotForm.source_type" type="text" placeholder="Источник" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" /></div><textarea v-model="snapshotForm.description" rows="2" placeholder="Описание" class="px-4 py-3 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"></textarea><input v-model="snapshotForm.captured_at" type="datetime-local" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm [color-scheme:light] dark:[color-scheme:dark]" /><label class="flex items-center gap-3 text-sm"><input v-model="snapshotForm.is_reference_for_retakes" type="checkbox" /> Использовать как reference snapshot</label><textarea v-model="snapshotForm.groups_json" rows="3" class="px-4 py-3 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-xs font-mono" placeholder='[{"uuid":"g-1","number":"ИВТ-101","name":"ИВТ-101"}]'></textarea><textarea v-model="snapshotForm.subjects_json" rows="3" class="px-4 py-3 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-xs font-mono" placeholder='[{"uuid":"s-1","name":"Математика"}]'></textarea><textarea v-model="snapshotForm.teachers_json" rows="3" class="px-4 py-3 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-xs font-mono" placeholder='[{"uuid":"t-1","fullName":"Иван Иванов","departmentIds":[1]}]'></textarea><textarea v-model="snapshotForm.schedule_items_json" rows="5" class="px-4 py-3 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-xs font-mono" placeholder='[{"groupUuid":"g-1","subjectUuid":"s-1","teacherUuids":["t-1"],"weekday":1,"slot":2}]'></textarea><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.snapshot">{{ busy.snapshot ? 'Сохраняем...' : 'Сохранить snapshot' }}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetSnapshotForm">Сбросить</button></div></form>
        <div class="space-y-2"><div v-for="item in scheduleSnapshots" :key="item.id" class="rounded-2xl border border-slate-200 dark:border-white/10 p-3 text-sm"><div class="font-semibold">{{ item.name }}<span class="text-xs text-slate-500"> • {{ item.semesterLabel }}</span></div><div class="text-xs text-slate-500 mt-1">{{ item.status }} • {{ item.sourceType }} • reference: {{ item.isReferenceForRetakes ? 'да' : 'нет' }}</div><div class="text-xs text-slate-500 mt-1">Группы: {{ item.groupCount }}, дисциплины: {{ item.subjectCount }}, преподаватели: {{ item.teacherCount }}, элементы: {{ item.scheduleItemCount }}</div><div class="text-xs text-slate-500 mt-1">Снят: {{ formatDateTime(item.capturedAt) }} • Создан: {{ formatDateTime(item.createdAt) }}</div><div class="mt-2 flex gap-2"><button type="button" class="text-xs font-semibold disabled:opacity-60" :disabled="busy.snapshotLoad" @click="editSnapshot(item)">{{ busy.snapshotLoad && editing.snapshotId === item.id ? 'Загружаем...' : 'Редактировать' }}</button><button type="button" class="text-xs font-semibold text-red-600 dark:text-red-300" @click="deleteEntity(`/schedule-snapshots/${item.id}`, 'Snapshot удалён.')">Удалить</button></div></div></div>
      </div>
    </div>
  </section>
</template>
