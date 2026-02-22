"""
Warden module routes for Outpass Management System.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection, get_cursor
from email_utils import send_email
from location_utils import is_within_radius, haversine_distance

router = APIRouter(prefix="/api/warden", tags=["Warden"])


# --- Request Models ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ApproveRejectRequest(BaseModel):
    request_id: int


class MarkAttendanceRequest(BaseModel):
    student_id: int
    date: str
    session: str  # MORNING or EVENING
    status: str  # PRESENT (requires location), ABSENT, OD
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MarkODRequest(BaseModel):
    student_id: int
    date: str
    session: str
    latitude: float
    longitude: float


class OverrideAttendanceRequest(BaseModel):
    record_id: int
    status: str  # PRESENT, ABSENT, OD
    latitude: float
    longitude: float


# --- Helper ---
def get_warden_by_credentials(username: str, password: str):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT warden_id, name, username, gender, email FROM wardens WHERE username = %s AND password = %s",
            (username, password),
        )
        return cursor.fetchone()


# --- Login ---
@router.post("/login")
def warden_login(data: LoginRequest):
    warden = get_warden_by_credentials(data.username, data.password)
    if not warden:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "warden": warden}


# --- Get requests: tutor_status=APPROVED, student.category=Hosteller (no gender filter on outpass) ---
@router.get("/requests")
def get_outpass_requests(username: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.request_id, o.student_id, o.reason, o.tutor_status, o.warden_status,
                   o.ready_for_exit, o.created_at,
                   s.name as student_name, s.email as student_email, s.gender, s.category
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE o.tutor_status = 'APPROVED' AND s.category = 'Hosteller'
              AND s.gender = %s AND o.warden_status = 'PENDING'
            ORDER BY o.created_at DESC
            """,
            (warden["gender"],),
        )
        requests = cursor.fetchall()

    return {"requests": requests}


# --- Approve ---
@router.post("/approve")
def approve_request(data: ApproveRejectRequest, username: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, name, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.*, s.name, s.email
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE o.request_id = %s AND o.tutor_status = 'APPROVED' AND s.category = 'Hosteller'
            AND s.gender = %s AND o.warden_status = 'PENDING'
            """,
            (data.request_id, warden["gender"]),
        )
        req = cursor.fetchone()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            UPDATE outpass_requests
            SET warden_status = 'APPROVED', ready_for_exit = TRUE
            WHERE request_id = %s
            """,
            (data.request_id,),
        )

    subject = "Outpass Request Approved by Warden"
    body = f"Dear {req['name']},\n\nYour outpass request (ID: {data.request_id}) has been approved by the warden.\n\nYou are ready for exit. Please proceed to the watchman."
    send_email(req["email"], subject, body)

    return {"success": True, "ready_for_exit": True}


# --- Reject ---
@router.post("/reject")
def reject_request(data: ApproveRejectRequest, username: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT o.*, s.name, s.email
            FROM outpass_requests o
            JOIN students s ON o.student_id = s.student_id
            WHERE o.request_id = %s AND o.tutor_status = 'APPROVED' AND s.category = 'Hosteller'
            AND s.gender = %s AND o.warden_status = 'PENDING'
            """,
            (data.request_id, warden["gender"]),
        )
        req = cursor.fetchone()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            UPDATE outpass_requests
            SET warden_status = 'REJECTED', ready_for_exit = FALSE
            WHERE request_id = %s
            """,
            (data.request_id,),
        )

    subject = "Outpass Request Rejected by Warden"
    body = f"Dear {req['name']},\n\nYour outpass request (ID: {data.request_id}) has been rejected by the warden."
    send_email(req["email"], subject, body)

    return {"success": True}


# --- Get hostel attendance (hostellers only, same gender as warden) ---
@router.get("/hostel-attendance")
def get_hostel_attendance(username: str = Query(...), date: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT s.student_id, s.name
            FROM students s
            WHERE s.category = 'Hosteller' AND s.gender = %s
            ORDER BY s.name
            """,
            (warden["gender"],),
        )
        students = cursor.fetchall()

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT record_id, student_id, session, status, verified_by
            FROM attendance_records
            WHERE type = 'HOSTEL' AND date = %s
            """,
            (date,),
        )
        records = cursor.fetchall()

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


