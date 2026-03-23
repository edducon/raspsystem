<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { Search, UserPlus, Save, Building, Users as UsersIcon, Plus, Edit2, Trash2, X, AlertTriangle, ShieldCheck } from 'lucide-vue-next';
import { actions } from 'astro:actions';
import { addToast } from '../composables/useToast';

const props = defineProps<{
  teachers: any[];
  departments: any[];
}>();

const activeTab = ref<'teachers' | 'departments'>('teachers');

onMounted(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('tab') === 'departments') {
    activeTab.value = 'departments';
  }
});

watch(activeTab, (newTab) => {
  const url = new URL(window.location.href);
  url.searchParams.set('tab', newTab);
  window.history.replaceState({}, '', url);
});

const searchQuery = ref('');
const teachersList = ref([...props.teachers].map(t => ({
  ...t,
  departmentIds: t.departmentIds || []
})));
const deptList = ref([...props.departments]);

const filteredTeachers = computed(() => {
  if (!searchQuery.value) return teachersList.value.slice(0, 50);
  const q = searchQuery.value.toLowerCase();
  return teachersList.value.filter(t => t.fullName.toLowerCase().includes(q)).slice(0, 50);
});

const openDeptDropdown = ref<string | null>(null);

const showProfileModal = ref(false);
const selectedTeacher = ref<any>(null);
const newProfile = ref({ username: '', password: '', role: 'TEACHER' as 'TEACHER' | 'EMPLOYEE' });
const isSubmitting = ref(false);

const generatePassword = () => Math.random().toString(36).slice(-6) + Math.floor(Math.random() * 100);

const openProfileModal = (teacher: any) => {
  if (!teacher.departmentIds || teacher.departmentIds.length === 0) {
    return addToast("Сначала назначьте преподавателю хотя бы одну кафедру!", "error");
  }
  selectedTeacher.value = teacher;
  const lastName = teacher.fullName.split(' ')[0].toLowerCase();
  newProfile.value.username = `${lastName}${Math.floor(100 + Math.random() * 900)}`;
  newProfile.value.password = generatePassword();
  newProfile.value.role = 'TEACHER';
  showProfileModal.value = true;
};

const changeDepartment = async (teacherUuid: string, newDeptIds: number[]) => {
  const { error } = await actions.admin.updateTeacherDept({ teacherUuid, departmentIds: newDeptIds });
  if (error) addToast(error.message, "error");
  else addToast("Кафедры обновлены", "success");
};

const submitProfile = async () => {
  isSubmitting.value = true;
  const { data, error } = await actions.admin.createProfile({
    teacherUuid: selectedTeacher.value.uuid,
    username: newProfile.value.username,
    password: newProfile.value.password,
    departmentIds: selectedTeacher.value.departmentIds,
    role: newProfile.value.role
  });
  isSubmitting.value = false;

  if (error) {
    addToast(error.message, "error");
  } else {
    addToast(data.message, "success");
    const tIndex = teachersList.value.findIndex(t => t.uuid === selectedTeacher.value.uuid);
    if (tIndex !== -1) {
      teachersList.value[tIndex].hasProfile = true;
      teachersList.value[tIndex].userRole = newProfile.value.role;
    }
    showProfileModal.value = false;
  }
};

const toggleRole = async (teacher: any) => {
  const newRole = teacher.userRole === 'EMPLOYEE' ? 'TEACHER' : 'EMPLOYEE';
  const actionName = newRole === 'EMPLOYEE' ? 'Назначен диспетчером' : 'Права диспетчера сняты';

  const { error } = await actions.admin.changeRole({ teacherUuid: teacher.uuid, newRole });
  if (error) {
    addToast(error.message, "error");
  } else {
    teacher.userRole = newRole;
    addToast(actionName, "success");
  }
};

const newDeptName = ref('');
const editingDeptId = ref<number | null>(null);
const editDeptName = ref('');

const showDeleteModal = ref(false);
const deptToDelete = ref<{id: number, name: string} | null>(null);

const addDepartment = async () => {
  if (!newDeptName.value) return;
  const { data, error } = await actions.admin.addDepartment({ name: newDeptName.value });
  if (error) addToast(error.message, "error");
  else if (data?.department) { deptList.value.push(data.department); newDeptName.value = ''; addToast("Кафедра создана", "success"); }
};

const saveDepartment = async (id: number) => {
  if (!editDeptName.value) return;
  const { error } = await actions.admin.updateDepartment({ id, name: editDeptName.value });
  if (error) addToast(error.message, "error");
  else {
    const dept = deptList.value.find(d => d.id === id);
    if (dept) dept.name = editDeptName.value;
    editingDeptId.value = null; addToast("Кафедра переименована", "success");
  }
};

