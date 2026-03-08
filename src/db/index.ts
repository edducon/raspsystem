import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const connectionString = import.meta.env.DATABASE_URL;

if (!connectionString) {
    throw new Error("Не задана переменная DATABASE_URL в файле .env");
}

const client = postgres(connectionString);

export const db = drizzle(client, { schema });