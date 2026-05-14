"""
Course Guidance Agent — helps students learn concepts and navigate courses.

Capabilities:
- Concept explanations
- Study plan generation
- Learning recommendations
- Resource suggestions
"""

import google.generativeai as genai

SYSTEM_PROMPT = """You are the Course Guidance Agent for an online education platform. Your role is to help students learn and understand concepts.

GUIDELINES:
1. Explain concepts clearly with examples
2. Break down complex topics into digestible parts
3. Suggest study plans and learning paths
4. Recommend resources (videos, articles, practice problems)
5. Use analogies and real-world examples
6. Be encouraging and supportive
7. Adapt explanations to the student's level

FORMAT your responses with:
- Clear headings using markdown
- Code examples when relevant (use ```language blocks)
- Bullet points for lists
- Emojis sparingly for engagement (📚, 💡, ✅, 🔍)

NEVER:
- Provide direct assignment answers
- Complete homework or exams
- Generate plagiarism-ready content
- Be condescending or dismissive

You are knowledgeable across: Computer Science, Mathematics, Physics, English, and general academics.
"""

# ── Built-in Knowledge Base for Fallback Mode ──
KNOWLEDGE_BASE = {
    "linear regression": (
        "📚 **Linear Regression — Concept Explanation**\n\n"
        "Linear regression is a **supervised machine learning algorithm** that models the relationship "
        "between a dependent variable (y) and one or more independent variables (x) by fitting a straight line.\n\n"
        "### 🔑 Key Idea\n"
        "Find the **best-fit line** through your data points: **y = mx + b**\n"
        "- **y** → predicted value (dependent variable)\n"
        "- **x** → input feature (independent variable)\n"
        "- **m** → slope (how much y changes when x changes by 1)\n"
        "- **b** → y-intercept (value of y when x = 0)\n\n"
        "### 📊 How It Works\n"
        "1. **Plot** your data points on a graph\n"
        "2. **Draw** a line that minimizes the total distance from all points to the line\n"
        "3. **Minimize** the cost using **Mean Squared Error (MSE)**:\n"
        "   `MSE = (1/n) × Σ(actual - predicted)²`\n"
        "4. **Optimize** using **Gradient Descent** to find the best m and b\n\n"
        "### 🌍 Real-World Example\n"
        "Predicting house prices:\n"
        "- **x** = house size (sq ft)\n"
        "- **y** = price ($)\n"
        "- A 1500 sq ft house → model predicts ~$300,000\n\n"
        "```python\n"
        "# Simple Linear Regression in Python\n"
        "from sklearn.linear_model import LinearRegression\n"
        "import numpy as np\n\n"
        "X = np.array([[1000], [1500], [2000], [2500]])\n"
        "y = np.array([200000, 300000, 400000, 500000])\n\n"
        "model = LinearRegression()\n"
        "model.fit(X, y)\n\n"
        "predicted = model.predict([[1800]])\n"
        "print(f'Predicted price: ${predicted[0]:,.0f}')\n"
        "```\n\n"
        "### 📖 Types\n"
        "- **Simple Linear Regression** — 1 input variable\n"
        "- **Multiple Linear Regression** — 2+ input variables: `y = b₀ + b₁x₁ + b₂x₂ + ...`\n\n"
        "### ✅ When to Use\n"
        "- Predicting continuous values (prices, temperatures, scores)\n"
        "- When the relationship between variables is approximately linear\n\n"
        "💡 *Want to dive deeper? Ask about gradient descent, overfitting, or try logistic regression next!*"
    ),
    "binary search": (
        "📚 **Binary Search — Concept Explanation**\n\n"
        "Binary search is an efficient algorithm for finding an element in a **sorted** array "
        "by repeatedly dividing the search space in half.\n\n"
        "### 🔑 Key Idea\n"
        "Instead of checking every element (linear search), compare the target with the **middle element** "
        "and eliminate half the remaining elements each time.\n\n"
        "### ⚡ Time Complexity: O(log n)\n"
        "- For 1,000,000 elements → only ~20 comparisons needed!\n"
        "- Linear search would need up to 1,000,000 comparisons\n\n"
        "### 📊 How It Works\n"
        "1. Start with the **entire sorted array**\n"
        "2. Find the **middle** element\n"
        "3. If middle == target → ✅ Found!\n"
        "4. If target < middle → search the **left half**\n"
        "5. If target > middle → search the **right half**\n"
        "6. Repeat until found or search space is empty\n\n"
        "```python\n"
        "def binary_search(arr, target):\n"
        "    low, high = 0, len(arr) - 1\n"
        "    while low <= high:\n"
        "        mid = (low + high) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        elif arr[mid] < target:\n"
        "            low = mid + 1\n"
        "        else:\n"
        "            high = mid - 1\n"
        "    return -1  # Not found\n\n"
        "# Example\n"
        "nums = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]\n"
        "print(binary_search(nums, 23))  # Output: 5\n"
        "```\n\n"
        "### ⚠️ Requirement\n"
        "The array **must be sorted**. If unsorted, sort first (O(n log n)) or use linear search.\n\n"
        "💡 *Want to learn about binary search trees, or see a recursive version?*"
    ),
    "recursion": (
        "📚 **Recursion — Concept Explanation**\n\n"
        "Recursion is when a **function calls itself** to solve a problem by breaking it into smaller sub-problems.\n\n"
        "### 🔑 Two Essential Parts\n"
        "1. **Base Case** — the stopping condition (prevents infinite loops)\n"
        "2. **Recursive Case** — the function calls itself with a smaller input\n\n"
        "### 🌍 Analogy\n"
        "Think of Russian nesting dolls 🪆 — each doll contains a smaller one inside, "
        "until you reach the tiniest doll (base case).\n\n"
        "### 📊 Classic Example: Factorial\n"
        "- 5! = 5 × 4 × 3 × 2 × 1 = 120\n"
        "- Recursively: `factorial(n) = n × factorial(n-1)`\n\n"
        "```python\n"
        "def factorial(n):\n"
        "    if n <= 1:        # Base case\n"
        "        return 1\n"
        "    return n * factorial(n - 1)  # Recursive case\n\n"
        "print(factorial(5))  # Output: 120\n"
        "```\n\n"
        "### 🔍 How It Executes\n"
        "```\n"
        "factorial(5)\n"
        "  → 5 × factorial(4)\n"
        "    → 4 × factorial(3)\n"
        "      → 3 × factorial(2)\n"
        "        → 2 × factorial(1)\n"
        "          → 1  (base case!)\n"
        "        → 2 × 1 = 2\n"
        "      → 3 × 2 = 6\n"
        "    → 4 × 6 = 24\n"
        "  → 5 × 24 = 120\n"
        "```\n\n"
        "### ✅ Common Uses\n"
        "- Tree/graph traversal\n"
        "- Divide and conquer (merge sort, quick sort)\n"
        "- Dynamic programming\n"
        "- Fibonacci, Tower of Hanoi\n\n"
        "💡 *Ask about tail recursion, memoization, or a specific recursive algorithm!*"
    ),
    "sorting": (
        "📚 **Sorting Algorithms — Overview**\n\n"
        "Sorting arranges elements in a specific order (ascending/descending).\n\n"
        "### 📊 Common Algorithms Compared\n\n"
        "| Algorithm | Best | Average | Worst | Space | Stable |\n"
        "|-----------|------|---------|-------|-------|--------|\n"
        "| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ |\n"
        "| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | ❌ |\n"
        "| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ |\n"
        "| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | ✅ |\n"
        "| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | ❌ |\n\n"
        "### 🔑 Quick Summary\n"
        "- **Small data?** → Insertion Sort (simple, fast for nearly sorted)\n"
        "- **Need guaranteed O(n log n)?** → Merge Sort\n"
        "- **General purpose fastest?** → Quick Sort\n"
        "- **Learning?** → Start with Bubble Sort to understand the concept\n\n"
        "```python\n"
        "# Quick Sort Example\n"
        "def quicksort(arr):\n"
        "    if len(arr) <= 1:\n"
        "        return arr\n"
        "    pivot = arr[len(arr) // 2]\n"
        "    left = [x for x in arr if x < pivot]\n"
        "    middle = [x for x in arr if x == pivot]\n"
        "    right = [x for x in arr if x > pivot]\n"
        "    return quicksort(left) + middle + quicksort(right)\n\n"
        "print(quicksort([3, 6, 8, 10, 1, 2, 1]))\n"
        "# Output: [1, 1, 2, 3, 6, 8, 10]\n"
        "```\n\n"
        "💡 *Ask about any specific sorting algorithm for a deep dive!*"
    ),
    "big o": (
        "📚 **Big O Notation — Concept Explanation**\n\n"
        "Big O describes how an algorithm's **performance scales** as the input size grows.\n\n"
        "### 🔑 Key Idea\n"
        "It answers: *\"How does the runtime/space grow as input gets larger?\"*\n\n"
        "### 📊 Common Complexities (fastest → slowest)\n\n"
        "| Big O | Name | Example |\n"
        "|-------|------|--------|\n"
        "| O(1) | Constant | Array access by index |\n"
        "| O(log n) | Logarithmic | Binary search |\n"
        "| O(n) | Linear | Loop through array |\n"
        "| O(n log n) | Linearithmic | Merge sort |\n"
        "| O(n²) | Quadratic | Nested loops |\n"
        "| O(2ⁿ) | Exponential | Recursive Fibonacci |\n\n"
        "### 🌍 Analogy\n"
        "Finding a name in a phone book:\n"
        "- **O(n)** — read every page (linear search)\n"
        "- **O(log n)** — open to middle, go left/right (binary search)\n"
        "- **O(1)** — you already know the page number\n\n"
        "### Rules\n"
        "1. **Drop constants**: O(2n) → O(n)\n"
        "2. **Drop smaller terms**: O(n² + n) → O(n²)\n"
        "3. Focus on **worst case** (usually)\n\n"
        "💡 *Ask about amortized analysis or space complexity for more!*"
    ),
    "oop": (
        "📚 **Object-Oriented Programming (OOP)**\n\n"
        "OOP is a programming paradigm that organizes code around **objects** — bundles of data and behavior.\n\n"
        "### 🔑 Four Pillars\n\n"
        "**1. Encapsulation** — Bundle data + methods, hide internals\n"
        "```python\n"
        "class BankAccount:\n"
        "    def __init__(self):\n"
        "        self.__balance = 0  # Private\n"
        "    def deposit(self, amount):\n"
        "        self.__balance += amount\n"
        "```\n\n"
        "**2. Inheritance** — Child class inherits from parent\n"
        "```python\n"
        "class Animal:\n"
        "    def speak(self): pass\n"
        "class Dog(Animal):\n"
        "    def speak(self): return 'Woof!'\n"
        "```\n\n"
        "**3. Polymorphism** — Same interface, different behavior\n"
        "```python\n"
        "for animal in [Dog(), Cat()]:\n"
        "    print(animal.speak())  # Different output\n"
        "```\n\n"
        "**4. Abstraction** — Hide complexity, show essentials\n\n"
        "💡 *Ask about any pillar for a deeper explanation with examples!*"
    ),
    "stack": (
        "📚 **Stack — Data Structure**\n\n"
        "A stack is a **LIFO** (Last In, First Out) data structure — like a stack of plates.\n\n"
        "### 🔑 Operations (all O(1))\n"
        "- **push(item)** — add to top\n"
        "- **pop()** — remove from top\n"
        "- **peek()** — view top without removing\n"
        "- **isEmpty()** — check if empty\n\n"
        "```python\n"
        "stack = []\n"
        "stack.append(10)   # push\n"
        "stack.append(20)   # push\n"
        "top = stack.pop()  # 20 (LIFO)\n"
        "```\n\n"
        "### ✅ Common Uses\n"
        "- Undo/redo operations\n"
        "- Browser back button\n"
        "- Function call stack\n"
        "- Expression evaluation\n"
        "- Balanced parentheses checking\n\n"
        "💡 *Ask about queues, linked lists, or see a stack implementation!*"
    ),
    "queue": (
        "📚 **Queue — Data Structure**\n\n"
        "A queue is a **FIFO** (First In, First Out) data structure — like a line at a store.\n\n"
        "### 🔑 Operations\n"
        "- **enqueue(item)** — add to rear\n"
        "- **dequeue()** — remove from front\n"
        "- **peek()** — view front without removing\n\n"
        "```python\n"
        "from collections import deque\n"
        "q = deque()\n"
        "q.append(10)      # enqueue\n"
        "q.append(20)      # enqueue\n"
        "front = q.popleft()  # 10 (FIFO)\n"
        "```\n\n"
        "### Types\n"
        "- **Simple Queue** — basic FIFO\n"
        "- **Circular Queue** — wraps around\n"
        "- **Priority Queue** — highest priority first\n"
        "- **Deque** — insert/remove from both ends\n\n"
        "💡 *Ask about priority queues or BFS (which uses queues)!*"
    ),
}

