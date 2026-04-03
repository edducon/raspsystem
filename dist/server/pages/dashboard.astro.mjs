/* empty css                                 */
import { e as createComponent, k as renderComponent, r as renderTemplate, h as createAstro, l as Fragment, n as defineScriptVars, g as addAttribute, m as maybeRenderHead } from '../chunks/astro/server__Jo3gmtv.mjs';
import 'piccolore';
import { a as addToast, _ as _export_sfc, $ as $$Layout } from '../chunks/Layout_BkxlrDkt.mjs';
import { useSSRContext, defineComponent, ref, computed, watch, mergeProps } from 'vue';
import { Trash2, Info, AlertTriangle, X, Globe, MapPin, ChevronDown, Search, CheckCircle, Users, Clock, Calendar, ChevronRight, ChevronLeft, CalendarDays } from 'lucide-vue-next';
import { f as fetchBackendFromBrowser, a as fetchBackendFromServer } from '../chunks/backend-api_iSCceNha.mjs';
import { n as normalizeForCompare, f as fuzzyMatch, c as cleanSubjectName } from '../chunks/subjectNorm_B8KQ8M6A.mjs';
import { ssrRenderAttrs, ssrRenderComponent, ssrRenderAttr, ssrRenderList, ssrInterpolate, ssrIncludeBooleanAttr, ssrLooseContain, ssrLooseEqual, ssrRenderClass } from 'vue/server-renderer';
/* empty css                                 */
import { g as getPublicBackendApiUrl } from '../chunks/backend-auth_-lm5w3qF.mjs';
export { renderers } from '../renderers.mjs';

