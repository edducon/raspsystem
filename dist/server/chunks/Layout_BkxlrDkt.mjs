import { e as createComponent, r as renderTemplate, k as renderComponent, o as renderSlot, p as renderHead, h as createAstro } from './astro/server__Jo3gmtv.mjs';
import 'piccolore';
import { ref, useSSRContext, defineComponent, mergeProps } from 'vue';
import { AlertTriangle, CheckCircle2 } from 'lucide-vue-next';
import { ssrRenderAttrs, ssrRenderList, ssrRenderClass, ssrRenderComponent, ssrInterpolate } from 'vue/server-renderer';
/* empty css                         */

const toasts = ref([]);
const addToast = (message, type = "success") => {
  const id = Date.now();
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }, 4e3);
};

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "ToastProvider",
  setup(__props, { expose: __expose }) {
    __expose();
    const __returned__ = { get toasts() {
      return toasts;
    }, get CheckCircle2() {
      return CheckCircle2;
    }, get AlertTriangle() {
      return AlertTriangle;
    } };
    Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
    return __returned__;
  }
});
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(mergeProps({ class: "fixed bottom-5 right-5 sm:bottom-6 sm:right-6 z-[80] flex flex-col gap-3 pointer-events-none" }, _attrs))}><!--[-->`);
  ssrRenderList($setup.toasts, (toast) => {
    _push(`<div class="${ssrRenderClass([
      "pointer-events-auto min-w-[280px] max-w-[360px] rounded-[22px] border backdrop-blur-2xl shadow-[0_20px_60px_rgba(15,23,42,0.18)] px-4 py-4 flex items-start gap-3.5 text-sm",
      toast.type === "success" ? "bg-white/90 dark:bg-[#12161d]/92 border-slate-200/80 dark:border-emerald-500/20 text-slate-800 dark:text-emerald-50" : "bg-white/90 dark:bg-[#181116]/92 border-slate-200/80 dark:border-red-500/20 text-slate-800 dark:text-red-50"
    ])}"><div class="${ssrRenderClass([
      "shrink-0 mt-0.5 w-9 h-9 rounded-2xl flex items-center justify-center border",
      toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-600 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400" : "bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-400"
    ])}">`);
    if (toast.type === "success") {
      _push(ssrRenderComponent($setup["CheckCircle2"], { class: "w-[18px] h-[18px]" }, null, _parent));
    } else {
      _push(ssrRenderComponent($setup["AlertTriangle"], { class: "w-[18px] h-[18px]" }, null, _parent));
    }
    _push(`</div><div class="min-w-0 flex-1"><div class="${ssrRenderClass([
      "text-[11px] uppercase tracking-[0.18em] font-bold mb-1",
      toast.type === "success" ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
    ])}">${ssrInterpolate(toast.type === "success" ? "Успешно" : "Ошибка")}</div><div class="leading-6 font-medium text-slate-700 dark:text-slate-200 break-words">${ssrInterpolate(toast.message)}</div></div></div>`);
  });
  _push(`<!--]--></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("src/components/ToastProvider.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ToastProvider = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro = createAstro();
const $$Layout = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Layout;
  const { title } = Astro2.props;
  const currentYear = (/* @__PURE__ */ new Date()).getFullYear();
  return renderTemplate(_a || (_a = __template(['<html lang="ru"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>', "</title><script>\n        const theme = (() => {\n            if (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) {\n                return localStorage.getItem('theme');\n            }\n            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {\n                return 'dark';\n            }\n            return 'light';\n        })();\n\n        if (theme === 'dark') {\n            document.documentElement.classList.add('dark');\n        } else {\n            document.documentElement.classList.remove('dark');\n        }\n    <\/script>", '</head> <body class="font-sans antialiased min-h-screen flex flex-col text-slate-900 dark:text-slate-100"> <div class="page-bg"></div> <div class="page-noise"></div> <header class="sticky top-0 z-50 px-3 pt-3 sm:px-4 sm:pt-4"> <div class="mx-auto max-w-7xl"> <div class="nav-shell h-16 px-4 sm:px-5 lg:px-6 flex items-center gap-4"> <a href="/" class="flex items-center gap-3 shrink-0 group"> <div class="brand-mark flex items-center justify-center overflow-hidden" style="background: white; background-image: none; box-shadow: 0 12px 30px rgba(0,0,0,0.1);"> <img src="/image/logo.png" alt="\u041B\u043E\u0433\u043E\u0442\u0438\u043F \u0443\u043D\u0438\u0432\u0435\u0440\u0441\u0438\u0442\u0435\u0442\u0430" class="w-8 h-8 object-contain"> </div> <div class="hidden sm:block"> <div class="font-extrabold text-[15px] leading-tight tracking-tight text-slate-800 dark:text-white">\n\u041F\u0435\u0440\u0435\u0441\u0434\u0430\u0447\u0438\n</div> <div class="text-[10px] text-slate-600 dark:text-white/55 font-semibold tracking-[0.22em] uppercase">\n\u041C\u043E\u0441\u043A\u043E\u0432\u0441\u043A\u043E\u0433\u043E \u043F\u043E\u043B\u0438\u0442\u0435\u0445\u043D\u0438\u0447\u0435\u0441\u043A\u043E\u0433\u043E \u0443\u043D\u0438\u0432\u0435\u0440\u0441\u0438\u0442\u0435\u0442\u0430\n</div> </div> </a> <div class="flex-1 flex items-center justify-center overflow-hidden min-w-0"> ', ' </div> <div class="flex items-center gap-2 shrink-0"> ', ' <div class="hidden sm:block w-px h-6 bg-white/10 dark:bg-white/10 mx-1"></div> <button id="theme-toggle" class="theme-button" title="\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0442\u0435\u043C\u0443" aria-label="\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0442\u0435\u043C\u0443"> <svg id="theme-toggle-dark-icon" class="hidden w-[18px] h-[18px]" fill="currentColor" viewBox="0 0 20 20"> <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path> </svg> <svg id="theme-toggle-light-icon" class="hidden w-[18px] h-[18px]" fill="currentColor" viewBox="0 0 20 20"> <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" fill-rule="evenodd" clip-rule="evenodd"></path> </svg> </button> </div> </div> </div> </header> <main class="flex-grow relative z-10 transition-colors duration-300"> ', " </main> ", ' <footer class="relative z-10 mt-auto px-3 pb-3 sm:px-4 sm:pb-4"> <div class="mx-auto max-w-7xl"> <div class="footer-shell px-4 py-5 sm:px-6"> <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 text-[11px]"> <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-4 text-slate-600 dark:text-white/45"> <span>&copy; ', ` \u0424\u0430\u043A\u0443\u043B\u044C\u0442\u0435\u0442 \u0438\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u043E\u043D\u043D\u044B\u0445 \u0442\u0435\u0445\u043D\u043E\u043B\u043E\u0433\u0438\u0439 \u041C\u041F\u0423</span> <span class="hidden sm:inline opacity-30 text-slate-400 dark:text-white/30">&middot;</span> <a href="tel:+74952230523" class="footer-link text-slate-600 dark:text-white/45 hover:text-slate-900 dark:hover:text-white transition-colors">+7 495 223-05-23, \u0434\u043E\u0431. 1709</a> <a href="mailto:fit@mospolytech.ru" class="footer-link text-slate-600 dark:text-white/45 hover:text-slate-900 dark:hover:text-white transition-colors">fit@mospolytech.ru</a> </div> <span class="flex items-center gap-1.5 text-slate-600 dark:text-white/50">
\u0420\u0430\u0437\u0440\u0430\u0431\u043E\u0442\u0430\u043D\u043E
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor" class="text-rose-500"> <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path> </svg> <a href="https://t.me/edducon" target="_blank" class="font-semibold text-slate-700 dark:text-white hover:text-red-500 dark:hover:text-red-400 transition-colors">
@edducon
</a> </span> </div> </div> </div> </footer> <script>
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    const themeToggleBtn = document.getElementById('theme-toggle');

    if (document.documentElement.classList.contains('dark')) {
        themeToggleLightIcon?.classList.remove('hidden');
    } else {
        themeToggleDarkIcon?.classList.remove('hidden');
    }

    themeToggleBtn?.addEventListener('click', function () {
        const isDark = document.documentElement.classList.contains('dark');

        const toggleTheme = () => {
            themeToggleDarkIcon?.classList.toggle('hidden');
            themeToggleLightIcon?.classList.toggle('hidden');

            if (isDark) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }
        };

        if (!document.startViewTransition) {
            toggleTheme();
            return;
        }

        const x = isDark ? innerWidth : 0;
        const y = isDark ? innerHeight : 0;
        const endRadius = Math.hypot(innerWidth, innerHeight);

        const transition = document.startViewTransition(toggleTheme);

        transition.ready.then(() => {
            document.documentElement.animate(
                {
                    clipPath: [
                        \`circle(0px at \${x}px \${y}px)\`,
                        \`circle(\${endRadius}px at \${x}px \${y}px)\`
                    ]
                },
                {
                    duration: 500,
                    easing: 'ease-in-out',
                    pseudoElement: '::view-transition-new(root)'
                }
            );
        });
    });
<\/script>  </body> </html>`], ['<html lang="ru"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>', "</title><script>\n        const theme = (() => {\n            if (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) {\n                return localStorage.getItem('theme');\n            }\n            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {\n                return 'dark';\n            }\n            return 'light';\n        })();\n\n        if (theme === 'dark') {\n            document.documentElement.classList.add('dark');\n        } else {\n            document.documentElement.classList.remove('dark');\n        }\n    <\/script>", '</head> <body class="font-sans antialiased min-h-screen flex flex-col text-slate-900 dark:text-slate-100"> <div class="page-bg"></div> <div class="page-noise"></div> <header class="sticky top-0 z-50 px-3 pt-3 sm:px-4 sm:pt-4"> <div class="mx-auto max-w-7xl"> <div class="nav-shell h-16 px-4 sm:px-5 lg:px-6 flex items-center gap-4"> <a href="/" class="flex items-center gap-3 shrink-0 group"> <div class="brand-mark flex items-center justify-center overflow-hidden" style="background: white; background-image: none; box-shadow: 0 12px 30px rgba(0,0,0,0.1);"> <img src="/image/logo.png" alt="\u041B\u043E\u0433\u043E\u0442\u0438\u043F \u0443\u043D\u0438\u0432\u0435\u0440\u0441\u0438\u0442\u0435\u0442\u0430" class="w-8 h-8 object-contain"> </div> <div class="hidden sm:block"> <div class="font-extrabold text-[15px] leading-tight tracking-tight text-slate-800 dark:text-white">\n\u041F\u0435\u0440\u0435\u0441\u0434\u0430\u0447\u0438\n</div> <div class="text-[10px] text-slate-600 dark:text-white/55 font-semibold tracking-[0.22em] uppercase">\n\u041C\u043E\u0441\u043A\u043E\u0432\u0441\u043A\u043E\u0433\u043E \u043F\u043E\u043B\u0438\u0442\u0435\u0445\u043D\u0438\u0447\u0435\u0441\u043A\u043E\u0433\u043E \u0443\u043D\u0438\u0432\u0435\u0440\u0441\u0438\u0442\u0435\u0442\u0430\n</div> </div> </a> <div class="flex-1 flex items-center justify-center overflow-hidden min-w-0"> ', ' </div> <div class="flex items-center gap-2 shrink-0"> ', ' <div class="hidden sm:block w-px h-6 bg-white/10 dark:bg-white/10 mx-1"></div> <button id="theme-toggle" class="theme-button" title="\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0442\u0435\u043C\u0443" aria-label="\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0442\u0435\u043C\u0443"> <svg id="theme-toggle-dark-icon" class="hidden w-[18px] h-[18px]" fill="currentColor" viewBox="0 0 20 20"> <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path> </svg> <svg id="theme-toggle-light-icon" class="hidden w-[18px] h-[18px]" fill="currentColor" viewBox="0 0 20 20"> <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" fill-rule="evenodd" clip-rule="evenodd"></path> </svg> </button> </div> </div> </div> </header> <main class="flex-grow relative z-10 transition-colors duration-300"> ', " </main> ", ' <footer class="relative z-10 mt-auto px-3 pb-3 sm:px-4 sm:pb-4"> <div class="mx-auto max-w-7xl"> <div class="footer-shell px-4 py-5 sm:px-6"> <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 text-[11px]"> <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-4 text-slate-600 dark:text-white/45"> <span>&copy; ', ` \u0424\u0430\u043A\u0443\u043B\u044C\u0442\u0435\u0442 \u0438\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u043E\u043D\u043D\u044B\u0445 \u0442\u0435\u0445\u043D\u043E\u043B\u043E\u0433\u0438\u0439 \u041C\u041F\u0423</span> <span class="hidden sm:inline opacity-30 text-slate-400 dark:text-white/30">&middot;</span> <a href="tel:+74952230523" class="footer-link text-slate-600 dark:text-white/45 hover:text-slate-900 dark:hover:text-white transition-colors">+7 495 223-05-23, \u0434\u043E\u0431. 1709</a> <a href="mailto:fit@mospolytech.ru" class="footer-link text-slate-600 dark:text-white/45 hover:text-slate-900 dark:hover:text-white transition-colors">fit@mospolytech.ru</a> </div> <span class="flex items-center gap-1.5 text-slate-600 dark:text-white/50">
\u0420\u0430\u0437\u0440\u0430\u0431\u043E\u0442\u0430\u043D\u043E
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor" class="text-rose-500"> <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path> </svg> <a href="https://t.me/edducon" target="_blank" class="font-semibold text-slate-700 dark:text-white hover:text-red-500 dark:hover:text-red-400 transition-colors">
@edducon
</a> </span> </div> </div> </div> </footer> <script>
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    const themeToggleBtn = document.getElementById('theme-toggle');

    if (document.documentElement.classList.contains('dark')) {
        themeToggleLightIcon?.classList.remove('hidden');
    } else {
        themeToggleDarkIcon?.classList.remove('hidden');
    }

    themeToggleBtn?.addEventListener('click', function () {
        const isDark = document.documentElement.classList.contains('dark');

        const toggleTheme = () => {
            themeToggleDarkIcon?.classList.toggle('hidden');
            themeToggleLightIcon?.classList.toggle('hidden');

            if (isDark) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }
        };

        if (!document.startViewTransition) {
            toggleTheme();
            return;
        }

        const x = isDark ? innerWidth : 0;
        const y = isDark ? innerHeight : 0;
        const endRadius = Math.hypot(innerWidth, innerHeight);

        const transition = document.startViewTransition(toggleTheme);

        transition.ready.then(() => {
            document.documentElement.animate(
                {
                    clipPath: [
                        \\\`circle(0px at \\\${x}px \\\${y}px)\\\`,
                        \\\`circle(\\\${endRadius}px at \\\${x}px \\\${y}px)\\\`
                    ]
                },
                {
                    duration: 500,
                    easing: 'ease-in-out',
                    pseudoElement: '::view-transition-new(root)'
                }
            );
        });
    });
<\/script>  </body> </html>`])), title, renderHead(), renderSlot($$result, $$slots["nav-center"]), renderSlot($$result, $$slots["nav-actions"]), renderSlot($$result, $$slots["default"]), renderComponent($$result, "ToastProvider", ToastProvider, { "client:load": true, "client:component-hydration": "load", "client:component-path": "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/components/ToastProvider.vue", "client:component-export": "default" }), currentYear);
}, "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/layouts/Layout.astro", void 0);

export { $$Layout as $, _export_sfc as _, addToast as a };
