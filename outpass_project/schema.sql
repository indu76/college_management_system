-- ==================================================
-- OUTPASS MANAGEMENT SYSTEM - DATABASE SCHEMA
-- ==================================================

CREATE DATABASE IF NOT EXISTS outpass_clean;
USE outpass_clean;

-- --------------------------------------------------
-- 1) tutors
-- --------------------------------------------------
CREATE TABLE tutors (
    tutor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- --------------------------------------------------
-- 2) wardens
-- --------------------------------------------------
CREATE TABLE wardens (
    warden_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    gender ENUM('Male','Female') NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- --------------------------------------------------
-- 3) students
-- --------------------------------------------------
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    gender ENUM('Male','Female') NOT NULL,
    category ENUM('DayScholar','Hosteller') NOT NULL
);

-- --------------------------------------------------
-- 4) outpass_requests
-- --------------------------------------------------
CREATE TABLE outpass_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    reason TEXT NOT NULL,
    tutor_status ENUM('PENDING','APPROVED','REJECTED') DEFAULT 'PENDING',
    warden_status ENUM('NOT_REQUIRED','PENDING','APPROVED','REJECTED') DEFAULT 'NOT_REQUIRED',
    ready_for_exit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- --------------------------------------------------
-- 5) attendance_location
-- --------------------------------------------------
CREATE TABLE attendance_location (
    id INT PRIMARY KEY,
    type ENUM('CLASS','HOSTEL') NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    allowed_radius INT NOT NULL COMMENT 'Radius in meters'
);

-- --------------------------------------------------
-- 6) attendance_records
-- --------------------------------------------------
CREATE TABLE attendance_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    type ENUM('CLASS','HOSTEL') NOT NULL,
    session ENUM('MORNING','EVENING') NOT NULL,
    status ENUM('PRESENT','ABSENT','OD') NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    date DATE NOT NULL,
    verified_by ENUM('AUTO','TUTOR','WARDEN') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY uk_student_date_type_session (student_id, date, type, session)
);

-- Indexes for performance
CREATE INDEX idx_outpass_student ON outpass_requests(student_id);
CREATE INDEX idx_outpass_tutor_status ON outpass_requests(tutor_status);
CREATE INDEX idx_outpass_warden_status ON outpass_requests(warden_status);
CREATE INDEX idx_attendance_student_date ON attendance_records(student_id, date, type);
