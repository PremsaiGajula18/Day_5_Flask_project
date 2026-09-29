import os
import uuid
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, url_for
from werkzeug.utils import secure_filename

# Read database settings from .env file
load_dotenv()

app = Flask(__name__)

# Configure upload directory for storing physical photos on disk
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Enforce 2 MB upload limit
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# Fallback in-memory list for registered users
registered_users = []


def allowed_file(filename):
    """Check if the uploaded file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle files exceeding the 2 MB limit."""
    return jsonify({
        "status": "error",
        "message": "File size exceeds the 2 MB limit."
    }), 413


def get_db():
    """Create and return a MySQL connection, or None if unavailable."""
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "student_registration"),
        )
    except Exception as e:
        print("Database connection error:", e)
        return None


def fetch_all_students():
    """Fetch all students from MySQL database, with in-memory fallback."""
    conn = get_db()
    if not conn:
        return registered_users

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, email, phone, dob, gender, course, qualification,
                   training_mode, skills, experience, address, website, photo, created_at
            FROM students ORDER BY id DESC
        """)
        data = cursor.fetchall()
        return data if data else registered_users
    except Exception as e:
        print("Database query error:", e)
        return registered_users
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


# Route 1: Home Page (renders registration form)
@app.route("/")
def home():
    return render_template("register.html")


# Route 2: Registration Page
@app.route("/register")
def register_page():
    return render_template("register.html")


# Route 3: API Endpoint — Receive complete registration form data + photo file
@app.route("/api/register", methods=["POST"])
def api_register():
    # Support both FormData (multipart/form-data) and JSON payloads
    if request.is_json:
        data = request.get_json() or {}
        uploaded_file = None
        photo_filename = data.get("photo", "").strip()
    else:
        data = request.form.to_dict()
        uploaded_file = request.files.get("photo")
        photo_filename = ""

    # Extract all fields
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    dob = data.get("dob", "").strip()
    gender = data.get("gender", "").strip()
    course = data.get("course", "").strip()
    qualification = data.get("qualification", "").strip()
    training_mode = data.get("training_mode", "").strip()
    skills = data.get("skills", "").strip()
    experience = int(data.get("experience", 0) or 0)
    address = data.get("address", "").strip()
    website = data.get("website", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    agree = data.get("agree") in [True, "true", "True", "on", "1", 1]

    # Server-side validation
    if not name or not email or not phone or not dob or not gender or not course or not qualification or not training_mode or not skills or not address or not password:
        return jsonify({
            "status": "error",
            "message": "Please fill in all required fields."
        }), 400

    if password != confirm_password:
        return jsonify({
            "status": "error",
            "message": "Password and Confirm Password do not match."
        }), 400

    if not agree:
        return jsonify({
            "status": "error",
            "message": "You must agree to the registration terms."
        }), 400

    # Handle actual physical file saving to static/uploads/
    saved_photo = ""
    if uploaded_file and uploaded_file.filename != "":
        if not allowed_file(uploaded_file.filename):
            return jsonify({
                "status": "error",
                "message": "Invalid photo format. Only JPEG or PNG under 2 MB allowed."
            }), 400

        # Create safe, unique filename (e.g., e7a2f1b4_myphoto.png)
        clean_name = secure_filename(uploaded_file.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        
        # Save physical file to disk
        uploaded_file.save(file_path)
        saved_photo = unique_name
    elif photo_filename:
        saved_photo = photo_filename

    user = {
        "id": len(registered_users) + 1,
        "name": name,
        "email": email,
        "phone": phone,
        "dob": dob,
        "gender": gender,
        "course": course,
        "qualification": qualification,
        "training_mode": training_mode,
        "skills": skills,
        "experience": experience,
        "address": address,
        "website": website,
        "photo": saved_photo,
    }

    # Persist record in MySQL database
    conn = get_db()
    if conn:
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (
                    name, email, phone, dob, gender, course, qualification,
                    training_mode, skills, experience, address, website, photo, password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, email, phone, dob, gender, course, qualification,
                training_mode, skills, experience, address, website, saved_photo, password
            ))
            conn.commit()
            user["id"] = cursor.lastrowid
        except Exception as e:
            print("MySQL insert error:", e)
        finally:
            if cursor:
                cursor.close()
            conn.close()

    # Keep in-memory list as well
    registered_users.append(user)

    return jsonify({
        "status": "success",
        "message": f"{name} registered successfully!",
        "user": user,
    })


# Route 4: All students display page
@app.route("/users")
def users_page():
    students = fetch_all_students()
    return render_template("users.html", users=students)


# Route 5: API Endpoint — Get all users as JSON
@app.route("/api/users", methods=["GET"])
def api_get_users():
    students = fetch_all_students()
    return jsonify({
        "status": "success",
        "count": len(students),
        "users": students,
    })


if __name__ == "__main__":
    app.run(debug=True)
