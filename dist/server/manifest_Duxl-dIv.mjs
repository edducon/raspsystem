import 'piccolore';
import { q as decodeKey } from './chunks/astro/server__Jo3gmtv.mjs';
import 'clsx';
import './chunks/astro-designed-error-pages_Bp_he5rZ.mjs';
import 'es-module-lexer';
import { N as NOOP_MIDDLEWARE_FN } from './chunks/noop-middleware_Cl4FjOE4.mjs';

function sanitizeParams(params) {
  return Object.fromEntries(
    Object.entries(params).map(([key, value]) => {
      if (typeof value === "string") {
        return [key, value.normalize().replace(/#/g, "%23").replace(/\?/g, "%3F")];
      }
      return [key, value];
    })
  );
}
function getParameter(part, params) {
  if (part.spread) {
    return params[part.content.slice(3)] || "";
  }
  if (part.dynamic) {
    if (!params[part.content]) {
      throw new TypeError(`Missing parameter: ${part.content}`);
    }
    return params[part.content];
  }
  return part.content.normalize().replace(/\?/g, "%3F").replace(/#/g, "%23").replace(/%5B/g, "[").replace(/%5D/g, "]");
}
function getSegment(segment, params) {
  const segmentPath = segment.map((part) => getParameter(part, params)).join("");
  return segmentPath ? "/" + segmentPath : "";
}
function getRouteGenerator(segments, addTrailingSlash) {
  return (params) => {
    const sanitizedParams = sanitizeParams(params);
    let trailing = "";
    if (addTrailingSlash === "always" && segments.length) {
      trailing = "/";
    }
    const path = segments.map((segment) => getSegment(segment, sanitizedParams)).join("") + trailing;
    return path || "/";
  };
}

function deserializeRouteData(rawRouteData) {
  return {
    route: rawRouteData.route,
    type: rawRouteData.type,
    pattern: new RegExp(rawRouteData.pattern),
    params: rawRouteData.params,
    component: rawRouteData.component,
    generate: getRouteGenerator(rawRouteData.segments, rawRouteData._meta.trailingSlash),
    pathname: rawRouteData.pathname || void 0,
    segments: rawRouteData.segments,
    prerender: rawRouteData.prerender,
    redirect: rawRouteData.redirect,
    redirectRoute: rawRouteData.redirectRoute ? deserializeRouteData(rawRouteData.redirectRoute) : void 0,
    fallbackRoutes: rawRouteData.fallbackRoutes.map((fallback) => {
      return deserializeRouteData(fallback);
    }),
    isIndex: rawRouteData.isIndex,
    origin: rawRouteData.origin
  };
}

function deserializeManifest(serializedManifest) {
  const routes = [];
  for (const serializedRoute of serializedManifest.routes) {
    routes.push({
      ...serializedRoute,
      routeData: deserializeRouteData(serializedRoute.routeData)
    });
    const route = serializedRoute;
    route.routeData = deserializeRouteData(serializedRoute.routeData);
  }
  const assets = new Set(serializedManifest.assets);
  const componentMetadata = new Map(serializedManifest.componentMetadata);
  const inlinedScripts = new Map(serializedManifest.inlinedScripts);
  const clientDirectives = new Map(serializedManifest.clientDirectives);
  const serverIslandNameMap = new Map(serializedManifest.serverIslandNameMap);
  const key = decodeKey(serializedManifest.key);
  return {
    // in case user middleware exists, this no-op middleware will be reassigned (see plugin-ssr.ts)
    middleware() {
      return { onRequest: NOOP_MIDDLEWARE_FN };
    },
    ...serializedManifest,
    assets,
    componentMetadata,
    inlinedScripts,
    clientDirectives,
    routes,
    serverIslandNameMap,
    key
  };
}

const manifest = deserializeManifest({"hrefRoot":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/","cacheDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/node_modules/.astro/","outDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/dist/","srcDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/src/","publicDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/public/","buildClientDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/dist/client/","buildServerDir":"file:///C:/Users/%D0%AD%D0%B4%D1%83%D0%B0%D1%80%D0%B4%20%D0%9F%D0%B0%D0%BD%D0%BF%D1%83%D1%88%D0%BD%D1%8B%D0%B9/IdeaProjects/website/dist/server/","adapterName":"@astrojs/node","routes":[{"file":"","links":[],"scripts":[],"styles":[],"routeData":{"type":"page","component":"_server-islands.astro","params":["name"],"segments":[[{"content":"_server-islands","dynamic":false,"spread":false}],[{"content":"name","dynamic":true,"spread":false}]],"pattern":"^\\/_server-islands\\/([^/]+?)\\/?$","prerender":false,"isIndex":false,"fallbackRoutes":[],"route":"/_server-islands/[name]","origin":"internal","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[],"routeData":{"type":"endpoint","isIndex":false,"route":"/_image","pattern":"^\\/_image\\/?$","segments":[[{"content":"_image","dynamic":false,"spread":false}]],"params":[],"component":"node_modules/astro/dist/assets/endpoint/node.js","pathname":"/_image","prerender":false,"fallbackRoutes":[],"origin":"internal","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"}],"routeData":{"route":"/404","isIndex":false,"type":"page","pattern":"^\\/404\\/?$","segments":[[{"content":"404","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/404.astro","pathname":"/404","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"}],"routeData":{"route":"/admin","isIndex":true,"type":"page","pattern":"^\\/admin\\/?$","segments":[[{"content":"admin","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/admin/index.astro","pathname":"/admin","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"},{"type":"inline","content":".hide-scrollbar[data-v-979a6e7a]::-webkit-scrollbar{display:none}.hide-scrollbar[data-v-979a6e7a]{-ms-overflow-style:none;scrollbar-width:none}\n"}],"routeData":{"route":"/dashboard","isIndex":true,"type":"page","pattern":"^\\/dashboard\\/?$","segments":[[{"content":"dashboard","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/dashboard/index.astro","pathname":"/dashboard","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"}],"routeData":{"route":"/login","isIndex":false,"type":"page","pattern":"^\\/login\\/?$","segments":[[{"content":"login","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/login.astro","pathname":"/login","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"}],"routeData":{"route":"/profile","isIndex":false,"type":"page","pattern":"^\\/profile\\/?$","segments":[[{"content":"profile","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/profile.astro","pathname":"/profile","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/index.DZ561Pxv.css"}],"routeData":{"route":"/","isIndex":true,"type":"page","pattern":"^\\/$","segments":[],"params":[],"component":"src/pages/index.astro","pathname":"/","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}}],"base":"/","trailingSlash":"ignore","compressHTML":true,"componentMetadata":[["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/404.astro",{"propagation":"none","containsHead":true}],["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/admin/index.astro",{"propagation":"none","containsHead":true}],["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/dashboard/index.astro",{"propagation":"none","containsHead":true}],["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/index.astro",{"propagation":"none","containsHead":true}],["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/login.astro",{"propagation":"none","containsHead":true}],["C:/Users/Эдуард Панпушный/IdeaProjects/website/src/pages/profile.astro",{"propagation":"none","containsHead":true}]],"renderers":[],"clientDirectives":[["idle","(()=>{var l=(n,t)=>{let i=async()=>{await(await n())()},e=typeof t.value==\"object\"?t.value:void 0,s={timeout:e==null?void 0:e.timeout};\"requestIdleCallback\"in window?window.requestIdleCallback(i,s):setTimeout(i,s.timeout||200)};(self.Astro||(self.Astro={})).idle=l;window.dispatchEvent(new Event(\"astro:idle\"));})();"],["load","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).load=e;window.dispatchEvent(new Event(\"astro:load\"));})();"],["media","(()=>{var n=(a,t)=>{let i=async()=>{await(await a())()};if(t.value){let e=matchMedia(t.value);e.matches?i():e.addEventListener(\"change\",i,{once:!0})}};(self.Astro||(self.Astro={})).media=n;window.dispatchEvent(new Event(\"astro:media\"));})();"],["only","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).only=e;window.dispatchEvent(new Event(\"astro:only\"));})();"],["visible","(()=>{var a=(s,i,o)=>{let r=async()=>{await(await s())()},t=typeof i.value==\"object\"?i.value:void 0,c={rootMargin:t==null?void 0:t.rootMargin},n=new IntersectionObserver(e=>{for(let l of e)if(l.isIntersecting){n.disconnect(),r();break}},c);for(let e of o.children)n.observe(e)};(self.Astro||(self.Astro={})).visible=a;window.dispatchEvent(new Event(\"astro:visible\"));})();"]],"entryModules":{"\u0000astro-internal:middleware":"_astro-internal_middleware.mjs","\u0000virtual:astro:actions/noop-entrypoint":"noop-entrypoint.mjs","\u0000@astro-page:src/pages/404@_@astro":"pages/404.astro.mjs","\u0000@astro-page:src/pages/admin/index@_@astro":"pages/admin.astro.mjs","\u0000@astro-page:src/pages/dashboard/index@_@astro":"pages/dashboard.astro.mjs","\u0000@astro-page:src/pages/login@_@astro":"pages/login.astro.mjs","\u0000@astro-page:src/pages/profile@_@astro":"pages/profile.astro.mjs","\u0000@astro-page:src/pages/index@_@astro":"pages/index.astro.mjs","\u0000@astrojs-ssr-virtual-entry":"entry.mjs","\u0000@astro-renderers":"renderers.mjs","\u0000@astro-page:node_modules/astro/dist/assets/endpoint/node@_@js":"pages/_image.astro.mjs","\u0000@astrojs-ssr-adapter":"_@astrojs-ssr-adapter.mjs","\u0000@astrojs-manifest":"manifest_Duxl-dIv.mjs","C:/Users/Эдуард Панпушный/IdeaProjects/website/node_modules/unstorage/drivers/fs-lite.mjs":"chunks/fs-lite_COtHaKzy.mjs","C:/Users/Эдуард Панпушный/IdeaProjects/website/node_modules/astro/dist/assets/services/sharp.js":"chunks/sharp_WaCbeaCv.mjs","C:/Users/Эдуард Панпушный/IdeaProjects/website/src/components/AdminPanel.vue":"_astro/AdminPanel.ChDhJBqC.js","C:/Users/Эдуард Панпушный/IdeaProjects/website/src/components/RetakeScheduler.vue":"_astro/RetakeScheduler.Dwl_-xW4.js","C:/Users/Эдуард Панпушный/IdeaProjects/website/src/components/TeacherBoard.vue":"_astro/TeacherBoard.7U_QY52i.js","C:/Users/Эдуард Панпушный/IdeaProjects/website/src/components/StudentBoard.vue":"_astro/StudentBoard.MOuoI0-7.js","C:/Users/Эдуард Панпушный/IdeaProjects/website/src/components/ToastProvider.vue":"_astro/ToastProvider.5CeomMcH.js","@astrojs/vue/client.js":"_astro/client.xn0MFj2A.js","astro:scripts/before-hydration.js":""},"inlinedScripts":[],"assets":["/_astro/index.DZ561Pxv.css","/_astro/AdminPanel.ChDhJBqC.js","/_astro/backend-api.BFeq0cqm.js","/_astro/client.xn0MFj2A.js","/_astro/createLucideIcon.ByuU82aT.js","/_astro/RetakeScheduler.Dwl_-xW4.js","/_astro/runtime-core.esm-bundler.CZxAPIZC.js","/_astro/runtime-dom.esm-bundler.fGW2igxu.js","/_astro/StudentBoard.MOuoI0-7.js","/_astro/TeacherBoard.7U_QY52i.js","/_astro/ToastProvider.5CeomMcH.js","/_astro/triangle-alert.Rgv0vdzK.js","/_astro/users.CYYklQCH.js","/_astro/useToast.BYElq5lK.js","/_astro/x.Dh6FpZiB.js","/_astro/_plugin-vue_export-helper.DlAUqK2U.js"],"buildFormat":"directory","checkOrigin":true,"allowedDomains":[],"actionBodySizeLimit":1048576,"serverIslandNameMap":[],"key":"PL24pUtHeuAsbMTnFwK2GunLwEmF7ZaXX6cHqC57a/M=","sessionConfig":{"driver":"fs-lite","options":{"base":"C:\\Users\\Эдуард Панпушный\\IdeaProjects\\website\\node_modules\\.astro\\sessions"}}});
if (manifest.sessionConfig) manifest.sessionConfig.driverModule = () => import('./chunks/fs-lite_COtHaKzy.mjs');

export { manifest };
