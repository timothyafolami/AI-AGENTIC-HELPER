# 🤖 AI Agentic Helper - Daily Planning Assistant

A sophisticated AI-powered daily planning and task management assistant built with **Groq LLM**, **LangGraph**, and **Streamlit**. This intelligent agent helps you create structured daily plans, manage tasks, and boost productivity through natural language interaction.

## ✨ Features

### 🎯 **Core Capabilities**
- **Intelligent Planning**: AI creates time-organized daily schedules with realistic estimates
- **Natural Language Interface**: Chat naturally to create and manage your plans
- **Structured Output**: Plans saved as JSON with detailed task information
- **Real-time Progress Tracking**: Monitor task completion and time estimates
- **Web Search Integration**: Get current information to enhance planning
- **Tool-based Architecture**: Extensible with multiple specialized tools

### 🛠️ **Available Tools**
- **`create_daily_plan`**: Generate structured daily plans with AI reasoning
- **`search_web`**: DuckDuckGo web search for current information
- **`get_current_time_info`**: Smart time/date context for scheduling
- **`save_daily_plan`**: Store plans as JSON files
- **`load_daily_plan`**: Retrieve saved plans
- **`list_saved_plans`**: View all created plans
- **`update_task_status`**: Mark tasks as completed/in progress

### 🎨 **User Interface**
- **Modern Streamlit Interface**: Clean, responsive web app
- **Sidebar Plan Viewer**: Real-time plan display with progress metrics
- **Interactive Chat**: Full conversation history with the AI agent
- **Progress Visualization**: Progress bars and completion statistics
- **Quick Actions**: One-click plan creation and summary viewing

## 🚀 Quick Start

### Prerequisites
```bash
# Make sure you have Python 3.8+ installed
python --version
```

### 1. Environment Setup
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.1-70b-versatile
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application

#### Option A: Streamlit Web Interface (Recommended)
```bash
streamlit run streamlit_chat.py
```
Visit `http://localhost:8501` in your browser.

#### Option B: Command Line Demo
```bash
python demo.py
```

#### Option C: Direct Python Usage
```python
from ai_agent import planning_agent

# Create a plan
response = planning_agent.chat("I want to be productive today with work, exercise, and cooking")
print(response)
```

## 📋 Usage Examples

### Creating Plans
```
🧑 "I have 6 hours today and want to learn Python, exercise, and cook dinner"

🤖 "I'll create a structured plan for you! Let me break this down into realistic tasks with proper timing..."
```

### Managing Tasks
```
🧑 "Show me my current plan status"
🧑 "Mark my exercise task as completed"
🧑 "I need to reschedule my cooking time"
```

### Getting Information
```
🧑 "Search for healthy meal prep ideas"
🧑 "What's the best time to exercise today?"
```

## 🏗️ Architecture

### Core Components

```
├── ai_agent.py          # Shim exposing PlanningAgent (back-compat)
├── prompts.py           # System prompts for different modes
├── streamlit_chat.py    # Web interface
├── demo.py              # Command-line demo
└── agentic_helper/      # Modular package (source of truth)
    ├── config.py            # Env + settings
    ├── logging_config.py    # Central Loguru setup
    ├── models.py            # Pydantic data models
    ├── llm.py               # Groq LLM configuration
    ├── utils/
    │   └── plans.py         # Format, progress, export helpers
    ├── tools/
    │   └── planning.py      # Tools: search, plan, save/load/list/update
    └── agent/
        └── planning.py      # PlanningAgent + LangGraph
```

### Data Models

**TodoTask**: Individual task with time, priority, and status
```json
{
  "id": "task_001",
  "title": "Learn Python basics",
  "description": "Study Python fundamentals for 2 hours",
  "priority": "high",
  "estimated_duration": 120,
  "scheduled_time": "09:00",
  "category": "learning",
  "status": "pending"
}
```

**DailyPlan**: Complete plan with multiple tasks
```json
{
  "plan_id": "plan_2024_01_15",
  "date": "2024-01-15",
  "total_tasks": 4,
  "estimated_total_duration": 360,
  "tasks": [...],
  "planning_notes": "AI reasoning about the schedule"
}
```

### Agent Flow
1. **Message Analysis**: Detect planning vs. general chat intent
2. **Tool Selection**: Choose appropriate tools based on request
3. **Context Gathering**: Get time info and existing plans
4. **AI Reasoning**: Use LLM with structured output for planning
5. **Response Generation**: Format and return user-friendly response

