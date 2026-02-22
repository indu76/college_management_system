"""
Tutor module routes for Outpass Management System.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection, get_cursor
from email_utils import send_email
from location_utils import is_within_radius

router = APIRouter(prefix="/api/tutor", tags=["Tutor"])


# --- Request Models ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ApproveRejectRequest(BaseModel):
    request_id: int


class MarkAttendanceRequest(BaseModel):
    student_id: int
    date: str  # YYYY-MM-DD
    session: str  # MORNING or EVENING
    status: str  # PRESENT (requires location), ABSENT, OD
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OverrideAttendanceRequest(BaseModel):
    record_id: int
    status: str  # PRESENT, ABSENT, OD
    latitude: float
    longitude: float


class MarkODRequest(BaseModel):
    student_id: int
    date: str
    session: str  # MORNING or EVENING
    latitude: float
    longitude: float


# --- Helper: Get tutor by credentials ---
def get_tutor_by_credentials(username: str, password: str):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT tutor_id, name, username, department, email FROM tutors WHERE username = %s AND password = %s",
            (username, password),
        )
        return cursor.fetchone()


# --- Login ---
@router.post("/login")
def tutor_login(data: LoginRequest):
    tutor = get_tutor_by_credentials(data.username, data.password)
    if not tutor:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "tutor": tutor}


# --- Get outpass requests (department match) ---
@router.get("/requests")
def get_outpass_requests(username: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT tutor_id, department FROM tutors WHERE username = %s",
            (username,),
        )
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.request_id, o.student_id, o.reason, o.tutor_status, o.warden_status,
                   o.ready_for_exit, o.created_at,
                   s.name as student_name, s.email as student_email, s.department, s.category
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE s.department = %s
            ORDER BY o.created_at DESC
            """,
            (tutor["department"],),
        )
        requests = cursor.fetchall()

    return {"requests": requests}


# --- Approve request ---
@router.post("/approve")
def approve_request(data: ApproveRejectRequest, username: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT tutor_id, department, name FROM tutors WHERE username = %s",
            (username,),
        )
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.*, s.name, s.email, s.category, s.department
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE o.request_id = %s AND s.department = %s AND o.tutor_status = 'PENDING'
            """,
            (data.request_id, tutor["department"]),
        )
        req = cursor.fetchone()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")

    if req["category"] == "DayScholar":
        tutor_status = "APPROVED"
        warden_status = "NOT_REQUIRED"
        ready_for_exit = True
    else:  # Hosteller
        tutor_status = "APPROVED"
        warden_status = "PENDING"
        ready_for_exit = False

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            UPDATE outpass_requests
            SET tutor_status = %s, warden_status = %s, ready_for_exit = %s
            WHERE request_id = %s
            """,
            (tutor_status, warden_status, ready_for_exit, data.request_id),
        )

    subject = "Outpass Request Approved"
    body = f"Dear {req['name']},\n\nYour outpass request (ID: {data.request_id}) has been approved by your tutor."
    if ready_for_exit:
        body += "\n\nYou are ready for exit. Please proceed to the watchman."
    else:
        body += "\n\nYour request is pending warden approval. You will be notified once approved."
    send_email(req["email"], subject, body)

    return {"success": True, "ready_for_exit": ready_for_exit}


# --- Reject request ---
@router.post("/reject")
def reject_request(data: ApproveRejectRequest, username: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT tutor_id, department FROM tutors WHERE username = %s",
            (username,),
        )
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.*, s.name, s.email
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE o.request_id = %s AND s.department = %s AND o.tutor_status = 'PENDING'
            """,
            (data.request_id, tutor["department"]),
        )
        req = cursor.fetchone()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            UPDATE outpass_requests
            SET tutor_status = 'REJECTED', warden_status = 'REJECTED', ready_for_exit = FALSE
            WHERE request_id = %s
            """,
            (data.request_id,),
        )

    subject = "Outpass Request Rejected"
    body = f"Dear {req['name']},\n\nYour outpass request (ID: {data.request_id}) has been rejected by your tutor."
    send_email(req["email"], subject, body)

    return {"success": True}


# --- Get students with attendance status for a date (table view) ---
@router.get("/students-attendance")
def get_students_attendance(username: str = Query(...), date: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT s.student_id, s.name, s.category
            FROM students s
            WHERE s.department = %s
            ORDER BY s.name
            """,
            (tutor["department"],),
        )
        students = cursor.fetchall()

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT record_id, student_id, session, status, verified_by
            FROM attendance_records
            WHERE type = 'CLASS' AND date = %s
            """,
            (date,),
        )
        records = cursor.fetchall()

    # Build session lookup: (student_id, session) -> {record_id, status, verified_by}
    rec_map = {}
    for r in records:
        key = (r["student_id"], r["session"])
        rec_map[key] = {"record_id": r["record_id"], "status": r["status"], "verified_by": r["verified_by"]}

    result = []
    for s in students:
        mid = rec_map.get((s["student_id"], "MORNING"))
        eid = rec_map.get((s["student_id"], "EVENING"))
        result.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "category": s["category"],
            "morning_status": mid["status"] if mid else "NOT MARKED",
            "evening_status": eid["status"] if eid else "NOT MARKED",
            "morning_verified_by": mid["verified_by"] if mid else None,
            "evening_verified_by": eid["verified_by"] if eid else None,
            "verified_by_morning": mid["verified_by"] if mid else None,
            "verified_by_evening": eid["verified_by"] if eid else None,
            "record_id_morning": mid["record_id"] if mid else None,
            "record_id_evening": eid["record_id"] if eid else None,
        })
    return {"students": result, "date": date}


