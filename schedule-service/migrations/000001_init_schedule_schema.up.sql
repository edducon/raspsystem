CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    address TEXT
);

CREATE TABLE IF NOT EXISTS campuses (
    id SERIAL PRIMARY KEY,
    building_id INT NOT NULL REFERENCES buildings(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    floor SMALLINT
);

CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    campus_id INT NOT NULL REFERENCES campuses(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    capacity SMALLINT
);

CREATE TABLE IF NOT EXISTS directions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    department_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    admission_year SMALLINT NOT NULL,
    study_form SMALLINT NOT NULL,
    direction_id INT NOT NULL REFERENCES directions(id) ON DELETE RESTRICT,
    stream SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT
);

CREATE TABLE IF NOT EXISTS subject_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT,
    is_online BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS schedule_slots (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES groups(id) ON DELETE RESTRICT,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    subject_type_id INT NOT NULL REFERENCES subject_types(id) ON DELETE RESTRICT,
    day_of_week SMALLINT NOT NULL,
    pair_number SMALLINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_by_user_id INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT valid_day CHECK (day_of_week BETWEEN 1 AND 7),
    CONSTRAINT valid_pair CHECK (pair_number BETWEEN 1 AND 8),
    CONSTRAINT valid_dates CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS schedule_slot_assignments (
    id SERIAL PRIMARY KEY,
    slot_id INT NOT NULL REFERENCES schedule_slots(id) ON DELETE CASCADE,
    teacher_id INT NOT NULL,
    room_id INT NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_campuses_building_id ON campuses(building_id);
CREATE INDEX IF NOT EXISTS idx_rooms_campus_id ON rooms(campus_id);
CREATE INDEX IF NOT EXISTS idx_groups_direction_id ON groups(direction_id);
CREATE INDEX IF NOT EXISTS idx_groups_admission_year ON groups(admission_year);
CREATE INDEX IF NOT EXISTS idx_schedule_slots_group_id ON schedule_slots(group_id);
CREATE INDEX IF NOT EXISTS idx_schedule_slot_assignments_slot_id ON schedule_slot_assignments(slot_id);
