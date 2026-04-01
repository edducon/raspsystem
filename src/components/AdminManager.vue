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
    return addToast('Сначала назначьте преподавателю хотя бы одну кафедру!', 'error');
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
  if (error) addToast(error.message, 'error');
  else addToast('Кафедры обновлены', 'success');
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
    addToast(error.message, 'error');
  } else {
    addToast(data.message, 'success');
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
    addToast(error.message, 'error');
  } else {
    teacher.userRole = newRole;
    addToast(actionName, 'success');
  }
};

const newDeptName = ref('');
const editingDeptId = ref<number | null>(null);
const editDeptName = ref('');

const showDeleteModal = ref(false);
const deptToDelete = ref<{ id: number; name: string } | null>(null);

const addDepartment = async () => {
  if (!newDeptName.value) return;
  const { data, error } = await actions.admin.addDepartment({ name: newDeptName.value });
  if (error) addToast(error.message, 'error');
  else if (data?.department) {
    deptList.value.push(data.department);
    newDeptName.value = '';
    addToast('Кафедра создана', 'success');
  }
};

const saveDepartment = async (id: number) => {
  if (!editDeptName.value) return;
  const { error } = await actions.admin.updateDepartment({ id, name: editDeptName.value });
  if (error) addToast(error.message, 'error');
  else {
    const dept = deptList.value.find(d => d.id === id);
    if (dept) dept.name = editDeptName.value;
    editingDeptId.value = null;
    addToast('Кафедра переименована', 'success');
  }
};

const confirmDelete = (dept: any) => {
  deptToDelete.value = dept;
  showDeleteModal.value = true;
};

const executeDelete = async () => {
  if (!deptToDelete.value) return;
  const targetId = deptToDelete.value.id;
  const { error } = await actions.admin.deleteDepartment({ id: targetId });
  if (error) addToast(error.message, 'error');
  else {
    deptList.value = deptList.value.filter(d => d.id !== targetId);
    teachersList.value.forEach(t => {
      if (t.departmentIds) t.departmentIds = t.departmentIds.filter(id => id !== targetId);
    });
    addToast('Кафедра удалена', 'success');
  }
  showDeleteModal.value = false;
};
</script>

