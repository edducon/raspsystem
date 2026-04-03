<script setup lang="ts">
import { reactive, ref } from 'vue';

import { BackendApiError, fetchBackendFromBrowser } from '../lib/backend-api';

type UserRole = 'ADMIN' | 'EMPLOYEE' | 'TEACHER';
type StatusKind = 'success' | 'error';

interface UserItem {
  id: number;
  username: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  departmentId: number | null;
  departmentIds: number[];
  teacherUuid: string | null;
}

interface DepartmentItem {
  id: number;
  name: string;
  short_name: string;
}

interface TeacherDirectoryItem {
  uuid: string;
  fullName: string;
  departmentIds: number[];
}

const props = defineProps<{
  backendApiUrl: string;
  initialUsers: UserItem[];
  initialDepartments: DepartmentItem[];
  initialTeacherDirectory: TeacherDirectoryItem[];
  initialLoadError?: string;
}>();

const users = ref([...props.initialUsers]);
const departments = ref([...props.initialDepartments]);
const teacherDirectory = ref([...props.initialTeacherDirectory]);
const loadError = ref(props.initialLoadError ?? '');
const status = ref<{ kind: StatusKind; message: string } | null>(null);
const busy = reactive({ reload: false, user: false, department: false, teacher: false, maintenance: false });
const editing = reactive<{ userId: number | null; departmentId: number | null; teacherUuid: string | null }>({
  userId: null,
  departmentId: null,
  teacherUuid: null,
});

const userForm = reactive({
  username: '',
  full_name: '',
  role: 'EMPLOYEE' as UserRole,
  is_active: true,
  department_id: '',
  department_ids: [] as number[],
  teacher_uuid: '',
  password: '',
});

const departmentForm = reactive({ name: '', short_name: '' });
const teacherForm = reactive({ full_name: '', department_ids: [] as number[] });

const errorText = (error: unknown, fallback: string) =>
  error instanceof BackendApiError ? error.detail : error instanceof Error ? error.message : fallback;
const setStatus = (kind: StatusKind, message: string) => {
  status.value = { kind, message };
};
const clearStatus = () => {
  status.value = null;
};
const uniq = (values: number[]) => [...new Set(values)];
const normalizeDeptIds = (primaryId: string, ids: number[]) => {
  const next = uniq(ids);
  if (primaryId) next.includes(Number(primaryId)) || next.push(Number(primaryId));
  return next;
};
const scopeLabel = (ids: number[]) =>
  ids.length
    ? ids
        .map((id) => {
          const department = departments.value.find((item) => item.id === id);
          return department ? `${department.short_name} (${department.name})` : `#${id}`;
        })
        .join(', ')
    : 'None';
const teacherLabel = (uuid: string | null) => {
  if (!uuid) return 'None';
  const teacher = teacherDirectory.value.find((item) => item.uuid === uuid);
  return teacher ? `${teacher.fullName} (${teacher.uuid})` : uuid;
};

function resetUserForm() {
  Object.assign(userForm, { username: '', full_name: '', role: 'EMPLOYEE', is_active: true, department_id: '', department_ids: [], teacher_uuid: '', password: '' });
  editing.userId = null;
}

function resetDepartmentForm() {
  Object.assign(departmentForm, { name: '', short_name: '' });
  editing.departmentId = null;
}

function resetTeacherForm() {
  Object.assign(teacherForm, { full_name: '', department_ids: [] });
  editing.teacherUuid = null;
}

function toggleSelection(target: number[], value: number, checked: boolean) {
  return checked ? uniq([...target, value]) : target.filter((item) => item !== value);
}

function checkboxChecked(event: Event) {
  return event.target instanceof HTMLInputElement ? event.target.checked : false;
}

async function reloadAll() {
  busy.reload = true;
  try {
    const [nextUsers, nextDepartments, nextTeacherDirectory] = await Promise.all([
      fetchBackendFromBrowser<UserItem[]>(props.backendApiUrl, '/users/'),
      fetchBackendFromBrowser<DepartmentItem[]>(props.backendApiUrl, '/departments/'),
      fetchBackendFromBrowser<TeacherDirectoryItem[]>(props.backendApiUrl, '/teacher-directory/'),
    ]);
    users.value = nextUsers;
    departments.value = nextDepartments;
    teacherDirectory.value = nextTeacherDirectory;
    loadError.value = '';
  } catch (error) {
    const message = errorText(error, 'Failed to reload admin data');
    loadError.value = message;
    setStatus('error', message);
  } finally {
    busy.reload = false;
  }
}

function editUser(user: UserItem) {
  clearStatus();
  editing.userId = user.id;
  Object.assign(userForm, { username: user.username, full_name: user.fullName, role: user.role, is_active: user.isActive, department_id: user.departmentId === null ? '' : String(user.departmentId), department_ids: [...user.departmentIds], teacher_uuid: user.teacherUuid ?? '', password: '' });
}

