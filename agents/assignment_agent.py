"""
Assignment Help Agent — guides students without giving direct answers.

Capabilities:
- Concept clarification for assignments
- Hint generation
- Example walkthroughs (non-assignment)
- Guided problem-solving

Restrictions:
- NEVER gives direct answers
- NEVER completes assignments
- NEVER writes full solutions
"""

import google.generativeai as genai

SYSTEM_PROMPT = """You are the Assignment Help Agent for an online education platform. Your CRITICAL role is to help students UNDERSTAND assignments WITHOUT giving them answers.

ABSOLUTE RULES:
1. NEVER provide direct answers to assignment questions
2. NEVER write complete code solutions for graded work
3. NEVER generate full essays or reports for submission
4. NEVER solve specific numbered questions from assignments/exams

INSTEAD, you MUST:
1. Explain the CONCEPTS needed to solve the problem
2. Provide HINTS that guide thinking
3. Walk through SIMILAR (but different) examples
4. Break down the problem-solving APPROACH
5. Ask guiding questions to help students think
6. Point students to relevant learning materials

RESPONSE FORMAT:
- Start with acknowledging what the student needs help with
- Provide conceptual explanation
- Give 2-3 hints (not answers)
- Show a similar worked example if helpful
- End with an encouraging prompt to try it themselves

Use markdown formatting with emojis (💡, 🔍, 📝, ✨, 🎯) sparingly.

If a student explicitly asks for a direct answer, politely redirect them to the learning approach.
"""

# Built-in hint database for common assignment topics
ASSIGNMENT_HINTS = {
    "recursion": {
        "concept": "Recursion means a function calling itself with a smaller input until a base case is reached.",
        "hints": [
            "💡 **Hint 1:** Every recursive function needs TWO things: a **base case** (when to stop) and a **recursive case** (how to break the problem down).",
            "💡 **Hint 2:** Think about the problem in terms of: *'If I knew the answer for a smaller input, how would I use that to get the answer for the current input?'*",
            "💡 **Hint 3:** Trace through your function by hand with a small input (e.g., n=3) to see the call stack.",
        ],
        "similar_example": (
            "**Similar Example — Sum of digits:**\n"
            "```python\n"
            "def sum_digits(n):\n"
            "    if n < 10:          # Base case: single digit\n"
            "        return n\n"
            "    return (n % 10) + sum_digits(n // 10)\n\n"
            "# sum_digits(123) → 3 + sum_digits(12) → 3 + 2 + sum_digits(1) → 3 + 2 + 1 = 6\n"
            "```\n"
            "Notice the pattern: extract one piece, recurse on the rest."
        ),
    },
    "sorting": {
        "concept": "Sorting algorithms arrange elements in order. Each algorithm has different trade-offs in speed and memory.",
        "hints": [
            "💡 **Hint 1:** Think about what **comparisons** are being made and how elements **swap** positions.",
            "💡 **Hint 2:** Trace the algorithm by hand on a small array like `[5, 2, 8, 1]` — write down each step.",
            "💡 **Hint 3:** Consider: How many passes does the algorithm need? What happens after each pass?",
        ],
        "similar_example": (
            "**Similar Example — Finding the minimum:**\n"
            "```python\n"
            "# Before sorting, understand finding min:\n"
            "def find_min(arr):\n"
            "    minimum = arr[0]\n"
            "    for i in range(1, len(arr)):\n"
            "        if arr[i] < minimum:\n"
            "            minimum = arr[i]\n"
            "    return minimum\n"
            "```\n"
            "Selection sort repeats this idea for each position!"
        ),
    },
    "sql": {
        "concept": "SQL queries retrieve and manipulate data from relational databases using structured commands.",
        "hints": [
            "💡 **Hint 1:** Think about the query order: `FROM` (which table?) → `WHERE` (which rows?) → `SELECT` (which columns?) → `ORDER BY` (what order?)",
            "💡 **Hint 2:** For JOINs, ask yourself: *'What column connects these two tables?'*",
            "💡 **Hint 3:** Use `GROUP BY` when you need aggregate results (COUNT, SUM, AVG) per category.",
        ],
        "similar_example": (
            "**Similar Example — Find top students:**\n"
            "```sql\n"
            "SELECT student_name, AVG(score) as avg_score\n"
            "FROM grades\n"
            "WHERE semester = 'Fall 2024'\n"
            "GROUP BY student_name\n"
            "HAVING AVG(score) > 80\n"
            "ORDER BY avg_score DESC;\n"
            "```\n"
            "Notice the flow: filter rows → group → filter groups → sort."
        ),
    },
    "loop": {
        "concept": "Loops repeat a block of code. `for` loops iterate a known number of times; `while` loops run until a condition is false.",
        "hints": [
            "💡 **Hint 1:** Identify: What should happen **each iteration**? What should be the **stopping condition**?",
            "💡 **Hint 2:** Use a **loop variable** to track progress (a counter, an index, etc.).",
            "💡 **Hint 3:** Test with edge cases: What happens with an empty input? A single element?",
        ],
        "similar_example": (
            "**Similar Example — Count vowels:**\n"
            "```python\n"
            "def count_vowels(text):\n"
            "    count = 0\n"
            "    for char in text:\n"
            "        if char.lower() in 'aeiou':\n"
            "            count += 1\n"
            "    return count\n"
            "```\n"
            "Pattern: initialize → iterate → check condition → update."
        ),
    },
    "array": {
        "concept": "Arrays store multiple values in a single variable, accessed by index (starting at 0).",
        "hints": [
            "💡 **Hint 1:** Remember indices start at **0**, so the last element is at index `len(arr) - 1`.",
            "💡 **Hint 2:** For array problems, consider: Do I need to **traverse**, **search**, **insert**, or **modify**?",
            "💡 **Hint 3:** Drawing the array on paper with indices labeled helps visualize the solution.",
        ],
        "similar_example": (
            "**Similar Example — Reverse an array:**\n"
            "```python\n"
            "def reverse_array(arr):\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left < right:\n"
            "        arr[left], arr[right] = arr[right], arr[left]\n"
            "        left += 1\n"
            "        right -= 1\n"
            "    return arr\n"
            "```\n"
            "Two-pointer technique — works from both ends toward the middle."
        ),
    },
}

