"""
Technical Support Agent — solves platform-related issues.

Capabilities:
- Login problem troubleshooting
- Video streaming fixes
- Upload failure resolution
- Payment/access issue handling
- Automated ticket generation
- Knowledge base search
"""

import google.generativeai as genai

SYSTEM_PROMPT = """You are the Technical Support Agent for an online education platform. You help students resolve platform-related technical issues.

COMMON ISSUES YOU HANDLE:
1. **Login Problems** — password reset, account locked, 2FA issues
2. **Video Streaming** — buffering, not loading, quality issues
3. **Upload Failures** — assignment upload errors, file size limits, format issues
4. **Payment/Access** — payment not reflected, course locked, subscription issues
5. **Browser/App Issues** — compatibility, cache problems, mobile issues
6. **Account Settings** — profile updates, notification preferences, email changes

TROUBLESHOOTING APPROACH:
1. Identify the exact issue
2. Provide step-by-step solution
3. If issue can't be resolved, recommend ticket creation or escalation
4. Be clear, concise, and numbered steps

RESPONSE FORMAT:
- Acknowledge the issue empathetically
- Provide numbered troubleshooting steps
- Include expected outcomes for each step
- Offer alternative solutions if first approach fails
- Suggest escalation if needed

Use markdown formatting. Be professional and supportive.
"""

# Common troubleshooting solutions for fallback
QUICK_SOLUTIONS = {
    "login": (
        "🔐 **Login Troubleshooting**\n\n"
        "Try these steps:\n\n"
        "1. **Clear browser cache** — Press `Ctrl+Shift+Delete` and clear cached data\n"
        "2. **Reset password** — Click 'Forgot Password' on the login page\n"
        "3. **Check email** — Ensure you're using the correct registered email\n"
        "4. **Try incognito mode** — Open a private/incognito window\n"
        "5. **Disable browser extensions** — Ad blockers can interfere\n\n"
        "If the issue persists, I can create a support ticket for you."
    ),
    "video": (
        "🎬 **Video Streaming Fix**\n\n"
        "Try these steps:\n\n"
        "1. **Refresh the page** — Press `F5` or `Ctrl+R`\n"
        "2. **Check internet speed** — Run a speed test (need 5+ Mbps)\n"
        "3. **Lower video quality** — Click the settings gear icon on the player\n"
        "4. **Try a different browser** — Chrome or Firefox recommended\n"
        "5. **Clear browser cache** — `Ctrl+Shift+Delete`\n"
        "6. **Disable VPN** — VPNs can slow streaming\n\n"
        "If buffering continues, the issue may be server-side. I'll create a ticket."
    ),
    "upload": (
        "📤 **Upload Issue Resolution**\n\n"
        "Check these:\n\n"
        "1. **File size** — Maximum upload is 25MB per file\n"
        "2. **File format** — Accepted: PDF, DOCX, ZIP, PNG, JPG\n"
        "3. **Internet connection** — Ensure stable connection during upload\n"
        "4. **Try again** — Close the tab and re-open the upload page\n"
        "5. **Rename file** — Remove special characters from filename\n\n"
        "If the error persists, share the error message and I'll investigate further."
    ),
    "payment": (
        "💳 **Payment/Access Issue**\n\n"
        "Here's what to check:\n\n"
        "1. **Check payment status** — Go to Profile → Billing → Transaction History\n"
        "2. **Wait 24 hours** — Bank processing can take up to 24 hours\n"
        "3. **Check email** — Look for payment confirmation email\n"
        "4. **Verify course enrollment** — Go to Dashboard → My Courses\n\n"
        "If payment was charged but access isn't granted after 24 hours, "
        "I'll escalate this to our billing team immediately."
    ),
}


class TechnicalAgent:
    """Agent for platform technical support."""

    def __init__(self, model=None):
        self.model = model
        self.agent_type = "technical"

    def generate_response(self, query, context=None):
        """Generate a technical support response."""
        if not self.model:
            return self._fallback_response(query)

        try:
            chat_history = []
            if context:
                for msg in context[-6:]:
                    role = "user" if msg.get("role") == "user" else "model"
                    chat_history.append({"role": role, "parts": [msg["content"]]})

            chat = self.model.start_chat(history=chat_history)
            response = chat.send_message(
                f"{SYSTEM_PROMPT}\n\nStudent's Technical Issue: {query}"
            )
            return response.text

        except Exception as e:
            print(f"Technical Agent Error: {e}")
            return self._fallback_response(query)

    def _fallback_response(self, query):
        """Provide troubleshooting help when AI is unavailable."""
        query_lower = query.lower()

        # Match to quick solutions
        for keyword, solution in QUICK_SOLUTIONS.items():
            if keyword in query_lower:
                return solution

        return (
            "🔧 **Technical Support**\n\n"
            f"I understand you're experiencing: *{query[:100]}*\n\n"
            "Here are general troubleshooting steps:\n\n"
            "1. **Refresh the page** — `Ctrl+R` or `F5`\n"
            "2. **Clear browser cache** — `Ctrl+Shift+Delete`\n"
            "3. **Try a different browser** — Chrome recommended\n"
            "4. **Check your internet connection**\n"
            "5. **Try incognito/private mode**\n\n"
            "If the issue persists, please create a **support ticket** "
            "with details about the error message and I'll escalate it.\n\n"
            "*Configure your Gemini API key for more specific troubleshooting.*"
        )
