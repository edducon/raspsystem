import { pgTable, text, timestamp, integer, uuid, primaryKey, jsonb } from "drizzle-orm/pg-core";

// --- ПОЛЬЗОВАТЕЛИ И АВТОРИЗАЦИЯ ---
export const users = pgTable("users", {
    id: text("id").primaryKey(), // Lucia требует text id
    username: text("username").notNull().unique(),
    passwordHash: text("password_hash").notNull(),
    role: text("role").notNull().default("TEACHER"), // ADMIN, EMPLOYEE, TEACHER
    departmentIds: integer("department_ids").array().default([]),
    teacherUuid: uuid("teacher_uuid"), // Привязка к API-шному UUID, если это препод
});

export const sessions = pgTable("sessions", {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    expiresAt: timestamp("expires_at", { withTimezone: true, mode: "date" }).notNull(),
});

// --- КАФЕДРЫ И ПРЕПОДАВАТЕЛИ (Локальный справочник) ---
export const departments = pgTable("departments", {
    id: integer("id").primaryKey().generatedAlwaysAsIdentity(),
    name: text("name").notNull(),
});

export const teachersLocal = pgTable("teachers_local", {
    uuid: uuid("uuid").primaryKey(), // UUID из внешнего API
    fullName: text("full_name").notNull(),
    departmentIds: integer("department_ids").array().default([]),
});

// --- ПЕРЕСДАЧИ (Главная таблица) ---
export const retakes = pgTable("retakes", {
    id: uuid("id").primaryKey().defaultRandom(),
    groupUuid: uuid("group_uuid").notNull(),
    subjectUuid: uuid("subject_uuid").notNull(),
    date: text("date").notNull(), // Формат YYYY-MM-DD
    timeSlots: integer("time_slots").array().notNull(), // Например: [3] или [3, 4]
    roomUuid: text("room_uuid"),
    link: text("link"),// Аудитория
    attemptNumber: integer("attempt_number").notNull().default(1),
    createdBy: text("created_by").references(() => users.id),
    createdAt: timestamp("created_at").defaultNow(),
});

export const retakeTeachers = pgTable("retake_teachers", {
    retakeId: uuid("retake_id").notNull().references(() => retakes.id, { onDelete: "cascade" }),
    teacherUuid: uuid("teacher_uuid").notNull().references(() => teachersLocal.uuid),
    role: text("role").notNull(), // MAIN (Ведущий) или COMMISSION (Комиссия)
}, (t) => ({
    pk: primaryKey({ columns: [t.retakeId, t.teacherUuid] }),
}));

export const scheduleCache = pgTable("schedule_cache", {
    id: uuid("id").primaryKey().defaultRandom(),
    entityType: text("entity_type").notNull(),
    entityIdentifier: text("entity_identifier").notNull(),
    dateStart: text("date_start").notNull(),
    dateEnd: text("date_end").notNull(),
    scheduleData: jsonb("schedule_data").notNull(),
    updatedAt: timestamp("updated_at").defaultNow(),
});

export const pastSemester = pgTable("past_semester", {
    id: uuid("id").primaryKey().defaultRandom(),
    groupName: text("group_name").notNull(),
    subjectName: text("subject_name").notNull(),
    teacherNames: text("teacher_names").array().notNull(),
});