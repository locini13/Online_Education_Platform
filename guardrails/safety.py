"""
Guardrails & Safety Engine for the Online Education Platform.

Implements:
1. Academic Integrity Filter — blocks cheating attempts
2. Toxicity Detection — blocks harassment and abuse
3. Prompt Injection Detection — prevents jailbreak attacks
4. Privacy Validator — prevents student data leakage
5. Output Moderation — final safety check on AI responses
"""

import re
from datetime import datetime


# ── Academic Integrity Patterns ──
CHEATING_PATTERNS = [
    r"\b(solve|complete|finish|do)\b.*\b(assignment|homework|quiz|exam|test|project)\b",
    r"\b(give|provide|send|write)\b.*\b(answer|solution|code|essay|submission)\b",
    r"\b(full|complete|entire|whole)\b.*\b(answer|solution|code|assignment|homework)\b",
    r"\bsolve\s+(question|problem|q)\s*\d+\b",
    r"\bwrite\s+(my|the|this)\b.*\b(essay|report|paper|code|program)\b",
    r"\bcopy\s*paste\b.*\b(answer|solution)\b",
    r"\bdo\s+(my|this|the)\s+(homework|assignment|project|lab)\b",
    r"\bjust\s+give\s+(me\s+)?(the\s+)?answer\b",
]

# ── Toxicity Patterns ──
TOXICITY_PATTERNS = [
    r"\b(stupid|idiot|dumb|useless|garbage|trash|pathetic)\b.*\b(bot|ai|system|platform|app)\b",
    r"\b(hate|kill|die|destroy|attack)\b",
    r"\b(shut\s*up|go\s*away|f\s*u\s*c\s*k|s\s*h\s*i\s*t|a\s*s\s*s)\b",
    r"\b(harassment|threaten|bully|abuse)\b",
]

# ── Prompt Injection Patterns ──
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"pretend\s+(to\s+be|you\s+are)",
    r"disregard\s+(your|all)\s+(rules|guidelines|instructions)",
    r"override\s+(safety|guardrails|filters|restrictions)",
    r"jailbreak",
    r"DAN\s+mode",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"system\s*prompt",
]

# ── Privacy-sensitive terms ──
PRIVACY_PATTERNS = [
    r"\b(ssn|social\s+security|tax\s+id)\b",
    r"\b(password|credentials|login\s+details)\b.*\b(other|another|someone)\b",
    r"\bshow\s+me\s+.*\b(grades|records|data)\s+of\s+",
    r"\baccess\s+.*\bstudent\s+(records|data|information|profile)\b",
]


class GuardrailsEngine:
    """Central guardrails engine that validates all inputs and outputs."""

    def __init__(self):
        self.violations_log = []

    def check_academic_integrity(self, text):
        """
        Check if the query attempts to cheat on assignments.
        Returns (is_safe, violation_details).
        """
        text_lower = text.lower().strip()

        for pattern in CHEATING_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return False, {
                    "type": "academic_integrity",
                    "matched_pattern": match.group(),
                    "severity": "high",
                    "message": (
                        "🎓 **Academic Integrity Notice**\n\n"
                        "I can't provide direct answers or complete solutions for graded work. "
                        "However, I'm here to help you **learn**!\n\n"
                        "I can:\n"
                        "- 💡 Explain the underlying concepts\n"
                        "- 🔍 Walk you through similar examples\n"
                        "- 📝 Give you hints to guide your thinking\n"
                        "- 📚 Suggest learning resources\n\n"
                        "Would you like me to help you understand the concept instead?"
                    )
                }

        return True, None

    def check_toxicity(self, text):
        """
        Check for harassment, abuse, or inappropriate content.
        Returns (is_safe, violation_details).
        """
        text_lower = text.lower().strip()

        for pattern in TOXICITY_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return False, {
                    "type": "toxicity",
                    "matched_pattern": match.group(),
                    "severity": "medium",
                    "message": (
                        "⚠️ **Respectful Communication**\n\n"
                        "I'm here to help you learn and succeed. "
                        "Let's keep our conversation respectful and productive.\n\n"
                        "If you're frustrated, I completely understand — "
                        "let me know what's bothering you and I'll do my best to help. "
                        "You can also escalate to a human support agent if you prefer."
                    )
                }

        return True, None

    def check_prompt_injection(self, text):
        """
        Detect prompt injection and jailbreak attempts.
        Returns (is_safe, violation_details).
        """
        text_lower = text.lower().strip()

        for pattern in INJECTION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return False, {
                    "type": "prompt_injection",
                    "matched_pattern": match.group(),
                    "severity": "high",
                    "message": (
                        "🛡️ **Safety Notice**\n\n"
                        "I operate within established educational guidelines to provide "
                        "the best learning experience. I can't modify my operational parameters.\n\n"
                        "How can I help you with your studies today?"
                    )
                }

        return True, None

    def check_privacy(self, text):
        """
        Check for attempts to access other students' private data.
        Returns (is_safe, violation_details).
        """
        text_lower = text.lower().strip()

        for pattern in PRIVACY_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return False, {
                    "type": "privacy",
                    "matched_pattern": match.group(),
                    "severity": "high",
                    "message": (
                        "🔒 **Privacy Protection**\n\n"
                        "I can't share or access other students' personal information, "
                        "grades, or records. This data is protected under our privacy policy "
                        "(aligned with GDPR & FERPA).\n\n"
                        "I can only help you with your own academic queries. "
                        "How can I assist you today?"
                    )
                }

        return True, None

    def validate_input(self, text, user_id=None):
        """
        Run all input guardrails. Returns the first violation found, or None if safe.
        """
        checks = [
            self.check_prompt_injection,
            self.check_academic_integrity,
            self.check_toxicity,
            self.check_privacy,
        ]

        for check_fn in checks:
            is_safe, violation = check_fn(text)
            if not is_safe:
                violation["user_id"] = user_id
                violation["original_query"] = text[:200]
                violation["timestamp"] = datetime.now().isoformat()
                self.violations_log.append(violation)
                return violation

        return None

    def validate_output(self, response_text):
        """
        Validate AI output before sending to the student.
        Ensures no accidental data leakage or unsafe content.
        """
        # Check if response accidentally contains assignment solutions
        solution_indicators = [
            r"here\s+is\s+the\s+(complete|full|final)\s+(solution|answer|code)",
            r"the\s+answer\s+(is|to\s+the\s+assignment)\s*:",
            r"submit\s+this\s+(as|for)\s+your\s+(assignment|homework)",
        ]

        for pattern in solution_indicators:
            if re.search(pattern, response_text.lower()):
                return False, "Response contained potential assignment solution. Filtered."

        return True, None

    def get_recent_violations(self, limit=20):
        """Get recent guardrail violations from the log."""
        return self.violations_log[-limit:]


# Singleton instance
guardrails = GuardrailsEngine()
