-- Supabase SQL Editor에서 실행

CREATE TABLE classes (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE students (
    id BIGSERIAL PRIMARY KEY,
    class_id BIGINT REFERENCES classes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    school_name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE exams (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    exam_type TEXT NOT NULL CHECK (exam_type IN ('중간', '기말', '모의고사')),
    exam_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE scores (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    exam_id BIGINT REFERENCES exams(id) ON DELETE CASCADE,
    total_score INTEGER NOT NULL CHECK (total_score >= 0 AND total_score <= 100),
    grade INTEGER CHECK (grade >= 1 AND grade <= 9),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, exam_id)
);

CREATE TABLE category_scores (
    id BIGSERIAL PRIMARY KEY,
    score_id BIGINT REFERENCES scores(id) ON DELETE CASCADE,
    category_id BIGINT REFERENCES categories(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0),
    UNIQUE(score_id, category_id)
);

CREATE TABLE consultations (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    exam_id BIGINT REFERENCES exams(id) ON DELETE CASCADE,
    ai_draft TEXT NOT NULL DEFAULT '',
    final_text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memos (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO categories (name, sort_order) VALUES
    ('문법', 1),
    ('독해', 2),
    ('문학', 3);
