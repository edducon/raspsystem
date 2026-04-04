<script setup lang="ts">
import { reactive, ref } from 'vue';
import { BackendApiError, fetchBackendFromBrowser } from '../lib/backend-api';

type UserRole = 'ADMIN' | 'EMPLOYEE' | 'TEACHER';
type StatusKind = 'success' | 'error';
type SnapshotSummary = { id: number; name: string; semesterLabel: string; status: string; sourceType: string; description: string | null; isReferenceForRetakes: boolean; capturedAt: string | null; createdAt: string; groupCount: number; subjectCount: number; teacherCount: number; scheduleItemCount: number };
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
}>();

const users = ref([...props.initialUsers]);
const departments = ref([...props.initialDepartments]);
const teacherDirectory = ref([...props.initialTeacherDirectory]);
const positions = ref([...props.initialPositions]);
const teachers = ref([...props.initialTeachers]);
const scheduleSnapshots = ref([...props.initialScheduleSnapshots]);
const status = ref<{ kind: StatusKind; message: string } | null>(null);

const activeTab = ref('teachers');
const tabs = [
  { id: 'teachers', label: 'Преподаватели' },
  { id: 'users', label: 'Пользователи' },
  { id: 'departments', label: 'Кафедры и должности' },
  { id: 'snapshots', label: 'Снимки расписания' }
];

const busy = reactive({ reload: false, maintenance: false, flow: false, department: false, position: false, user: false });

const showTeacherModal = ref(false);
const teacherFlowForm = reactive({ full_name: '', department_id: '', position_id: '', create_account: false, username: '', password: '' });
const departmentForm = reactive({ name: '', short_name: '' });
const positionForm = reactive({ name: '', sort_order: 0, is_active: true });
const userForm = reactive({ username: '', full_name: '', role: 'EMPLOYEE' as UserRole, is_active: true, department_id: '', department_ids: [] as number[], teacher_uuid: '', password: '' });

const errorText = (error: unknown, fallback: string) => error instanceof BackendApiError ? error.detail : error instanceof Error ? error.message : fallback;
const setStatus = (kind: StatusKind, message: string) => { status.value = { kind, message }; setTimeout(() => status.value = null, 5000); };

const getDepartmentName = (id: number | null | string) => {
  if (!id) return '—';
  const dept = departments.value.find(d => String(d.id) === String(id));
  return dept ? dept.short_name : `ID:${id}`;
};

const getPositionName = (id: number | null | string) => {
  if (!id) return '—';
  const pos = positions.value.find(p => String(p.id) === String(id));
  return pos ? pos.name : `ID:${id}`;
};

const getAccountForTeacher = (fullName: string) => users.value.find(u => u.fullName === fullName);

async function reloadAll() {
  busy.reload = true;
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
  } catch (error) { setStatus('error', errorText(error, 'Ошибка обновления данных.')); }
  finally { busy.reload = false; }
}

