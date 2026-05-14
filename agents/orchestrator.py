"""
AI Orchestrator — Central controller and decision engine.

Responsibilities:
1. Intent Detection — classify queries into agent categories
2. Context Management — maintain conversation history
3. Agent Routing — dispatch to specialized agents
4. Policy Enforcement — run guardrails before and after
5. Escalation Handling — detect and manage escalations
"""

import os
import google.generativeai as genai
from agents.course_agent import CourseAgent
from agents.assignment_agent import AssignmentAgent
from agents.technical_agent import TechnicalAgent
from agents.escalation_agent import EscalationAgent
from guardrails.safety import guardrails
from monitoring.tracker import tracker


# Intent classification keywords
INTENT_KEYWORDS = {
    "course": [
        "explain", "concept", "understand", "what is", "how does", "teach me",
        "learn", "study", "tutorial", "theory", "definition", "example of",
        "tell me about", "describe", "course", "topic", "subject", "module",
        "recursion", "algorithm", "data structure", "programming", "math",
        "physics", "chemistry", "biology", "history", "literature",
        "study plan", "resources", "recommend", "guide me"
    ],
    "assignment": [
        "assignment", "homework", "quiz", "exam", "test", "project",
        "question", "problem set", "lab", "exercise", "graded",
        "submission", "due date", "deadline", "marks", "rubric",
        "help with assignment", "assignment help", "hint", "guidance",
        "how to approach", "clarification"
    ],
    "technical": [
        "login", "password", "video", "buffering", "upload", "download",
        "error", "bug", "crash", "loading", "slow", "not working",
        "broken", "payment", "access", "locked", "subscription",
        "account", "profile", "settings", "browser", "app", "mobile",
        "notification", "email", "certificate", "reset", "install"
    ],
    "escalation": [
        "human", "person", "agent", "supervisor", "manager",
        "escalate", "complaint", "frustrated", "angry", "terrible",
        "wrong grade", "grade dispute", "unfair", "unacceptable",
        "speak to someone", "real person", "not helpful"
    ]
}


class GrokChat:
    def __init__(self, history):
        self.history = history

    def send_message(self, prompt):
        import os
        import requests
        
        grok_api_key = os.getenv("GROK_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {grok_api_key}"
        }
        
        messages = []
        if self.history:
            for msg in self.history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["parts"][0]})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "messages": messages,
            "model": "grok-2-latest",
            "stream": False,
            "temperature": 0.3
        }
        
        class Response:
            def __init__(self, text):
                self.text = text
                
        try:
            res = requests.post("https://api.x.ai/v1/chat/completions", json=data, headers=headers, timeout=15)
            res.raise_for_status()
            result_data = res.json()
            answer = result_data["choices"][0]["message"]["content"]
            return Response(answer)
        except Exception as e:
            print(f"Grok API Error: {e}")
            if 'res' in locals():
                print(f"Response: {res.text}")
            raise e

class DualChat:
    def __init__(self, history, gemini_chat, grok_chat):
        self.history = history
        self.gemini_chat = gemini_chat
        self.grok_chat = grok_chat

    def send_message(self, prompt):
        # Attempt Gemini first if available
        if self.gemini_chat:
            try:
                return self.gemini_chat.send_message(prompt)
            except Exception as e:
                print(f"[WARN] Gemini send_message failed: {e}. Falling back to Grok.")
        
        # Fallback to Grok if Gemini fails or is missing
        if self.grok_chat:
            try:
                return self.grok_chat.send_message(prompt)
            except Exception as e:
                print(f"[WARN] Grok send_message failed: {e}.")
        
        raise Exception("Both Gemini and Grok models failed or are missing.")

class DualModel:
    def __init__(self, use_gemini=True, use_grok=True):
        self.use_gemini = use_gemini
        self.use_grok = use_grok
        
    def start_chat(self, history=None):
        gemini_chat = None
        if self.use_gemini:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-2.5-flash")
            gemini_chat = model.start_chat(history=history)
            
        grok_chat = GrokChat(history) if self.use_grok else None
        
        return DualChat(history, gemini_chat, grok_chat)