# --- Get attendance location for CLASS ---
@router.get("/attendance/location")
def get_class_location():
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT id, type, latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'CLASS'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="CLASS location not configured")
    return loc


# --- Mark CLASS attendance (strict location validation for all statuses) ---
@router.post("/mark-attendance")
def mark_attendance(data: MarkAttendanceRequest, username: str = Query(...)):
    if data.session not in ("MORNING", "EVENING"):
        raise HTTPException(status_code=400, detail="session must be MORNING or EVENING")
    if data.status not in ("PRESENT", "ABSENT", "OD"):
        raise HTTPException(status_code=400, detail="status must be PRESENT, ABSENT or OD")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, department FROM students WHERE student_id = %s",
            (data.student_id,),
        )
        student = cursor.fetchone()
    if not student or student["department"] != tutor["department"]:
        raise HTTPException(status_code=403, detail="Student not in your department")

    # Step 1 & 2: fetch allowed CLASS location and validate tutor position
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'CLASS'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="CLASS location not configured")

    within = is_within_radius(
        data.latitude,
        data.longitude,
        float(loc["latitude"]),
        float(loc["longitude"]),
        loc["allowed_radius"],
    )
    if not within:
        return {
            "success": False,
            "message": "You must be inside the allowed location to mark attendance.",
        }

    # Step 3: insert or update, always updating existing record
    status = data.status
    verified_by = "TUTOR"
    lat, lon = data.latitude, data.longitude

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT record_id FROM attendance_records
            WHERE student_id = %s AND date = %s AND type = 'CLASS' AND session = %s
            """,
            (data.student_id, data.date, data.session),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE attendance_records
                SET status = %s,
                    latitude = %s,
                    longitude = %s,
                    verified_by = %s
                WHERE record_id = %s
                """,
                (status, lat, lon, verified_by, existing["record_id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO attendance_records
                    (student_id, type, session, status, latitude, longitude, date, verified_by)
                VALUES
                    (%s, 'CLASS', %s, %s, %s, %s, %s, %s)
                """,
                (data.student_id, data.session, status, lat, lon, data.date, verified_by),
            )

    return {"success": True, "status": status}




# --- Tutor override attendance (by record_id) ---
@router.post("/attendance/override")
def override_attendance(data: OverrideAttendanceRequest, username: str = Query(...)):
    if data.status not in ("PRESENT", "ABSENT", "OD"):
        raise HTTPException(status_code=400, detail="Invalid status")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT ar.*, s.department
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            WHERE ar.record_id = %s AND ar.type = 'CLASS' AND s.department = %s
            """,
            (data.record_id, tutor["department"]),
        )
        rec = cursor.fetchone()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")

    # Strict location validation for override
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'CLASS'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="CLASS location not configured")

    within = is_within_radius(
        data.latitude,
        data.longitude,
        float(loc["latitude"]),
        float(loc["longitude"]),
        loc["allowed_radius"],
    )
    if not within:
        return {
            "success": False,
            "message": "You must be inside the allowed location to mark attendance.",
        }

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            UPDATE attendance_records
            SET status = %s,
                verified_by = 'TUTOR',
                latitude = %s,
                longitude = %s
            WHERE record_id = %s
            """,
            (data.status, data.latitude, data.longitude, data.record_id),
        )

    return {"success": True, "status": data.status}


# --- Mark OD (tutor sets OD without location) ---
@router.post("/mark-od")
def mark_od(data: MarkODRequest, username: str = Query(...)):
    if data.session not in ("MORNING", "EVENING"):
        raise HTTPException(status_code=400, detail="session must be MORNING or EVENING")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, department FROM students WHERE student_id = %s",
            (data.student_id,),
        )
        student = cursor.fetchone()
    if not student or student["department"] != tutor["department"]:
        raise HTTPException(status_code=403, detail="Student not in your department")

    # Strict location validation for OD marking
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'CLASS'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="CLASS location not configured")

    within = is_within_radius(
        data.latitude,
        data.longitude,
        float(loc["latitude"]),
        float(loc["longitude"]),
        loc["allowed_radius"],
    )
    if not within:
        return {
            "success": False,
            "message": "You must be inside the allowed location to mark attendance.",
        }

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT record_id FROM attendance_records
            WHERE student_id = %s AND date = %s AND type = 'CLASS' AND session = %s
            """,
            (data.student_id, data.date, data.session),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE attendance_records
                SET status = 'OD',
                    verified_by = 'TUTOR',
                    latitude = %s,
                    longitude = %s
                WHERE record_id = %s
                """,
                (data.latitude, data.longitude, existing["record_id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO attendance_records (student_id, type, session, status, latitude, longitude, date, verified_by)
                VALUES (%s, 'CLASS', %s, 'OD', %s, %s, %s, 'TUTOR')
                """,
                (data.student_id, data.session, data.latitude, data.longitude, data.date),
            )

    return {"success": True, "status": "OD"}


# --- Get students for attendance (department) ---
@router.get("/students")
def get_students(username: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, name, email, department, category FROM students WHERE department = %s ORDER BY name",
            (tutor["department"],),
        )
        students = cursor.fetchall()
    return {"students": students}


# --- Get attendance records for a date ---
@router.get("/attendance/records")
def get_attendance_records(username: str = Query(...), date: str = Query(...)):
    tutor = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT tutor_id, department FROM tutors WHERE username = %s", (username,))
        tutor = cursor.fetchone()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT ar.record_id, ar.student_id, ar.type, ar.session, ar.status, ar.date, ar.verified_by,
                   s.name as student_name
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            WHERE ar.type = 'CLASS' AND s.department = %s AND ar.date = %s
            ORDER BY s.name, ar.session
            """,
            (tutor["department"], date),
        )
        records = cursor.fetchall()
    return {"records": records}
