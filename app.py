import os
import json
import hashlib
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "edu-platform-secret-key-2024")

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://onlineeducationplatform.up.railway.app",
    "https://online-education-platform.vercel.app"  # replace with your actual vercel url
])

from database.models import init_db, get_db, dict_from_row, dicts_from_rows
from database.seed import seed_database
from agents.orchestrator import Orchestrator
from monitoring.tracker import tracker

orchestrator = Orchestrator()

# Initialize database on startup (works with gunicorn)
init_db()
seed_database()


# ── Helper Functions ──

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Static Files ──

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Auth Routes ──

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_dict = dict_from_row(user)
    session["user_id"] = user_dict["id"]
    session["username"] = user_dict["username"]
    session["role"] = user_dict["role"]
    session["display_name"] = user_dict["display_name"]

    conn = get_db()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                 (datetime.now().isoformat(), user_dict["id"]))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "display_name": user_dict["display_name"],
            "role": user_dict["role"],
            "email": user_dict["email"],
            "enrolled_courses": json.loads(user_dict.get("enrolled_courses", "[]"))
        }
    })


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    display_name = data.get("display_name", "").strip()
    email = data.get("email", "").strip()

    if not all([username, password, display_name]):
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username already exists"}), 409

    conn.execute(
        "INSERT INTO users (username, password_hash, display_name, email, role) VALUES (?, ?, ?, ?, ?)",
        (username, hash_password(password), display_name, email, "student")
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Registration successful. Please login."}), 201


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 401

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 401

    user_dict = dict_from_row(user)
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "display_name": user_dict["display_name"],
            "role": user_dict["role"],
            "email": user_dict["email"],
            "enrolled_courses": json.loads(user_dict.get("enrolled_courses", "[]"))
        }
    })


# ── Chat Routes ──

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.json
    query = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")

    if not query:
        return jsonify({"error": "Message is required"}), 400

    user_id = session["user_id"]
    context = []

    conn = get_db()
    if conversation_id:
        messages = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        ).fetchall()
        context = dicts_from_rows(messages)
    else:
        conn.execute(
            "INSERT INTO conversations (user_id, agent_type, title) VALUES (?, ?, ?)",
            (user_id, "orchestrator", query[:80])
        )
        conn.commit()
        conversation_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, "user", query)
    )
    conn.commit()
    conn.close()

    result = orchestrator.process_query(query, user_id, context)

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, agent_type) VALUES (?, ?, ?, ?)",
        (conversation_id, "assistant", result["response"], result["agent_type"])
    )
    conn.execute(
        "UPDATE conversations SET agent_type = ?, updated_at = ? WHERE id = ?",
        (result["agent_type"], datetime.now().isoformat(), conversation_id)
    )

    if result.get("escalated"):
        conn.execute(
            "INSERT INTO escalations (conversation_id, user_id, reason, summary, priority) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, user_id, result["metadata"].get("escalation_reason", "unknown"),
             query[:200], "high" if result.get("guardrail_triggered") else "medium")
        )

    conn.commit()
    conn.close()

    return jsonify({
        "response": result["response"],
        "conversation_id": conversation_id,
        "agent_type": result["agent_type"],
        "intent": result.get("intent"),
        "guardrail_triggered": result.get("guardrail_triggered", False),
        "escalated": result.get("escalated", False)
    })


# ── Conversation Routes ──

@app.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():
    conn = get_db()
    conversations = conn.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 20",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify({"conversations": dicts_from_rows(conversations)})


@app.route("/api/conversations/<int:conv_id>/messages", methods=["GET"])
@login_required
def get_messages(conv_id):
    conn = get_db()
    messages = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,)
    ).fetchall()
    conn.close()
    return jsonify({"messages": dicts_from_rows(messages)})


# ── Ticket Routes ──

@app.route("/api/tickets", methods=["GET"])
@login_required
def get_tickets():
    conn = get_db()
    if session.get("role") == "admin":
        tickets = conn.execute("SELECT * FROM support_tickets ORDER BY created_at DESC").fetchall()
    else:
        tickets = conn.execute(
            "SELECT * FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC",
            (session["user_id"],)
        ).fetchall()
    conn.close()
    return jsonify({"tickets": dicts_from_rows(tickets)})


@app.route("/api/tickets", methods=["POST"])
@login_required
def create_ticket():
    data = request.json
    category = data.get("category", "general")
    subject = data.get("subject", "").strip()
    description = data.get("description", "").strip()

    if not subject:
        return jsonify({"error": "Subject is required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO support_tickets (user_id, category, subject, description) VALUES (?, ?, ?, ?)",
        (session["user_id"], category, subject, description)
    )
    conn.commit()
    ticket_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    tracker.log_event("ticket_created", session["user_id"], metadata={"category": category})

    return jsonify({"message": "Ticket created", "ticket_id": ticket_id}), 201


# ── Escalation Routes ──

@app.route("/api/escalate", methods=["POST"])
@login_required
def escalate():
    data = request.json
    conversation_id = data.get("conversation_id")
    reason = data.get("reason", "student_request")

    conn = get_db()
    conn.execute(
        "INSERT INTO escalations (conversation_id, user_id, reason, summary, priority) VALUES (?, ?, ?, ?, ?)",
        (conversation_id or 0, session["user_id"], reason,
         data.get("summary", "Student requested escalation"), "high")
    )
    conn.commit()
    conn.close()

    tracker.log_event("escalation", session["user_id"], "escalation", metadata={"reason": reason})

    return jsonify({
        "message": "Escalated to human support",
        "estimated_wait": "2-5 minutes"
    })


# ── Course Routes ──

@app.route("/api/courses", methods=["GET"])
@login_required
def get_courses():
    conn = get_db()
    courses = conn.execute("SELECT * FROM courses ORDER BY title").fetchall()
    conn.close()
    return jsonify({"courses": dicts_from_rows(courses)})


# ── Admin Routes ──

@app.route("/api/admin/stats", methods=["GET"])
@login_required
def admin_stats():
    if session.get("role") not in ("admin", "faculty"):
        return jsonify({"error": "Admin access required"}), 403
    stats = tracker.get_dashboard_stats()
    return jsonify(stats)


@app.route("/api/admin/escalations", methods=["GET"])
@login_required
def admin_escalations():
    if session.get("role") not in ("admin", "faculty"):
        return jsonify({"error": "Admin access required"}), 403

    conn = get_db()
    escalations = conn.execute(
        "SELECT e.*, u.display_name FROM escalations e JOIN users u ON e.user_id = u.id ORDER BY e.created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify({"escalations": dicts_from_rows(escalations)})


@app.route("/api/admin/violations", methods=["GET"])
@login_required
def admin_violations():
    if session.get("role") not in ("admin", "faculty"):
        return jsonify({"error": "Admin access required"}), 403

    conn = get_db()
    violations = conn.execute(
        "SELECT * FROM guardrail_violations ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify({"violations": dicts_from_rows(violations)})


# ── Initialize & Run ──

if __name__ == "__main__":
    print("[*] Starting server at http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

