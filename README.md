# AI Services Agency 👨‍💼🚀

An enterprise-grade AI agency application built with [Streamlit](https://streamlit.io/) and [Agency Swarm](https://github.com/VRSEN/agency-swarm). It simulates a full-service digital consulting agency using collaborative AI agents to evaluate, architect, plan, and strategize software projects end-to-end.

> 📖 **Detailed Architecture & Multi-Agent Guide**: Check out [PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md) for an in-depth breakdown of how the project works, multi-model compatibility, and agent-to-agent communication.

---

## 📺 Demo

https://github.com/user-attachments/assets/a0befa3a-f4c3-400d-9790-4b9e37254405

---

## 🌟 Key Features

### 1. Multi-Provider & Unified Key Support
Choose your preferred AI provider directly from the sidebar without modifying code:

| Provider | Supported Models | Description |
|---|---|---|
| **OmniKey AI** | `gemini-2.5-flash`, `gemini-1.5-flash`, `gpt-4o-mini`, `gpt-4o`, `llama-3.3-70b-versatile`, `claude-3-5-sonnet` | Unified OpenAI-compatible key router managing multiple upstream keys |
| **Google Gemini** | `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash` | Native Google AI Studio OpenAI-compatible endpoint |
| **OpenRouter** | `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-chat`, etc. | Access dozens of free and commercial models |
| **Groq** | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768` | Ultra-fast inference engine |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` | Official OpenAI models |
| **DeepSeek** | `deepseek-chat`, `deepseek-reasoner` | High-performance cost-effective reasoning models |
| **Ollama (Local)** | `llama3.2`, `llama3.1`, `mistral`, `qwen2.5` | 100% private, free local execution |
| **Custom Endpoint** | User-defined model | Any OpenAI-compatible server (vLLM, LM Studio, LocalAI) |

---

### 2. Five Specialized AI Agents

Each agent represents a core leadership role in the software project lifecycle:

- 👔 **CEO Agent (Project Director)**: Strategic leader and executive decision-maker
  - Analyzes project requirements and strategic feasibility
  - Evaluates market opportunity, risks, and ROI
  - Uses the `AnalyzeProjectRequirements` tool
- 📐 **CTO Agent (Technical Architect)**: Technical architecture and feasibility specialist
  - Defines architecture (monolithic, microservices, serverless, hybrid)
  - Selects optimal core technologies and frameworks
  - Evaluates scalability and uses the `CreateTechnicalSpecification` tool
- 📋 **Product Manager Agent**: Scope, roadmap, and delivery expert
  - Defines product roadmap and milestones
  - Prioritizes MVP features and user stories
  - Focuses on product-market fit and scope boundaries
- 💻 **Lead Developer Agent**: Technical implementation expert
  - Designs software modules and database schemas
  - Estimates development effort and cloud hosting costs
  - Reviews implementation risks and technical constraints
- 🎯 **Client Success Manager Agent**: Market growth and customer success leader
  - Develops go-to-market (GTM) strategy
  - Plans customer acquisition and retention frameworks
  - Establishes communication and onboarding KPIs

---

### 3. Cross-Provider Compatibility & Schema Resilience
- **Gemini / OmniKey Schema Compatibility**: Built-in dynamic schema sanitizer automatically cleans parameter schemas (stripping `additionalProperties` and enforcing non-strict mode) to ensure seamless compatibility with Google Gemini and gateway routers.
- **Graceful Fallback Handling**: Intelligent ad-hoc tool handling intercepts unexpected or hallucinated function calls, returning synthetic tool feedback so the agent pipeline completes reliably without crashes.
- **Pydantic Token Validation Patch**: Automatically ensures compatibility between modern `openai` (`>=2.54.0`) and `agency-swarm` / `openai-agents`.

---

## 🤝 Multi-Agent Collaboration Flows

The agency coordinates all 5 specialists through explicit communication flows:
- **CEO** ↔️ All Agents (Strategic Oversight & Direction)
- **CTO** ↔️ **Lead Developer** (Architecture to Implementation)
- **Product Manager** ↔️ **Client Success** (Product-Market Fit & GTM)
- **Product Manager** ↔️ **Lead Developer** (Feature Feasibility & Effort)

Each agent's output is neatly organized into dedicated tabs in the interactive Streamlit dashboard.

---

## 🚀 How to Run

### 1. Prerequisites
- Python 3.10+ installed
- An API key from your chosen provider (e.g., [OmniKey AI](https://omnikey-ai-unified-key-manager.onrender.com), [Google AI Studio](https://aistudio.google.com/app/apikey), [OpenRouter](https://openrouter.ai/keys), [Groq](https://console.groq.com/keys), or [OpenAI](https://platform.openai.com/api-keys))

### 2. Clone & Navigate
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency
```

### 3. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Launch the Application
```bash
streamlit run agency.py
```

### 5. Using the App
1. Open your browser at **`http://localhost:8501`**.
2. Select your **AI Provider** in the sidebar (e.g., **OmniKey AI**, **Google Gemini**, or **OpenRouter**).
3. Paste your API Key and select your model.
4. Fill in the **Project Details** (Project Name, Description, Type, Timeline, Budget, etc.).
5. Click **"Analyze Project"**.
6. View the detailed multi-agent analyses across the 5 output tabs!
