import { d as defineMiddleware, s as sequence } from './chunks/index_JovVBmbp.mjs';
import { f as fetchCurrentUser } from './chunks/backend-auth_-lm5w3qF.mjs';
import 'es-module-lexer';
import './chunks/astro-designed-error-pages_Bp_he5rZ.mjs';
import 'piccolore';
import './chunks/astro/server__Jo3gmtv.mjs';
import 'clsx';

const onRequest$1 = defineMiddleware(async (context, next) => {
  try {
    context.locals.user = await fetchCurrentUser(context.request);
  } catch (error) {
    console.error("Failed to resolve backend auth session", error);
    context.locals.user = null;
  }
  return next();
});

const onRequest = sequence(
	
	onRequest$1
	
);

export { onRequest };
