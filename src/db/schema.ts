import { pgTable, text, timestamp, integer, uuid, primaryKey, jsonb } from "drizzle-orm/pg-core";

export const departments = pgTable("departments", {
    id: integer("id").primaryKey().generatedAlwaysAsIdentity(),
    name: text("name").notNull(),
});

export const teachersLocal = pgTable("teachers_local", {
    uuid: uuid("uuid").primaryKey(),
    fullName: text("full_name").notNull(),
    departmentIds: integer("department_ids").array().default([]),
});

export const retakes = pgTable("retakes", {
    id: uuid("id").primaryKey().defaultRandom(),
    groupUuid: uuid("group_uuid").notNull(),
    subjectUuid: uuid("subject_uuid").notNull(),
    date: text("date").notNull(),
    timeSlots: integer("time_slots").array().notNull(),
    roomUuid: text("room_uuid"),
    link: text("link"),
    attemptNumber: integer("attempt_number").notNull().default(1),
    createdBy: text("created_by"),
    createdAt: timestamp("created_at").defaultNow(),
});

export const retakeTeachers = pgTable("retake_teachers", {
    retakeId: uuid("retake_id").notNull().references(() => retakes.id, { onDelete: "cascade" }),
    teacherUuid: uuid("teacher_uuid").notNull().references(() => teachersLocal.uuid),
    role: text("role").notNull(),
}, (table) => ({
    pk: primaryKey({ columns: [table.retakeId, table.teacherUuid] }),
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
