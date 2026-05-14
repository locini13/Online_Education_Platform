# EduAI — AI-Powered Online Education Platform

EduAI is a state-of-the-art, multi-agent educational support system designed to provide students with high-quality learning assistance while maintaining strict academic integrity.

## Key Features

### Multi-Agent AI Pipeline
The platform uses a sophisticated **Orchestrator** that intelligently routes student queries to specialized AI agents:
- **Learning Agent (Course Agent):** Provides deep conceptual explanations, study plans, and resource recommendations.
- **Assignment Agent:** Offers guided hints, strategies, and similar examples for homework without ever giving direct answers.
- **Technical Agent:** Troubleshoots platform issues like login errors, video buffering, and payment problems.
- **Escalation Agent:** Monitors student frustration and automatically connects them to human support when needed.

### Smart Architecture & Safety
- **DualModel Integration:** Seamlessly supports both **Gemini 2.5 Flash** and **Grok 2**. The system automatically fails over from Gemini to Grok if quota or connection issues occur.
- **Dynamic Fallbacks:** If all LLMs are unavailable, the system automatically falls back to **Tavily AI Search**, then to **Wikipedia**, and finally to an internal **Knowledge Base**.
- **LLM Intent Routing:** Uses AI to understand student context and route them to the correct agent with lightning-fast keyword-matching as a backup.
- **Safety Guardrails:** Built-in input/output validation to prevent cheating, PII leakage, and toxic content.

## Tech Stack
- **Backend:** Flask (Python 3.x)
- **Database:** SQLite with dynamic session management
- **Frontend:** Modern Vanilla JS with a premium Glassmorphic Dashboard
- **AI Integrations:** Google Generative AI (Gemini), xAI (Grok), Tavily AI Search, Wikipedia API

## Configuration
The platform is configured via the `.env` file. You must provide valid API keys for full functionality:
- `GEMINI_API_KEY`: Your Google AI Studio key
- `GROK_API_KEY`: Your xAI API key
- `TAVILY_API_KEY`: Your Tavily Search API key
- `SECRET_KEY`: Flask session security key

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Configure your `.env` file.
3. Run the application: `python app.py`
4. Access the platform at `http://localhost:5000`

## DEMO
https://drive.google.com/file/d/1gH8x10Ib_Wv-iE_KXvUsAvDI5ENBNOYC/view?usp=sharing

#### Admin 
<img width="1500" height="700" alt="image" src="https://github.com/user-attachments/assets/8689f5c3-9888-4e47-99d5-da5cc4e94a7d" />

### Student 

<img width="1700" height="700" alt="image" src="https://github.com/user-attachments/assets/334434c6-79a1-4730-9690-9d14d610a04d" />


## Deployment
https://onlineeducationplatform.up.railway.app

## Admin Features
Admins can access a real-time dashboard at `/api/admin/stats` to monitor:
- Total query volume and agent distribution
- AI response times and escalation rates
- Recent guardrail violations and human support requests
