"""
Seed the database with demo data for testing.
"""

import json
import hashlib
from datetime import datetime, timedelta
from database.models import get_db, init_db


def hash_password(password):
    """Simple password hashing for demo purposes."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_database():
    """Populate the database with sample data."""
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # ── Seed Users ──
    users = [
        ("student1", hash_password("student123"), "Arjun Mehta", "arjun@edu.com", "student", '["CS101", "MATH201"]'),
        ("student2", hash_password("student123"), "Priya Sharma", "priya@edu.com", "student", '["CS101", "ENG102"]'),
        ("student3", hash_password("student123"), "Rahul Kumar", "rahul@edu.com", "student", '["MATH201", "PHY301"]'),
        ("admin", hash_password("admin123"), "Dr. Admin", "admin@edu.com", "admin", '[]'),
        ("faculty1", hash_password("faculty123"), "Prof. Verma", "verma@edu.com", "faculty", '["CS101"]'),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password_hash, display_name, email, role, enrolled_courses) VALUES (?, ?, ?, ?, ?, ?)",
        users
    )

    # ── Seed Courses ──
    courses = [
        ("CS101", "Introduction to Computer Science", "Prof. Verma", "Computer Science", "beginner",
         json.dumps(["Variables & Data Types", "Control Flow", "Functions", "OOP Basics", "Data Structures"])),
        ("MATH201", "Linear Algebra", "Prof. Gupta", "Mathematics", "intermediate",
         json.dumps(["Vectors", "Matrices", "Eigenvalues", "Linear Transformations", "Applications"])),
        ("ENG102", "Technical Writing", "Prof. Singh", "English", "beginner",
         json.dumps(["Grammar Review", "Report Writing", "Documentation", "Research Papers", "Presentations"])),
        ("PHY301", "Quantum Mechanics", "Prof. Das", "Physics", "advanced",
         json.dumps(["Wave Functions", "Schrodinger Equation", "Quantum States", "Entanglement", "Applications"])),
    ]
    cursor.executemany(
        "INSERT INTO courses (title, description, instructor, category, difficulty, modules) VALUES (?, ?, ?, ?, ?, ?)",
        courses
    )

    # ── Seed Conversations with Messages ──
    now = datetime.now()

    # Conversation 1: Course help
    cursor.execute(
        "INSERT INTO conversations (user_id, agent_type, title, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (1, "course", "Help with Recursion", "active", (now - timedelta(hours=2)).isoformat())
    )
    conv1_id = cursor.lastrowid
    cursor.executemany("INSERT INTO messages (conversation_id, role, content, agent_type, created_at) VALUES (?, ?, ?, ?, ?)", [
        (conv1_id, "user", "Can you explain how recursion works in Python?", None, (now - timedelta(hours=2)).isoformat()),
        (conv1_id, "assistant", "Recursion is when a function calls itself to solve a smaller version of the same problem. Think of it like Russian nesting dolls — each doll contains a smaller one inside.\n\n**Key Components:**\n1. **Base Case** — The condition that stops recursion\n2. **Recursive Case** — The function calling itself with a simpler input\n\n**Example:**\n```python\ndef factorial(n):\n    if n <= 1:  # Base case\n        return 1\n    return n * factorial(n - 1)  # Recursive case\n```\n\nWould you like me to walk through more examples or explain the call stack?", "course", (now - timedelta(hours=2, minutes=-1)).isoformat()),
    ])

    # Conversation 2: Assignment help (with guardrail trigger)
    cursor.execute(
        "INSERT INTO conversations (user_id, agent_type, title, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (2, "assignment", "Assignment 3 Question", "active", (now - timedelta(hours=5)).isoformat())
    )
    conv2_id = cursor.lastrowid
    cursor.executemany("INSERT INTO messages (conversation_id, role, content, agent_type, created_at) VALUES (?, ?, ?, ?, ?)", [
        (conv2_id, "user", "I need help understanding question 3 of Assignment 2", None, (now - timedelta(hours=5)).isoformat()),
        (conv2_id, "assistant", "I'd be happy to help you understand the concepts behind Question 3! Let me guide you through the approach without giving the direct answer.\n\nThe question involves sorting algorithms. Here's how to think about it:\n\n1. **Understand what the question asks** — It's about comparing time complexities\n2. **Key concept** — Big-O notation measures worst-case performance\n3. **Hint** — Compare how each algorithm handles already-sorted data\n\nTry working through these steps and let me know where you get stuck! 📚", "assignment", (now - timedelta(hours=5, minutes=-1)).isoformat()),
    ])

    # ── Seed Support Tickets ──
    tickets = [
        (1, "technical", "Video not loading", "Course CS101 Module 3 video shows buffer error", "resolved", "high", "Cleared CDN cache, video restored", (now - timedelta(days=1)).isoformat(), now.isoformat()),
        (2, "access", "Cannot access Assignment 2", "Getting 403 error when opening assignment link", "open", "medium", None, (now - timedelta(hours=3)).isoformat(), None),
        (3, "payment", "Payment not reflected", "Paid for PHY301 but still shows locked", "in_progress", "high", None, (now - timedelta(hours=6)).isoformat(), None),
    ]
    cursor.executemany(
        "INSERT INTO support_tickets (user_id, category, subject, description, status, priority, resolution, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tickets
    )

    # ── Seed Analytics Events ──
    event_types = ["query", "response", "escalation", "guardrail_trigger", "ticket_created", "ticket_resolved"]
    agent_types = ["course", "assignment", "technical", "escalation"]

    import random
    for i in range(50):
        event = random.choice(event_types)
        agent = random.choice(agent_types) if event in ["query", "response"] else None
        user = random.randint(1, 3)
        time_offset = timedelta(hours=random.randint(0, 72))
        resp_time = random.randint(200, 3000) if event == "response" else None

        cursor.execute(
            "INSERT INTO analytics_events (event_type, user_id, agent_type, response_time_ms, created_at) VALUES (?, ?, ?, ?, ?)",
            (event, user, agent, resp_time, (now - time_offset).isoformat())
        )

    # ── Seed Guardrail Violations ──
    violations = [
        (2, "academic_integrity", "Give me the complete answer for Assignment 2 Question 5", "blocked", "high"),
        (1, "academic_integrity", "Solve this exam question for me", "blocked", "high"),
        (3, "toxicity", "This platform is garbage, you stupid bot", "warned", "medium"),
    ]
    cursor.executemany(
        "INSERT INTO guardrail_violations (user_id, violation_type, original_query, action_taken, severity) VALUES (?, ?, ?, ?, ?)",
        violations
    )

    conn.commit()
    conn.close()
    print("[OK] Database seeded successfully!")


if __name__ == "__main__":
    seed_database()
