import { renderers } from './renderers.mjs';
import { c as createExports, s as serverEntrypointModule } from './chunks/_@astrojs-ssr-adapter_C_I47ki5.mjs';
import { manifest } from './manifest_Duxl-dIv.mjs';

const serverIslandMap = new Map();;

const _page0 = () => import('./pages/_image.astro.mjs');
const _page1 = () => import('./pages/404.astro.mjs');
const _page2 = () => import('./pages/admin.astro.mjs');
const _page3 = () => import('./pages/dashboard.astro.mjs');
const _page4 = () => import('./pages/login.astro.mjs');
const _page5 = () => import('./pages/profile.astro.mjs');
const _page6 = () => import('./pages/index.astro.mjs');
const pageMap = new Map([
    ["node_modules/astro/dist/assets/endpoint/node.js", _page0],
    ["src/pages/404.astro", _page1],
    ["src/pages/admin/index.astro", _page2],
    ["src/pages/dashboard/index.astro", _page3],
    ["src/pages/login.astro", _page4],
    ["src/pages/profile.astro", _page5],
    ["src/pages/index.astro", _page6]
]);

const _manifest = Object.assign(manifest, {
    pageMap,
    serverIslandMap,
    renderers,
    actions: () => import('./noop-entrypoint.mjs'),
    middleware: () => import('./_astro-internal_middleware.mjs')
});
const _args = {
    "mode": "standalone",
    "client": "file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/dist/client/",
    "server": "file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/dist/server/",
    "host": false,
    "port": 4321,
    "assets": "_astro",
    "experimentalStaticHeaders": false
};
const _exports = createExports(_manifest, _args);
const handler = _exports['handler'];
const startServer = _exports['startServer'];
const options = _exports['options'];
const _start = 'start';
if (Object.prototype.hasOwnProperty.call(serverEntrypointModule, _start)) {
	serverEntrypointModule[_start](_manifest, _args);
}

export { handler, options, pageMap, startServer };
