-- database/init.sql
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    weight_total INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    title VARCHAR(255) NOT NULL,
    deadline TIMESTAMP NOT NULL,
    max_score INTEGER NOT NULL,
    weight INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id),
    student_id VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL
);

-- Mock Data
INSERT INTO courses (name, description) VALUES ('AI for Beginners', 'Introduction to AI concepts');
INSERT INTO courses (name, description) VALUES ('Software Engineering', 'Best practices for software development');

INSERT INTO assignments (course_id, title, deadline, max_score, weight) VALUES 
(1, 'Lab 1: Neural Networks', '2026-04-10 23:59:00', 10, 10),
(1, 'Lab 2: Computer Vision', '2026-04-17 23:59:00', 10, 10),
(2, 'Lab 8: Agents', '2026-04-05 23:59:00', 100, 20),
(2, 'Lab 9: Hackathon', '2026-04-12 23:59:00', 100, 30);

INSERT INTO grades (assignment_id, student_id, score) VALUES 
(1, 'student_01', 9),
(3, 'student_01', 95);