const confirmDelete = (dept: any) => { deptToDelete.value = dept; showDeleteModal.value = true; };
const executeDelete = async () => {
  if (!deptToDelete.value) return;
  const targetId = deptToDelete.value.id;
  const { error } = await actions.admin.deleteDepartment({ id: targetId });
  if (error) addToast(error.message, "error");
  else {
    deptList.value = deptList.value.filter(d => d.id !== targetId);
    teachersList.value.forEach(t => { if (t.departmentIds) t.departmentIds = t.departmentIds.filter(id => id !== targetId); });
    addToast("Кафедра удалена", "success");
  }
  showDeleteModal.value = false;
};
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden relative z-10 transition-colors">

    <!-- Tabs -->
    <div class="flex border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
      <button @click="activeTab = 'teachers'"
        :class="['flex-1 py-3.5 text-sm font-semibold flex items-center justify-center gap-2 transition-all outline-none border-b-2',
          activeTab === 'teachers'
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 bg-white dark:bg-slate-900'
            : 'text-slate-400 dark:text-slate-500 border-transparent hover:text-slate-700 dark:hover:text-slate-300 hover:bg-white dark:hover:bg-slate-900']">
        <UsersIcon class="w-4 h-4" /> Сотрудники
      </button>
      <button @click="activeTab = 'departments'"
        :class="['flex-1 py-3.5 text-sm font-semibold flex items-center justify-center gap-2 transition-all outline-none border-b-2',
          activeTab === 'departments'
            ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400 bg-white dark:bg-slate-900'
            : 'text-slate-400 dark:text-slate-500 border-transparent hover:text-slate-700 dark:hover:text-slate-300 hover:bg-white dark:hover:bg-slate-900']">
        <Building class="w-4 h-4" /> Кафедры
      </button>
    </div>

    <!-- Teachers tab -->
    <div v-if="activeTab === 'teachers'" class="p-4 md:p-6 min-h-[500px]">
      <div class="mb-5">
        <div class="relative w-full md:w-80">
          <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input v-model="searchQuery" type="text" placeholder="Поиск по ФИО..."
            class="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white dark:bg-slate-950 dark:text-white outline-none text-sm transition-all" />
        </div>
      </div>

      <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 pb-48">
        <table class="w-full min-w-[700px] text-left border-collapse relative z-10">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider font-bold whitespace-nowrap">
              <th class="py-3 px-4 w-1/3">Преподаватель</th>
              <th class="py-3 px-4 w-1/2">Кафедры</th>
              <th class="py-3 px-4 text-right">Доступ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="teacher in filteredTeachers" :key="teacher.uuid" class="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
              <td class="py-3 px-4 font-medium text-sm text-slate-800 dark:text-slate-200 whitespace-nowrap">{{ teacher.fullName }}</td>
              <td class="py-3 px-4">
                <div class="relative" :class="{ 'z-50': openDeptDropdown === teacher.uuid }">
                  <div @click="openDeptDropdown = openDeptDropdown === teacher.uuid ? null : teacher.uuid"
                    class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm rounded-xl p-2 min-h-[38px] w-full flex flex-wrap gap-1.5 items-center transition-all cursor-pointer relative z-20 hover:border-blue-400 dark:hover:border-blue-600">
                    <template v-if="teacher.departmentIds && teacher.departmentIds.length > 0">
                      <span v-for="dId in teacher.departmentIds" :key="dId" class="bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-800/50 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-lg text-[10px] font-bold whitespace-nowrap">{{ deptList.find(d => d.id === dId)?.name || 'Удалена' }}</span>
                    </template>
                    <span v-else class="text-slate-400 dark:text-slate-500 pl-1 text-xs">Выбрать кафедры</span>
                  </div>
                  <div v-if="openDeptDropdown === teacher.uuid" @click.stop class="absolute left-0 top-full mt-1.5 w-72 max-h-60 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl z-30">
                    <label v-for="dept in deptList" :key="dept.id" class="flex items-center px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
                      <input type="checkbox" :value="dept.id" v-model="teacher.departmentIds" @change="changeDepartment(teacher.uuid, teacher.departmentIds)" class="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 mr-3 cursor-pointer">
                      <span class="text-sm text-slate-700 dark:text-slate-200">{{ dept.name }}</span>
                    </label>
                  </div>
                  <div v-if="openDeptDropdown === teacher.uuid" @click.stop="openDeptDropdown = null" class="fixed inset-0 z-10 cursor-default"></div>
                </div>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div v-if="teacher.hasProfile" class="flex items-center justify-end">
                  <button @click="toggleRole(teacher)"
                    :class="teacher.userRole === 'EMPLOYEE'
                      ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700'"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all hover:opacity-80 border"
                    :title="teacher.userRole === 'EMPLOYEE' ? 'Снять права диспетчера' : 'Дать права диспетчера'">
                    <ShieldCheck v-if="teacher.userRole === 'EMPLOYEE'" class="w-3 h-3" />
                    {{ teacher.userRole === 'EMPLOYEE' ? 'Диспетчер' : 'Преподаватель' }}
                  </button>
                </div>
                <button v-else @click="openProfileModal(teacher)"
                  class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-blue-600/20">
                  <UserPlus class="w-3.5 h-3.5" /> Создать
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Departments tab -->
    <div v-if="activeTab === 'departments'" class="p-4 md:p-6 min-h-[500px]">
      <div class="flex flex-col sm:flex-row gap-3 mb-6 max-w-2xl">
        <input v-model="newDeptName" @keyup.enter="addDepartment" type="text" placeholder="Название новой кафедры"
          class="flex-1 border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-white dark:bg-slate-950 dark:text-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm transition-all" />
        <button @click="addDepartment"
          class="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white px-6 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-600/20 text-sm w-full sm:w-auto">
          <Plus class="w-4 h-4" /> Добавить
        </button>
      </div>

      <div class="grid gap-2.5">
        <div v-for="dept in deptList" :key="dept.id"
          class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-all gap-3">
          <div v-if="editingDeptId === dept.id" class="flex-1 flex gap-2 w-full">
            <input v-model="editDeptName" @keyup.enter="saveDepartment(dept.id)" type="text"
              class="flex-1 border border-slate-300 dark:border-slate-700 rounded-lg p-2.5 bg-white dark:bg-slate-950 dark:text-white outline-none focus:border-blue-500 text-sm min-w-0" />
            <button @click="saveDepartment(dept.id)" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 rounded-lg transition-colors shrink-0"><Save class="w-4 h-4" /></button>
            <button @click="editingDeptId = null" class="bg-slate-400 hover:bg-slate-500 text-white px-4 rounded-lg transition-colors shrink-0"><X class="w-4 h-4" /></button>
          </div>
          <div v-else class="font-semibold text-slate-800 dark:text-slate-200 flex-1 text-base">{{ dept.name }}</div>
          <div v-if="editingDeptId !== dept.id" class="flex gap-2 shrink-0 self-end sm:self-auto">
            <button @click="editingDeptId = dept.id; editDeptName = dept.name"
              class="p-2 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg transition-all hover:border-blue-300 dark:hover:border-blue-700">
              <Edit2 class="w-4 h-4" />
            </button>
            <button @click="confirmDelete(dept)"
              class="p-2 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg transition-all hover:border-rose-300 dark:hover:border-rose-700">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create profile modal -->
    <div v-if="showProfileModal" class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md p-7 border border-slate-200 dark:border-slate-800 relative z-50">
        <h3 class="text-lg font-bold dark:text-white mb-0.5">Создание профиля</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">{{ selectedTeacher?.fullName }}</p>
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Роль</label>
            <div class="flex gap-1.5 p-1 bg-slate-100 dark:bg-slate-950 rounded-xl">
              <button @click="newProfile.role = 'TEACHER'" type="button"
                :class="newProfile.role === 'TEACHER' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'"
                class="flex-1 py-2 text-sm font-semibold rounded-lg transition-all">Преподаватель</button>
              <button @click="newProfile.role = 'EMPLOYEE'" type="button"
                :class="newProfile.role === 'EMPLOYEE' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'"
                class="flex-1 py-2 text-sm font-semibold rounded-lg transition-all">Диспетчер</button>
            </div>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Логин</label>
            <input v-model="newProfile.username" type="text" class="w-full border border-slate-200 dark:border-slate-800 rounded-xl p-3 font-mono text-blue-700 dark:text-blue-400 bg-blue-50/50 dark:bg-slate-950 outline-none focus:border-blue-500 transition-all text-sm">
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider">Пароль</label>
            <div class="flex gap-2">
              <input v-model="newProfile.password" type="text" readonly class="w-full border border-slate-200 dark:border-slate-800 rounded-xl p-3 font-mono text-lg bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 outline-none transition-colors">
              <button @click="newProfile.password = generatePassword()" class="px-4 border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition-all text-lg">&#x1f504;</button>
            </div>
          </div>
        </div>
        <div class="mt-7 flex justify-end gap-3">
          <button @click="showProfileModal = false" class="px-5 py-2.5 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl font-semibold transition-all text-sm">Отмена</button>
          <button @click="submitProfile" :disabled="isSubmitting"
            class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white rounded-xl font-bold flex items-center gap-2 disabled:opacity-60 transition-all shadow-lg shadow-blue-600/20 text-sm">
            <Save class="w-4 h-4" /> Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-sm p-7 text-center border border-slate-200 dark:border-slate-800 relative z-50">
        <div class="w-14 h-14 bg-rose-100 dark:bg-rose-900/30 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-5"><AlertTriangle class="w-7 h-7" /></div>
        <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-1">Удалить кафедру?</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">{{ deptToDelete?.name }}</p>
        <div class="flex gap-3">
          <button @click="showDeleteModal = false" class="flex-1 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl font-semibold transition-all text-sm">Отмена</button>
          <button @click="executeDelete" class="flex-1 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold transition-all shadow-md text-sm">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>
