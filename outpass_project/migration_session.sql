-- Migration: Add MORNING/EVENING session to attendance_records
-- Run this if you already have the database: mysql -u outpass_user -p outpass_clean < migration_session.sql

USE outpass_clean;

-- Add session column (default MORNING for existing rows)
ALTER TABLE attendance_records
ADD COLUMN session ENUM('MORNING','EVENING') NOT NULL DEFAULT 'MORNING' AFTER type;

-- Ensure one record per student per date per type per session
-- First remove duplicate indexes if any, then add unique constraint
ALTER TABLE attendance_records
ADD UNIQUE KEY uk_student_date_type_session (student_id, date, type, session);
