/* empty css                                 */
import { e as createComponent, k as renderComponent, r as renderTemplate, m as maybeRenderHead } from '../chunks/astro/server__Jo3gmtv.mjs';
import 'piccolore';
import { $ as $$Layout } from '../chunks/Layout_BkxlrDkt.mjs';
export { renderers } from '../renderers.mjs';

const prerender = false;
const $$404 = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "\u0410\u0443\u0434\u0438\u0442\u043E\u0440\u0438\u044F 404 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u0430" }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<div class="min-h-[85vh] flex flex-col items-center justify-center text-center p-4 relative overflow-hidden transition-colors"> <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div> <div class="relative z-10 max-w-2xl mx-auto flex flex-col items-center"> <!-- 4(логотип в белом круге)4 вместо 404 --> <div class="flex items-center justify-center gap-2 mb-6"> <span class="text-6xl md:text-8xl font-black text-slate-900 dark:text-white tracking-tighter drop-shadow-sm">4</span> <div class="w-20 h-20 md:w-28 md:h-28 rounded-full bg-white dark:bg-white flex items-center justify-center overflow-hidden shadow-xl"> <img src="/image/logo.png" alt="Логотип университета" class="w-12 h-12 md:w-16 md:h-16 object-contain brightness-100 contrast-100 saturate-100" style="filter: none; mix-blend-mode: normal;"> </div> <span class="text-6xl md:text-8xl font-black text-slate-900 dark:text-white tracking-tighter drop-shadow-sm">4</span> </div> <h1 class="text-xl md:text-2xl text-slate-800 dark:text-slate-200 mb-3 font-semibold">
Кажется, этой аудитории нет на схеме корпуса.
</h1> <p class="text-base text-slate-500 dark:text-slate-400 mb-10 max-w-lg mx-auto leading-relaxed">
Возможно, пара была перенесена, преподаватель ушел пить кофе, или вы просто опечатались в ссылке. В любом случае, здесь никого нет.
</p> <button onclick="window.history.back()" class="px-8 py-3.5 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-200 text-white dark:text-slate-900 font-bold rounded-xl shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5">
Вернуться к расписанию
</button> <div class="mt-20 p-6 bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm text-sm text-slate-600 dark:text-slate-400 max-w-md mx-auto w-full transition-colors"> <p class="font-medium mb-3 text-slate-800 dark:text-slate-200">👨‍💻 Разработчик системы:</p> <a href="https://t.me/edducon" target="_blank" class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 font-bold rounded-xl hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors w-full sm:w-auto"> <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.892-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"></path></svg>
Написать в Telegram (@edducon)
</a> <p class="mt-3 text-xs opacity-70">Нашли уязвимость или баг? Срочно пишите!</p> </div> </div> </div> ` })}`;
}, "C:/Users/\u042D\u0434\u0443\u0430\u0440\u0434 \u041F\u0430\u043D\u043F\u0443\u0448\u043D\u044B\u0439/IdeaProjects/website/src/pages/404.astro", void 0);

const $$file = "C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/404.astro";
const $$url = "/404";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
    __proto__: null,
    default: $$404,
    file: $$file,
    prerender,
    url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