function editDepartment(department: DepartmentItem) {
  clearStatus();
  editing.departmentId = department.id;
  Object.assign(departmentForm, { name: department.name, short_name: department.short_name });
}

function editTeacher(teacher: TeacherDirectoryItem) {
  clearStatus();
  editing.teacherUuid = teacher.uuid;
  Object.assign(teacherForm, { full_name: teacher.fullName, department_ids: [...teacher.departmentIds] });
}

async function submitUser() {
  clearStatus();
  if (editing.userId === null && !userForm.password.trim()) return setStatus('error', 'Password is required for new users');
  busy.user = true;
  try {
    const isCreate = editing.userId === null;
    const payload: Record<string, unknown> = {
      username: userForm.username.trim(),
      full_name: userForm.full_name.trim(),
      role: userForm.role,
      is_active: userForm.is_active,
      department_id: userForm.department_id ? Number(userForm.department_id) : null,
      department_ids: normalizeDeptIds(userForm.department_id, userForm.department_ids),
      teacher_uuid: userForm.teacher_uuid || null,
    };
    if (userForm.password.trim()) payload.password = userForm.password.trim();
    await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/users/' : `/users/${editing.userId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify(payload) });
    resetUserForm();
    setStatus('success', isCreate ? 'User created' : 'User updated');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to save user'));
  } finally {
    busy.user = false;
  }
}

async function removeUser(user: UserItem) {
  if (!window.confirm(`Delete user "${user.username}"?`)) return;
  busy.user = true;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/users/${user.id}`, { method: 'DELETE' });
    if (editing.userId === user.id) resetUserForm();
    setStatus('success', 'User deleted');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to delete user'));
  } finally {
    busy.user = false;
  }
}

async function submitDepartment() {
  clearStatus();
  busy.department = true;
  try {
    const isCreate = editing.departmentId === null;
    await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/departments/' : `/departments/${editing.departmentId}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ name: departmentForm.name.trim(), short_name: departmentForm.short_name.trim() }) });
    resetDepartmentForm();
    setStatus('success', isCreate ? 'Department created' : 'Department updated');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to save department'));
  } finally {
    busy.department = false;
  }
}

