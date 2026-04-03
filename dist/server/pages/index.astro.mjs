/* empty css                                 */
import { e as createComponent, k as renderComponent, r as renderTemplate, m as maybeRenderHead } from '../chunks/astro/server__Jo3gmtv.mjs';
import 'piccolore';
import { _ as _export_sfc, $ as $$Layout } from '../chunks/Layout_BkxlrDkt.mjs';
import { ref, useSSRContext, defineComponent, onMounted, computed, mergeProps } from 'vue';
import { X, Info, Users, ChevronDown, Globe, MapPin, Clock, Search } from 'lucide-vue-next';
import { ssrRenderAttrs, ssrRenderComponent, ssrRenderAttr, ssrRenderList, ssrInterpolate, ssrRenderStyle, ssrRenderClass } from 'vue/server-renderer';
import { a as fetchBackendFromServer } from '../chunks/backend-api_iSCceNha.mjs';
import { c as cleanSubjectName } from '../chunks/subjectNorm_B8KQ8M6A.mjs';
export { renderers } from '../renderers.mjs';

function daysUntil(dateStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const target = new Date(y, m - 1, d);
  const today = /* @__PURE__ */ new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / (1e3 * 60 * 60 * 24));
}
function getDateLabel(dateStr) {
  const days = daysUntil(dateStr);
  if (days < 0) {
    return {
      text: "Прошёл",
      colorClass: "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500",
      sortPriority: 4
    };
  }
  if (days === 0) {
    return {
      text: "Сегодня",
      colorClass: "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300",
      sortPriority: 0
    };
  }
  if (days === 1) {
    return {
      text: "Завтра",
      colorClass: "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300",
      sortPriority: 1
    };
  }
  if (days <= 6) {
    return {
      text: `Через ${days} дн.`,
      colorClass: "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300",
      sortPriority: 2
    };
  }
  return {
    text: `Через ${days} дн.`,
    colorClass: "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400",
    sortPriority: 3
  };
}

const STORAGE_KEY = "poli-rasp:recent-groups";
const MAX_RECENT = 5;
function useRecentGroups() {
  const recentGroups = ref(loadFromStorage());
  function loadFromStorage() {
    if (typeof localStorage === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  }
  function saveToStorage(groups) {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(groups));
  }
  function addRecentGroup(group) {
    const filtered = recentGroups.value.filter((g) => g.uuid !== group.uuid);
    const updated = [group, ...filtered].slice(0, MAX_RECENT);
    recentGroups.value = updated;
    saveToStorage(updated);
  }
  function clearRecentGroups() {
    recentGroups.value = [];
    saveToStorage([]);
  }
  return { recentGroups, addRecentGroup, clearRecentGroups };
}

