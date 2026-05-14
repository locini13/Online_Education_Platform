"""
Escalation Agent — handles complex or sensitive cases requiring human intervention.

Triggers:
- AI uncertainty / cannot resolve
- Repeated student frustration
- Grading disputes
- Abuse or harassment (after guardrail block)
- Policy-sensitive issues

Provides human handoff with:
- Conversation history summary
- Query classification
- Suggested actions
"""


class EscalationAgent:
    """Agent for managing escalation to human support."""

    def __init__(self, model=None):
        self.model = model
        self.agent_type = "escalation"

    def should_escalate(self, query, context=None, violation=None):
        """
        Determine if a conversation should be escalated.
        Returns (should_escalate: bool, reason: str).
        """
        query_lower = query.lower()

        # Direct escalation requests
        escalation_phrases = [
            "talk to a human", "speak to someone", "real person",
            "human agent", "escalate", "supervisor", "manager",
            "not helpful", "this isn't working", "connect me to",
            "human support", "speak to agent", "real support"
        ]
        for phrase in escalation_phrases:
            if phrase in query_lower:
                return True, "student_request"

        # Grading disputes
        grading_phrases = [
            "wrong grade", "grading error", "grade dispute",
            "unfair grade", "regrading", "grade appeal",
            "my grade is wrong", "incorrect marks"
        ]
        for phrase in grading_phrases:
            if phrase in query_lower:
                return True, "grading_dispute"

        # Repeated frustration (check context for frustrated messages)
        if context and len(context) >= 4:
            frustration_count = 0
            for msg in context[-4:]:
                if msg.get("role") == "user":
                    content = msg.get("content", "").lower()
                    if any(w in content for w in ["frustrated", "angry", "annoyed", "terrible", "worst", "horrible", "useless"]):
                        frustration_count += 1
            if frustration_count >= 2:
                return True, "repeated_frustration"

        # Post-violation escalation
        if violation:
            return True, "policy_violation"

        return False, None

    def generate_escalation_response(self, reason, query, context=None):
        """Generate an escalation message for the student."""
        reason_messages = {
            "student_request": (
                "👤 **Connecting to Human Support**\n\n"
                "I'm transferring you to a human support agent. Here's what happens next:\n\n"
                "1. ✅ Your conversation history has been saved\n"
                "2. 📋 A summary has been prepared for the agent\n"
                "3. ⏳ Expected wait time: **2-5 minutes**\n"
                "4. 🔔 You'll receive a notification when connected\n\n"
                "Your ticket has been prioritized. A support agent will assist you shortly."
            ),
            "grading_dispute": (
                "📊 **Grading Dispute — Escalated**\n\n"
                "I understand you have a concern about your grade. "
                "This requires human review from the academic team.\n\n"
                "**What's happening:**\n"
                "1. ✅ Your concern has been logged\n"
                "2. 📋 Conversation forwarded to the grading team\n"
                "3. 🎯 Priority: **High**\n"
                "4. ⏳ Expected response: **Within 24 hours**\n\n"
                "A faculty member or grading coordinator will review your case. "
                "You'll receive an email update."
            ),
            "repeated_frustration": (
                "🤝 **We Want to Help Better**\n\n"
                "I sense that my responses haven't been meeting your needs, "
                "and I sincerely apologize for the frustration.\n\n"
                "I'm connecting you with a **human support specialist** who can provide "
                "more personalized assistance.\n\n"
                "1. ✅ Your full conversation has been preserved\n"
                "2. 📋 The agent will have full context\n"
                "3. ⏳ Expected wait: **2-5 minutes**\n\n"
                "Thank you for your patience."
            ),
            "policy_violation": (
                "⚠️ **Escalated for Review**\n\n"
                "Your recent interaction has been flagged for review by our support team. "
                "A human agent will follow up if needed.\n\n"
                "In the meantime, I'm happy to help with any learning-related questions."
            ),
        }

        return reason_messages.get(reason, reason_messages["student_request"])

    def prepare_handoff_summary(self, query, context=None, reason=None):
        """Prepare a summary for the human agent receiving the escalation."""
        summary = {
            "escalation_reason": reason,
            "student_query": query,
            "conversation_length": len(context) if context else 0,
            "recent_messages": [],
        }

        if context:
            for msg in context[-5:]:
                summary["recent_messages"].append({
                    "role": msg.get("role"),
                    "content": msg.get("content", "")[:200],
                })

        return summary
