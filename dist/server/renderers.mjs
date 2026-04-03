import { defineComponent, h, createSSRApp } from 'vue';
import { renderToString } from 'vue/server-renderer';

const setup = () => {};

const contexts = /* @__PURE__ */ new WeakMap();
const ID_PREFIX = "s";
function getContext(rendererContextResult) {
  if (contexts.has(rendererContextResult)) {
    return contexts.get(rendererContextResult);
  }
  const ctx = {
    currentIndex: 0,
    get id() {
      return ID_PREFIX + this.currentIndex.toString();
    }
  };
  contexts.set(rendererContextResult, ctx);
  return ctx;
}
function incrementId(rendererContextResult) {
  const ctx = getContext(rendererContextResult);
  const id = ctx.id;
  ctx.currentIndex++;
  return id;
}

const StaticHtml = defineComponent({
  props: {
    value: String,
    name: String,
    hydrate: {
      type: Boolean,
      default: true
    }
  },
  setup({ name, value, hydrate }) {
    if (!value) return () => null;
    let tagName = hydrate ? "astro-slot" : "astro-static-slot";
    return () => h(tagName, { name, innerHTML: value });
  }
});
var static_html_default = StaticHtml;

async function check(Component) {
  return !!Component["ssrRender"] || !!Component["__ssrInlineRender"];
}
async function renderToStaticMarkup(Component, inputProps, slotted, metadata) {
  let prefix;
  if (this && this.result) {
    prefix = incrementId(this.result);
  }
  const attrs = { prefix };
  const slots = {};
  const props = { ...inputProps };
  delete props.slot;
  for (const [key, value] of Object.entries(slotted)) {
    slots[key] = () => h(static_html_default, {
      value,
      name: key === "default" ? void 0 : key,
      // Adjust how this is hydrated only when the version of Astro supports `astroStaticSlot`
      hydrate: metadata?.astroStaticSlot ? !!metadata.hydrate : true
    });
  }
  const app = createSSRApp({ render: () => h(Component, props, slots) });
  app.config.idPrefix = prefix;
  await setup();
  const html = await renderToString(app);
  return { html, attrs };
}
const renderer = {
  name: "@astrojs/vue",
  check,
  renderToStaticMarkup,
  supportsAstroStaticSlot: true
};
var server_default = renderer;

const renderers = [Object.assign({"name":"@astrojs/vue","clientEntrypoint":"@astrojs/vue/client.js","serverEntrypoint":"@astrojs/vue/server.js"}, { ssr: server_default }),];

export { renderers };
