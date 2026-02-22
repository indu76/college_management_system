# Outpass Management System

Complete Outpass Management System with Tutor and Warden modules. Supports DayScholar and Hosteller workflows with geolocation-based attendance.

## Tech Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Backend:** FastAPI (Python)
- **Database:** MySQL
- **Email:** Gmail SMTP (smtplib)

## Workflow

### Outpass Flow
- **DayScholar:** Student → Tutor → Watchman (no warden)
- **Hosteller:** Student → Tutor → Warden → Watchman

### Attendance Flow
- **Tutor:** CLASS attendance for ALL students (department-based). Morning & Evening sessions.
- **Warden:** HOSTEL attendance for HOSTELLERS ONLY, filtered by warden gender (male warden → male hostellers only). Morning & Evening sessions.

---

## How to Run

### 1. Start MySQL

Ensure MySQL server is running on your system.

```bash
# Linux (systemd)
sudo systemctl start mysql

# Or start MySQL service as per your OS
```

### 2. Create Database and Tables

**EASIEST: Use the setup script (recommended):**
```bash
cd outpass_project
./setup_mysql.sh
```
This script will guide you through MySQL setup and create the database automatically.

**MANUAL: If MySQL root requires password:**
```bash
mysql -u root -p < schema.sql
# Enter your MySQL root password when prompted
```

**MANUAL: If MySQL root uses auth_socket (Ubuntu/Debian):**
```bash
sudo mysql < schema.sql
```

**MANUAL: Create a dedicated MySQL user (recommended for production):**
```bash
# First, access MySQL as root
sudo mysql -u root

# Then run these SQL commands:
CREATE USER 'outpass_user'@'localhost' IDENTIFIED BY 'outpass123';
GRANT ALL PRIVILEGES ON outpass_clean.* TO 'outpass_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Then use this user:
mysql -u outpass_user -poutpass123 < schema.sql
```

### 3. Insert Dummy Data

**If you used setup_mysql.sh, this is already done!**

**Otherwise:**
```bash
mysql -u root -p < dummy_data.sql
# OR
sudo mysql < dummy_data.sql
# OR with dedicated user:
mysql -u outpass_user -poutpass123 < dummy_data.sql
```

**If you already had the database before Morning/Evening attendance was added**, run the migration:
```bash
mysql -u outpass_user -p outpass_clean < migration_session.sql
```

### 4. Install Python Dependencies

```bash
cd outpass_project
pip install -r requirements.txt
```

### 5. Set Environment Variables

**Option A: Export in terminal (recommended for testing)**

Run these commands in your terminal **before** starting the server:

```bash
export GMAIL_USER="indhu9186@gmail.com"
export GMAIL_APP_PASSWORD="kmetedggwvfwegep"

# MySQL config - IMPORTANT: Set password if MySQL root requires it
export MYSQL_HOST="localhost"
export MYSQL_USER="root"
export MYSQL_PASSWORD="your_mysql_password"  # Change this!
export MYSQL_DATABASE="outpass_clean"

# OR if you created a dedicated user:
# export MYSQL_USER="outpass_user"
# export MYSQL_PASSWORD="outpass123"
```

**Option B: Create a startup script**

Create a file `start.sh`:

```bash
#!/bin/bash
export GMAIL_USER="indhu9186@gmail.com"
export GMAIL_APP_PASSWORD="kmetedggwvfwegep"
export MYSQL_HOST="localhost"
export MYSQL_USER="root"
export MYSQL_PASSWORD="your_mysql_password"  # Change this!
export MYSQL_DATABASE="outpass_clean"
uvicorn main:app --reload
```

Make it executable: `chmod +x start.sh` and run: `./start.sh`

**Note:** These variables are only active in the current terminal session. If you close the terminal, you'll need to export them again.

### 6. Run the Application

**Easy way (using startup script):**
```bash
./start.sh
```

**Manual way:**
```bash
# Make sure you've exported environment variables first (see step 5)
uvicorn main:app --reload
# Or if uvicorn not in PATH:
python3 -m uvicorn main:app --reload
```

### 7. Open in Browser

- **Tutor Login:** http://127.0.0.1:8000/tutor_login.html
- **Warden Login:** http://127.0.0.1:8000/warden_login.html

---

## Dummy Credentials

