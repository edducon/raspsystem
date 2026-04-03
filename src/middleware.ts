import { defineMiddleware } from "astro:middleware";
import { fetchCurrentUser } from "./lib/backend-auth";

export const onRequest = defineMiddleware(async (context, next) => {
    try {
        context.locals.user = await fetchCurrentUser(context.request);
    } catch (error) {
        console.error("Failed to resolve backend auth session", error);
        context.locals.user = null;
    }

    return next();
});