const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "RetakeScheduler",
  props: {
    backendApiUrl: {},
    groups: {},
    subjects: {},
    teachers: {},
    currentUser: {}
  },
  setup(__props, { expose: __expose }) {
    __expose();
    const props = __props;
    const selectedDate = ref("");
    const selectedSubject = ref("");
    const selectedSlots = ref([]);
    const mainTeachers = ref([]);
    const commissionTeachers = ref([]);
    const chairmanTeacher = ref(null);
    const isSubmitting = ref(false);
    const retakeFormat = ref("offline");
    const roomUuid = ref("");
    const onlineLink = ref("");
    const attemptNumber = ref(1);
    const groupSearchQuery = ref("");
    const selectedGroupUuid = ref("");
    const showGroupDropdown = ref(false);
    const filteredGroups = computed(() => {
      if (!groupSearchQuery.value) return props.groups.slice(0, 50);
      const q = groupSearchQuery.value.toLowerCase();
      return props.groups.filter((g) => g.number.toLowerCase().includes(q)).slice(0, 50);
    });
    const selectGroup = (group) => {
      selectedGroupUuid.value = group.uuid;
      groupSearchQuery.value = group.number;
      showGroupDropdown.value = false;
    };
    const groupHistory = ref([]);
    const existingGroupRetakes = ref([]);
    const sectionsCollapsed = ref({ slots: false, format: false, commission: false });
    const formatShortName = (fullName) => {
      if (!fullName) return "";
      const parts = fullName.trim().split(/\s+/);
      if (parts.length === 1) return parts[0];
      if (parts.length === 2) return `${parts[0]} ${parts[1][0]}.`;
      return `${parts[0]} ${parts[1][0]}.${parts[2][0]}.`;
    };
    const availableSubjects = computed(() => {
      if (groupHistory.value.length === 0) return [];
      const historyNames = groupHistory.value.map((item) => item.subjectName);
      const cleanedHistoryNames = historyNames.map((name) => normalizeForCompare(name));
      let matched = props.subjects.filter(
        (subject) => cleanedHistoryNames.some((historyName) => historyName === normalizeForCompare(subject.name))
      );
      if (matched.length === 0) {
        matched = props.subjects.filter(
          (subject) => historyNames.some((historyName) => fuzzyMatch(historyName, subject.name))
        );
      }
      const uniqueSubjects = [];
      const seenNames = /* @__PURE__ */ new Set();
      for (const subject of matched) {
        const cleaned = cleanSubjectName(subject.name);
        if (!seenNames.has(cleaned)) {
          seenNames.add(cleaned);
          uniqueSubjects.push({ uuid: subject.uuid, name: cleaned });
        }
      }
      return uniqueSubjects.sort((a, b) => a.name.localeCompare(b.name, "ru"));
    });
    const loadGroupContext = async (groupUuid) => {
      const group = props.groups.find((item) => item.uuid === groupUuid);
      if (!group) return;
      try {
        const [history, retakes] = await Promise.all([
          fetchBackendFromBrowser(
            props.backendApiUrl,
            `/retakes/history/group/${encodeURIComponent(group.number)}`
          ),
          fetchBackendFromBrowser(props.backendApiUrl, `/retakes/group/${groupUuid}`)
        ]);
        groupHistory.value = history;
        existingGroupRetakes.value = retakes;
      } catch (error) {
        addToast(error instanceof Error ? error.message : "�� ������� ��������� ������ ������", "error");
      }
    };
    watch(selectedGroupUuid, async (newUuid) => {
      selectedSubject.value = "";
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
    const formatDate = (dateStr) => {
      return new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(dateStr));
    };
    const showMainDropdown = ref(false);
    const showCommDropdown = ref(false);
    const showChairmanDropdown = ref(false);
    const mainSearchQuery = ref("");
    const chairmanSearchQuery = ref("");
    const commSearchQuery = ref("");
    watch(showMainDropdown, (value) => {
      if (!value) mainSearchQuery.value = "";
    });
    watch(showChairmanDropdown, (value) => {
      if (!value) chairmanSearchQuery.value = "";
    });
    watch(showCommDropdown, (value) => {
      if (!value) commSearchQuery.value = "";
    });
    const allTeachersForSelectedSubject = computed(() => {
      if (!selectedSubject.value) return [];
      const subject = props.subjects.find((item) => item.uuid === selectedSubject.value);
      if (!subject) return [];
      const cleanedSubjectName = cleanSubjectName(subject.name);
      const historyRecords = groupHistory.value.filter((item) => cleanSubjectName(item.subjectName) === cleanedSubjectName);
      return historyRecords.flatMap((item) => item.teacherNames);
    });
    const subjectBelongsToAnotherDept = computed(() => {
      if (props.currentUser.role === "ADMIN" || !selectedSubject.value) return false;
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
      if (props.currentUser.role !== "ADMIN") {
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
    const removeMainTeacher = (uuid) => {
      mainTeachers.value = mainTeachers.value.filter((id) => id !== uuid);
    };
    const removeCommTeacher = (uuid) => {
      commissionTeachers.value = commissionTeachers.value.filter((id) => id !== uuid);
    };
    const selectChairman = (uuid) => {
      chairmanTeacher.value = uuid;
      showChairmanDropdown.value = false;
    };
    const TIME_MAPPING = {
      1: "09:00-10:30",
      2: "10:40-12:10",
      3: "12:20-13:50",
      4: "14:30-16:00",
      5: "16:10-17:40",
      6: "17:50-19:20",
      7: "19:30-21:00"
    };
    const isLoadingSlots = ref(false);
    const daySchedule = ref(null);
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
            daySchedule.value = await fetchBackendFromBrowser(
              props.backendApiUrl,
              "/retakes/merged-day",
              {
                method: "POST",
                body: JSON.stringify({
                  groupNumber: group.number,
                  groupUuid: group.uuid,
                  teacherUuids: allSelectedTeacherUuids,
                  date: selectedDate.value
                })
              }
            );
          } catch (error) {
            addToast(error instanceof Error ? error.message : "�� ������� ��������� ���������� �� ����", "error");
          }
        }
        isLoadingSlots.value = false;
      }
    });
    const toggleSlot = (slot) => {
      if (daySchedule.value && daySchedule.value[slot.toString()] !== null) return;
      const index = selectedSlots.value.indexOf(slot);
      if (index === -1) selectedSlots.value.push(slot);
      else selectedSlots.value.splice(index, 1);
      selectedSlots.value.sort();
    };
    const submitRetake = async () => {
      if (subjectBelongsToAnotherDept.value) return addToast("��� ������� � ����������!", "error");
      if (selectedSlots.value.length === 0 || mainTeachers.value.length === 0) return addToast("�������� ����� � �������� �������������!", "error");
      if (attemptNumber.value > 1 && !chairmanTeacher.value) return addToast("��� 2-� � 3-� ������� ���������� ��������� ������������ ��������!", "error");
      if (retakeFormat.value === "offline" && !roomUuid.value) return addToast("������� ��������� ��� ���������� ���������", "error");
      if (retakeFormat.value === "online" && !onlineLink.value) return addToast("������� ������ �� �����������", "error");
      if (assignedAttempts.value.includes(attemptNumber.value)) return addToast("��� ������� ��������� ��� ���������!", "error");
      isSubmitting.value = true;
      try {
        const group = props.groups.find((item) => item.uuid === selectedGroupUuid.value);
        if (!group) throw new Error("������ �� �������");
        await fetchBackendFromBrowser(
          props.backendApiUrl,
          "/retakes",
          {
            method: "POST",
            body: JSON.stringify({
              groupNumber: group.number,
              groupUuid: selectedGroupUuid.value,
              subjectUuid: selectedSubject.value,
              date: selectedDate.value,
              timeSlots: selectedSlots.value,
              roomUuid: retakeFormat.value === "offline" ? roomUuid.value : void 0,
              link: retakeFormat.value === "online" ? onlineLink.value : void 0,
              attemptNumber: attemptNumber.value,
              mainTeachersUuids: mainTeachers.value,
              commissionTeachersUuids: commissionTeachers.value,
              chairmanUuid: chairmanTeacher.value || void 0
            })
          }
        );
        await loadGroupContext(selectedGroupUuid.value);
        selectedSlots.value = [];
        selectedDate.value = "";
        addToast("��������� ������� ���������!", "success");
        roomUuid.value = "";
        onlineLink.value = "";
        chairmanTeacher.value = null;
        commissionTeachers.value = [];
      } catch (error) {
        addToast(error instanceof Error ? error.message : "�� ������� ������� ���������", "error");
      } finally {
        isSubmitting.value = false;
      }
    };
    const deleteRetake = async (id) => {
      if (!confirm("�� �������, ��� ������ ������� ��� ���������?")) return;
      try {
        await fetchBackendFromBrowser(props.backendApiUrl, `/retakes/${id}`, { method: "DELETE" });
        addToast("��������� ��������", "success");
        existingGroupRetakes.value = existingGroupRetakes.value.filter((item) => item.id !== id);
        selectedDate.value = "";
      } catch (error) {
        addToast(error instanceof Error ? error.message : "�� ������� ������� ���������", "error");
      }
    };
    const __returned__ = { props, selectedDate, selectedSubject, selectedSlots, mainTeachers, commissionTeachers, chairmanTeacher, isSubmitting, retakeFormat, roomUuid, onlineLink, attemptNumber, groupSearchQuery, selectedGroupUuid, showGroupDropdown, filteredGroups, selectGroup, groupHistory, existingGroupRetakes, sectionsCollapsed, formatShortName, availableSubjects, loadGroupContext, currentSubjectRetakes, assignedAttempts, formatDate, showMainDropdown, showCommDropdown, showChairmanDropdown, mainSearchQuery, chairmanSearchQuery, commSearchQuery, allTeachersForSelectedSubject, subjectBelongsToAnotherDept, availableMainTeachers, validCommissionPool, mainTeacherLacksDept, availableChairmen, availableCommissionTeachers, displayMainTeachers, displayChairmen, displayCommTeachers, removeMainTeacher, removeCommTeacher, selectChairman, TIME_MAPPING, isLoadingSlots, daySchedule, toggleSlot, submitRetake, deleteRetake, get Calendar() {
      return Calendar;
    }, get Clock() {
      return Clock;
    }, get Users() {
      return Users;
    }, get CheckCircle() {
      return CheckCircle;
    }, get Search() {
      return Search;
    }, get ChevronDown() {
      return ChevronDown;
    }, get MapPin() {
      return MapPin;
    }, get Globe() {
      return Globe;
    }, get X() {
      return X;
    }, get AlertTriangle() {
      return AlertTriangle;
    }, get Info() {
      return Info;
    }, get Trash2() {
      return Trash2;
    } };
    Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
    return __returned__;
  }
});
function _sfc_ssrRender$1(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(mergeProps({ class: "relative z-10 rounded-[30px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_20px_70px_rgba(15,23,42,0.10)] overflow-hidden transition-colors" }, _attrs))}><div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-slate-100 dark:border-white/10 flex items-center gap-4"><div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 via-red-600 to-blue-600 flex items-center justify-center shadow-[0_16px_40px_rgba(239,68,68,0.24)] shrink-0">`);
  _push(ssrRenderComponent($setup["Calendar"], { class: "w-5 h-5 text-white" }, null, _parent));
  _push(`</div><div><p class="text-[11px] uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold"> Управление </p><h2 class="mt-1 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white"> Назначение пересдачи </h2><p class="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400"> Заполните шаги для создания новой записи </p></div></div><div class="p-5 sm:p-6 lg:p-7"><div class="flex items-center gap-3 mb-4"><div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]"> 1 </div><h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white"> Группа, дисциплина и дата </h3></div><div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8"><div class="relative"><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Группа </label><div class="relative"><input${ssrRenderAttr("value", $setup.groupSearchQuery)} type="text" placeholder="Номер группы..." class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 pr-10 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all">`);
  _push(ssrRenderComponent($setup["ChevronDown"], { class: "absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" }, null, _parent));
  _push(`</div>`);
  if ($setup.showGroupDropdown && $setup.filteredGroups.length > 0) {
    _push(`<div class="absolute z-20 w-full mt-2 max-h-60 overflow-y-auto bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)]"><!--[-->`);
    ssrRenderList($setup.filteredGroups, (g) => {
      _push(`<div class="px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer text-sm text-slate-700 dark:text-slate-200 font-semibold transition-colors">${ssrInterpolate(g.number)}</div>`);
    });
    _push(`<!--]--></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.showGroupDropdown) {
    _push(`<div class="fixed inset-0 z-10"></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div><div><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Дисциплина </label><select${ssrIncludeBooleanAttr(!$setup.selectedGroupUuid || $setup.availableSubjects.length === 0) ? " disabled" : ""} class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none disabled:opacity-50 transition-all"><option value="" disabled${ssrIncludeBooleanAttr(Array.isArray($setup.selectedSubject) ? ssrLooseContain($setup.selectedSubject, "") : ssrLooseEqual($setup.selectedSubject, "")) ? " selected" : ""}>${ssrInterpolate($setup.availableSubjects.length === 0 ? "Сначала выберите группу" : "Выберите предмет...")}</option><!--[-->`);
  ssrRenderList($setup.availableSubjects, (s) => {
    _push(`<option${ssrRenderAttr("value", s.uuid)}${ssrIncludeBooleanAttr(Array.isArray($setup.selectedSubject) ? ssrLooseContain($setup.selectedSubject, s.uuid) : ssrLooseEqual($setup.selectedSubject, s.uuid)) ? " selected" : ""}>${ssrInterpolate(s.name)}</option>`);
  });
  _push(`<!--]--></select>`);
  if ($setup.subjectBelongsToAnotherDept) {
    _push(`<p class="text-xs text-red-500 dark:text-red-400 font-medium mt-2 flex items-start gap-1.5">`);
    _push(ssrRenderComponent($setup["AlertTriangle"], { class: "w-3.5 h-3.5 mt-0.5 shrink-0" }, null, _parent));
    _push(` Дисциплина другой кафедры. Нет прав назначения. </p>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div><div><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Дата </label><input type="date"${ssrRenderAttr("value", $setup.selectedDate)}${ssrIncludeBooleanAttr(!$setup.selectedSubject) ? " disabled" : ""} class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none disabled:opacity-50 [color-scheme:light] dark:[color-scheme:dark] transition-all"></div></div>`);
  if ($setup.currentSubjectRetakes.length > 0) {
    _push(`<div class="mb-8 p-4 sm:p-5 rounded-[24px] bg-amber-50/80 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 flex items-start gap-3">`);
    _push(ssrRenderComponent($setup["Info"], { class: "w-5 h-5 text-amber-500 shrink-0 mt-0.5" }, null, _parent));
    _push(`<div class="w-full"><h4 class="text-[11px] font-bold text-amber-800 dark:text-amber-400 uppercase tracking-[0.18em] mb-3"> Уже назначенные пересдачи </h4><div class="space-y-2"><!--[-->`);
    ssrRenderList($setup.currentSubjectRetakes, (r) => {
      _push(`<div class="text-sm text-amber-900 dark:text-amber-100 flex items-center justify-between gap-3 bg-white/60 dark:bg-black/20 p-3 rounded-2xl border border-amber-200/60 dark:border-amber-500/10"><div class="flex items-center gap-2 flex-wrap"><span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span><span>Попытка ${ssrInterpolate(r.attemptNumber)} — <span class="font-bold">${ssrInterpolate($setup.formatDate(r.date))}</span></span></div>`);
      if (r.canDelete) {
        _push(`<button class="text-red-500 hover:text-red-700 dark:hover:text-red-400 p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" title="Удалить">`);
        _push(ssrRenderComponent($setup["Trash2"], { class: "w-4 h-4" }, null, _parent));
        _push(`</button>`);
      } else {
        _push(`<!---->`);
      }
      _push(`</div>`);
    });
    _push(`<!--]--></div></div></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.selectedDate && $setup.selectedGroupUuid) {
    _push(`<div class="mb-8"><div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div><div class="flex items-center justify-between mb-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]"> 2 </div><h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">`);
    _push(ssrRenderComponent($setup["Clock"], { class: "w-4 h-4 text-red-500" }, null, _parent));
    _push(` Расписание на день </h3></div><button class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">`);
    _push(ssrRenderComponent($setup["ChevronDown"], {
      class: ["w-4 h-4 text-slate-400 transition-transform duration-200", $setup.sectionsCollapsed.slots ? "-rotate-90" : ""]
    }, null, _parent));
    _push(`</button></div><div class="${ssrRenderClass({ "hidden md:block": $setup.sectionsCollapsed.slots })}">`);
    if ($setup.isLoadingSlots) {
      _push(`<div class="flex items-center justify-center p-10 text-slate-500 dark:text-slate-400"><div class="w-5 h-5 rounded-full border-2 border-red-500 border-t-transparent animate-spin mr-3"></div> Загрузка расписания... </div>`);
    } else if ($setup.daySchedule) {
      _push(`<div class="grid grid-cols-1 gap-3"><!--[-->`);
      ssrRenderList(7, (slot) => {
        _push(`<div class="${ssrRenderClass([
          "p-4 rounded-[22px] border flex flex-col md:flex-row justify-between md:items-center gap-3 transition-all select-none",
          $setup.daySchedule[slot.toString()] ? "bg-slate-50 dark:bg-black/10 border-slate-200 dark:border-white/10 opacity-70 cursor-not-allowed" : $setup.selectedSlots.includes(slot) ? "bg-red-500 border-red-500 text-white shadow-[0_16px_40px_rgba(239,68,68,0.20)] cursor-pointer scale-[1.01]" : "bg-white dark:bg-white/[0.03] border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15 cursor-pointer hover:shadow-[0_14px_34px_rgba(15,23,42,0.08)]"
        ])}"><div class="flex items-center gap-4"><div class="${ssrRenderClass([
          "w-11 h-11 rounded-2xl flex items-center justify-center font-black text-base shrink-0",
          $setup.selectedSlots.includes(slot) && !$setup.daySchedule[slot.toString()] ? "bg-white/20 text-white" : "bg-slate-100 dark:bg-white/[0.05] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-white/10"
        ])}">${ssrInterpolate(slot)}</div><div><div class="${ssrRenderClass([$setup.selectedSlots.includes(slot) && !$setup.daySchedule[slot.toString()] ? "text-white" : "text-slate-900 dark:text-slate-100", "font-semibold text-sm"])}">${ssrInterpolate($setup.TIME_MAPPING[slot])}</div>`);
        if ($setup.daySchedule[slot.toString()]) {
          _push(`<div class="mt-0.5 flex flex-col gap-0.5"><div class="text-xs text-red-500 font-semibold flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-red-500 inline-block"></span> ${ssrInterpolate($setup.daySchedule[slot.toString()].reason)}</div>`);
          if ($setup.daySchedule[slot.toString()].details) {
            _push(`<div class="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px] sm:max-w-xs md:max-w-md">${ssrInterpolate($setup.daySchedule[slot.toString()].details.subject)}</div>`);
          } else {
            _push(`<!---->`);
          }
          _push(`</div>`);
        } else {
          _push(`<div class="${ssrRenderClass([$setup.selectedSlots.includes(slot) ? "text-red-100" : "text-emerald-600 dark:text-emerald-500", "text-xs font-semibold mt-0.5 flex items-center gap-1"])}"><span class="${ssrRenderClass([$setup.selectedSlots.includes(slot) ? "bg-red-100" : "bg-emerald-500", "w-1.5 h-1.5 rounded-full inline-block"])}"></span> ${ssrInterpolate($setup.selectedSlots.includes(slot) ? "Выбрано" : "Свободно")}</div>`);
        }
        _push(`</div></div>`);
        if ($setup.daySchedule[slot.toString()]?.details) {
          _push(`<div class="text-right text-xs"><div class="text-slate-500 dark:text-slate-400 font-medium">${ssrInterpolate($setup.daySchedule[slot.toString()].details.type)}</div><div class="font-medium text-slate-700 dark:text-slate-300 mt-0.5 truncate max-w-[220px]">${ssrInterpolate($setup.daySchedule[slot.toString()].details.location)}</div></div>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div>`);
      });
      _push(`<!--]--></div>`);
    } else {
      _push(`<!---->`);
    }
    _push(`</div></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div><div class="flex items-center justify-between mb-4"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]"> 3 </div><h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white"> Формат и попытка </h3></div><button class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">`);
  _push(ssrRenderComponent($setup["ChevronDown"], {
    class: ["w-4 h-4 text-slate-400 transition-transform duration-200", $setup.sectionsCollapsed.format ? "-rotate-90" : ""]
  }, null, _parent));
  _push(`</button></div><div class="${ssrRenderClass({ "hidden md:block": $setup.sectionsCollapsed.format })}"><div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 p-5 sm:p-6 bg-slate-50/80 dark:bg-black/10 rounded-[24px] border border-slate-100 dark:border-white/10"><div><h4 class="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-[0.18em]"> Формат проведения </h4><div class="flex gap-2 mb-3"><button class="${ssrRenderClass([$setup.retakeFormat === "offline" ? "bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]" : "bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15", "flex-1 py-2.5 px-3 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all text-sm border"])}">`);
  _push(ssrRenderComponent($setup["MapPin"], { class: "w-4 h-4" }, null, _parent));
  _push(` Очно </button><button class="${ssrRenderClass([$setup.retakeFormat === "online" ? "bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]" : "bg-white dark:bg-white/[0.03] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15", "flex-1 py-2.5 px-3 rounded-2xl font-semibold flex items-center justify-center gap-2 transition-all text-sm border"])}">`);
  _push(ssrRenderComponent($setup["Globe"], { class: "w-4 h-4" }, null, _parent));
  _push(` Онлайн </button></div>`);
  if ($setup.retakeFormat === "offline") {
    _push(`<input${ssrRenderAttr("value", $setup.roomUuid)} type="text" placeholder="Аудитория (А-414)" class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all">`);
  } else {
    _push(`<input${ssrRenderAttr("value", $setup.onlineLink)} type="url" placeholder="Ссылка на подключение" class="w-full h-12 rounded-2xl border border-slate-300 dark:border-white/10 focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 px-4 text-sm bg-white dark:bg-white/[0.03] dark:text-white outline-none transition-all">`);
  }
  _push(`</div><div><h4 class="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-[0.18em]"> Номер попытки </h4><div class="flex flex-col gap-2"><!--[-->`);
  ssrRenderList(3, (n) => {
    _push(`<label class="${ssrRenderClass([$setup.assignedAttempts.includes(n) ? "opacity-40 cursor-not-allowed border-transparent bg-slate-50 dark:bg-white/[0.03]" : "cursor-pointer border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] hover:border-slate-300 dark:hover:border-white/15", "flex items-center gap-3 p-3 rounded-2xl transition-all border"])}"><input type="radio"${ssrIncludeBooleanAttr(ssrLooseEqual($setup.attemptNumber, n)) ? " checked" : ""}${ssrRenderAttr("value", n)}${ssrIncludeBooleanAttr($setup.assignedAttempts.includes(n)) ? " disabled" : ""} class="w-4 h-4 text-red-500 disabled:cursor-not-allowed"><span class="${ssrRenderClass([[
      $setup.assignedAttempts.includes(n) ? "text-slate-400 dark:text-slate-500 line-through" : n === 3 ? "text-red-600 dark:text-red-400" : "text-slate-800 dark:text-slate-200"
    ], "text-sm font-semibold"])}">${ssrInterpolate(n)}-я пересдача ${ssrInterpolate(n > 1 ? "(Комиссия)" : "")} `);
    if ($setup.assignedAttempts.includes(n)) {
      _push(`<span class="text-xs ml-1 font-normal">(Назначена)</span>`);
    } else {
      _push(`<!---->`);
    }
    _push(`</span></label>`);
  });
  _push(`<!--]--></div></div></div></div><div class="h-px bg-slate-100 dark:bg-white/10 mb-6"></div><div class="${ssrRenderClass([{ "opacity-40 pointer-events-none": $setup.subjectBelongsToAnotherDept }, "flex items-center justify-between mb-4"])}"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-[0_10px_24px_rgba(239,68,68,0.20)]"> 4 </div><h3 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">`);
  _push(ssrRenderComponent($setup["Users"], { class: "w-4 h-4 text-red-500" }, null, _parent));
  _push(` Комиссия </h3></div><button class="md:hidden p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors">`);
  _push(ssrRenderComponent($setup["ChevronDown"], {
    class: ["w-4 h-4 text-slate-400 transition-transform duration-200", $setup.sectionsCollapsed.commission ? "-rotate-90" : ""]
  }, null, _parent));
  _push(`</button></div><div class="${ssrRenderClass({ "hidden md:block": $setup.sectionsCollapsed.commission })}"><div class="${ssrRenderClass([{ "opacity-40 pointer-events-none": $setup.subjectBelongsToAnotherDept }, "mb-8"])}">`);
  if ($setup.mainTeacherLacksDept) {
    _push(`<div class="mb-5 text-sm text-amber-800 dark:text-amber-200 bg-amber-50/80 dark:bg-amber-500/10 p-4 rounded-[22px] border border-amber-200 dark:border-amber-500/20 flex items-start gap-3">`);
    _push(ssrRenderComponent($setup["AlertTriangle"], { class: "w-5 h-5 text-amber-500 shrink-0 mt-0.5" }, null, _parent));
    _push(`<div><span class="font-bold block mb-0.5">Кафедра не указана</span> Назначьте кафедру ведущему преподавателю в панели администратора для формирования состава комиссии. </div></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<div class="grid grid-cols-1 md:grid-cols-3 gap-5"><div class="relative"><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Ведущий `);
  if ($setup.availableMainTeachers.length === 0 && $setup.selectedSubject && !$setup.subjectBelongsToAnotherDept) {
    _push(`<span class="text-red-500 normal-case tracking-normal"> (Нет в истории) </span>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</label><div class="${ssrRenderClass([
    "w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all",
    !$setup.selectedSubject ? "bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed" : "bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500"
  ])}">`);
  if ($setup.mainTeachers.length === 0) {
    _push(`<span class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm"> Выберите... </span>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<!--[-->`);
  ssrRenderList($setup.mainTeachers, (uuid) => {
    _push(`<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-500/20 text-xs font-semibold">${ssrInterpolate($setup.formatShortName($setup.availableMainTeachers.find((t) => t.uuid === uuid)?.fullName))} `);
    _push(ssrRenderComponent($setup["X"], {
      class: "w-3 h-3 hover:text-blue-900 dark:hover:text-white cursor-pointer",
      onClick: ($event) => $setup.removeMainTeacher(uuid)
    }, null, _parent));
    _push(`</span>`);
  });
  _push(`<!--]--></div>`);
  if ($setup.showMainDropdown) {
    _push(`<div class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"><div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0"><div class="relative">`);
    _push(ssrRenderComponent($setup["Search"], { class: "absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" }, null, _parent));
    _push(`<input type="text"${ssrRenderAttr("value", $setup.mainSearchQuery)} placeholder="Поиск..." class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"></div></div><div class="overflow-y-auto flex-1"><!--[-->`);
    ssrRenderList($setup.displayMainTeachers, (t) => {
      _push(`<label class="flex items-center px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"><input type="checkbox"${ssrRenderAttr("value", t.uuid)}${ssrIncludeBooleanAttr(Array.isArray($setup.mainTeachers) ? ssrLooseContain($setup.mainTeachers, t.uuid) : $setup.mainTeachers) ? " checked" : ""} class="w-4 h-4 text-red-500 rounded border-slate-300 focus:ring-red-500 mr-3"><span class="text-sm text-slate-700 dark:text-slate-200">${ssrInterpolate(t.fullName)}</span></label>`);
    });
    _push(`<!--]-->`);
    if ($setup.displayMainTeachers.length === 0) {
      _push(`<div class="p-4 text-sm text-slate-400 text-center"> Ничего не найдено </div>`);
    } else {
      _push(`<!---->`);
    }
    _push(`</div></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.showMainDropdown) {
    _push(`<div class="fixed inset-0 z-10"></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div><div class="relative"><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Председатель `);
  if ($setup.attemptNumber > 1) {
    _push(`<span class="text-red-500">*</span>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</label><div class="${ssrRenderClass([
    "w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all",
    $setup.availableChairmen.length === 0 ? "bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed" : "bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500"
  ])}">`);
  if (!$setup.chairmanTeacher) {
    _push(`<span class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm"> Выберите... </span>`);
  } else {
    _push(`<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/20 text-xs font-semibold">${ssrInterpolate($setup.formatShortName($setup.props.teachers.find((t) => t.uuid === $setup.chairmanTeacher)?.fullName))} `);
    _push(ssrRenderComponent($setup["X"], {
      class: "w-3 h-3 hover:text-amber-900 dark:hover:text-white cursor-pointer",
      onClick: ($event) => $setup.chairmanTeacher = null
    }, null, _parent));
    _push(`</span>`);
  }
  _push(`</div>`);
  if ($setup.showChairmanDropdown) {
    _push(`<div class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"><div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0"><div class="relative">`);
    _push(ssrRenderComponent($setup["Search"], { class: "absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" }, null, _parent));
    _push(`<input type="text"${ssrRenderAttr("value", $setup.chairmanSearchQuery)} placeholder="Поиск..." class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"></div></div><div class="overflow-y-auto flex-1"><!--[-->`);
    ssrRenderList($setup.displayChairmen, (t) => {
      _push(`<div class="px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer text-sm text-slate-700 dark:text-slate-200 transition-colors">${ssrInterpolate(t.fullName)}</div>`);
    });
    _push(`<!--]-->`);
    if ($setup.displayChairmen.length === 0) {
      _push(`<div class="p-4 text-sm text-slate-400 text-center"> Ничего не найдено </div>`);
    } else {
      _push(`<!---->`);
    }
    _push(`</div></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.showChairmanDropdown) {
    _push(`<div class="fixed inset-0 z-10"></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div><div class="relative"><label class="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-[0.18em]"> Члены комиссии </label><div class="${ssrRenderClass([
    "w-full min-h-[48px] rounded-[22px] border p-2.5 flex flex-wrap gap-1.5 items-center transition-all",
    $setup.availableCommissionTeachers.length === 0 ? "bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 opacity-50 cursor-not-allowed" : "bg-white dark:bg-white/[0.03] border-slate-300 dark:border-white/10 cursor-pointer hover:border-red-400 dark:hover:border-red-500"
  ])}">`);
  if ($setup.commissionTeachers.length === 0) {
    _push(`<span class="text-slate-400 dark:text-slate-500 pl-0.5 text-sm"> Выберите... </span>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<!--[-->`);
  ssrRenderList($setup.commissionTeachers, (uuid) => {
    _push(`<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-white/[0.05] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-white/10 text-xs font-semibold">${ssrInterpolate($setup.formatShortName($setup.availableCommissionTeachers.find((t) => t.uuid === uuid)?.fullName))} `);
    _push(ssrRenderComponent($setup["X"], {
      class: "w-3 h-3 hover:text-red-500 cursor-pointer",
      onClick: ($event) => $setup.removeCommTeacher(uuid)
    }, null, _parent));
    _push(`</span>`);
  });
  _push(`<!--]--></div>`);
  if ($setup.showCommDropdown) {
    _push(`<div class="absolute z-20 w-full mt-2 max-h-64 flex flex-col bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl border border-slate-200/80 dark:border-white/10 rounded-[22px] shadow-[0_20px_60px_rgba(15,23,42,0.16)] overflow-hidden"><div class="p-2 border-b border-slate-100 dark:border-white/10 shrink-0"><div class="relative">`);
    _push(ssrRenderComponent($setup["Search"], { class: "absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" }, null, _parent));
    _push(`<input type="text"${ssrRenderAttr("value", $setup.commSearchQuery)} placeholder="Поиск..." class="w-full pl-8 pr-3 py-2 text-sm bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 rounded-xl outline-none focus:border-red-400 dark:text-white transition-colors"></div></div><div class="overflow-y-auto flex-1"><!--[-->`);
    ssrRenderList($setup.displayCommTeachers, (t) => {
      _push(`<label class="flex items-center px-4 py-3 hover:bg-red-50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"><input type="checkbox"${ssrRenderAttr("value", t.uuid)}${ssrIncludeBooleanAttr(Array.isArray($setup.commissionTeachers) ? ssrLooseContain($setup.commissionTeachers, t.uuid) : $setup.commissionTeachers) ? " checked" : ""} class="w-4 h-4 text-red-500 rounded border-slate-300 focus:ring-red-500 mr-3"><span class="text-sm text-slate-700 dark:text-slate-200">${ssrInterpolate(t.fullName)}</span></label>`);
    });
    _push(`<!--]-->`);
    if ($setup.displayCommTeachers.length === 0) {
      _push(`<div class="p-4 text-sm text-slate-400 text-center"> Ничего не найдено </div>`);
    } else {
      _push(`<!---->`);
    }
    _push(`</div></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.showCommDropdown) {
    _push(`<div class="fixed inset-0 z-10"></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div></div></div></div><div class="flex justify-end pt-6 border-t border-slate-100 dark:border-white/10"><button${ssrIncludeBooleanAttr($setup.isSubmitting || $setup.subjectBelongsToAnotherDept) ? " disabled" : ""} class="h-12 px-8 rounded-2xl bg-red-500 hover:bg-red-600 text-white font-black shadow-[0_16px_40px_rgba(239,68,68,0.24)] flex items-center gap-2 transition-all hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0">`);
  if ($setup.isSubmitting) {
    _push(`<div class="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>`);
  } else {
    _push(ssrRenderComponent($setup["CheckCircle"], { class: "w-5 h-5" }, null, _parent));
  }
  _push(` Сохранить </button></div></div></div>`);
}
const _sfc_setup$1 = _sfc_main$1.setup;
_sfc_main$1.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("src/components/RetakeScheduler.vue");
  return _sfc_setup$1 ? _sfc_setup$1(props, ctx) : void 0;
};
const RetakeScheduler = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["ssrRender", _sfc_ssrRender$1]]);

const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "TeacherBoard",
  props: {
    teacherFullName: {},
    retakes: {},
    baseSchedule: {}
  },
  setup(__props, { expose: __expose }) {
    __expose();
    const props = __props;
    const currentDate = ref(/* @__PURE__ */ new Date());
    const setToday = () => {
      currentDate.value = /* @__PURE__ */ new Date();
    };
    const nextWeek = () => {
      const d = new Date(currentDate.value);
      d.setDate(d.getDate() + 7);
      currentDate.value = d;
    };
    const prevWeek = () => {
      const d = new Date(currentDate.value);
      d.setDate(d.getDate() - 7);
      currentDate.value = d;
    };
    const currentWeekStart = computed(() => {
      const d = new Date(currentDate.value);
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const start = new Date(d.setDate(diff));
      start.setHours(0, 0, 0, 0);
      return start;
    });
    const daysOfWeekNames = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
    const shortDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
    const weekDays = computed(() => {
      return daysOfWeekNames.map((dayName, idx) => {
        const date = new Date(currentWeekStart.value);
        date.setDate(date.getDate() + idx);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return { id: dayName, date, dateStr: `${year}-${month}-${day}`, label: `${shortDays[idx]}, ${day}.${month}` };
      });
    });
    const weekDateRange = computed(() => {
      const start = weekDays.value[0].date;
      const end = weekDays.value[5].date;
      const format = (d) => d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
      if (start.getMonth() !== end.getMonth()) {
        return `${format(start).split(" ")[0]} ${format(start).split(" ")[1].slice(0, 3)} — ${format(end)}`;
      }
      return `${start.getDate()} — ${format(end)}`;
    });
    const activeTab = ref("monday");
    watch(currentDate, (val) => {
      const d = val.getDay();
      if (d >= 1 && d <= 6) activeTab.value = daysOfWeekNames[d - 1];
      else activeTab.value = "monday";
    }, { immediate: true });
    const TIME_MAPPING = {
      1: "09:00-10:30",
      2: "10:40-12:10",
      3: "12:20-13:50",
      4: "14:30-16:00",
      5: "16:10-17:40",
      6: "17:50-19:20",
      7: "19:30-21:00"
    };
    const parseDateString = (ds) => {
      if (!ds) return 0;
      const [y, m, d] = ds.split("-");
      return new Date(Number(y), Number(m) - 1, Number(d)).getTime();
    };
    const mergedDaySchedule = computed(() => {
      const activeDay = weekDays.value.find((d) => d.id === activeTab.value);
      if (!activeDay) return [];
      const targetTime = parseDateString(activeDay.dateStr);
      const items = [];
      const processedRetakeIds = /* @__PURE__ */ new Set();
      const todaysRetakes = props.retakes.filter((r) => r.date === activeDay.dateStr);
      todaysRetakes.forEach((retake) => {
        if (!processedRetakeIds.has(retake.id)) {
          processedRetakeIds.add(retake.id);
          let hasConflict = false;
          retake.timeSlots.forEach((slot) => {
            if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
              const conflictingPair = props.baseSchedule[activeDay.id][slot].find((p) => {
                if (!p.start_date || !p.end_date) return true;
                return targetTime >= parseDateString(p.start_date) && targetTime <= parseDateString(p.end_date);
              });
              if (conflictingPair) hasConflict = true;
            }
          });
          items.push({ type: "retake", startSlot: Math.min(...retake.timeSlots), data: retake, hasConflict });
        }
      });
      for (let slot = 1; slot <= 7; slot++) {
        if (props.baseSchedule && props.baseSchedule[activeDay.id] && props.baseSchedule[activeDay.id][slot]) {
          const pairsInSlot = props.baseSchedule[activeDay.id][slot];
          const regularPair = pairsInSlot.find((p) => {
            if (!p.start_date || !p.end_date) return true;
            const start = parseDateString(p.start_date);
            const end = parseDateString(p.end_date);
            return targetTime >= start && targetTime <= end;
          });
          if (regularPair) {
            const isRetakeInThisSlot = todaysRetakes.some((r) => r.timeSlots.includes(slot));
            if (!isRetakeInThisSlot) {
              items.push({ type: "regular", startSlot: slot, data: regularPair });
            }
          }
        }
      }
      return items.sort((a, b) => a.startSlot - b.startSlot);
    });
    const getRoleBadge = (role) => {
      if (role === "CHAIRMAN") {
        return {
          text: "Председатель",
          class: "bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20"
        };
      }
      if (role === "MAIN") {
        return {
          text: "Ведущий",
          class: "bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20"
        };
      }
      return {
        text: "Комиссия",
        class: "bg-slate-50 text-slate-600 border border-slate-200 dark:bg-white/[0.04] dark:text-slate-400 dark:border-white/10"
      };
    };
    const __returned__ = { props, currentDate, setToday, nextWeek, prevWeek, currentWeekStart, daysOfWeekNames, shortDays, weekDays, weekDateRange, activeTab, TIME_MAPPING, parseDateString, mergedDaySchedule, getRoleBadge, get CalendarDays() {
      return CalendarDays;
    }, get ChevronLeft() {
      return ChevronLeft;
    }, get ChevronRight() {
      return ChevronRight;
    }, get MapPin() {
      return MapPin;
    }, get Globe() {
      return Globe;
    }, get AlertTriangle() {
      return AlertTriangle;
    }, get Users() {
      return Users;
    } };
    Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
    return __returned__;
  }
});
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(mergeProps({ class: "relative z-10 rounded-[30px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_20px_70px_rgba(15,23,42,0.10)] overflow-hidden transition-colors" }, _attrs))} data-v-979a6e7a><div class="px-5 py-5 sm:px-6 sm:py-6 border-b border-slate-100 dark:border-white/10 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5" data-v-979a6e7a><div class="flex items-center gap-4" data-v-979a6e7a><div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-red-500 via-red-600 to-blue-600 flex items-center justify-center shadow-[0_16px_40px_rgba(239,68,68,0.24)] shrink-0" data-v-979a6e7a>`);
  _push(ssrRenderComponent($setup["CalendarDays"], { class: "w-5 h-5 text-white" }, null, _parent));
  _push(`</div><div data-v-979a6e7a><p class="text-[11px] uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold" data-v-979a6e7a> Кабинет преподавателя </p><h2 class="mt-1 text-xl sm:text-2xl font-black tracking-[-0.03em] text-slate-950 dark:text-white" data-v-979a6e7a> Моё расписание </h2><p class="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400" data-v-979a6e7a>${ssrInterpolate($props.teacherFullName)}</p></div></div><div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 w-full lg:w-auto" data-v-979a6e7a><button class="h-11 px-4 rounded-2xl text-sm font-semibold text-slate-700 dark:text-slate-200 bg-white/90 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/[0.07] hover:-translate-y-0.5 transition-all" data-v-979a6e7a> Сегодня </button><div class="flex items-center justify-between sm:justify-start bg-white/90 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 p-1 rounded-2xl" data-v-979a6e7a><button class="w-10 h-10 flex items-center justify-center rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.07] transition-colors" data-v-979a6e7a>`);
  _push(ssrRenderComponent($setup["ChevronLeft"], { class: "w-4 h-4" }, null, _parent));
  _push(`</button><div class="px-3 text-center text-sm font-black tracking-tight text-slate-900 dark:text-white min-w-[150px]" data-v-979a6e7a>${ssrInterpolate($setup.weekDateRange)}</div><button class="w-10 h-10 flex items-center justify-center rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/[0.07] transition-colors" data-v-979a6e7a>`);
  _push(ssrRenderComponent($setup["ChevronRight"], { class: "w-4 h-4" }, null, _parent));
  _push(`</button></div></div></div><div class="flex overflow-x-auto border-b border-slate-100 dark:border-white/10 hide-scrollbar bg-slate-50/70 dark:bg-black/10 px-2 sm:px-3 py-2" data-v-979a6e7a><!--[-->`);
  ssrRenderList($setup.weekDays, (day) => {
    _push(`<button class="${ssrRenderClass([
      "flex-1 min-w-[92px] rounded-2xl py-3 text-center text-sm transition-all outline-none border",
      $setup.activeTab === day.id ? "text-white bg-red-500 border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.20)]" : "text-slate-500 dark:text-slate-400 border-transparent hover:border-slate-200 dark:hover:border-white/10 hover:bg-white dark:hover:bg-white/[0.04]"
    ])}" data-v-979a6e7a><div class="text-xs font-black tracking-tight" data-v-979a6e7a>${ssrInterpolate(day.label.split(",")[0])}</div><div class="${ssrRenderClass([$setup.activeTab === day.id ? "text-white/70" : "opacity-70", "text-[10px] mt-0.5"])}" data-v-979a6e7a>${ssrInterpolate(day.label.split(",")[1])}</div></button>`);
  });
  _push(`<!--]--></div><div class="p-5 sm:p-6 min-h-[380px]" data-v-979a6e7a>`);
  if ($setup.mergedDaySchedule.length === 0) {
    _push(`<div class="flex flex-col items-center justify-center py-20 text-center" data-v-979a6e7a><div class="w-16 h-16 rounded-full flex items-center justify-center mb-5 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10" data-v-979a6e7a>`);
    _push(ssrRenderComponent($setup["CalendarDays"], { class: "w-7 h-7 text-slate-300 dark:text-slate-600" }, null, _parent));
    _push(`</div><h3 class="text-lg font-black tracking-tight text-slate-700 dark:text-slate-200" data-v-979a6e7a> Пар нет </h3><p class="text-sm text-slate-400 dark:text-slate-500 mt-2 max-w-xs leading-6" data-v-979a6e7a> На этот день занятия не запланированы </p></div>`);
  } else {
    _push(`<div class="space-y-4" data-v-979a6e7a><!--[-->`);
    ssrRenderList($setup.mergedDaySchedule, (item, idx) => {
      _push(`<div class="flex flex-col lg:flex-row gap-3 lg:gap-4" data-v-979a6e7a><div class="lg:w-28 shrink-0 flex lg:flex-col items-center lg:items-start gap-2 lg:gap-1 lg:pt-3" data-v-979a6e7a><div class="px-3.5 py-2 rounded-2xl font-bold text-slate-600 dark:text-slate-300 text-xs whitespace-nowrap bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10" data-v-979a6e7a>${ssrInterpolate(item.type === "retake" ? item.data.timeSlots.join(", ") : item.startSlot)} пара </div><div class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 font-mono lg:mt-1" data-v-979a6e7a>`);
      if (item.type === "retake") {
        _push(`<!--[-->${ssrInterpolate($setup.TIME_MAPPING[item.data.timeSlots[0]].split("-")[0])} - ${ssrInterpolate($setup.TIME_MAPPING[item.data.timeSlots[item.data.timeSlots.length - 1]].split("-")[1])}<!--]-->`);
      } else {
        _push(`<!--[-->${ssrInterpolate($setup.TIME_MAPPING[item.startSlot])}<!--]-->`);
      }
      _push(`</div></div>`);
      if (item.type === "regular") {
        _push(`<div class="flex-1" data-v-979a6e7a><div class="rounded-[24px] border border-slate-200/80 dark:border-white/10 bg-white/90 dark:bg-white/[0.04] backdrop-blur-xl p-4 sm:p-5 hover:-translate-y-1 hover:shadow-[0_20px_60px_rgba(15,23,42,0.10)] transition-all duration-300" data-v-979a6e7a><div class="flex flex-wrap items-center gap-2 mb-3" data-v-979a6e7a><span class="px-2.5 py-1 text-[10px] font-black rounded-xl uppercase tracking-[0.16em] bg-slate-100 dark:bg-white/[0.05] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10" data-v-979a6e7a> Расписание </span><span class="text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1.5" data-v-979a6e7a>`);
        _push(ssrRenderComponent($setup["Users"], { class: "w-3.5 h-3.5 opacity-60" }, null, _parent));
        _push(` ${ssrInterpolate(item.data.group.number)}</span><span class="text-[10px] text-slate-400 dark:text-slate-500 font-semibold bg-slate-50 dark:bg-white/[0.04] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-white/10" data-v-979a6e7a>${ssrInterpolate(item.data.subject_type.type)}</span></div><h4 class="font-black tracking-tight text-slate-950 dark:text-white text-lg sm:text-xl mb-3" data-v-979a6e7a>${ssrInterpolate(item.data.subject.name)}</h4><div class="${ssrRenderClass([item.data.link ? "text-blue-600 dark:text-blue-400" : "text-slate-500 dark:text-slate-400", "flex flex-wrap items-center gap-3 text-sm font-medium"])}" data-v-979a6e7a>`);
        if (item.data.link) {
          _push(`<a${ssrRenderAttr("href", item.data.link)} target="_blank" class="flex items-center gap-2 hover:underline" data-v-979a6e7a>`);
          _push(ssrRenderComponent($setup["Globe"], { class: "w-4 h-4" }, null, _parent));
          _push(` Онлайн </a>`);
        } else {
          _push(`<span class="flex items-center gap-2" data-v-979a6e7a>`);
          _push(ssrRenderComponent($setup["MapPin"], { class: "w-4 h-4" }, null, _parent));
          _push(` ${ssrInterpolate(item.data.location.name)} `);
          if (item.data.rooms && item.data.rooms[0]) {
            _push(`<span class="font-bold text-slate-700 dark:text-slate-200" data-v-979a6e7a> (${ssrInterpolate(item.data.rooms[0].number)}) </span>`);
          } else {
            _push(`<!---->`);
          }
          _push(`</span>`);
        }
        _push(`</div></div></div>`);
      } else {
        _push(`<!---->`);
      }
      if (item.type === "retake") {
        _push(`<div class="flex-1" data-v-979a6e7a><div class="${ssrRenderClass([
          "rounded-[24px] border p-4 sm:p-5 relative overflow-hidden backdrop-blur-xl hover:-translate-y-1 transition-all duration-300",
          item.hasConflict ? "bg-red-50/90 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 hover:shadow-[0_20px_60px_rgba(239,68,68,0.14)]" : "bg-white/90 dark:bg-white/[0.04] border-slate-200/80 dark:border-white/10 hover:shadow-[0_20px_60px_rgba(15,23,42,0.10)]"
        ])}" data-v-979a6e7a><div class="${ssrRenderClass([item.hasConflict ? "bg-red-500" : "bg-gradient-to-b from-red-500 to-blue-600", "absolute left-0 top-0 bottom-0 w-1.5"])}" data-v-979a6e7a></div><div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 pl-3" data-v-979a6e7a><div class="flex flex-wrap items-center gap-2" data-v-979a6e7a><span class="${ssrRenderClass([item.hasConflict ? "bg-red-500" : "bg-gradient-to-r from-red-500 to-blue-600", "px-3 py-1.5 text-white text-[10px] font-black rounded-xl uppercase tracking-[0.16em]"])}" data-v-979a6e7a> Пересдача </span><span class="${ssrRenderClass([item.hasConflict ? "bg-white/70 dark:bg-black/20 text-red-700 dark:text-red-300 border-red-200 dark:border-red-500/20" : "bg-slate-50 dark:bg-white/[0.04] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-white/10", "px-3 py-1.5 text-[10px] font-bold rounded-xl border"])}" data-v-979a6e7a> Попытка ${ssrInterpolate(item.data.attemptNumber)}</span><span class="${ssrRenderClass([item.hasConflict ? "text-red-700 dark:text-red-300" : "text-slate-600 dark:text-slate-300", "text-xs font-semibold flex items-center gap-1.5"])}" data-v-979a6e7a>`);
        _push(ssrRenderComponent($setup["Users"], { class: "w-3.5 h-3.5" }, null, _parent));
        _push(` ${ssrInterpolate(item.data.groupName)}</span></div>`);
        if (item.hasConflict) {
          _push(`<div class="flex items-center gap-1.5 text-red-600 dark:text-red-400 text-[10px] font-black bg-white dark:bg-red-950/40 px-2.5 py-1.5 rounded-xl border border-red-200 dark:border-red-500/20 self-start" data-v-979a6e7a>`);
          _push(ssrRenderComponent($setup["AlertTriangle"], { class: "w-3 h-3" }, null, _parent));
          _push(` Накладка </div>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div><h4 class="${ssrRenderClass([item.hasConflict ? "text-red-950 dark:text-red-50" : "text-slate-950 dark:text-white", "font-black tracking-tight text-lg sm:text-xl mb-3 pl-3"])}" data-v-979a6e7a>${ssrInterpolate(item.data.subjectName)}</h4><div class="${ssrRenderClass([item.hasConflict ? "text-red-700 dark:text-red-300" : "text-slate-500 dark:text-slate-400", "flex flex-wrap items-center gap-3 text-sm pl-3 font-medium"])}" data-v-979a6e7a>`);
        if (item.data.link) {
          _push(`<a${ssrRenderAttr("href", item.data.link)} target="_blank" class="flex items-center gap-2 hover:underline" data-v-979a6e7a>`);
          _push(ssrRenderComponent($setup["Globe"], { class: "w-4 h-4" }, null, _parent));
          _push(` Онлайн </a>`);
        } else {
          _push(`<span class="flex items-center gap-2" data-v-979a6e7a>`);
          _push(ssrRenderComponent($setup["MapPin"], { class: "w-4 h-4" }, null, _parent));
          _push(` ${ssrInterpolate(item.data.room || "Аудитория уточняется")}</span>`);
        }
        _push(`<span class="${ssrRenderClass([$setup.getRoleBadge(item.data.myRole).class, "px-2.5 py-1 rounded-xl text-[10px] font-black uppercase tracking-[0.14em]"])}" data-v-979a6e7a>${ssrInterpolate($setup.getRoleBadge(item.data.myRole).text)}</span></div></div></div>`);
      } else {
        _push(`<!---->`);
      }
      _push(`</div>`);
    });
    _push(`<!--]--></div>`);
  }
  _push(`</div></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("src/components/TeacherBoard.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const TeacherBoard = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender], ["__scopeId", "data-v-979a6e7a"]]);

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro = createAstro();
const prerender = false;
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Index;
  const user = Astro2.locals.user;
  if (!user) {
    return Astro2.redirect("/login");
  }
  const isAdmin = user.role === "ADMIN";
  const isEmployee = user.role === "EMPLOYEE";
  const canSchedule = isAdmin || isEmployee;
  const hasOwnSchedule = !!user.teacherUuid;
  const activeTab = Astro2.url.searchParams.get("tab") || (hasOwnSchedule ? "schedule" : "retakes");
  let apiGroups = [];
  let apiSubjects = [];
  let localTeachers = [];
  if (canSchedule || hasOwnSchedule) {
    try {
      const dictionaries = await fetchBackendFromServer("/schedule-data/dictionaries", {}, Astro2.request);
      apiGroups = dictionaries?.groups ?? [];
      apiSubjects = dictionaries?.subjects ?? [];
    } catch (error) {
      console.error("Failed to load dictionaries", error);
    }
  }
  if (canSchedule) {
    try {
      localTeachers = await fetchBackendFromServer("/teacher-directory/", {}, Astro2.request);
    } catch (error) {
      console.error("Failed to load teacher directory", error);
    }
  }
  let teacherFullName = user.fullName || user.username;
  let teacherBaseSchedule = null;
  let teacherRetakesFormatted = [];
  if (hasOwnSchedule) {
    try {
      const teacherSchedule = user.teacherUuid ? await fetchBackendFromServer(`/schedule-data/teacher/${user.teacherUuid}`, {}, Astro2.request) : null;
      if (teacherSchedule) {
        teacherFullName = teacherSchedule.teacherFullName;
        teacherBaseSchedule = teacherSchedule.schedule ?? null;
      }
      const myRetakes = await fetchBackendFromServer("/retakes/mine", {}, Astro2.request);
      teacherRetakesFormatted = myRetakes.map((retake) => ({
        ...retake,
        groupName: apiGroups.find((group) => group.uuid === retake.groupUuid)?.number || "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD",
        subjectName: cleanSubjectName(apiSubjects.find((subject) => subject.uuid === retake.subjectUuid)?.name || "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD")
      }));
    } catch (error) {
      console.error("Failed to load teacher retakes", error);
    }
  }
  const roleLabel = isAdmin ? "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD" : isEmployee ? "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD" : "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD";
  const backendApiUrl = getPublicBackendApiUrl();
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "\u0420\u0430\u0431\u043E\u0447\u0438\u0439 \u0441\u0442\u043E\u043B" }, { "default": async ($$result2) => renderTemplate(_a || (_a = __template(["   ", '<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> <div class="mb-6"> <p class="text-[11px] uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500 font-bold">\nBackend-driven auth\n</p> <h1 class="mt-3 text-3xl sm:text-4xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">\n\u0420\u0430\u0431\u043E\u0447\u0438\u0439 \u043A\u0430\u0431\u0438\u043D\u0435\u0442\n</h1> <p class="mt-3 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-2xl leading-7">\n\u0421\u0435\u0441\u0441\u0438\u044F \u0438 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044C \u0442\u0435\u043F\u0435\u0440\u044C \u043E\u043F\u0440\u0435\u0434\u0435\u043B\u044F\u044E\u0442\u0441\u044F \u0447\u0435\u0440\u0435\u0437 backend FastAPI. \u0424\u0440\u043E\u043D\u0442\u0435\u043D\u0434 \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0435\u0442 \u0442\u043E\u043B\u044C\u043A\u043E UI \u0438 backend session cookie.\n</p> </div> ', " ", " ", " </section> <script>(function(){", "\n        const logoutBtn = document.querySelector('#logout-btn');\n\n        logoutBtn?.addEventListener('click', async () => {\n            await fetch(`${backendApiUrl}/auth/logout`, {\n                method: 'POST',\n                credentials: 'include',\n            });\n            window.location.href = '/';\n        });\n    })();<\/script> "], ["   ", '<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> <div class="mb-6"> <p class="text-[11px] uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500 font-bold">\nBackend-driven auth\n</p> <h1 class="mt-3 text-3xl sm:text-4xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">\n\u0420\u0430\u0431\u043E\u0447\u0438\u0439 \u043A\u0430\u0431\u0438\u043D\u0435\u0442\n</h1> <p class="mt-3 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-2xl leading-7">\n\u0421\u0435\u0441\u0441\u0438\u044F \u0438 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044C \u0442\u0435\u043F\u0435\u0440\u044C \u043E\u043F\u0440\u0435\u0434\u0435\u043B\u044F\u044E\u0442\u0441\u044F \u0447\u0435\u0440\u0435\u0437 backend FastAPI. \u0424\u0440\u043E\u043D\u0442\u0435\u043D\u0434 \u0438\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0435\u0442 \u0442\u043E\u043B\u044C\u043A\u043E UI \u0438 backend session cookie.\n</p> </div> ', " ", " ", " </section> <script>(function(){", "\n        const logoutBtn = document.querySelector('#logout-btn');\n\n        logoutBtn?.addEventListener('click', async () => {\n            await fetch(\\`\\${backendApiUrl}/auth/logout\\`, {\n                method: 'POST',\n                credentials: 'include',\n            });\n            window.location.href = '/';\n        });\n    })();<\/script> "])), maybeRenderHead(), hasOwnSchedule && canSchedule && renderTemplate`<div class="mb-6 overflow-x-auto hide-scrollbar"> <div class="inline-flex p-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm"> <a href="?tab=schedule"${addAttribute(`px-5 py-2.5 text-sm font-semibold rounded-xl transition-all whitespace-nowrap ${activeTab === "schedule" ? "bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800"}`, "class")}>
Моё расписание
</a> <a href="?tab=retakes"${addAttribute(`px-5 py-2.5 text-sm font-semibold rounded-xl transition-all whitespace-nowrap ${activeTab === "retakes" ? "bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800"}`, "class")}>
Назначение пересдач
</a> </div> </div>`, activeTab === "retakes" && canSchedule && renderTemplate`${renderComponent($$result2, "RetakeScheduler", RetakeScheduler, { "client:load": true, "backendApiUrl": backendApiUrl, "groups": apiGroups, "subjects": apiSubjects, "teachers": localTeachers, "currentUser": {
    id: String(user.id),
    role: user.role,
    departmentIds: user.departmentIds
  }, "client:component-hydration": "load", "client:component-path": "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/components/RetakeScheduler.vue", "client:component-export": "default" })}`, activeTab === "schedule" && hasOwnSchedule && renderTemplate`${renderComponent($$result2, "TeacherBoard", TeacherBoard, { "client:load": true, "teacherFullName": teacherFullName, "retakes": teacherRetakesFormatted, "baseSchedule": teacherBaseSchedule, "client:component-hydration": "load", "client:component-path": "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/components/TeacherBoard.vue", "client:component-export": "default" })}`, defineScriptVars({ backendApiUrl })), "nav-actions": async ($$result2) => renderTemplate`${renderComponent($$result2, "Fragment", Fragment, { "slot": "nav-actions" }, { "default": async ($$result3) => renderTemplate`${isAdmin && renderTemplate`<a href="/admin" class="text-xs font-semibold text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-800/50 px-3 py-1.5 rounded-xl hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-all">
Админка
</a>`}<a href="/profile" class="text-xs font-medium text-gray-700 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-all">
Профиль
</a> <button id="logout-btn" class="text-xs font-medium text-gray-700 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-rose-950/30 transition-all">
Выйти
</button> ` })}`, "nav-center": async ($$result2) => renderTemplate`${renderComponent($$result2, "Fragment", Fragment, { "slot": "nav-center" }, { "default": async ($$result3) => renderTemplate` <div class="hidden sm:flex items-center gap-2 min-w-0"> <span class="text-sm font-medium text-slate-700 dark:text-slate-300 truncate"> ${teacherFullName} </span> <span class="inline-flex px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"> ${roleLabel} </span> </div> ` })}` })}`;
}, "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/pages/dashboard/index.astro", void 0);

const $$file = "C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/dashboard/index.astro";
const $$url = "/dashboard";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Index,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
