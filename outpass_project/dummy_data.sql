-- ==================================================
-- OUTPASS MANAGEMENT SYSTEM - DUMMY DATA
-- ==================================================

USE outpass_clean;

-- --------------------------------------------------
-- Tutors (2 tutors: CSE, ECE)
-- --------------------------------------------------
INSERT INTO tutors (name, username, password, department, email) VALUES
('Dr. Rajesh Kumar', 'tutor_cse', 'tutor123', 'CSE', 'indhu9186@gmail.com'),
('Dr. Priya Sharma', 'tutor_ece', 'tutor123', 'ECE', 'indhu9186@gmail.com');

-- --------------------------------------------------
-- Wardens (1 male, 1 female)
-- --------------------------------------------------
INSERT INTO wardens (name, username, password, gender, email) VALUES
('Mr. Suresh Menon', 'warden_male', 'warden123', 'Male', 'indhu9186@gmail.com'),
('Ms. Lakshmi Devi', 'warden_female', 'warden123', 'Female', 'indhu9186@gmail.com');

-- --------------------------------------------------
-- Students (10 students: mix DayScholar & Hosteller)
-- --------------------------------------------------
INSERT INTO students (name, email, department, gender, category) VALUES
('Arun Kumar', 'indhu9186@gmail.com', 'CSE', 'Male', 'DayScholar'),
('Bhavya Reddy', 'indhu9186@gmail.com', 'CSE', 'Female', 'Hosteller'),
('Chandra Sekhar', 'indhu9186@gmail.com', 'CSE', 'Male', 'Hosteller'),
('Divya Nair', 'indhu9186@gmail.com', 'ECE', 'Female', 'DayScholar'),
('Eshwar Prasad', 'indhu9186@gmail.com', 'ECE', 'Male', 'Hosteller'),
('Fathima Begum', 'indhu9186@gmail.com', 'CSE', 'Female', 'DayScholar'),
('Ganesh Rao', 'indhu9186@gmail.com', 'ECE', 'Male', 'DayScholar'),
('Hema Krishnan', 'indhu9186@gmail.com', 'CSE', 'Female', 'Hosteller'),
('Ibrahim Khan', 'indhu9186@gmail.com', 'ECE', 'Male', 'Hosteller'),
('Jyothi Venkat', 'indhu9186@gmail.com', 'ECE', 'Female', 'DayScholar');

-- --------------------------------------------------
-- Outpass Requests (10 requests)
-- --------------------------------------------------
INSERT INTO outpass_requests (student_id, reason, tutor_status, warden_status, ready_for_exit) VALUES
(1, 'Medical appointment at city hospital', 'PENDING', 'NOT_REQUIRED', FALSE),
(2, 'Family function in hometown', 'PENDING', 'NOT_REQUIRED', FALSE),
(3, 'Interview for internship', 'PENDING', 'NOT_REQUIRED', FALSE),
(4, 'Dental checkup', 'PENDING', 'NOT_REQUIRED', FALSE),
(5, 'Wedding of relative', 'PENDING', 'NOT_REQUIRED', FALSE),
(6, 'Bank work - document verification', 'PENDING', 'NOT_REQUIRED', FALSE),
(7, 'Sports competition in another city', 'PENDING', 'NOT_REQUIRED', FALSE),
(8, 'Emergency - family member unwell', 'PENDING', 'NOT_REQUIRED', FALSE),
(9, 'Project presentation at company', 'PENDING', 'NOT_REQUIRED', FALSE),
(10, 'Visa appointment at consulate', 'PENDING', 'NOT_REQUIRED', FALSE);

-- --------------------------------------------------
-- Attendance Locations (CLASS and HOSTEL)
-- --------------------------------------------------
-- CLASS: Example coordinates (adjust for your institution)
INSERT INTO attendance_location (id, type, latitude, longitude, allowed_radius) VALUES
(1, 'CLASS', 17.385044, 78.486671, 100),
(2, 'HOSTEL', 17.386044, 78.487671, 150);