# --- Get HOSTEL attendance location ---
@router.get("/attendance/location")
def get_hostel_location():
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT id, type, latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'HOSTEL'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="HOSTEL location not configured")
    return loc


# --- Mark HOSTEL attendance (strict location validation for all statuses); hostellers same gender only ---
@router.post("/mark-attendance")
def mark_attendance(data: MarkAttendanceRequest, username: str = Query(...)):
    if data.session not in ("MORNING", "EVENING"):
        raise HTTPException(status_code=400, detail="session must be MORNING or EVENING")
    if data.status not in ("PRESENT", "ABSENT", "OD"):
        raise HTTPException(status_code=400, detail="status must be PRESENT, ABSENT or OD")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, gender FROM students WHERE student_id = %s AND category = 'Hosteller'",
            (data.student_id,),
        )
        student = cursor.fetchone()
    if not student or student["gender"] != warden["gender"]:
        raise HTTPException(status_code=403, detail="Student not in your hostel (gender filter)")

    # Strict location validation for ALL statuses
    print(f"\n{'='*60}")
    print("WARDEN ATTENDANCE DEBUG - Location Validation")
    print(f"{'='*60}")
    print(f"Incoming request data:")
    print(f"  student_id: {data.student_id}")
    print(f"  date: {data.date}")
    print(f"  session: {data.session}")
    print(f"  status: {data.status}")
    print(f"  latitude: {data.latitude} (type: {type(data.latitude)})")
    print(f"  longitude: {data.longitude} (type: {type(data.longitude)})")
    
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'HOSTEL'"
        )
        loc = cursor.fetchone()
    
    if not loc:
        print("ERROR: HOSTEL location not found in database!")
        raise HTTPException(status_code=404, detail="HOSTEL location not configured")
    
    print(f"\nDatabase HOSTEL location:")
    print(f"  latitude: {loc['latitude']} (type: {type(loc['latitude'])})")
    print(f"  longitude: {loc['longitude']} (type: {type(loc['longitude'])})")
    print(f"  allowed_radius: {loc['allowed_radius']} meters")
    
    # Convert to float explicitly
    user_lat = float(data.latitude)
    user_lon = float(data.longitude)
    loc_lat = float(loc["latitude"])
    loc_lon = float(loc["longitude"])
    allowed_radius = int(loc["allowed_radius"])
    
    print(f"\nConverted values for distance calculation:")
    print(f"  user_lat: {user_lat}")
    print(f"  user_lon: {user_lon}")
    print(f"  loc_lat: {loc_lat}")
    print(f"  loc_lon: {loc_lon}")
    print(f"  allowed_radius: {allowed_radius} meters")
    
    within = is_within_radius(
        user_lat,
        user_lon,
        loc_lat,
        loc_lon,
        allowed_radius,
    )
    
    # Calculate actual distance for debugging
    actual_distance = haversine_distance(user_lat, user_lon, loc_lat, loc_lon)
    print(f"\nDistance calculation:")
    print(f"  Actual distance: {actual_distance:.2f} meters")
    print(f"  Allowed radius: {allowed_radius} meters")
    print(f"  Within radius: {within}")
    print(f"{'='*60}\n")
    
    if not within:
        return {
            "success": False,
            "message": f"You must be inside the allowed location to mark attendance. (Distance: {actual_distance:.0f}m, Required: within {allowed_radius}m)",
        }

    # Always set verified_by = 'WARDEN' for warden actions (PRESENT, ABSENT, OD)
    status = data.status
    verified_by = "WARDEN"
    lat, lon = data.latitude, data.longitude

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT record_id FROM attendance_records
            WHERE student_id = %s AND date = %s AND type = 'HOSTEL' AND session = %s
            """,
            (data.student_id, data.date, data.session),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE attendance_records
                SET status = %s,
                    verified_by = 'WARDEN',
                    latitude = %s,
                    longitude = %s
                WHERE record_id = %s
                """,
                (status, lat, lon, existing["record_id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO attendance_records (student_id, type, session, status, latitude, longitude, date, verified_by)
                VALUES (%s, 'HOSTEL', %s, %s, %s, %s, %s, 'WARDEN')
                """,
                (data.student_id, data.session, status, lat, lon, data.date),
            )

    return {"success": True, "status": status}


# --- Mark OD (warden) ---
@router.post("/mark-od")
def mark_od(data: MarkODRequest, username: str = Query(...)):
    if data.session not in ("MORNING", "EVENING"):
        raise HTTPException(status_code=400, detail="session must be MORNING or EVENING")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, gender FROM students WHERE student_id = %s AND category = 'Hosteller'",
            (data.student_id,),
        )
        student = cursor.fetchone()
    if not student or student["gender"] != warden["gender"]:
        raise HTTPException(status_code=403, detail="Student not in your hostel")

    # Strict location validation for OD marking
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'HOSTEL'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="HOSTEL location not configured")

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
            WHERE student_id = %s AND date = %s AND type = 'HOSTEL' AND session = %s
            """,
            (data.student_id, data.date, data.session),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE attendance_records
                SET status = 'OD',
                    verified_by = 'WARDEN',
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
                VALUES (%s, 'HOSTEL', %s, 'OD', %s, %s, %s, 'WARDEN')
                """,
                (data.student_id, data.session, data.latitude, data.longitude, data.date),
            )

    return {"success": True, "status": "OD"}


# --- Warden override attendance ---
@router.post("/attendance/override")
def override_attendance(data: OverrideAttendanceRequest, username: str = Query(...)):
    if data.status not in ("PRESENT", "ABSENT", "OD"):
        raise HTTPException(status_code=400, detail="Invalid status")
    if data.latitude is None or data.longitude is None:
        raise HTTPException(status_code=400, detail="latitude and longitude required")

    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT ar.*, s.category, s.gender
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            WHERE ar.record_id = %s AND ar.type = 'HOSTEL' AND s.category = 'Hosteller' AND s.gender = %s
            """,
            (data.record_id, warden["gender"]),
        )
        rec = cursor.fetchone()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")

    # Strict location validation for override
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT latitude, longitude, allowed_radius FROM attendance_location WHERE type = 'HOSTEL'"
        )
        loc = cursor.fetchone()
    if not loc:
        raise HTTPException(status_code=404, detail="HOSTEL location not configured")

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
                verified_by = 'WARDEN',
                latitude = %s,
                longitude = %s
            WHERE record_id = %s
            """,
            (data.status, data.latitude, data.longitude, data.record_id),
        )

    return {"success": True, "status": data.status}


# --- Get hosteller students (same gender as warden only) ---
@router.get("/students")
def get_students(username: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            "SELECT student_id, name, email, gender, category FROM students WHERE category = 'Hosteller' AND gender = %s ORDER BY name",
            (warden["gender"],),
        )
        students = cursor.fetchall()
    return {"students": students}


# --- Get hostel attendance records (same gender) ---
@router.get("/attendance/records")
def get_attendance_records(username: str = Query(...), date: str = Query(...)):
    warden = None
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("SELECT warden_id, gender FROM wardens WHERE username = %s", (username,))
        warden = cursor.fetchone()
    if not warden:
        raise HTTPException(status_code=401, detail="Warden not found")

    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            """
            SELECT ar.record_id, ar.student_id, ar.type, ar.session, ar.status, ar.date, ar.verified_by,
                   s.name as student_name
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            WHERE ar.type = 'HOSTEL' AND s.category = 'Hosteller' AND s.gender = %s AND ar.date = %s
            ORDER BY s.name
            """,
            (warden["gender"], date),
        )
        records = cursor.fetchall()
    return {"records": records}
