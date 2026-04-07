/// <reference path="../.astro/types.d.ts" />
declare namespace App {
    interface Locals {
        user: import("./lib/backend-auth").BackendAuthUser | null;
        csrfToken: string | null;
    }
}
