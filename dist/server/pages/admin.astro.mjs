/* empty css                                 */
import { e as createComponent, k as renderComponent, r as renderTemplate, h as createAstro, l as Fragment, m as maybeRenderHead } from '../chunks/astro/server__Jo3gmtv.mjs';
import 'piccolore';
import { useSSRContext, defineComponent, ref, reactive, mergeProps } from 'vue';
import { f as fetchBackendFromBrowser, B as BackendApiError, a as fetchBackendFromServer } from '../chunks/backend-api_iSCceNha.mjs';
import { ssrRenderAttrs, ssrIncludeBooleanAttr, ssrInterpolate, ssrRenderClass, ssrRenderAttr, ssrLooseContain, ssrLooseEqual, ssrRenderList } from 'vue/server-renderer';
import { _ as _export_sfc, $ as $$Layout } from '../chunks/Layout_BkxlrDkt.mjs';
import { g as getPublicBackendApiUrl } from '../chunks/backend-auth_-lm5w3qF.mjs';
export { renderers } from '../renderers.mjs';

const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "AdminPanel",
  props: {
    backendApiUrl: {},
    initialUsers: {},
    initialDepartments: {},
    initialTeacherDirectory: {},
    initialLoadError: {}
  },
  setup(__props, { expose: __expose }) {
    __expose();
    const props = __props;
    const users = ref([...props.initialUsers]);
    const departments = ref([...props.initialDepartments]);
    const teacherDirectory = ref([...props.initialTeacherDirectory]);
    const loadError = ref(props.initialLoadError ?? "");
    const status = ref(null);
    const busy = reactive({ reload: false, user: false, department: false, teacher: false, maintenance: false });
    const editing = reactive({
      userId: null,
      departmentId: null,
      teacherUuid: null
    });
    const userForm = reactive({
      username: "",
      full_name: "",
      role: "EMPLOYEE",
      is_active: true,
      department_id: "",
      department_ids: [],
      teacher_uuid: "",
      password: ""
    });
    const departmentForm = reactive({ name: "", short_name: "" });
    const teacherForm = reactive({ full_name: "", department_ids: [] });
    const errorText = (error, fallback) => error instanceof BackendApiError ? error.detail : error instanceof Error ? error.message : fallback;
    const setStatus = (kind, message) => {
      status.value = { kind, message };
    };
    const clearStatus = () => {
      status.value = null;
    };
    const uniq = (values) => [...new Set(values)];
    const normalizeDeptIds = (primaryId, ids) => {
      const next = uniq(ids);
      if (primaryId) next.includes(Number(primaryId)) || next.push(Number(primaryId));
      return next;
    };
    const scopeLabel = (ids) => ids.length ? ids.map((id) => {
      const department = departments.value.find((item) => item.id === id);
      return department ? `${department.short_name} (${department.name})` : `#${id}`;
    }).join(", ") : "None";
    const teacherLabel = (uuid) => {
      if (!uuid) return "None";
      const teacher = teacherDirectory.value.find((item) => item.uuid === uuid);
      return teacher ? `${teacher.fullName} (${teacher.uuid})` : uuid;
    };
    function resetUserForm() {
      Object.assign(userForm, { username: "", full_name: "", role: "EMPLOYEE", is_active: true, department_id: "", department_ids: [], teacher_uuid: "", password: "" });
      editing.userId = null;
    }
    function resetDepartmentForm() {
      Object.assign(departmentForm, { name: "", short_name: "" });
      editing.departmentId = null;
    }
    function resetTeacherForm() {
      Object.assign(teacherForm, { full_name: "", department_ids: [] });
      editing.teacherUuid = null;
    }
    function toggleSelection(target, value, checked) {
      return checked ? uniq([...target, value]) : target.filter((item) => item !== value);
    }
    function checkboxChecked(event) {
      return event.target instanceof HTMLInputElement ? event.target.checked : false;
    }
    async function reloadAll() {
      busy.reload = true;
      try {
        const [nextUsers, nextDepartments, nextTeacherDirectory] = await Promise.all([
          fetchBackendFromBrowser(props.backendApiUrl, "/users/"),
          fetchBackendFromBrowser(props.backendApiUrl, "/departments/"),
          fetchBackendFromBrowser(props.backendApiUrl, "/teacher-directory/")
        ]);
        users.value = nextUsers;
        departments.value = nextDepartments;
        teacherDirectory.value = nextTeacherDirectory;
        loadError.value = "";
      } catch (error) {
        const message = errorText(error, "Failed to reload admin data");
        loadError.value = message;
        setStatus("error", message);
      } finally {
        busy.reload = false;
      }
    }
    function editUser(user) {
      clearStatus();
      editing.userId = user.id;
      Object.assign(userForm, { username: user.username, full_name: user.fullName, role: user.role, is_active: user.isActive, department_id: user.departmentId === null ? "" : String(user.departmentId), department_ids: [...user.departmentIds], teacher_uuid: user.teacherUuid ?? "", password: "" });
    }
    function editDepartment(department) {
      clearStatus();
      editing.departmentId = department.id;
      Object.assign(departmentForm, { name: department.name, short_name: department.short_name });
    }
    function editTeacher(teacher) {
      clearStatus();
      editing.teacherUuid = teacher.uuid;
      Object.assign(teacherForm, { full_name: teacher.fullName, department_ids: [...teacher.departmentIds] });
    }
    async function submitUser() {
      clearStatus();
      if (editing.userId === null && !userForm.password.trim()) return setStatus("error", "Password is required for new users");
      busy.user = true;
      try {
        const isCreate = editing.userId === null;
        const payload = {
          username: userForm.username.trim(),
          full_name: userForm.full_name.trim(),
          role: userForm.role,
          is_active: userForm.is_active,
          department_id: userForm.department_id ? Number(userForm.department_id) : null,
          department_ids: normalizeDeptIds(userForm.department_id, userForm.department_ids),
          teacher_uuid: userForm.teacher_uuid || null
        };
        if (userForm.password.trim()) payload.password = userForm.password.trim();
        await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? "/users/" : `/users/${editing.userId}`, { method: isCreate ? "POST" : "PUT", body: JSON.stringify(payload) });
        resetUserForm();
        setStatus("success", isCreate ? "User created" : "User updated");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to save user"));
      } finally {
        busy.user = false;
      }
    }
    async function removeUser(user) {
      if (!window.confirm(`Delete user "${user.username}"?`)) return;
      busy.user = true;
      try {
        await fetchBackendFromBrowser(props.backendApiUrl, `/users/${user.id}`, { method: "DELETE" });
        if (editing.userId === user.id) resetUserForm();
        setStatus("success", "User deleted");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to delete user"));
      } finally {
        busy.user = false;
      }
    }
    async function submitDepartment() {
      clearStatus();
      busy.department = true;
      try {
        const isCreate = editing.departmentId === null;
        await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? "/departments/" : `/departments/${editing.departmentId}`, { method: isCreate ? "POST" : "PUT", body: JSON.stringify({ name: departmentForm.name.trim(), short_name: departmentForm.short_name.trim() }) });
        resetDepartmentForm();
        setStatus("success", isCreate ? "Department created" : "Department updated");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to save department"));
      } finally {
        busy.department = false;
      }
    }
    async function removeDepartment(department) {
      if (!window.confirm(`Delete department "${department.name}"?`)) return;
      busy.department = true;
      try {
        await fetchBackendFromBrowser(props.backendApiUrl, `/departments/${department.id}`, { method: "DELETE" });
        if (editing.departmentId === department.id) resetDepartmentForm();
        setStatus("success", "Department deleted");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to delete department"));
      } finally {
        busy.department = false;
      }
    }
    async function submitTeacher() {
      clearStatus();
      busy.teacher = true;
      try {
        const isCreate = editing.teacherUuid === null;
        await fetchBackendFromBrowser(props.backendApiUrl, isCreate ? "/teacher-directory/" : `/teacher-directory/${editing.teacherUuid}`, { method: isCreate ? "POST" : "PUT", body: JSON.stringify({ full_name: teacherForm.full_name.trim(), department_ids: uniq(teacherForm.department_ids) }) });
        resetTeacherForm();
        setStatus("success", isCreate ? "Local teacher created" : "Local teacher updated");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to save local teacher"));
      } finally {
        busy.teacher = false;
      }
    }
    async function removeTeacher(teacher) {
      if (!window.confirm(`Delete local teacher "${teacher.fullName}"?`)) return;
      busy.teacher = true;
      try {
        await fetchBackendFromBrowser(props.backendApiUrl, `/teacher-directory/${teacher.uuid}`, { method: "DELETE" });
        if (editing.teacherUuid === teacher.uuid) resetTeacherForm();
        setStatus("success", "Local teacher deleted");
        await reloadAll();
      } catch (error) {
        setStatus("error", errorText(error, "Failed to delete local teacher"));
      } finally {
        busy.teacher = false;
      }
    }
    async function importPastSemester() {
      busy.maintenance = true;
      try {
        const payload = await fetchBackendFromBrowser(props.backendApiUrl, "/retakes/admin/past-semester/import", { method: "POST", body: JSON.stringify({}) });
        setStatus("success", `${payload.message}. Source: ${payload.sourcePath ?? "n/a"}`);
      } catch (error) {
        setStatus("error", errorText(error, "Failed to import past semester"));
      } finally {
        busy.maintenance = false;
      }
    }
    async function resetRetakes() {
      if (!window.confirm("Delete all retakes and retake teacher links?")) return;
      busy.maintenance = true;
      try {
        const payload = await fetchBackendFromBrowser(props.backendApiUrl, "/retakes/admin/reset", { method: "POST" });
        setStatus("success", `${payload.message}. Retakes: ${payload.deletedRetakes}, links: ${payload.deletedTeacherLinks}`);
      } catch (error) {
        setStatus("error", errorText(error, "Failed to reset retakes"));
      } finally {
        busy.maintenance = false;
      }
    }
    const __returned__ = { props, users, departments, teacherDirectory, loadError, status, busy, editing, userForm, departmentForm, teacherForm, errorText, setStatus, clearStatus, uniq, normalizeDeptIds, scopeLabel, teacherLabel, resetUserForm, resetDepartmentForm, resetTeacherForm, toggleSelection, checkboxChecked, reloadAll, editUser, editDepartment, editTeacher, submitUser, removeUser, submitDepartment, removeDepartment, submitTeacher, removeTeacher, importPastSemester, resetRetakes };
    Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
    return __returned__;
  }
});
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<section${ssrRenderAttrs(mergeProps({ class: "max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-6" }, _attrs))}><div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] space-y-4"><div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Backend admin</p><h1 class="mt-2 text-3xl font-black tracking-[-0.04em] text-slate-950 dark:text-white">Admin panel on backend API</h1><p class="mt-3 text-sm text-slate-500 dark:text-slate-400 max-w-3xl leading-7"> CRUD forms below use FastAPI directly. No Astro actions, no frontend DB writes, no legacy auth fallbacks. </p></div><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.reload) ? " disabled" : ""}>${ssrInterpolate($setup.busy.reload ? "Refreshing..." : "Refresh data")}</button></div>`);
  if ($setup.status) {
    _push(`<div class="${ssrRenderClass([$setup.status.kind === "error" ? "border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300" : "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300", "rounded-2xl px-4 py-3 text-sm border"])}">${ssrInterpolate($setup.status.message)}</div>`);
  } else {
    _push(`<!---->`);
  }
  if ($setup.loadError) {
    _push(`<div class="rounded-2xl px-4 py-3 text-sm border border-red-200 bg-red-50 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">${ssrInterpolate($setup.loadError)}</div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`</div><div class="grid grid-cols-1 md:grid-cols-3 gap-4"><div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Users</p><div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.users.length)}</div></div><div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p><div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.departments.length)}</div></div><div class="rounded-[24px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-5"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Teacher Directory</p><div class="mt-2 text-4xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.teacherDirectory.length)}</div></div></div><div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6 space-y-4"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Maintenance</p><h2 class="mt-2 text-2xl font-black text-slate-950 dark:text-white">Retake admin operations</h2></div><div class="flex flex-wrap gap-3"><button type="button" class="h-11 px-5 rounded-2xl bg-blue-600 text-white text-sm font-black disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.maintenance) ? " disabled" : ""}>${ssrInterpolate($setup.busy.maintenance ? "Working..." : "Import past semester")}</button><button type="button" class="h-11 px-5 rounded-2xl bg-red-500 text-white text-sm font-black disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.maintenance) ? " disabled" : ""}>${ssrInterpolate($setup.busy.maintenance ? "Working..." : "Reset retakes")}</button></div></div><div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6"><div class="grid gap-6 lg:grid-cols-[360px,minmax(0,1fr)]"><form class="space-y-4"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Users</p><h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.editing.userId === null ? "Create user" : `Edit user #${$setup.editing.userId}`)}</h2></div><input${ssrRenderAttr("value", $setup.userForm.username)} type="text" required placeholder="Username" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><input${ssrRenderAttr("value", $setup.userForm.full_name)} type="text" required placeholder="Full name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><div class="grid gap-3 sm:grid-cols-2"><select class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value="ADMIN"${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.role) ? ssrLooseContain($setup.userForm.role, "ADMIN") : ssrLooseEqual($setup.userForm.role, "ADMIN")) ? " selected" : ""}>ADMIN</option><option value="EMPLOYEE"${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.role) ? ssrLooseContain($setup.userForm.role, "EMPLOYEE") : ssrLooseEqual($setup.userForm.role, "EMPLOYEE")) ? " selected" : ""}>EMPLOYEE</option><option value="TEACHER"${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.role) ? ssrLooseContain($setup.userForm.role, "TEACHER") : ssrLooseEqual($setup.userForm.role, "TEACHER")) ? " selected" : ""}>TEACHER</option></select><select class="h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value=""${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.department_id) ? ssrLooseContain($setup.userForm.department_id, "") : ssrLooseEqual($setup.userForm.department_id, "")) ? " selected" : ""}>Primary department: none</option><!--[-->`);
  ssrRenderList($setup.departments, (department) => {
    _push(`<option${ssrRenderAttr("value", String(department.id))}${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.department_id) ? ssrLooseContain($setup.userForm.department_id, String(department.id)) : ssrLooseEqual($setup.userForm.department_id, String(department.id))) ? " selected" : ""}>${ssrInterpolate(department.short_name)} (${ssrInterpolate(department.name)})</option>`);
  });
  _push(`<!--]--></select></div><select class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><option value=""${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.teacher_uuid) ? ssrLooseContain($setup.userForm.teacher_uuid, "") : ssrLooseEqual($setup.userForm.teacher_uuid, "")) ? " selected" : ""}>Linked teacher: none</option><!--[-->`);
  ssrRenderList($setup.teacherDirectory, (teacher) => {
    _push(`<option${ssrRenderAttr("value", teacher.uuid)}${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.teacher_uuid) ? ssrLooseContain($setup.userForm.teacher_uuid, teacher.uuid) : ssrLooseEqual($setup.userForm.teacher_uuid, teacher.uuid)) ? " selected" : ""}>${ssrInterpolate(teacher.fullName)} (${ssrInterpolate(teacher.uuid)})</option>`);
  });
  _push(`<!--]--></select><input${ssrRenderAttr("value", $setup.userForm.password)}${ssrIncludeBooleanAttr($setup.editing.userId === null) ? " required" : ""} type="password"${ssrRenderAttr("placeholder", $setup.editing.userId === null ? "Password" : "Password (optional)")} class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><label class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200"><input${ssrIncludeBooleanAttr(Array.isArray($setup.userForm.is_active) ? ssrLooseContain($setup.userForm.is_active, null) : $setup.userForm.is_active) ? " checked" : ""} type="checkbox"> <span>Active user</span></label><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Department scope</p><!--[-->`);
  ssrRenderList($setup.departments, (department) => {
    _push(`<label class="flex items-center gap-3 text-sm"><input type="checkbox"${ssrIncludeBooleanAttr($setup.userForm.department_ids.includes(department.id)) ? " checked" : ""}><span>${ssrInterpolate(department.short_name)} (${ssrInterpolate(department.name)})</span></label>`);
  });
  _push(`<!--]--></div><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.user) ? " disabled" : ""}>${ssrInterpolate($setup.busy.user ? "Saving..." : $setup.editing.userId === null ? "Create user" : "Save changes")}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold">Reset</button></div></form><div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10"><table class="w-full text-sm"><thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400"><tr><th class="px-4 py-3 text-left">Username</th><th class="px-4 py-3 text-left">Full name</th><th class="px-4 py-3 text-left">Role</th><th class="px-4 py-3 text-left">Departments</th><th class="px-4 py-3 text-left">Teacher</th><th class="px-4 py-3 text-left">Actions</th></tr></thead><tbody>`);
  if ($setup.users.length === 0) {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10"><td colspan="6" class="px-4 py-6 text-slate-500">No users.</td></tr>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<!--[-->`);
  ssrRenderList($setup.users, (user) => {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10 align-top"><td class="px-4 py-3 font-mono text-xs">${ssrInterpolate(user.username)}<div class="mt-1">${ssrInterpolate(user.isActive ? "active" : "inactive")}</div></td><td class="px-4 py-3">${ssrInterpolate(user.fullName)}</td><td class="px-4 py-3">${ssrInterpolate(user.role)}</td><td class="px-4 py-3"><div>${ssrInterpolate(user.departmentId === null ? "None" : $setup.scopeLabel([user.departmentId]))}</div><div class="mt-1 text-xs">${ssrInterpolate($setup.scopeLabel(user.departmentIds))}</div></td><td class="px-4 py-3">${ssrInterpolate($setup.teacherLabel(user.teacherUuid))}</td><td class="px-4 py-3"><div class="flex flex-wrap gap-2"><button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold">Edit</button><button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold">Delete</button></div></td></tr>`);
  });
  _push(`<!--]--></tbody></table></div></div></div><div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6"><div class="grid gap-6 lg:grid-cols-[300px,minmax(0,1fr)]"><form class="space-y-4"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p><h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.editing.departmentId === null ? "Create department" : `Edit department #${$setup.editing.departmentId}`)}</h2></div><input${ssrRenderAttr("value", $setup.departmentForm.name)} type="text" required placeholder="Department name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><input${ssrRenderAttr("value", $setup.departmentForm.short_name)} type="text" required placeholder="Short name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.department) ? " disabled" : ""}>${ssrInterpolate($setup.busy.department ? "Saving..." : $setup.editing.departmentId === null ? "Create department" : "Save changes")}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold">Reset</button></div></form><div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10"><table class="w-full text-sm"><thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400"><tr><th class="px-4 py-3 text-left">ID</th><th class="px-4 py-3 text-left">Name</th><th class="px-4 py-3 text-left">Short name</th><th class="px-4 py-3 text-left">Actions</th></tr></thead><tbody>`);
  if ($setup.departments.length === 0) {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10"><td colspan="4" class="px-4 py-6 text-slate-500">No departments.</td></tr>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<!--[-->`);
  ssrRenderList($setup.departments, (department) => {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10"><td class="px-4 py-3 font-mono text-xs">${ssrInterpolate(department.id)}</td><td class="px-4 py-3">${ssrInterpolate(department.name)}</td><td class="px-4 py-3">${ssrInterpolate(department.short_name)}</td><td class="px-4 py-3"><div class="flex flex-wrap gap-2"><button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold">Edit</button><button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold">Delete</button></div></td></tr>`);
  });
  _push(`<!--]--></tbody></table></div></div></div><div class="rounded-[28px] border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.04] p-6"><div class="grid gap-6 lg:grid-cols-[360px,minmax(0,1fr)]"><form class="space-y-4"><div><p class="text-[11px] uppercase tracking-[0.18em] text-slate-500 font-bold">Teacher directory</p><h2 class="mt-2 text-xl font-black text-slate-950 dark:text-white">${ssrInterpolate($setup.editing.teacherUuid === null ? "Create local teacher" : `Edit local teacher ${$setup.editing.teacherUuid}`)}</h2></div>`);
  if ($setup.editing.teacherUuid) {
    _push(`<div class="rounded-2xl border border-slate-200 dark:border-white/10 px-4 py-3 text-sm">UUID: <span class="font-mono text-xs">${ssrInterpolate($setup.editing.teacherUuid)}</span></div>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<input${ssrRenderAttr("value", $setup.teacherForm.full_name)} type="text" required placeholder="Teacher full name" class="w-full h-11 px-4 rounded-2xl border border-slate-300 dark:border-white/10 bg-white dark:bg-white/[0.03] text-sm"><div class="rounded-2xl border border-slate-200 dark:border-white/10 p-4 space-y-2"><p class="text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">Departments</p><!--[-->`);
  ssrRenderList($setup.departments, (department) => {
    _push(`<label class="flex items-center gap-3 text-sm"><input type="checkbox"${ssrIncludeBooleanAttr($setup.teacherForm.department_ids.includes(department.id)) ? " checked" : ""}><span>${ssrInterpolate(department.short_name)} (${ssrInterpolate(department.name)})</span></label>`);
  });
  _push(`<!--]--></div><div class="flex gap-3"><button type="submit" class="h-11 px-5 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 text-sm font-black disabled:opacity-60"${ssrIncludeBooleanAttr($setup.busy.teacher) ? " disabled" : ""}>${ssrInterpolate($setup.busy.teacher ? "Saving..." : $setup.editing.teacherUuid === null ? "Create local teacher" : "Save changes")}</button><button type="button" class="h-11 px-5 rounded-2xl border border-slate-300 dark:border-white/10 text-sm font-semibold">Reset</button></div></form><div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-white/10 max-h-[540px]"><table class="w-full text-sm"><thead class="bg-slate-50 dark:bg-black/10 text-slate-500 dark:text-slate-400 sticky top-0"><tr><th class="px-4 py-3 text-left">UUID</th><th class="px-4 py-3 text-left">Full name</th><th class="px-4 py-3 text-left">Departments</th><th class="px-4 py-3 text-left">Actions</th></tr></thead><tbody>`);
  if ($setup.teacherDirectory.length === 0) {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10"><td colspan="4" class="px-4 py-6 text-slate-500">No local teachers.</td></tr>`);
  } else {
    _push(`<!---->`);
  }
  _push(`<!--[-->`);
  ssrRenderList($setup.teacherDirectory, (teacher) => {
    _push(`<tr class="border-t border-slate-100 dark:border-white/10 align-top"><td class="px-4 py-3 font-mono text-xs">${ssrInterpolate(teacher.uuid)}</td><td class="px-4 py-3">${ssrInterpolate(teacher.fullName)}</td><td class="px-4 py-3">${ssrInterpolate($setup.scopeLabel(teacher.departmentIds))}</td><td class="px-4 py-3"><div class="flex flex-wrap gap-2"><button type="button" class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-white/10 text-xs font-semibold">Edit</button><button type="button" class="px-3 py-2 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-xs font-semibold">Delete</button></div></td></tr>`);
  });
  _push(`<!--]--></tbody></table></div></div></div></section>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("src/components/AdminPanel.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const AdminPanel = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);

const $$Astro = createAstro();
const prerender = false;
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Index;
  const user = Astro2.locals.user;
  if (!user) {
    return Astro2.redirect("/login");
  }
  if (user.role !== "ADMIN") {
    return Astro2.redirect("/dashboard");
  }
  let users = [];
  let departments = [];
  let teacherDirectory = [];
  let loadError = "";
  try {
    const [usersRes, departmentsRes, teacherDirectoryRes] = await Promise.all([
      fetchBackendFromServer("/users/", {}, Astro2.request),
      fetchBackendFromServer("/departments/", {}, Astro2.request),
      fetchBackendFromServer("/teacher-directory/", {}, Astro2.request)
    ]);
    users = usersRes;
    departments = departmentsRes;
    teacherDirectory = teacherDirectoryRes;
  } catch (error) {
    console.error("Failed to load admin data", error);
    loadError = error instanceof Error ? error.message : "Failed to load admin data";
  }
  const backendApiUrl = getPublicBackendApiUrl();
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "Admin" }, { "default": async ($$result2) => renderTemplate`  ${renderComponent($$result2, "AdminPanel", AdminPanel, { "client:load": true, "backendApiUrl": backendApiUrl, "initialUsers": users, "initialDepartments": departments, "initialTeacherDirectory": teacherDirectory, "initialLoadError": loadError, "client:component-hydration": "load", "client:component-path": "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/components/AdminPanel.vue", "client:component-export": "default" })} `, "nav-actions": async ($$result2) => renderTemplate`${renderComponent($$result2, "Fragment", Fragment, { "slot": "nav-actions" }, { "default": async ($$result3) => renderTemplate` ${maybeRenderHead()}<a href="/dashboard" class="inline-flex items-center justify-center h-10 px-4 rounded-2xl border border-gray-300 dark:border-white/10 bg-white dark:bg-white/5 text-gray-700 dark:text-white/80 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-400 dark:hover:border-white/15 backdrop-blur-xl text-sm font-semibold transition-all duration-300 hover:-translate-y-0.5">
&larr; Dashboard
</a> ` })}` })}`;
}, "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/pages/admin/index.astro", void 0);

const $$file = "C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/admin/index.astro";
const $$url = "/admin";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Index,
  file: $$file,
  prerender,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