class Orchestrator:
    """Central AI orchestrator that routes queries to specialized agents."""

    def __init__(self):
        self.model = None
        self._init_models()

        # Initialize all agents
        self.agents = {
            "course": CourseAgent(self.model),
            "assignment": AssignmentAgent(self.model),
            "technical": TechnicalAgent(self.model),
            "escalation": EscalationAgent(self.model),
        }

    def _init_models(self):
        """Initialize the DualModel with available API keys."""
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        grok_key = os.getenv("GROK_API_KEY", "")
        
        use_gemini = bool(gemini_key and gemini_key != "your_gemini_api_key_here")
        use_grok = bool(grok_key and grok_key != "your_grok_api_key_here")
        
        if use_gemini:
            try:
                genai.configure(api_key=gemini_key)
                print("[OK] Gemini AI API key configured")
            except Exception as e:
                print(f"[WARN] Gemini configuration failed: {e}")
                use_gemini = False
                
        if use_grok:
            print("[OK] Grok AI API key configured")
            
        if use_gemini or use_grok:
            self.model = DualModel(use_gemini=use_gemini, use_grok=use_grok)
            print("[OK] DualModel initialized successfully")
        else:
            print("[WARN] No valid AI API keys found. Running in fallback mode.")

    def detect_intent(self, query):
        """
        Detect the intent of a student query using the AI model, with keyword fallback.
        Returns the agent type to route to.
        """
        # Step 1: Try AI-based routing first
        if self.model:
            try:
                chat = self.model.start_chat()
                prompt = (
                    "Classify the following student query into exactly one of these categories: "
                    "'course', 'assignment', 'technical', 'escalation'.\n"
                    "- course: general questions, concepts, tutorials, study plans.\n"
                    "- assignment: homework, graded work, hints, exams, rubrics.\n"
                    "- technical: login issues, video buffering, app bugs, payments.\n"
                    "- escalation: complaining, angry, wants to speak to a human.\n\n"
                    "Respond with ONLY the category name in lowercase and absolutely no other text.\n\n"
                    f"Query: {query}"
                )
                response = chat.send_message(prompt)
                
                import re
                # Clean up response (remove punctuation, whitespace, backticks)
                intent = re.sub(r'[^a-z]', '', response.text.strip().lower())
                
                if intent in INTENT_KEYWORDS:
                    print(f"[*] LLM successfully routed query to: {intent}")
                    return intent
                else:
                    print(f"[WARN] LLM returned invalid intent: '{intent}'. Falling back to keywords.")
            except Exception as e:
                print(f"[WARN] LLM intent routing failed: {e}. Falling back to keywords.")

        # Step 2: Keyword Fallback
        query_lower = query.lower().strip()
        scores = {intent: 0 for intent in INTENT_KEYWORDS}

        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent] += 1
                    # Boost for exact phrase matches
                    if len(keyword.split()) > 1:
                        scores[intent] += 1

        # Get the highest scoring intent
        best_intent = max(scores, key=scores.get)

        # If no strong match, default to course guidance
        if scores[best_intent] == 0:
            return "course"

        print(f"[*] Keyword router selected: {best_intent}")
        return best_intent

    def process_query(self, query, user_id=None, context=None):
        """
        Process a student query through the full pipeline:
        1. Guardrails check (input)
        2. Intent detection
        3. Escalation check
        4. Agent routing
        5. Guardrails check (output)
        6. Monitoring log
        """
        import uuid
        request_id = str(uuid.uuid4())[:8]
        tracker.start_timer(request_id)

        result = {
            "response": "",
            "agent_type": "orchestrator",
            "intent": None,
            "guardrail_triggered": False,
            "escalated": False,
            "metadata": {}
        }

        # Step 1: Input guardrails
        violation = guardrails.validate_input(query, user_id)
        if violation:
            result["response"] = violation["message"]
            result["guardrail_triggered"] = True
            result["metadata"]["violation_type"] = violation["type"]

            # Log violation
            tracker.log_violation(
                user_id, violation["type"], query,
                "blocked", violation.get("severity", "medium")
            )
            tracker.log_event("guardrail_trigger", user_id, metadata={"type": violation["type"]})

            # Check if escalation is needed post-violation
            esc_agent = self.agents["escalation"]
            should_esc, esc_reason = esc_agent.should_escalate(query, context, violation)
            if should_esc:
                result["escalated"] = True
                result["metadata"]["escalation_reason"] = esc_reason

            response_time = tracker.stop_timer(request_id)
            tracker.log_event("response", user_id, "guardrails", response_time_ms=response_time)
            return result

        # Step 2: Detect intent
        intent = self.detect_intent(query)
        result["intent"] = intent

        # Step 3: Check for escalation
        esc_agent = self.agents["escalation"]
        should_esc, esc_reason = esc_agent.should_escalate(query, context)
        if should_esc:
            result["response"] = esc_agent.generate_escalation_response(esc_reason, query, context)
            result["agent_type"] = "escalation"
            result["escalated"] = True
            result["metadata"]["escalation_reason"] = esc_reason

            tracker.log_event("escalation", user_id, "escalation", metadata={"reason": esc_reason})
            response_time = tracker.stop_timer(request_id)
            tracker.log_event("response", user_id, "escalation", response_time_ms=response_time)
            return result

        # Step 4: Route to specialized agent
        agent = self.agents.get(intent, self.agents["course"])
        result["agent_type"] = agent.agent_type

        tracker.log_event("query", user_id, agent.agent_type)

        try:
            response_text = agent.generate_response(query, context)
        except Exception as e:
            response_text = (
                "I apologize, but I encountered an issue processing your request. "
                "Please try again or contact support if the problem persists."
            )
            print(f"Agent error: {e}")

        # Step 5: Output guardrails
        is_safe, filter_reason = guardrails.validate_output(response_text)
        if not is_safe:
            response_text = (
                "📝 I have guidance to share but need to ensure it aligns with our academic "
                "integrity policies. Let me rephrase:\n\n"
                "I can help you **understand the concept** behind this problem. "
                "Could you tell me which specific part you're struggling with?"
            )

        result["response"] = response_text

        # Step 6: Log monitoring
        response_time = tracker.stop_timer(request_id)
        tracker.log_event("response", user_id, agent.agent_type, response_time_ms=response_time)

        return result

