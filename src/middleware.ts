import { defineMiddleware } from "astro:middleware";
import { fetchCurrentSession } from "./lib/backend-auth";

export const onRequest = defineMiddleware(async (context, next) => {
    try {
        const session = await fetchCurrentSession(context.request);
        context.locals.user = session?.user ?? null;
        context.locals.csrfToken = session?.csrfToken ?? null;
    } catch (error) {
        console.error("Failed to resolve backend auth session", error);
        context.locals.user = null;
        context.locals.csrfToken = null;
    }

    return next();
});