async function submitDepartment() {
  busy.department = true;
  try {
    // Используем camelCase для Pydantic v2
    await fetchBackendFromBrowser(props.backendApiUrl, '/departments/', {
      method: 'POST',
      body: JSON.stringify({ name: departmentForm.name.trim(), shortName: departmentForm.short_name.trim() })
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
    // Используем camelCase для Pydantic v2
    await fetchBackendFromBrowser(props.backendApiUrl, '/positions/', {
      method: 'POST',
      body: JSON.stringify({ name: positionForm.name.trim(), sortOrder: Number(positionForm.sort_order), isActive: positionForm.is_active })
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
    const directoryRes = await fetchBackendFromBrowser<{uuid: string}>(props.backendApiUrl, '/teacher-directory/', {
      method: 'POST', body: JSON.stringify({ fullName: teacherFlowForm.full_name, departmentIds: [Number(teacherFlowForm.department_id)] })
    });

    await fetchBackendFromBrowser(props.backendApiUrl, '/teachers/', {
      method: 'POST', body: JSON.stringify({ fullName: teacherFlowForm.full_name, departmentId: Number(teacherFlowForm.department_id), positionId: teacherFlowForm.position_id ? Number(teacherFlowForm.position_id) : null })
    });

    if (teacherFlowForm.create_account) {
      await fetchBackendFromBrowser(props.backendApiUrl, '/users/', {
        method: 'POST', body: JSON.stringify({ username: teacherFlowForm.username, password: teacherFlowForm.password, fullName: teacherFlowForm.full_name, role: 'TEACHER', isActive: true, departmentId: Number(teacherFlowForm.department_id), departmentIds: [Number(teacherFlowForm.department_id)], teacherUuid: directoryRes.uuid })
      });
    }

    setStatus('success', 'Преподаватель успешно добавлен!');
    showTeacherModal.value = false;
    Object.assign(teacherFlowForm, { full_name: '', department_id: '', position_id: '', create_account: false, username: '', password: '' });
    await reloadAll();
  } catch (error) { setStatus('error', errorText(error, 'Ошибка при создании преподавателя.')); }
  finally { busy.flow = false; }
}

async function deleteEntity(path: string, msg: string) {
  if (!window.confirm('Вы уверены?')) return;
  try { await fetchBackendFromBrowser(props.backendApiUrl, path, { method: 'DELETE' }); setStatus('success', msg); await reloadAll(); }
  catch(error) { setStatus('error', 'Ошибка при удалении.'); }
}

function formatDateTime(value: string | null) {
  return value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : 'Не указано';
}
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-6 relative">

    <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 mb-6">
      <div class="flex justify-between items-end">
        <div>
          <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Администрирование</p>
          <h1 class="text-3xl font-black text-slate-900 dark:text-white mt-2">Панель администратора</h1>
        </div>
        <div class="flex gap-3">
          <button @click="reloadAll" class="px-5 py-2.5 bg-white dark:bg-white/10 border border-slate-300 dark:border-white/10 rounded-2xl text-sm font-bold shadow-sm hover:bg-slate-50 dark:hover:bg-white/20 transition-colors">
            {{ busy.reload ? 'Обновление...' : 'Синхронизировать' }}
          </button>
        </div>
      </div>

      <div v-if="status" class="mt-4 p-4 rounded-xl text-sm font-medium border" :class="status.kind === 'error' ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800/30 dark:text-red-300' : 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800/30 dark:text-green-300'">
        {{ status.message }}
      </div>
    </div>

    <div class="flex space-x-6 border-b border-slate-200 dark:border-white/10 overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
              :class="['pb-4 text-sm font-bold transition-colors whitespace-nowrap', activeTab === tab.id ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300']">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="activeTab === 'teachers'" class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <div class="flex flex-wrap justify-between items-center mb-6 gap-4">
        <h2 class="text-xl font-black text-slate-900 dark:text-white">Штат преподавателей</h2>
        <div class="flex gap-2">
          <button class="px-4 py-2 border border-slate-300 dark:border-white/20 rounded-xl text-sm font-bold hover:bg-slate-50 dark:hover:bg-white/10">🔄 Подтянуть из API</button>
          <button @click="showTeacherModal = true" class="px-5 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all">+ Добавить</button>
        </div>
      </div>

      <div class="overflow-x-auto rounded-2xl border border-slate-100 dark:border-white/5">
        <table class="w-full text-sm text-left">
          <thead class="bg-slate-50 dark:bg-black/20 text-slate-600 dark:text-slate-400">
          <tr>
            <th class="px-5 py-4 font-bold">ФИО Преподавателя</th>
            <th class="px-5 py-4 font-bold">Кафедра</th>
            <th class="px-5 py-4 font-bold">Должность</th>
            <th class="px-5 py-4 font-bold">Аккаунт системы</th>
            <th class="px-5 py-4 font-bold text-right">Действия</th>
          </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-white/5">
          <tr v-for="t in teachers" :key="t.id" class="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
            <td class="px-5 py-4 font-semibold text-slate-900 dark:text-white">{{ t.full_name }}</td>
            <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ getDepartmentName(t.department_id) }}</td>
            <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ getPositionName(t.position_id) }}</td>
            <td class="px-5 py-4">
              <span v-if="getAccountForTeacher(t.full_name)" class="px-2.5 py-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 rounded-lg text-xs font-bold">Есть ({{ getAccountForTeacher(t.full_name)?.username }})</span>
              <span v-else class="px-2.5 py-1 bg-slate-100 text-slate-500 dark:bg-white/10 dark:text-slate-400 rounded-lg text-xs font-bold">Нет</span>
            </td>
            <td class="px-5 py-4 text-right">
              <button @click="deleteEntity(`/teachers/${t.id}`, 'Удалено')" class="text-red-500 font-bold hover:text-red-700 text-xs">Удалить</button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showTeacherModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div class="bg-white dark:bg-slate-900 rounded-3xl p-8 max-w-md w-full shadow-2xl relative border border-slate-200 dark:border-slate-700">
        <h3 class="text-2xl font-black mb-6 dark:text-white">Новый преподаватель</h3>
        <form @submit.prevent="submitTeacherFlow" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 mb-1">ФИО (Полностью)</label>
            <input v-model="teacherFlowForm.full_name" required type="text" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Кафедра</label>
              <select v-model="teacherFlowForm.department_id" required class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm">
                <option value="" disabled>Выберите...</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.short_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Должность</label>
              <select v-model="teacherFlowForm.position_id" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 dark:text-white text-sm">
                <option value="">Не указана</option>
                <option v-for="p in positions" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
          </div>
          <div class="pt-4 border-t border-slate-100 dark:border-slate-700 mt-2">
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="teacherFlowForm.create_account" type="checkbox" class="w-5 h-5 rounded" />
              <span class="text-sm font-bold dark:text-slate-300">Создать аккаунт для входа</span>
            </label>
          </div>
          <div v-if="teacherFlowForm.create_account" class="space-y-4 bg-blue-50/50 dark:bg-blue-900/10 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/30">
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Логин</label>
              <input v-model="teacherFlowForm.username" required type="text" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 dark:text-white text-sm" />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 mb-1">Пароль</label>
              <input v-model="teacherFlowForm.password" required type="password" class="w-full h-11 px-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 dark:text-white text-sm" />
            </div>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="submit" :disabled="busy.flow" class="flex-1 h-12 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">Создать</button>
            <button type="button" @click="showTeacherModal = false" class="px-6 h-12 bg-slate-100 dark:bg-slate-800 dark:text-white rounded-xl font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">Отмена</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="activeTab === 'departments'" class="grid gap-6 md:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4">
        <h2 class="text-xl font-black text-slate-950 dark:text-white">Кафедры</h2>
        <form class="grid gap-3" @submit.prevent="submitDepartment">
          <input v-model="departmentForm.name" type="text" required placeholder="Полное название кафедры" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <input v-model="departmentForm.short_name" type="text" required placeholder="Аббревиатура (напр. ИВТ)" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
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
          <input v-model="positionForm.name" type="text" required placeholder="Название должности" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
          <input v-model.number="positionForm.sort_order" type="number" placeholder="Порядок сортировки (цифра)" class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm" />
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

    <div v-if="activeTab === 'snapshots'" class="rounded-3xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6">
      <h2 class="text-xl font-black dark:text-white mb-6">Снимки расписания (Эталоны)</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="item in scheduleSnapshots" :key="item.id" class="p-5 border rounded-3xl" :class="item.isReferenceForRetakes ? 'border-green-400 bg-green-50 dark:bg-green-900/10 dark:border-green-600' : 'border-slate-200 dark:border-white/10 bg-white dark:bg-white/5'">
          <span v-if="item.isReferenceForRetakes" class="px-2.5 py-1 bg-green-500 text-white text-[10px] uppercase font-black rounded-lg mb-2 inline-block">Текущий эталон</span>
          <div class="font-bold text-lg dark:text-white">{{ item.name }}</div>
          <div class="text-sm text-slate-600 dark:text-slate-300 font-medium">Семестр: {{ item.semesterLabel }}</div>
          <div class="text-xs text-slate-500 mt-3 space-y-1">
            <p>Групп: {{item.groupCount}} | Предметов: {{item.subjectCount}} | Записей: {{item.scheduleItemCount}}</p>
            <p>Дата фиксации: {{ formatDateTime(item.capturedAt) }}</p>
          </div>
        </div>
      </div>

      <div class="mt-8 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30 p-5 rounded-2xl">
        <h3 class="font-bold text-blue-900 dark:text-blue-300 mb-2">Обновление расписания на новый семестр</h3>
        <p class="text-sm text-blue-700 dark:text-blue-400 mb-4">Для загрузки нового эталонного расписания, подготовьте JSON файл. Загрузка через интерфейс будет добавлена в следующем обновлении API.</p>
        <button class="px-6 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-xl text-sm disabled:opacity-50" disabled>Загрузить файл (Скоро)</button>
      </div>
    </div>

  </section>
</template>