## 🔧 Configuration

### Environment Variables
- `GROQ_API_KEY`: Your Groq API key (required)
- `MODEL_NAME`: Groq model to use (default: llama-3.1-70b-versatile)

### Supported Models
- `llama-3.1-405b-reasoning` (recommended for complex planning)
- `llama-3.1-70b-versatile` (good balance of speed/quality)
- `llama-3.1-8b-instant` (fastest, basic planning)

## 📁 File Structure

```
AI-AGENTIC-HELPER/
├── 🤖 ai_agent.py           # Agent shim (uses agentic_helper.agent)
├── 💬 prompts.py            # System prompts
├── 🌐 streamlit_chat.py     # Web interface
├── 🎮 demo.py               # Demo script
├── 📦 requirements.txt      # Dependencies
├── 📁 agentic_helper/       # Modular package (source of truth)
│   ├── config.py            # Settings
│   ├── logging_config.py    # Logger
│   ├── models.py            # Data models
│   ├── llm.py               # Groq LLM (import as agentic_helper.llm)
│   ├── utils/
│   │   └── plans.py         # Plan helpers
│   ├── tools/
│   │   └── planning.py      # Tools
│   └── agent/
│       └── planning.py      # PlanningAgent
├── 📁 plans/                # Generated JSON plans (auto-created)
│   ├── plan_YYYY-MM-DD_HHMMSS.json
│   └── ...
└── 📖 README.md             # This file
```

## 🎨 Customization

### Adding New Tools
```python
from langchain_core.tools import tool

@tool
def my_custom_tool(input_param: str) -> str:
    """Description of what this tool does"""
    # Your implementation
    return result

# Add to AGENT_TOOLS list in agentic_helper/tools/planning.py
```

### Custom Prompts
Edit `prompts.py` to customize how the agent behaves:
- `GENERAL_CHAT_PROMPT`: Basic conversation mode
- `PLANNING_AGENT_PROMPT`: Planning-specific behavior
- `PLAN_CREATION_PROMPT`: Guidelines for plan creation

### UI Modifications
Customize `streamlit_chat.py` to modify the web interface:
- Change colors, layout, or components
- Add new sidebar features
- Modify chat display format

## 🔍 Troubleshooting

### Common Issues

**❌ "Error: Groq API key not found"**
- Check your `.env` file exists and contains `GROQ_API_KEY`
- Verify the API key is valid

**❌ "No module named 'langgraph'"**
- Run `pip install -r requirements.txt`
- Ensure you're in the correct virtual environment

**❌ "Plans directory not found"**
- The `plans/` directory is created automatically
- Check file permissions in your project directory

**❌ "Agent not responding"**
- Check your internet connection for web search tools
- Verify Groq API quota and rate limits

### Debug Mode
Enable debug output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/AI-AGENTIC-HELPER.git

# Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest

# Run tests
python -m pytest

# Format code
black .
```

## 📈 Roadmap

### Upcoming Features
- [ ] **Calendar Integration**: Sync with Google Calendar
- [ ] **Recurring Tasks**: Support for daily/weekly routines
- [ ] **Team Planning**: Multi-user plan collaboration
- [ ] **Voice Interface**: Speech-to-text plan creation
- [ ] **Mobile App**: React Native companion app
- [ ] **Analytics Dashboard**: Productivity insights and trends
- [ ] **Smart Notifications**: Task reminders and updates
- [ ] **Template Library**: Pre-built plan templates

### Technical Improvements
- [ ] **Database Backend**: PostgreSQL for plan storage
- [ ] **User Authentication**: Multi-user support
- [ ] **API Endpoints**: REST API for integrations
- [ ] **Caching Layer**: Redis for performance
- [ ] **Deployment**: Docker containerization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq** for fast LLM inference
- **LangChain/LangGraph** for agent framework
- **Streamlit** for beautiful web interfaces
- **DuckDuckGo** for web search capabilities

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/AI-AGENTIC-HELPER/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/AI-AGENTIC-HELPER/discussions)
- 📧 **Email**: your-email@example.com

---

<div align="center">

**🚀 Built with ❤️ using Groq LLM, LangGraph, and Streamlit**

*Transform your productivity with AI-powered planning!*

</div>