# Map keywords to hint topics
HINT_KEYWORDS = {
    "recursion": ["recursion", "recursive", "base case", "factorial", "fibonacci"],
    "sorting": ["sort", "sorting", "bubble", "merge sort", "quick sort", "selection sort"],
    "sql": ["sql", "query", "database", "select", "join", "table"],
    "loop": ["loop", "for loop", "while loop", "iteration", "iterate", "repeat"],
    "array": ["array", "list", "index", "element", "matrix"],
}


def match_hint_topic(query):
    """Match query to a hint topic."""
    query_lower = query.lower()
    best_topic = None
    best_score = 0
    for topic, keywords in HINT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic


class AssignmentAgent:
    """Agent for assignment help with academic integrity guardrails."""

    def __init__(self, model=None):
        self.model = model
        self.agent_type = "assignment"

    def generate_response(self, query, context=None):
        """Generate an assignment help response (hints only, no answers)."""
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
                f"{SYSTEM_PROMPT}\n\nStudent's Assignment Question: {query}"
            )
            return response.text

        except Exception as e:
            print(f"Assignment Agent Error: {e}")
            return self._fallback_response(query)

    def _fallback_response(self, query):
        """Provide real guided help from Tavily or the built-in hint database."""
        import os
        import requests
        
        # 1. Try to use Tavily API as the primary fallback model
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key and tavily_api_key != "your_tavily_api_key_here":
                headers = {"Content-Type": "application/json"}
                
                # Prompting Tavily to act as an assignment helper giving hints/pseudocode
                tavily_query = (
                    "Act as an educational assignment helper. Do NOT give the direct answer or full code. "
                    "Provide a conceptual hint and pseudocode or a similar example to help solve this: "
                    f"{query}"
                )
                
                data = {
                    "api_key": tavily_api_key,
                    "query": tavily_query,
                    "search_depth": "basic",
                    "include_answer": True
                }
                response = requests.post("https://api.tavily.com/search", json=data, headers=headers, timeout=8)
                result_data = response.json()
                
                answer = result_data.get("answer")
                if not answer and result_data.get("results"):
                    answer = result_data["results"][0].get("content")
                    
                if answer:
                    return (
                        f"📝 **Tavily AI Assignment Guide**\n\n"
                        f"{answer}\n\n"
                        f"### 🎯 Your Next Step\n"
                        f"Try applying this hint and pseudocode to your specific problem. Start with the simplest case and build up.\n\n"
                        f"✨ *You've got this! Understanding the process is more valuable than the answer.*"
                    )
        except Exception as e:
            print(f"Tavily search error in assignment agent: {e}")

        # 2. Try Built-in Hint Database
        topic = match_hint_topic(query)
        if topic and topic in ASSIGNMENT_HINTS:
            data = ASSIGNMENT_HINTS[topic]
            hints_text = "\n".join(data["hints"])
            return (
                f"📝 **Assignment Guidance**\n\n"
                f"I see you need help with a **{topic}** problem. "
                f"I can't give you the direct answer, but I'll guide you!\n\n"
                f"### 🔑 Core Concept\n"
                f"{data['concept']}\n\n"
                f"### 🔍 Hints to Guide You\n"
                f"{hints_text}\n\n"
                f"### 📊 Similar Worked Example\n"
                f"{data['similar_example']}\n\n"
                f"### 🎯 Your Next Step\n"
                f"Try applying the pattern from the example to your specific problem. "
                f"Start with the simplest case and build up.\n\n"
                f"✨ *You've got this! Understanding the process is more valuable than the answer.*"
            )

        # 3. Generic but structured help
        return (
            f"📝 **Assignment Guidance**\n\n"
            f"I see you need help with: *{query[:100]}*\n\n"
            "I can't provide direct answers, but here's a structured approach:\n\n"
            "### 💡 Step 1: Understand the Problem\n"
            "- Re-read the question and underline **key terms**\n"
            "- Identify what **input** you're given and what **output** is expected\n"
            "- Write it in your own words\n\n"
            "### 🔍 Step 2: Break It Down\n"
            "- Split the problem into **smaller sub-problems**\n"
            "- Solve the simplest version first (e.g., with tiny input)\n"
            "- Build up to the full solution\n\n"
            "### 📊 Step 3: Find Patterns\n"
            "- Look at worked examples from your notes or textbook\n"
            "- What approach did they use? Can you apply the same pattern?\n\n"
            "### 🎯 Step 4: Test Your Solution\n"
            "- Try your solution with the example inputs from the question\n"
            "- Test edge cases (empty input, single element, very large input)\n\n"
            "💡 *Try asking about specific concepts like 'help with recursion' or "
            "'hints for sorting' for detailed guidance!*\n\n"
            "✨ *Remember: understanding the process is more valuable than just getting the answer.*"
        )