const INFO_KEY = "poli-rasp:info-dismissed";
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "StudentBoard",
  props: {
    groups: {},
    retakes: {},
    today: {}
  },
  setup(__props, { expose: __expose }) {
    __expose();
    const props = __props;
    const groupSearchQuery = ref("");
    const selectedGroupUuid = ref("");
    const showGroupDropdown = ref(false);
    const selectedSubjectFilter = ref("");
    const { recentGroups, addRecentGroup, clearRecentGroups } = useRecentGroups();
    const infoDismissed = ref(false);
    const infoCollapsed = ref(false);
    onMounted(() => {
      if (localStorage.getItem(INFO_KEY) === "1") infoDismissed.value = true;
    });
    function dismissInfo() {
      infoDismissed.value = true;
      localStorage.setItem(INFO_KEY, "1");
    }
    const openCommissions = ref(/* @__PURE__ */ new Set());
    function toggleCommission(id) {
      const s = new Set(openCommissions.value);
      s.has(id) ? s.delete(id) : s.add(id);
      openCommissions.value = s;
    }
    const filteredGroups = computed(() => {
      if (!groupSearchQuery.value) return props.groups.slice(0, 50);
      const q = groupSearchQuery.value.toLowerCase();
      return props.groups.filter((g) => g.number.toLowerCase().includes(q)).slice(0, 50);
    });
    const selectGroup = (group) => {
      selectedGroupUuid.value = group.uuid;
      groupSearchQuery.value = group.number;
      showGroupDropdown.value = false;
      selectedSubjectFilter.value = "";
      addRecentGroup(group);
    };
    const sortTeachers = (teachers) => {
      if (!teachers) return [];
      const roleWeights = { MAIN: 1, CHAIRMAN: 2, COMMISSION: 3 };
      return [...teachers].sort((a, b) => (roleWeights[a.role] || 99) - (roleWeights[b.role] || 99));
    };
    const studentRetakes = computed(() => {
      if (!selectedGroupUuid.value) return [];
      return props.retakes.filter((r) => r.groupUuid === selectedGroupUuid.value).map((r) => ({ ...r, teachers: sortTeachers(r.teachers), dateLabel: getDateLabel(r.date) })).sort((a, b) => {
        const pastA = daysUntil(a.date) < 0 ? 1 : 0;
        const pastB = daysUntil(b.date) < 0 ? 1 : 0;
        if (pastA !== pastB) return pastA - pastB;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });
    });
    const availableSubjects = computed(() => {
      const subjects = /* @__PURE__ */ new Set();
      studentRetakes.value.forEach((r) => subjects.add(r.subjectName));
      return Array.from(subjects).sort();
    });
    const groupedRetakes = computed(() => {
      let filtered = studentRetakes.value;
      if (selectedSubjectFilter.value) {
        filtered = filtered.filter((r) => r.subjectName === selectedSubjectFilter.value);
      }
      const grouped = {};
      filtered.forEach((r) => {
        if (!grouped[r.subjectName]) grouped[r.subjectName] = [];
        grouped[r.subjectName].push(r);
      });
      return grouped;
    });
    const TIME_MAPPING = {
      1: "09:00–10:30",
      2: "10:40–12:10",
      3: "12:20–13:50",
      4: "14:30–16:00",
      5: "16:10–17:40",
      6: "17:50–19:20",
      7: "19:30–21:00"
    };
    const formatDate = (dateStr) => {
      return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(new Date(dateStr));
    };
    const getRoleName = (role) => {
      if (role === "MAIN") return "Ведущий";
      if (role === "CHAIRMAN") return "Председатель";
      return "Комиссия";
    };
    const getRoleColor = (role) => {
      if (role === "MAIN") return "text-blue-600 dark:text-blue-400";
      if (role === "CHAIRMAN") return "text-amber-600 dark:text-amber-400";
      return "text-slate-500 dark:text-slate-400";
    };
    const __returned__ = { props, groupSearchQuery, selectedGroupUuid, showGroupDropdown, selectedSubjectFilter, recentGroups, addRecentGroup, clearRecentGroups, infoDismissed, infoCollapsed, INFO_KEY, dismissInfo, openCommissions, toggleCommission, filteredGroups, selectGroup, sortTeachers, studentRetakes, availableSubjects, groupedRetakes, TIME_MAPPING, formatDate, getRoleName, getRoleColor, get Search() {
      return Search;
    }, get Clock() {
      return Clock;
    }, get MapPin() {
      return MapPin;
    }, get Globe() {
      return Globe;
    }, get ChevronDown() {
      return ChevronDown;
    }, get Users() {
      return Users;
    }, get Info() {
      return Info;
    }, get X() {
      return X;
    }, get daysUntil() {
      return daysUntil;
    } };
    Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
    return __returned__;
  }
});
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(mergeProps({ class: "w-full relative z-10" }, _attrs))}><div class="mb-8"><div class="mb-3"><p class="text-[11px] uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500 font-bold"> Поиск </p><h3 class="mt-2 text-2xl sm:text-3xl font-black tracking-[-0.04em] text-slate-950 dark:text-white"> Найдите свою группу </h3><p class="mt-2 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-2xl leading-7"> Введите номер группы, чтобы быстро получить актуальное расписание пересдач. </p></div><div class="relative mt-5"><div class="relative group">`);
  _push(ssrRenderComponent($setup["Search"], { class: "absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-slate-500 pointer-events-none transition-colors group-focus-within:text-red-500" }, null, _parent));
  _push(`<input${ssrRenderAttr("value", $setup.groupSearchQuery)} type="text" placeholder="Введите номер группы для поиска пересдач..." class="w-full h-16 pl-14 pr-5 text-base rounded-[22px] border border-slate-200/80 dark:border-white/10 bg-white/85 dark:bg-white/[0.04] backdrop-blur-xl shadow-[0_10px_30px_rgba(15,23,42,0.06)] dark:shadow-none focus:border-red-400 dark:focus:border-red-500 focus:ring-4 focus:ring-red-500/10 outline-none transition-all text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500"></div>`);
  if ($setup.showGroupDropdown && ($setup.filteredGroups.length > 0 || $setup.recentGroups.length > 0 && !$setup.groupSearchQuery)) {
    _push(`<div class="absolute z-30 w-full mt-3 rounded-[24px] border border-slate-200/80 dark:border-white/10 bg-white/95 dark:bg-[#14171d]/95 backdrop-blur-2xl shadow-[0_24px_80px_rgba(15,23,42,0.18)] overflow-hidden max-h-80 overflow-y-auto">`);
    if ($setup.recentGroups.length > 0 && !$setup.groupSearchQuery) {
      _push(`<div class="border-b border-slate-100 dark:border-white/10"><div class="px-5 py-3 flex items-center justify-between"><span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.22em]">Недавние</span><button class="text-[10px] font-semibold text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors uppercase tracking-[0.16em]"> Очистить </button></div><!--[-->`);
      ssrRenderList($setup.recentGroups, (g) => {
        _push(`<div class="px-5 py-3.5 text-sm cursor-pointer text-slate-700 dark:text-slate-200 flex items-center gap-3 hover:bg-red-50 dark:hover:bg-white/[0.04] transition-colors">`);
        _push(ssrRenderComponent($setup["Clock"], { class: "w-4 h-4 text-slate-400 shrink-0" }, null, _parent));
        _push(`<span class="font-semibold">${ssrInterpolate(g.number)}</span></div>`);
      });
      _push(`<!--]--></div>`);
    } else {
      _push(`<!---->`);
    }
    _push(`<!--[-->`);
    ssrRenderList($setup.filteredGroups, (g) => {
      _push(`<div class="px-5 py-3.5 text-sm cursor-pointer text-slate-700 dark:text-slate-200 font-semibold hover:bg-red-50 dark:hover:bg-white/[0.04] transition-colors">${ssrInterpolate(g.number)}</div>`);
    });
    _push(`<!--]--></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.showGroupDropdown) {
    _push(`<div class="fixed inset-0 z-20"></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div></div>`);
  if (!$setup.infoDismissed) {
    _push(`<div class="mb-8 rounded-[26px] overflow-hidden border border-slate-200/80 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_12px_40px_rgba(15,23,42,0.08)]"><div class="flex items-center gap-3 px-5 sm:px-6 py-4 bg-red-50/70 dark:bg-red-500/10"><div class="w-10 h-10 rounded-2xl bg-red-100 dark:bg-red-500/15 flex items-center justify-center shrink-0">`);
    _push(ssrRenderComponent($setup["Info"], { class: "w-4 h-4 text-red-600 dark:text-red-400" }, null, _parent));
    _push(`</div><h3 class="text-sm sm:text-[15px] font-extrabold text-slate-900 dark:text-white flex-grow tracking-tight"> Порядок проведения пересдач </h3><button class="p-2 rounded-xl hover:bg-red-100/70 dark:hover:bg-red-500/10 transition-colors text-slate-400">`);
    _push(ssrRenderComponent($setup["ChevronDown"], {
      class: ["w-4 h-4 transition-transform duration-200", $setup.infoCollapsed ? "-rotate-90" : "rotate-0"]
    }, null, _parent));
    _push(`</button><button class="p-2 rounded-xl hover:bg-red-100/70 dark:hover:bg-red-500/10 transition-colors text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">`);
    _push(ssrRenderComponent($setup["X"], { class: "w-4 h-4" }, null, _parent));
    _push(`</button></div><div class="px-5 sm:px-6 py-5 space-y-3 text-sm text-slate-600 dark:text-slate-300 leading-7 border-t border-slate-100 dark:border-white/10" style="${ssrRenderStyle(!$setup.infoCollapsed ? null : { display: "none" })}"><p> Всего предусмотрено <span class="font-bold text-slate-900 dark:text-white">3 повторные промежуточные аттестации</span>. <span class="font-bold text-slate-900 dark:text-white">Последняя (3-я) повторная аттестация</span> назначается для обучающихся, пропустивших первую и/или вторую аттестации по уважительным причинам, или ввиду удовлетворения апелляции. </p><p> Третья дата назначается <span class="font-bold text-slate-900 dark:text-white">только по заявлению обучающегося</span> и при предоставлении подтверждающих документов. </p><p class="text-xs text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-white/10"> * Заявление на апелляцию подается в день проведения пересдачи. </p></div></div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.selectedGroupUuid) {
    _push(`<div>`);
    if ($setup.studentRetakes.length === 0) {
      _push(`<div class="py-20 text-center"><div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 bg-slate-100 dark:bg-white/[0.05] border border-slate-200 dark:border-white/10">`);
      _push(ssrRenderComponent($setup["Search"], { class: "w-8 h-8 text-slate-300 dark:text-slate-600" }, null, _parent));
      _push(`</div><h3 class="text-xl font-black tracking-tight text-slate-800 dark:text-slate-200 mb-2"> Пересдачи не назначены </h3><p class="text-sm text-slate-400 dark:text-slate-500 max-w-sm mx-auto leading-7"> Для группы <span class="font-semibold text-slate-500 dark:text-slate-400">${ssrInterpolate($setup.groupSearchQuery)}</span> пересдачи ещё не запланированы. </p></div>`);
    } else {
      _push(`<div>`);
      if ($setup.availableSubjects.length > 1) {
        _push(`<div class="mb-8 flex flex-wrap items-center gap-2 overflow-x-auto hide-scrollbar pb-1"><button class="${ssrRenderClass([$setup.selectedSubjectFilter === "" ? "bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.2)]" : "bg-white/90 dark:bg-white/[0.04] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15", "px-4 py-2.5 rounded-2xl text-xs font-bold border transition-all whitespace-nowrap hover:-translate-y-0.5"])}"> Все </button><!--[-->`);
        ssrRenderList($setup.availableSubjects, (sub) => {
          _push(`<button class="${ssrRenderClass([$setup.selectedSubjectFilter === sub ? "bg-red-500 text-white border-red-500 shadow-[0_12px_28px_rgba(239,68,68,0.2)]" : "bg-white/90 dark:bg-white/[0.04] text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/15", "px-4 py-2.5 rounded-2xl text-xs font-bold border transition-all whitespace-nowrap hover:-translate-y-0.5"])}">${ssrInterpolate(sub)}</button>`);
        });
        _push(`<!--]--></div>`);
      } else {
        _push(`<!---->`);
      }
      _push(`<!--[-->`);
      ssrRenderList($setup.groupedRetakes, (retakesList, subjectName) => {
        _push(`<div class="mb-10"><div class="flex items-center gap-3 mb-4"><div class="w-1.5 h-6 rounded-full bg-red-500"></div><h3 class="text-base sm:text-lg font-black tracking-tight text-slate-950 dark:text-white">${ssrInterpolate(subjectName)}</h3><span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-white/[0.05] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-white/10">${ssrInterpolate(retakesList.length)}</span></div><div class="space-y-4"><!--[-->`);
        ssrRenderList(retakesList, (retake) => {
          _push(`<div class="${ssrRenderClass([{ "opacity-55": $setup.daysUntil(retake.date) < 0 }, "rounded-[26px] border border-slate-200/80 dark:border-white/10 bg-white/88 dark:bg-white/[0.04] backdrop-blur-xl p-5 sm:p-6 shadow-[0_14px_40px_rgba(15,23,42,0.07)] hover:shadow-[0_22px_60px_rgba(15,23,42,0.12)] hover:-translate-y-1 transition-all duration-300"])}"><div class="flex flex-wrap items-center gap-2 mb-4"><span class="${ssrRenderClass([retake.attemptNumber === 1 ? "bg-blue-600" : retake.attemptNumber === 2 ? "bg-amber-500" : "bg-red-500", "px-3 py-1.5 text-[10px] font-extrabold rounded-xl uppercase tracking-[0.16em] text-white"])}"> Попытка ${ssrInterpolate(retake.attemptNumber || 1)}</span><span class="${ssrRenderClass([retake.dateLabel.colorClass, "px-3 py-1.5 text-[10px] font-bold rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-white/[0.04]"])}">${ssrInterpolate(retake.dateLabel.text)}</span></div><div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4"><div><div class="text-xl sm:text-2xl font-black tracking-tight text-slate-950 dark:text-white">${ssrInterpolate($setup.formatDate(retake.date))}</div><div class="flex flex-wrap items-center gap-x-5 gap-y-2 mt-2.5 text-sm text-slate-500 dark:text-slate-400"><span class="flex items-center gap-2">`);
          _push(ssrRenderComponent($setup["Clock"], { class: "w-4 h-4 shrink-0 opacity-70" }, null, _parent));
          _push(` ${ssrInterpolate(retake.timeSlots.map((s) => $setup.TIME_MAPPING[s]).join(", "))}</span><span class="${ssrRenderClass([retake.link ? "text-blue-600 dark:text-blue-400" : "", "flex items-center gap-2"])}">`);
          if (retake.link) {
            _push(`<!--[-->`);
            _push(ssrRenderComponent($setup["Globe"], { class: "w-4 h-4 opacity-90" }, null, _parent));
            _push(`<a${ssrRenderAttr("href", retake.link)} target="_blank" class="hover:underline font-semibold"> Онлайн </a><!--]-->`);
          } else {
            _push(`<!--[-->`);
            _push(ssrRenderComponent($setup["MapPin"], { class: "w-4 h-4 opacity-70" }, null, _parent));
            _push(` ${ssrInterpolate(retake.room || "Аудитория уточняется")}<!--]-->`);
          }
          _push(`</span></div></div><div class="self-start lg:self-center"><div class="px-4 py-2 rounded-2xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-xs font-bold text-slate-500 dark:text-slate-400 whitespace-nowrap">${ssrInterpolate(retake.timeSlots.join(", "))} пара </div></div></div><div class="mt-5 pt-5 border-t border-slate-100 dark:border-white/10"><button class="md:hidden w-full flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3"><span class="flex items-center gap-2">`);
          _push(ssrRenderComponent($setup["Users"], { class: "w-4 h-4" }, null, _parent));
          _push(` Комиссия (${ssrInterpolate(retake.teachers.length)}) </span>`);
          _push(ssrRenderComponent($setup["ChevronDown"], {
            class: ["w-4 h-4 transition-transform duration-200", $setup.openCommissions.has(retake.id) ? "rotate-180" : ""]
          }, null, _parent));
          _push(`</button><div class="${ssrRenderClass({ "hidden md:block": !$setup.openCommissions.has(retake.id), "block": $setup.openCommissions.has(retake.id) })}">`);
          if (retake.teachers && retake.teachers.length > 0) {
            _push(`<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3"><!--[-->`);
            ssrRenderList(retake.teachers, (t) => {
              _push(`<div class="flex items-center gap-3 p-3 rounded-2xl bg-slate-50/90 dark:bg-white/[0.04] border border-slate-200/70 dark:border-white/10"><div class="${ssrRenderClass([t.role === "MAIN" ? "bg-blue-500" : t.role === "CHAIRMAN" ? "bg-amber-500" : "bg-slate-400", "w-2 h-2 rounded-full shrink-0"])}"></div><div class="min-w-0"><div class="${ssrRenderClass([$setup.getRoleColor(t.role), "text-[10px] font-bold uppercase tracking-[0.18em]"])}">${ssrInterpolate($setup.getRoleName(t.role))}</div><div class="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">${ssrInterpolate(t.name)}</div></div></div>`);
            });
            _push(`<!--]--></div>`);
          } else {
            _push(`<div class="text-sm text-slate-400 italic"> Преподаватели не назначены </div>`);
          }
          _push(`</div></div></div>`);
        });
        _push(`<!--]--></div></div>`);
      });
      _push(`<!--]--></div>`);
    }
    _push(`</div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("src/components/StudentBoard.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const StudentBoard = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);

const prerender = false;
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  let apiGroups = [];
  let apiSubjects = [];
  let allRetakes = [];
  try {
    const [dictionaries, retakesRes] = await Promise.all([
      fetchBackendFromServer("/schedule-data/dictionaries"),
      fetchBackendFromServer("/retakes/")
    ]);
    apiGroups = dictionaries?.groups ?? [];
    apiSubjects = dictionaries?.subjects ?? [];
    allRetakes = retakesRes;
  } catch (error) {
    console.error("Failed to load public retakes", error);
  }
  const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
  const formattedRetakes = allRetakes.map((retake) => ({
    id: retake.id,
    groupUuid: retake.groupUuid,
    groupName: apiGroups.find((group) => group.uuid === retake.groupUuid)?.number || "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD",
    subjectName: cleanSubjectName(apiSubjects.find((subject) => subject.uuid === retake.subjectUuid)?.name || "\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD"),
    date: retake.date,
    timeSlots: retake.timeSlots,
    room: retake.roomUuid,
    link: retake.link,
    attemptNumber: retake.attemptNumber,
    teachers: retake.teachers || []
  }));
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "\u0420\u0430\u0441\u043F\u0438\u0441\u0430\u043D\u0438\u0435 \u043F\u0435\u0440\u0435\u0441\u0434\u0430\u0447" }, { "default": async ($$result2) => renderTemplate`  ${maybeRenderHead()}<div class="relative"> <section class="relative min-h-[78vh] sm:min-h-[82vh] flex items-center overflow-hidden"> <div class="absolute inset-0 pointer-events-none"> <div class="absolute inset-0 bg-[radial-gradient(circle_at_18%_22%,rgba(239,68,68,0.34),transparent_22%),radial-gradient(circle_at_82%_16%,rgba(59,130,246,0.24),transparent_20%),linear-gradient(180deg,rgba(5,7,11,0.88)_0%,rgba(10,10,14,0.82)_42%,rgba(15,23,42,0.72)_100%)] dark:bg-[radial-gradient(circle_at_18%_22%,rgba(239,68,68,0.38),transparent_22%),radial-gradient(circle_at_82%_16%,rgba(59,130,246,0.26),transparent_20%),linear-gradient(180deg,rgba(4,4,6,0.92)_0%,rgba(8,10,15,0.88)_42%,rgba(15,23,42,0.82)_100%)]"></div> <div class="absolute inset-0 opacity-[0.08] bg-[linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] bg-[size:42px_42px]"></div> <div class="absolute -top-20 left-[8%] w-[420px] h-[300px] rounded-full bg-red-500/15 blur-3xl animate-pulse"></div> <div class="absolute top-[12%] right-[8%] w-[360px] h-[300px] rounded-full bg-blue-500/15 blur-3xl animate-pulse"></div> <div class="absolute bottom-[-120px] left-1/2 -translate-x-1/2 w-[900px] h-[300px] rounded-full border border-white/10"></div> <div class="absolute bottom-[-170px] left-1/2 -translate-x-1/2 w-[1200px] h-[420px] rounded-full border border-white/5"></div> </div> <div class="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-4 sm:-mt-6 pb-28 sm:pb-32"> <div class="max-w-3xl"> <h1 class="text-white text-4xl sm:text-6xl lg:text-7xl font-black tracking-[-0.05em] leading-[0.94]">
Расписание
<span class="block text-white/75">пересдач</span> </h1> <div class="mt-8 flex flex-wrap items-center gap-3"> <div class="mt-8 flex flex-wrap items-center gap-3"> <a href="#board" class="inline-flex items-center justify-center h-12 px-6 rounded-2xl bg-red-500 text-white text-sm font-bold shadow-[0_16px_40px_rgba(239,68,68,0.28)] hover:bg-blue-600 hover:shadow-[0_16px_40px_rgba(37,99,235,0.28)] hover:-translate-y-0.5 transition-all duration-300">
Смотреть расписание
</a> <a href="/login" class="inline-flex items-center justify-center h-12 px-6 rounded-2xl border border-white/12 bg-white/8 text-white/90 text-sm font-semibold backdrop-blur-xl hover:border-blue-500/50 hover:bg-blue-500/20 hover:text-blue-600 dark:hover:text-white/90 hover:-translate-y-0.5 transition-all duration-300">
Личный кабинет
</a> </div> </div> </div> </div></section> <section class="relative z-20 -mt-32 sm:-mt-40 pb-8"> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"> <div class="grid grid-cols-1 lg:grid-cols-[1.05fr_1.25fr] rounded-[28px] overflow-hidden shadow-[0_24px_80px_rgba(15,23,42,0.22)] border border-white/10"> <div class="bg-red-500 px-6 py-7 sm:px-8 sm:py-8 text-white"> <p class="text-[11px] sm:text-xs uppercase tracking-[0.22em] text-white/70 font-bold">
Сервис
</p> <h2 class="mt-3 text-2xl sm:text-3xl font-black tracking-tight leading-tight">
Всё расписание пересдач
                            в одном месте
</h2> <p class="mt-4 text-sm sm:text-base text-white/80 max-w-md leading-7">
Быстрый доступ к предметам, группам, датам, времени проведения
                            и преподавателям без лишних переходов.
</p> </div> <div class="bg-white dark:bg-[#111318] px-6 py-7 sm:px-8 sm:py-8"> <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-5"> <div> <p class="text-[11px] sm:text-xs uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500 font-bold">
Актуальность
</p> <h3 class="mt-3 text-2xl sm:text-3xl font-black tracking-tight text-slate-950 dark:text-white">
Удобный поиск и
<br class="hidden sm:block">
актуальные данные
</h3> </div> <div class="shrink-0"> <div class="text-5xl sm:text-6xl font-black tracking-[-0.06em] text-slate-950 dark:text-white"> ${formattedRetakes.length} </div> <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">
записей в системе
</div> </div> </div> </div> </div> </div> </section> <section id="board" class="relative z-10 pb-16 sm:pb-20"> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"> <div class="mb-6 sm:mb-8"> <p class="text-[11px] sm:text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500 font-bold">
Основной раздел
</p> <h2 class="mt-3 text-2xl sm:text-4xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">
Актуальное расписание
</h2> <p class="mt-3 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-2xl leading-7">
Здесь можно быстро найти нужную пересдачу по группе, предмету,
                        преподавателю и дате.
</p> </div> <div class="rounded-[32px] border border-white/10 bg-white/60 dark:bg-white/[0.04] backdrop-blur-2xl shadow-[0_24px_80px_rgba(15,23,42,0.14)] p-3 sm:p-4 lg:p-5"> ${renderComponent($$result2, "StudentBoard", StudentBoard, { "client:load": true, "groups": apiGroups, "retakes": formattedRetakes, "today": today, "client:component-hydration": "load", "client:component-path": "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/components/StudentBoard.vue", "client:component-export": "default" })} </div> </div> </section> </div> `, "nav-actions": async ($$result2) => renderTemplate`<a href="/login" class="inline-flex items-center justify-center h-10 px-4 rounded-2xl border border-gray-300 bg-white text-gray-900 hover:bg-gray-100 hover:border-gray-400 backdrop-blur-xl text-sm font-semibold transition-all duration-300 hover:-translate-y-0.5" style="background-color: white; color: #1f2937; border-color: #d1d5db;">
Войти
</a>` })}`;
}, "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/pages/index.astro", void 0);

const $$file = "C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/index.astro";
const $$url = "";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Index,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
