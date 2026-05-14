"""
Monitoring & Analytics Tracker for the Online Education Platform.

Tracks:
- Query/response events
- Response times
- Escalation rates
- Guardrail violations
- Student satisfaction
- AI performance metrics
"""

import time
from datetime import datetime, timedelta
from database.models import get_db, dicts_from_rows


class MonitoringTracker:
    """Tracks and reports platform metrics."""

    def __init__(self):
        self._timers = {}

    def start_timer(self, request_id):
        """Start a response-time timer for a request."""
        self._timers[request_id] = time.time()

    def stop_timer(self, request_id):
        """Stop a timer and return elapsed milliseconds."""
        start = self._timers.pop(request_id, None)
        if start:
            return int((time.time() - start) * 1000)
        return None

    def log_event(self, event_type, user_id=None, agent_type=None, metadata=None, response_time_ms=None):
        """Log an analytics event to the database."""
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO analytics_events (event_type, user_id, agent_type, metadata, response_time_ms) VALUES (?, ?, ?, ?, ?)",
                (event_type, user_id, agent_type, str(metadata or {}), response_time_ms)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Monitoring log error: {e}")

    def log_violation(self, user_id, violation_type, query, action, severity="medium"):
        """Log a guardrail violation to the database."""
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO guardrail_violations (user_id, violation_type, original_query, action_taken, severity) VALUES (?, ?, ?, ?, ?)",
                (user_id, violation_type, query[:500], action, severity)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Violation log error: {e}")

    def get_dashboard_stats(self):
        """Get aggregate statistics for the admin dashboard."""
        conn = get_db()
        stats = {}

        # Total queries
        row = conn.execute("SELECT COUNT(*) as count FROM analytics_events WHERE event_type = 'query'").fetchone()
        stats["total_queries"] = row["count"] if row else 0

        # Total escalations
        row = conn.execute("SELECT COUNT(*) as count FROM escalations").fetchone()
        stats["total_escalations"] = row["count"] if row else 0

        # Escalation rate
        row = conn.execute("SELECT COUNT(*) as count FROM analytics_events WHERE event_type = 'escalation'").fetchone()
        escalation_count = row["count"] if row else 0
        stats["escalation_rate"] = round((escalation_count / max(stats["total_queries"], 1)) * 100, 1)

        # Average response time
        row = conn.execute("SELECT AVG(response_time_ms) as avg_time FROM analytics_events WHERE response_time_ms IS NOT NULL").fetchone()
        stats["avg_response_time_ms"] = round(row["avg_time"]) if row and row["avg_time"] else 0

        # Total violations
        row = conn.execute("SELECT COUNT(*) as count FROM guardrail_violations").fetchone()
        stats["total_violations"] = row["count"] if row else 0

        # Open tickets
        row = conn.execute("SELECT COUNT(*) as count FROM support_tickets WHERE status != 'resolved'").fetchone()
        stats["open_tickets"] = row["count"] if row else 0

        # Total users
        row = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'").fetchone()
        stats["total_students"] = row["count"] if row else 0

        # Resolved tickets
        row = conn.execute("SELECT COUNT(*) as count FROM support_tickets WHERE status = 'resolved'").fetchone()
        stats["resolved_tickets"] = row["count"] if row else 0

        # Queries by agent type
        rows = conn.execute(
            "SELECT agent_type, COUNT(*) as count FROM analytics_events WHERE event_type = 'query' AND agent_type IS NOT NULL GROUP BY agent_type"
        ).fetchall()
        stats["queries_by_agent"] = {row["agent_type"]: row["count"] for row in rows}

        # Recent events
        rows = conn.execute(
            "SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        stats["recent_events"] = dicts_from_rows(rows)

        # Recent violations
        rows = conn.execute(
            "SELECT * FROM guardrail_violations ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        stats["recent_violations"] = dicts_from_rows(rows)

        # Response time trend (last 7 data points)
        rows = conn.execute("""
            SELECT 
                DATE(created_at) as date, 
                AVG(response_time_ms) as avg_time,
                COUNT(*) as count
            FROM analytics_events 
            WHERE response_time_ms IS NOT NULL 
            GROUP BY DATE(created_at) 
            ORDER BY date DESC 
            LIMIT 7
        """).fetchall()
        stats["response_time_trend"] = dicts_from_rows(rows)

        # Satisfaction score (simulated based on escalation rate)
        stats["satisfaction_score"] = max(0, min(100, 100 - stats["escalation_rate"] * 2 - stats["total_violations"] * 3))

        conn.close()
        return stats


# Singleton instance
tracker = MonitoringTracker()