# Keywords mapped to knowledge base entries for flexible matching
TOPIC_KEYWORDS = {
    "linear regression": ["linear regression", "regression line", "best fit line", "least squares"],
    "binary search": ["binary search", "binary find", "search algorithm sorted"],
    "recursion": ["recursion", "recursive", "base case", "recursive function"],
    "sorting": ["sorting", "bubble sort", "merge sort", "quick sort", "selection sort", "insertion sort", "sort algorithm"],
    "big o": ["big o", "time complexity", "space complexity", "algorithm complexity", "o(n)", "o(1)"],
    "oop": ["oop", "object oriented", "encapsulation", "inheritance", "polymorphism", "abstraction", "class and object"],
    "stack": ["stack", "lifo", "push pop"],
    "queue": ["queue", "fifo", "enqueue", "dequeue"],
}


def match_topic(query):
    """Match a query to a knowledge base topic using keyword matching."""
    query_lower = query.lower()
    best_topic = None
    best_score = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in query_lower:
                score += len(kw)  # Longer match = higher score
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


class CourseAgent:
    """Agent for course guidance and concept explanations."""

    def __init__(self, model=None):
        self.model = model
        self.agent_type = "course"

    def generate_response(self, query, context=None):
        """Generate a course guidance response."""
        if not self.model:
            return self._fallback_response(query)

        try:
            chat_history = []
            if context:
                for msg in context[-6:]:  # Last 6 messages for context
                    role = "user" if msg.get("role") == "user" else "model"
                    chat_history.append({"role": role, "parts": [msg["content"]]})

            chat = self.model.start_chat(history=chat_history)
            response = chat.send_message(
                f"{SYSTEM_PROMPT}\n\nStudent Query: {query}"
            )
            return response.text

        except Exception as e:
            print(f"Course Agent Error: {e}")
            return self._fallback_response(query)

    def _fallback_response(self, query):
        """Provide a real educational response from Tavily, knowledge base, or Wikipedia."""
        import os
        import requests
        
        # 1. Try to use Tavily API as the primary fallback model
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key and tavily_api_key != "your_tavily_api_key_here":
                headers = {"Content-Type": "application/json"}
                data = {
                    "api_key": tavily_api_key,
                    "query": f"explain {query}",
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
                        f"🤖 **Tavily AI Model Fallback**\n\n"
                        f"{answer}\n\n"
                        f"### 💡 Next Steps\n"
                        f"1. **Read more:** Search for this topic on educational sites.\n"
                        f"2. **Find examples:** Look for worked examples to build intuition.\n\n"
                        f"💡 *Configure a valid Gemini API key in `.env` for fully customized interactive answers!*"
                    )
        except Exception as e:
            print(f"Tavily search error: {e}")

        # 2. Try Built-in Knowledge Base
        topic = match_topic(query)
        if topic and topic in KNOWLEDGE_BASE:
            return KNOWLEDGE_BASE[topic]

        # 3. Try Wikipedia as a general fallback
        try:
            import urllib.parse
            
            clean_query = query.lower()
            for word in ["explain ", "what is ", "tell me about ", "concept of ", "how does ", " work", "?", "the "]:
                clean_query = clean_query.replace(word, "").strip()
                
            if not clean_query:
                clean_query = query
                
            headers = {"User-Agent": "EduAI-Bot/1.0 (test@example.com)"}
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": clean_query,
                "format": "json",
                "utf8": 1,
                "srlimit": 1
            }
            response = requests.get(search_url, params=search_params, headers=headers, timeout=5)
            data = response.json()
            
            if data.get("query", {}).get("search"):
                title = data["query"]["search"][0]["title"]
                
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                summary_resp = requests.get(summary_url, headers=headers, timeout=5)
                summary_data = summary_resp.json()
                
                if "extract" in summary_data:
                    return (
                        f"📚 **{title} — Concept Explanation**\n\n"
                        f"{summary_data['extract']}\n\n"
                        f"### 💡 Next Steps\n"
                        f"1. **Read more:** Search for '{title}' on Wikipedia or educational sites.\n"
                        f"2. **Find examples:** Look for worked examples to build intuition.\n\n"
                        f"💡 *Configure a valid Gemini API key in `.env` for fully customized, AI-powered interactive answers!*"
                    )
        except Exception as e:
            print(f"Wikipedia fetch error: {e}")

        # Generic but still helpful response for unknown topics if everything fails.
        return (
            f"📚 **Let me help you with: *{query[:100]}***\n\n"
            "I couldn't find a direct explanation for this topic, "
            "but here's how you can learn effectively:\n\n"
            "### 💡 Suggested Approach\n"
            "1. **Break it down** — Identify the core concept and sub-topics\n"
            "2. **Find examples** — Search for worked examples to build intuition\n"
            "3. **Practice** — Solve progressively harder problems\n"
            "4. **Teach it** — Explaining to someone else deepens understanding\n\n"
            "### 📖 Recommended Resources\n"
            "- **Khan Academy** — Free video lessons on most academic topics\n"
            "- **GeeksforGeeks** — CS concepts with code examples\n"
            "- **MIT OpenCourseWare** — University-level materials\n"
            "- **YouTube (3Blue1Brown)** — Excellent math visualizations\n\n"
            "💡 *Configure a valid Gemini API key in `.env` for AI-powered answers on any topic!*"
        )
