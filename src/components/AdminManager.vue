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
  else addToast("Кафедры успешно обновлены", "success");
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
    addToast("Кафедра успешно удалена", "success");
  }
  showDeleteModal.value = false;
};
</script>

<template>
  <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden relative z-10">
    <div class="flex border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
      <button @click="activeTab = 'teachers'" :class="['flex-1 py-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors outline-none', activeTab === 'teachers' ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 bg-white dark:bg-slate-800' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 border-b-2 border-transparent']"><UsersIcon class="w-4 h-4" /> Сотрудники</button>
      <button @click="activeTab = 'departments'" :class="['flex-1 py-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors outline-none', activeTab === 'departments' ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 bg-white dark:bg-slate-800' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 border-b-2 border-transparent']"><Building class="w-4 h-4" /> Кафедры</button>
    </div>

    <div v-if="activeTab === 'teachers'" class="p-4 md:p-8 min-h-[500px]">
      <div class="flex flex-col justify-between items-center mb-6">
        <div class="relative w-full md:w-80 self-start">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input v-model="searchQuery" type="text" placeholder="Поиск по ФИО..." class="w-full box-border m-0 pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 bg-slate-50 dark:bg-slate-900 dark:text-white outline-none transition-colors" />
        </div>
      </div>

      <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 pb-48">
        <table class="w-full min-w-[700px] text-left border-collapse relative z-10">
          <thead>
          <tr class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
            <th class="py-3 px-4 font-medium w-1/3">ФИО Преподавателя</th>
            <th class="py-3 px-4 font-medium w-1/2">Привязанные кафедры</th>
            <th class="py-3 px-4 font-medium text-right">Права доступа</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="teacher in filteredTeachers" :key="teacher.uuid" class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition-colors">
            <td class="py-3 px-4 font-medium text-slate-800 dark:text-slate-200 whitespace-nowrap">{{ teacher.fullName }}</td>
            <td class="py-3 px-4">
              <div class="relative" :class="{ 'z-50': openDeptDropdown === teacher.uuid }">
                <div @click="openDeptDropdown = openDeptDropdown === teacher.uuid ? null : teacher.uuid" class="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-sm rounded-lg p-2 min-h-[38px] w-full flex flex-wrap gap-1.5 items-center transition-colors cursor-pointer relative z-20 hover:border-indigo-400">
                  <template v-if="teacher.departmentIds && teacher.departmentIds.length > 0">
                    <span v-for="dId in teacher.departmentIds" :key="dId" class="bg-indigo-50 dark:bg-indigo-900/40 border border-indigo-100 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-md text-xs font-medium whitespace-nowrap">{{ deptList.find(d => d.id === dId)?.name || 'Удаленная кафедра' }}</span>
                  </template>
                  <span v-else class="text-slate-400 dark:text-slate-500 pl-1 text-xs">Нажмите, чтобы выбрать</span>
                </div>
                <div v-if="openDeptDropdown === teacher.uuid" @click.stop class="absolute left-0 top-full mt-1 w-72 max-h-60 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-xl z-30">
                  <label v-for="dept in deptList" :key="dept.id" class="flex items-center px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b last:border-0 border-slate-100 dark:border-slate-700/50 transition-colors"><input type="checkbox" :value="dept.id" v-model="teacher.departmentIds" @change="changeDepartment(teacher.uuid, teacher.departmentIds)" class="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500 mr-3 cursor-pointer"><span class="text-sm text-slate-700 dark:text-slate-200 leading-tight">{{ dept.name }}</span></label>
                </div>
                <div v-if="openDeptDropdown === teacher.uuid" @click.stop="openDeptDropdown = null" class="fixed inset-0 z-10 cursor-default"></div>
              </div>
            </td>

            <td class="py-3 px-4 text-right whitespace-nowrap">
              <div v-if="teacher.hasProfile" class="flex items-center justify-end gap-2">
                <button @click="toggleRole(teacher)" :class="teacher.userRole === 'EMPLOYEE' ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700'" class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-colors hover:opacity-80" :title="teacher.userRole === 'EMPLOYEE' ? 'Забрать права диспетчера' : 'Дать права диспетчера'">
                  <ShieldCheck v-if="teacher.userRole === 'EMPLOYEE'" class="w-3.5 h-3.5" />
                  {{ teacher.userRole === 'EMPLOYEE' ? 'Сотрудник (Диспетчер)' : 'Преподаватель' }}
                </button>
              </div>
              <button v-else @click="openProfileModal(teacher)" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"><UserPlus class="w-4 h-4" /> Создать</button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="activeTab === 'departments'" class="p-4 md:p-8 min-h-[500px]">
      <div class="flex flex-col sm:flex-row gap-3 mb-8 max-w-2xl">
        <input v-model="newDeptName" @keyup.enter="addDepartment" type="text" placeholder="Название новой кафедры" class="flex-1 box-border m-0 border border-slate-300 dark:border-slate-600 rounded-xl p-3 bg-slate-50 dark:bg-slate-900 dark:text-white outline-none focus:border-indigo-500 transition-colors" />
        <button @click="addDepartment" class="bg-slate-900 hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-colors shadow-sm w-full sm:w-auto"><Plus class="w-5 h-5" /> Добавить</button>
      </div>
      <div class="grid gap-3">
        <div v-for="dept in deptList" :key="dept.id" class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 hover:border-slate-300 dark:hover:border-slate-600 transition-colors gap-4">
          <div v-if="editingDeptId === dept.id" class="flex-1 flex gap-2 w-full">
            <input v-model="editDeptName" @keyup.enter="saveDepartment(dept.id)" type="text" class="flex-1 box-border m-0 border border-slate-300 dark:border-slate-600 rounded-lg p-2.5 bg-white dark:bg-slate-800 dark:text-white outline-none focus:border-indigo-500 min-w-0" />
            <button @click="saveDepartment(dept.id)" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 rounded-lg transition-colors shrink-0"><Save class="w-4 h-4" /></button>
            <button @click="editingDeptId = null" class="bg-slate-500 hover:bg-slate-600 text-white px-4 rounded-lg transition-colors shrink-0"><X class="w-4 h-4" /></button>
          </div>
          <div v-else class="font-medium text-slate-800 dark:text-slate-200 flex-1 text-lg break-words">{{ dept.name }}</div>
          <div v-if="editingDeptId !== dept.id" class="flex gap-2 shrink-0 self-end sm:self-auto">
            <button @click="editingDeptId = dept.id; editDeptName = dept.name" class="p-2.5 text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg transition-colors shadow-sm"><Edit2 class="w-4 h-4" /></button>
            <button @click="confirmDelete(dept)" class="p-2.5 text-slate-500 hover:text-red-600 dark:hover:text-red-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg transition-colors shadow-sm"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showProfileModal" class="fixed inset-0 bg-slate-900/50 dark:bg-slate-900/80 flex items-center justify-center p-4 z-50 transition-opacity">
      <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-xl w-full max-w-md p-8 border border-slate-200 dark:border-slate-700 relative z-50">
        <h3 class="text-xl font-bold mb-1 dark:text-white">Создание профиля</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">{{ selectedTeacher?.fullName }}</p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Права доступа</label>
            <div class="flex gap-2 p-1 bg-slate-100 dark:bg-slate-900 rounded-xl">
              <button @click="newProfile.role = 'TEACHER'" type="button" :class="newProfile.role === 'TEACHER' ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'" class="flex-1 py-2 text-sm font-medium rounded-lg transition-all">Преподаватель</button>
              <button @click="newProfile.role = 'EMPLOYEE'" type="button" :class="newProfile.role === 'EMPLOYEE' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'" class="flex-1 py-2 text-sm font-medium rounded-lg transition-all">Диспетчер</button>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Логин</label>
            <input v-model="newProfile.username" type="text" class="w-full border-slate-300 dark:border-slate-600 rounded-xl p-3 font-mono text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-slate-900/50 outline-none transition-colors">
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Пароль</label>
            <div class="flex gap-2">
              <input v-model="newProfile.password" type="text" readonly class="w-full border-slate-300 dark:border-slate-600 rounded-xl p-3 font-mono text-lg bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 outline-none transition-colors">
              <button @click="newProfile.password = generatePassword()" class="px-4 border border-slate-300 dark:border-slate-600 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors">🔄</button>
            </div>
          </div>
        </div>
        <div class="mt-8 flex justify-end gap-3">
          <button @click="showProfileModal = false" class="px-5 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl font-medium transition-colors">Отмена</button>
          <button @click="submitProfile" :disabled="isSubmitting" class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white rounded-xl font-medium flex items-center gap-2 disabled:opacity-70 transition-colors shadow-sm"><Save class="w-4 h-4" /> Сохранить</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="fixed inset-0 bg-slate-900/50 dark:bg-slate-900/80 flex items-center justify-center p-4 z-50 transition-opacity">
      <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl w-full max-w-sm p-8 text-center border border-slate-200 dark:border-slate-700 relative z-50">
        <div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center mx-auto mb-5"><AlertTriangle class="w-8 h-8" /></div>
        <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">Удалить кафедру?</h3>
        <div class="flex flex-col sm:flex-row gap-3 mt-8">
          <button @click="showDeleteModal = false" class="flex-1 px-4 py-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-xl font-medium transition-colors">Отмена</button>
          <button @click="executeDelete" class="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors shadow-sm">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>