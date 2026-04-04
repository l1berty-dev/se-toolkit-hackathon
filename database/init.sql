-- Пересоздаем таблицы с каскадным удалением для безопасности
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS grade_thresholds;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE grade_thresholds (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    grade_letter CHAR(1) NOT NULL,
    min_score INTEGER NOT NULL
);

CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    deadline TIMESTAMP NOT NULL,
    weight DECIMAL(3,2) NOT NULL, 
    max_score INTEGER DEFAULT 100
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE UNIQUE,
    score DECIMAL(5,2) NOT NULL
);

-- Тестовые данные
INSERT INTO courses (name, code) VALUES ('Mathematical Analysis', 'MATH-01'), ('AGLA', 'MATH-02');
INSERT INTO grade_thresholds (course_id, grade_letter, min_score) VALUES 
(1, 'A', 90), (1, 'B', 80), (1, 'C', 70),
(2, 'A', 85), (2, 'B', 75), (2, 'C', 65);
INSERT INTO assignments (course_id, title, deadline, weight) VALUES 
(1, 'Test', '2026-02-28 23:59:00', 0.30),
(1, 'Midterm', '2026-04-04 23:59:00', 0.30),
(1, 'Final Exam', '2026-05-15 23:59:00', 0.40),
(2, 'Test 1', '2026-02-20 23:59:00', 0.20),
(2, 'Midterm', '2026-03-20 23:59:00', 0.30),
(2, 'Test 2', '2026-04-10 23:59:00', 0.20),
(2, 'Final Exam', '2026-05-14 23:59:00', 0.30);
INSERT INTO grades (assignment_id, score) VALUES (1, 96.66), (4, 100.00), (5, 76.66);