async function removeDepartment(department: DepartmentItem) {
  if (!window.confirm(`Delete department "${department.name}"?`)) return;
  busy.department = true;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/departments/${department.id}`, { method: 'DELETE' });
    if (editing.departmentId === department.id) resetDepartmentForm();
    setStatus('success', 'Department deleted');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to delete department'));
  } finally {
    busy.department = false;
  }
}

async function submitTeacher() {
  clearStatus();
  busy.teacher = true;
  try {
    const isCreate = editing.teacherUuid === null;
    await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? '/teacher-directory/' : `/teacher-directory/${editing.teacherUuid}`, { method: isCreate ? 'POST' : 'PUT', body: JSON.stringify({ full_name: teacherForm.full_name.trim(), department_ids: uniq(teacherForm.department_ids) }) });
    resetTeacherForm();
    setStatus('success', isCreate ? 'Local teacher created' : 'Local teacher updated');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to save local teacher'));
  } finally {
    busy.teacher = false;
  }
}

async function removeTeacher(teacher: TeacherDirectoryItem) {
  if (!window.confirm(`Delete local teacher "${teacher.fullName}"?`)) return;
  busy.teacher = true;
  try {
    await fetchBackendFromBrowser(props.backendApiUrl, `/teacher-directory/${teacher.uuid}`, { method: 'DELETE' });
    if (editing.teacherUuid === teacher.uuid) resetTeacherForm();
    setStatus('success', 'Local teacher deleted');
    await reloadAll();
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to delete local teacher'));
  } finally {
    busy.teacher = false;
  }
}

async function importPastSemester() {
  busy.maintenance = true;
  try {
    const payload = await fetchBackendFromBrowser<{ message: string; sourcePath?: string }>(props.backendApiUrl, '/retakes/admin/past-semester/import', { method: 'POST', body: JSON.stringify({}) });
    setStatus('success', `${payload.message}. Source: ${payload.sourcePath ?? 'n/a'}`);
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to import past semester'));
  } finally {
    busy.maintenance = false;
  }
}

async function resetRetakes() {
  if (!window.confirm('Delete all retakes and retake teacher links?')) return;
  busy.maintenance = true;
  try {
    const payload = await fetchBackendFromBrowser<{ message: string; deletedRetakes: number; deletedTeacherLinks: number }>(props.backendApiUrl, '/retakes/admin/reset', { method: 'POST' });
    setStatus('success', `${payload.message}. Retakes: ${payload.deletedRetakes}, links: ${payload.deletedTeacherLinks}`);
  } catch (error) {
    setStatus('error', errorText(error, 'Failed to reset retakes'));
  } finally {
    busy.maintenance = false;
  }
}
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-6">
    <div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] space-y-4">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Backend admin</p>
          <h1 class="mt-2 text-3xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">Admin panel on backend API</h1>
          <p class="mt-3 text-sm text-slate-500 dark:text-slate-400 max-w-3xl leading-7">
            CRUD forms below use FastAPI directly. No Astro actions, no frontend DB writes, no legacy auth fallbacks.
          </p>
        </div>
        <button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold disabled:opacity-60" :disabled="busy.reload" @click="reloadAll">
          {{ busy.reload ? 'Refreshing...' : 'Refresh data' }}
        </button>
      </div>

      <div v-if="status" class="rounded-2xl px-4 py-3 text-sm border" :class="status.kind === 'error' ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300' : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300'">
        {{ status.message }}
      </div>
      <div v-if="loadError" class="rounded-2xl px-4 py-3 text-sm border border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
        {{ loadError }}
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Users</p>
        <div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">{{ users.length }}</div>
      </div>
      <div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p>
        <div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">{{ departments.length }}</div>
      </div>
      <div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Teacher Directory</p>
        <div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">{{ teacherDirectory.length }}</div>
      </div>
    </div>

    <div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
      <div>
        <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Maintenance</p>
        <h2 class="mt-2 text-2xl font-black text-slate-950 dark:text-white">Retake admin operations</h2>
      </div>
      <div class="flex flex-wrap gap-3">
        <button type="button" class="h-11 px-5 rounded-2xl bg-blue-600 text-white text-sm font-black disabled:opacity-60" :disabled="busy.maintenance" @click="importPastSemester">
          {{ busy.maintenance ? 'Working...' : 'Import past semester' }}
        </button>
        <button type="button" class="h-11 px-5 rounded-2xl bg-red-500 text-white text-sm font-black disabled:opacity-60" :disabled="busy.maintenance" @click="resetRetakes">
          {{ busy.maintenance ? 'Working...' : 'Reset retakes' }}
        </button>
      </div>
    </div>

    <div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <div class="grid gap-6 lg:grid-cols-[360px,minmax(0,1fr)]">
        <form class="space-y-4" @submit.prevent="submitUser">
          <div>
            <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Users</p>
            <h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">{{ editing.userId === null ? 'Create user' : `Edit user #${editing.userId}` }}</h2>
          </div>
          <input v-model="userForm.username" type="text" required placeholder="Username" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <input v-model="userForm.full_name" type="text" required placeholder="Full name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <div class="grid gap-3 sm:grid-cols-2">
            <select v-model="userForm.role" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm">
              <option value="ADMIN">ADMIN</option>
              <option value="EMPLOYEE">EMPLOYEE</option>
              <option value="TEACHER">TEACHER</option>
            </select>
            <select v-model="userForm.department_id" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm">
              <option value="">Primary department: none</option>
              <option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.short_name }} ({{ department.name }})</option>
            </select>
          </div>
          <select v-model="userForm.teacher_uuid" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm">
            <option value="">Linked teacher: none</option>
            <option v-for="teacher in teacherDirectory" :key="teacher.uuid" :value="teacher.uuid">{{ teacher.fullName }} ({{ teacher.uuid }})</option>
          </select>
          <input v-model="userForm.password" :required="editing.userId === null" type="password" :placeholder="editing.userId === null ? 'Password' : 'Password (optional)'" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <label class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200"><input v-model="userForm.is_active" type="checkbox" /> <span>Active user</span></label>
          <div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Department scope</p>
            <label v-for="department in departments" :key="department.id" class="flex items-center gap-3 text-sm">
              <input type="checkbox" :checked="userForm.department_ids.includes(department.id)" @change="userForm.department_ids = toggleSelection(userForm.department_ids, department.id, checkboxChecked($event))" />
              <span>{{ department.short_name }} ({{ department.name }})</span>
            </label>
          </div>
          <div class="flex gap-3">
            <button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.user">{{ busy.user ? 'Saving...' : editing.userId === null ? 'Create user' : 'Save changes' }}</button>
            <button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetUserForm">Reset</button>
          </div>
        </form>

        <div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400">
              <tr>
                <th class="px-4 py-3 text-left">Username</th>
                <th class="px-4 py-3 text-left">Full name</th>
                <th class="px-4 py-3 text-left">Role</th>
                <th class="px-4 py-3 text-left">Departments</th>
                <th class="px-4 py-3 text-left">Teacher</th>
                <th class="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="users.length === 0" class="border-t border-slate-100 dark:border-white/10"><td colspan="6" class="px-4 py-6 text-slate-500">No users.</td></tr>
              <tr v-for="user in users" :key="user.id" class="border-t border-slate-100 dark:border-white/10 align-top">
                <td class="px-4 py-3 font-mono text-xs">{{ user.username }}<div class="mt-1">{{ user.isActive ? 'active' : 'inactive' }}</div></td>
                <td class="px-4 py-3">{{ user.fullName }}</td>
                <td class="px-4 py-3">{{ user.role }}</td>
                <td class="px-4 py-3"><div>{{ user.departmentId === null ? 'None' : scopeLabel([user.departmentId]) }}</div><div class="mt-1 text-xs">{{ scopeLabel(user.departmentIds) }}</div></td>
                <td class="px-4 py-3">{{ teacherLabel(user.teacherUuid) }}</td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap gap-2">
                    <button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold" @click="editUser(user)">Edit</button>
                    <button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold" @click="removeUser(user)">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <div class="grid gap-6 lg:grid-cols-[300px,minmax(0,1fr)]">
        <form class="space-y-4" @submit.prevent="submitDepartment">
          <div>
            <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p>
            <h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">{{ editing.departmentId === null ? 'Create department' : `Edit department #${editing.departmentId}` }}</h2>
          </div>
          <input v-model="departmentForm.name" type="text" required placeholder="Department name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <input v-model="departmentForm.short_name" type="text" required placeholder="Short name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <div class="flex gap-3">
            <button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.department">{{ busy.department ? 'Saving...' : editing.departmentId === null ? 'Create department' : 'Save changes' }}</button>
            <button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetDepartmentForm">Reset</button>
          </div>
        </form>

        <div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400">
              <tr>
                <th class="px-4 py-3 text-left">ID</th>
                <th class="px-4 py-3 text-left">Name</th>
                <th class="px-4 py-3 text-left">Short name</th>
                <th class="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="departments.length === 0" class="border-t border-slate-100 dark:border-white/10"><td colspan="4" class="px-4 py-6 text-slate-500">No departments.</td></tr>
              <tr v-for="department in departments" :key="department.id" class="border-t border-slate-100 dark:border-white/10">
                <td class="px-4 py-3 font-mono text-xs">{{ department.id }}</td>
                <td class="px-4 py-3">{{ department.name }}</td>
                <td class="px-4 py-3">{{ department.short_name }}</td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap gap-2">
                    <button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold" @click="editDepartment(department)">Edit</button>
                    <button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold" @click="removeDepartment(department)">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <div class="grid gap-6 lg:grid-cols-[360px,minmax(0,1fr)]">
        <form class="space-y-4" @submit.prevent="submitTeacher">
          <div>
            <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Teacher directory</p>
            <h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">{{ editing.teacherUuid === null ? 'Create local teacher' : `Edit local teacher ${editing.teacherUuid}` }}</h2>
          </div>
          <div v-if="editing.teacherUuid" class="rounded-2xl border border-slate-200 dark:border-white/10 px-4 py-3 text-sm">UUID: <span class="font-mono text-xs">{{ editing.teacherUuid }}</span></div>
          <input v-model="teacherForm.full_name" type="text" required placeholder="Teacher full name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p>
            <label v-for="department in departments" :key="department.id" class="flex items-center gap-3 text-sm">
              <input type="checkbox" :checked="teacherForm.department_ids.includes(department.id)" @change="teacherForm.department_ids = toggleSelection(teacherForm.department_ids, department.id, checkboxChecked($event))" />
              <span>{{ department.short_name }} ({{ department.name }})</span>
            </label>
          </div>
          <div class="flex gap-3">
            <button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60" :disabled="busy.teacher">{{ busy.teacher ? 'Saving...' : editing.teacherUuid === null ? 'Create local teacher' : 'Save changes' }}</button>
            <button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold" @click="resetTeacherForm">Reset</button>
          </div>
        </form>

        <div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10 max-h-[540px]">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400 sticky top-0">
              <tr>
                <th class="px-4 py-3 text-left">UUID</th>
                <th class="px-4 py-3 text-left">Full name</th>
                <th class="px-4 py-3 text-left">Departments</th>
                <th class="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="teacherDirectory.length === 0" class="border-t border-slate-100 dark:border-white/10"><td colspan="4" class="px-4 py-6 text-slate-500">No local teachers.</td></tr>
              <tr v-for="teacher in teacherDirectory" :key="teacher.uuid" class="border-t border-slate-100 dark:border-white/10 align-top">
                <td class="px-4 py-3 font-mono text-xs">{{ teacher.uuid }}</td>
                <td class="px-4 py-3">{{ teacher.fullName }}</td>
                <td class="px-4 py-3">{{ scopeLabel(teacher.departmentIds) }}</td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap gap-2">
                    <button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold" @click="editTeacher(teacher)">Edit</button>
                    <button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold" @click="removeTeacher(teacher)">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>
