import { defineConfig } from 'drizzle-kit';
import * as dotenv from 'dotenv';

// Загружаем переменные из .env для Drizzle Kit
dotenv.config();

export default defineConfig({
    output: 'server',
    schema: './src/db/schema.ts',
    out: './drizzle',
    dialect: 'postgresql',
    dbCredentials: {
        url: process.env.DATABASE_URL!,
    },
    verbose: true,
    strict: true,
});