<template>
  <div class="relative z-10 rounded-[30px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_20px_70px_rgba(15,23,42,0.10)] overflow-hidden transition-colors">
    <div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-slate-100 dark:border-white/10 flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 via-red-600 to-blue-600 flex items-center justify-center shadow-[0_16px_40px_rgba(239,68,68,0.24)] shrink-0">
        <ShieldCheck class="w-5 h-5 text-white" />
      </div>
      <div>
        <p class="text-[11px] uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold">
          Администрирование
        </p>
        <h2 class="mt-1 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white">
          Сотрудники и кафедры
        </h2>
        <p class="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          Управление доступами, профилями и кафедрами
        </p>
      </div>
    </div>
    <div class="flex border-b border-slate-100 dark:border-white/10 bg-slate-50/70 dark:bg-black/10 px-2 sm:px-3 py-2">
      <button
          @click="activeTab = 'teachers'"
          :class="[
          'flex-1 min-w-[120px] py-3 rounded-2xl text-sm font-semibold flex items-center justify-center gap-2 transition-all outline-none border',
          activeTab === 'teachers'
            ? 'text-white bg-red-500 border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]'
            : 'text-slate-500 dark:text-slate-400 border-transparent hover:border-slate-200 dark:hover:border-white/10 hover:bg-white dark:hover:bg-white/[0.04]'
        ]"
      >
        <UsersIcon class="w-4 h-4" />
        Сотрудники
      </button>

      <button
          @click="activeTab = 'departments'"
          :class="[
          'flex-1 min-w-[120px] py-3 rounded-2xl text-sm font-semibold flex items-center justify-center gap-2 transition-all outline-none border',
          activeTab === 'departments'
            ? 'text-white bg-red-500 border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]'
            : 'text-slate-500 dark:text-slate-400 border-transparent hover:border-slate-200 dark:hover:border-white/10 hover:bg-white dark:hover:bg-white/[0.04]'
        ]"
      >
        <Building class="w-4 h-4" />
        Кафедры
      </button>
    </div>

    <!-- Teachers tab -->
    <div v-if="activeTab === 'teachers'" class="p-5 sm:p-6 min-h-[520px]">
      <div class="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-500 font-bold">
            Список сотрудников
          </p>
          <h3 class="mt-2 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white">
            Управление преподавателями
          </h3>
        </div>

        <div class="relative w-full sm:w-80">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск по ФИО..."
              class="w-full h-12 pl-11 pr-4 border border-slate-200 dark:border-white/10 rounded-2xl focus:ring-4 focus:ring-red-500/10 focus:border-red-400 dark:focus:border-red-500 bg-white dark:bg-white/[0.03] dark:text-white outline-none text-sm transition-all"
          />
        </div>
      </div>

      <div class="overflow-x-auto rounded-[24px] border border-slate-200/80 dark:border-white/10 bg-white/70 dark:bg-white/[0.02] pb-40">
        <table class="w-full min-w-[760px] text-left border-collapse relative z-10">
          <thead>
          <tr class="border-b border-slate-200 dark:border-white/10 text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-[0.18em] font-bold whitespace-nowrap bg-slate-50/80 dark:bg-black/10">
            <th class="py-4 px-5 w-[34%]">Преподаватель</th>
            <th class="py-4 px-5 w-[46%]">Кафедры</th>
            <th class="py-4 px-5 text-right">Доступ</th>
          </tr>
          </thead>

          <tbody>
          <tr
              v-for="teacher in filteredTeachers"
              :key="teacher.uuid"
              class="border-b border-slate-100 dark:border-white/10 hover:bg-slate-50/70 dark:hover:bg-white/[0.03] transition-colors"
          >
            <td class="py-4 px-5 align-top">
              <div class="font-semibold text-sm text-slate-800 dark:text-slate-200 whitespace-nowrap">
                {{ teacher.fullName }}
              </div>
            </td>

            <td class="py-4 px-5 align-top">
              <div class="relative" :class="{ 'z-50': openDeptDropdown === teacher.uuid }">
                <div
                    @click="openDeptDropdown = openDeptDropdown === teacher.uuid ? null : teacher.uuid"
                    class="bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 text-sm rounded-[20px] p-2.5 min-h-[44px] w-full flex flex-wrap gap-1.5 items-center transition-all cursor-pointer relative z-20 hover:border-red-400 dark:hover:border-red-500"
                >
                  <template v-if="teacher.departmentIds && teacher.departmentIds.length > 0">
                      <span
                          v-for="dId in teacher.departmentIds"
                          :key="dId"
                          class="bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-blue-700 dark:text-blue-300 px-2.5 py-1 rounded-xl text-[10px] font-bold whitespace-nowrap"
                      >
                        {{ deptList.find(d => d.id === dId)?.name || 'Удалена' }}
                      </span>
                  </template>

                  <span v-else class="text-slate-400 dark:text-slate-500 pl-1 text-xs">
                      Выбрать кафедры
                    </span>
                </div>

                <div
                    v-if="openDeptDropdown === teacher.uuid"
                    @click.stop
                    class="absolute left-0 top-full mt-2 w-72 max-h-60 overflow-y-auto bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] z-30"
                >
                  <label
                      v-for="dept in deptList"
                      :key="dept.id"
                      class="flex items-center px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"
                  >
                    <input
                        type="checkbox"
                        :value="dept.id"
                        v-model="teacher.departmentIds"
                        @change="changeDepartment(teacher.uuid, teacher.departmentIds)"
                        class="w-4 h-4 text-red-500 rounded border-slate-300 focus:ring-red-500 mr-3 cursor-pointer"
                    >
                    <span class="text-sm text-slate-700 dark:text-slate-200">{{ dept.name }}</span>
                  </label>
                </div>

                <div
                    v-if="openDeptDropdown === teacher.uuid"
                    @click.stop="openDeptDropdown = null"
                    class="fixed inset-0 z-10 cursor-default"
                ></div>
              </div>
            </td>

            <td class="py-4 px-5 text-right align-top whitespace-nowrap">
              <div v-if="teacher.hasProfile" class="flex items-center justify-end">
                <button
                    @click="toggleRole(teacher)"
                    :class="teacher.userRole === 'EMPLOYEE'
                      ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20'
                      : 'bg-slate-100 dark:bg-white/[0.05] text-slate-500 dark:text-slate-400 border-slate-200 dark:border-white/10'"
                    class="flex items-center gap-1.5 px-3 py-2 rounded-xl text-[10px] font-bold uppercase tracking-[0.14em] transition-all hover:opacity-90 border"
                    :title="teacher.userRole === 'EMPLOYEE' ? 'Снять права диспетчера' : 'Дать права диспетчера'"
                >
                  <ShieldCheck v-if="teacher.userRole === 'EMPLOYEE'" class="w-3.5 h-3.5" />
                  {{ teacher.userRole === 'EMPLOYEE' ? 'Диспетчер' : 'Преподаватель' }}
                </button>
              </div>

              <button
                  v-else
                  @click="openProfileModal(teacher)"
                  class="inline-flex items-center gap-1.5 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl text-xs font-black transition-all shadow-[0_12px_28px_rgba(239,68,68,0.20)]"
              >
                <UserPlus class="w-3.5 h-3.5" />
                Создать
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Departments tab -->
    <div v-if="activeTab === 'departments'" class="p-5 sm:p-6 min-h-[520px]">
      <div class="mb-6">
        <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-500 font-bold">
          Список кафедр
        </p>
        <h3 class="mt-2 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white">
          Управление кафедрами
        </h3>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 mb-6 max-w-2xl">
        <input
            v-model="newDeptName"
            @keyup.enter="addDepartment"
            type="text"
            placeholder="Название новой кафедры"
            class="flex-1 h-12 border border-slate-200 dark:border-white/10 rounded-2xl px-4 bg-white dark:bg-white/[0.03] dark:text-white outline-none focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 text-sm transition-all"
        />

        <button
            @click="addDepartment"
            class="bg-red-500 hover:bg-red-600 text-white px-6 h-12 rounded-2xl font-black flex items-center justify-center gap-2 transition-all shadow-[0_16px_40px_rgba(239,68,68,0.22)] text-sm w-full sm:w-auto"
        >
          <Plus class="w-4 h-4" />
          Добавить
        </button>
      </div>

      <div class="grid gap-3">
        <div
            v-for="dept in deptList"
            :key="dept.id"
            class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-[22px] border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/[0.03] hover:border-slate-300 dark:hover:border-white/15 transition-all gap-3"
        >
          <div v-if="editingDeptId === dept.id" class="flex-1 flex gap-2 w-full">
            <input
                v-model="editDeptName"
                @keyup.enter="saveDepartment(dept.id)"
                type="text"
                class="flex-1 h-11 border border-slate-300 dark:border-white/10 rounded-xl px-3 bg-white dark:bg-white/[0.03] dark:text-white outline-none focus:border-red-400 text-sm min-w-0"
            />

            <button
                @click="saveDepartment(dept.id)"
                class="h-11 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-colors shrink-0"
            >
              <Save class="w-4 h-4" />
            </button>

            <button
                @click="editingDeptId = null"
                class="h-11 px-4 bg-slate-400 hover:bg-slate-500 text-white rounded-xl transition-colors shrink-0"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div v-else class="font-semibold text-slate-800 dark:text-slate-200 flex-1 text-base">
            {{ dept.name }}
          </div>

          <div v-if="editingDeptId !== dept.id" class="flex gap-2 shrink-0 self-end sm:self-auto">
            <button
                @click="editingDeptId = dept.id; editDeptName = dept.name"
                class="p-2.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 rounded-xl transition-all hover:border-blue-300 dark:hover:border-blue-500/20"
            >
              <Edit2 class="w-4 h-4" />
            </button>

            <button
                @click="confirmDelete(dept)"
                class="p-2.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 rounded-xl transition-all hover:border-red-300 dark:hover:border-red-500/20"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create profile modal -->
    <div
        v-if="showProfileModal"
        class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm"
    >
      <div class="bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl rounded-[28px] shadow-[0_24px_80px_rgba(15,23,42,0.22)] w-full max-w-md p-7 border border-slate-200/80 dark:border-white/10 relative z-50">
        <h3 class="text-xl font-black tracking-tight dark:text-white mb-1">
          Создание профиля
        </h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">
          {{ selectedTeacher?.fullName }}
        </p>

        <div class="space-y-4">
          <div>
            <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
              Роль
            </label>

            <div class="flex gap-1.5 p-1 bg-slate-100 dark:bg-black/10 rounded-2xl border border-slate-200 dark:border-white/10">
              <button
                  @click="newProfile.role = 'TEACHER'"
                  type="button"
                  :class="newProfile.role === 'TEACHER'
                  ? 'bg-white dark:bg-white/[0.05] text-slate-900 dark:text-white shadow-sm border border-slate-200 dark:border-white/10'
                  : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 border border-transparent'"
                  class="flex-1 py-2.5 text-sm font-semibold rounded-xl transition-all"
              >
                Преподаватель
              </button>

              <button
                  @click="newProfile.role = 'EMPLOYEE'"
                  type="button"
                  :class="newProfile.role === 'EMPLOYEE'
                  ? 'bg-emerald-600 text-white shadow-sm border border-emerald-600'
                  : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 border border-transparent'"
                  class="flex-1 py-2.5 text-sm font-semibold rounded-xl transition-all"
              >
                Диспетчер
              </button>
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
              Логин
            </label>

            <input
                v-model="newProfile.username"
                type="text"
                class="w-full h-12 border border-slate-200 dark:border-white/10 rounded-2xl px-4 font-mono text-blue-700 dark:text-blue-400 bg-blue-50/50 dark:bg-white/[0.03] outline-none focus:border-red-400 transition-all text-sm"
            >
          </div>

          <div>
            <label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]">
              Пароль
            </label>

            <div class="flex gap-2">
              <input
                  v-model="newProfile.password"
                  type="text"
                  readonly
                  class="w-full h-12 border border-slate-200 dark:border-white/10 rounded-2xl px-4 font-mono text-base bg-slate-50 dark:bg-white/[0.03] text-slate-700 dark:text-slate-300 outline-none transition-colors"
              >
              <button
                  @click="newProfile.password = generatePassword()"
                  class="h-12 px-4 border border-slate-200 dark:border-white/10 rounded-2xl hover:bg-slate-100 dark:hover:bg-white/[0.05] text-slate-500 transition-all text-lg"
              >
                &#x1f504;
              </button>
            </div>
          </div>
        </div>

        <div class="mt-7 flex justify-end gap-3">
          <button
              @click="showProfileModal = false"
              class="px-5 h-11 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.05] rounded-2xl font-semibold transition-all text-sm"
          >
            Отмена
          </button>

          <button
              @click="submitProfile"
              :disabled="isSubmitting"
              class="px-6 h-11 bg-red-500 hover:bg-red-600 text-white rounded-2xl font-black flex items-center gap-2 disabled:opacity-60 transition-all shadow-[0_16px_40px_rgba(239,68,68,0.22)] text-sm"
          >
            <Save class="w-4 h-4" />
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div
        v-if="showDeleteModal"
        class="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm"
    >
      <div class="bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl rounded-[28px] shadow-[0_24px_80px_rgba(15,23,42,0.22)] w-full max-w-sm p-7 text-center border border-slate-200/80 dark:border-white/10 relative z-50">
        <div class="w-14 h-14 bg-red-50 dark:bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-5 border border-red-200 dark:border-red-500/20">
          <AlertTriangle class="w-7 h-7" />
        </div>

        <h3 class="text-lg font-black tracking-tight text-slate-900 dark:text-white mb-1">
          Удалить кафедру?
        </h3>

        <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">
          {{ deptToDelete?.name }}
        </p>

        <div class="flex gap-3">
          <button
              @click="showDeleteModal = false"
              class="flex-1 h-11 bg-slate-100 hover:bg-slate-200 dark:bg-white/[0.05] dark:hover:bg-white/[0.08] text-slate-700 dark:text-slate-200 rounded-2xl font-semibold transition-all text-sm"
          >
            Отмена
          </button>

          <button
              @click="executeDelete"
              class="flex-1 h-11 bg-red-500 hover:bg-red-600 text-white rounded-2xl font-black transition-all shadow-[0_12px_28px_rgba(239,68,68,0.18)] text-sm"
          >
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>