| Role   | Username     | Password  |
|--------|--------------|-----------|
| Tutor (CSE) | tutor_cse   | tutor123  |
| Tutor (ECE) | tutor_ece   | tutor123  |
| Warden (Male) | warden_male | warden123 |
| Warden (Female) | warden_female | warden123 |

---

## Testing Guide

### 1. Tutor Login Test
- Open http://127.0.0.1:8000/tutor_login.html
- Login with `tutor_cse` / `tutor123`
- Verify dashboard loads with outpass requests from CSE department

### 2. Approve DayScholar → ready_for_exit TRUE
- As tutor_cse, find a request from a DayScholar student (e.g., Arun Kumar - student_id 1)
- Click **Approve**
- Verify: `tutor_status=APPROVED`, `warden_status=NOT_REQUIRED`, `ready_for_exit=TRUE`
- Check email at indhu9186@gmail.com for approval notification

### 3. Approve Hosteller → Appears in Warden
- As tutor_cse, approve a Hosteller request (e.g., Bhavya Reddy - student_id 2)
- Verify: `tutor_status=APPROVED`, `warden_status=PENDING`, `ready_for_exit=FALSE`
- Logout, login as `warden_male` / `warden123`
- Verify the approved Hosteller request appears in Warden dashboard

### 4. Warden Approve → ready_for_exit TRUE
- As warden, click **Approve** on a pending Hosteller request
- Verify: `warden_status=APPROVED`, `ready_for_exit=TRUE`
- Check email for approval notification

### 5. Email Verification
- Ensure `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set
- Approve or reject any request
- Check server logs for "Connecting to SMTP..." and "Email sent successfully"
- Check inbox at indhu9186@gmail.com

### 6. Attendance Location Testing
- **Tutor:** Go to Class Attendance section. Mark attendance for a student with browser location enabled.
  - If within CLASS location radius (100m of 17.385044, 78.486671): status = PRESENT
  - Else: status = ABSENT
- **Warden:** Go to Hostel Attendance. Only hostellers appear. Uses HOSTEL location (150m radius of 17.386044, 78.487671).
- Use Override dropdown to change status (PRESENT/ABSENT/OD) manually.

### 7. Update Location Coordinates
Edit `dummy_data.sql` or run:

```sql
UPDATE attendance_location SET latitude = YOUR_LAT, longitude = YOUR_LON, allowed_radius = 100 WHERE type = 'CLASS';
UPDATE attendance_location SET latitude = YOUR_LAT, longitude = YOUR_LON, allowed_radius = 150 WHERE type = 'HOSTEL';
```

---

## Project Structure

```
outpass_project/
├── main.py              # FastAPI app, routes, static serving
├── database.py          # MySQL connection
├── email_utils.py       # Gmail SMTP email
├── location_utils.py    # Haversine distance
├── tutor_routes.py      # Tutor APIs
├── warden_routes.py     # Warden APIs
├── schema.sql           # Database schema
├── dummy_data.sql       # Seed data
├── requirements.txt
├── README.md
├── templates/
│   ├── tutor_login.html
│   ├── tutor_dashboard.html
│   ├── warden_login.html
│   └── warden_dashboard.html
└── static/
    └── css/
        └── style.css
```

---

## API Endpoints

### Tutor
- `POST /api/tutor/login` - Login
- `GET /api/tutor/requests?username=` - Get department requests
- `POST /api/tutor/approve?username=` - Approve request
- `POST /api/tutor/reject?username=` - Reject request
- `GET /api/tutor/students?username=` - Get department students
- `GET /api/tutor/attendance/location` - Get CLASS location
- `POST /api/tutor/attendance/mark?username=` - Mark CLASS attendance
- `POST /api/tutor/attendance/override?username=` - Override attendance
- `GET /api/tutor/attendance/records?username=&date=` - Get records

### Warden
- `POST /api/warden/login` - Login
- `GET /api/warden/requests?username=` - Get pending hosteller requests
- `POST /api/warden/approve?username=` - Approve request
- `POST /api/warden/reject?username=` - Reject request
- `GET /api/warden/students?username=` - Get hostellers
- `GET /api/warden/attendance/location` - Get HOSTEL location
- `POST /api/warden/attendance/mark?username=` - Mark HOSTEL attendance
- `POST /api/warden/attendance/override?username=` - Override attendance
- `GET /api/warden/attendance/records?username=&date=` - Get records
