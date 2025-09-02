import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from langchain_core.tools import tool

from agentic_helper.logging_config import setup_logger
from agentic_helper.llm import llm
from agentic_helper.models import PlannerResponse, DailyPlan


logger = setup_logger()


# Try to import DuckDuckGo search tool, make it optional
try:
    from langchain_community.tools import DuckDuckGoSearchRun

    SEARCH_AVAILABLE = True
except ImportError:
    print("⚠️  DuckDuckGo search not available. Install with: pip install -U duckduckgo-search")
    SEARCH_AVAILABLE = False

if SEARCH_AVAILABLE:
    try:
        search_tool = DuckDuckGoSearchRun()
    except Exception as e:
        print(f"⚠️  Could not initialize DuckDuckGo search: {e}")
        search_tool = None
        SEARCH_AVAILABLE = False
else:
    search_tool = None


structured_llm = llm.with_structured_output(PlannerResponse)


@tool
def search_web(query: str) -> str:
    """Search the web using DuckDuckGo for current information"""
    logger.info(f"🔍 Search tool called with query: '{query}'")

    if not SEARCH_AVAILABLE or search_tool is None:
        logger.warning("⚠️  Search tool not available")
        return (
            "🔍 Web search not available. Query was: '"
            + query
            + "'\n\nTo enable search, install: pip install -U duckduckgo-search\nAlternatively, try manually searching in your browser."
        )

    try:
        logger.debug(f"🌐 Executing search for: {query}")
        results = search_tool.invoke(query)
        logger.info(f"✅ Search completed for: '{query}'")
        return f"🔍 Search results for '{query}':\n{results}"
    except Exception as e:
        logger.error(f"❌ Search failed for '{query}': {str(e)}")
        return f"❌ Search failed: {str(e)}\nYou can manually search for '{query}' in your browser instead."


@tool
def get_current_time_info() -> Dict[str, Any]:
    """Get current time and date information for planning"""
    logger.debug("⏰ Getting current time information")
    now = datetime.now()
    time_info = {
        "current_time": now.strftime("%H:%M"),
        "current_date": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A"),
        "timestamp": now.isoformat(),
        "remaining_hours_today": 24 - now.hour,
        "is_morning": now.hour < 12,
        "is_afternoon": 12 <= now.hour < 18,
        "is_evening": now.hour >= 18,
    }
    logger.debug(f"📅 Time info: {time_info['current_date']} {time_info['current_time']}")
    return time_info


@tool
def create_daily_plan(user_input: str) -> str:
    """
    Create a structured daily plan based on user input using AI reasoning.
    This tool automatically gets current time information and creates a complete plan.

    Args:
        user_input: The user's description of what they want to accomplish today

    Returns:
        JSON string of the created plan with scheduled times
    """
    logger.info(
        f"📋 Creating daily plan for: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'"
    )

    try:
        logger.debug("⏰ Getting time info for planning")
        time_info = get_current_time_info.invoke({})

        planning_prompt = f"""
        You are an expert AI planner. Create a detailed, time-organized daily plan based on the user's input.

        Current Context:
        - Current time: {time_info['current_time']}
        - Date: {time_info['current_date']} ({time_info['day_of_week']})
        - Remaining hours today: {time_info['remaining_hours_today']}
        - Time of day: {'Morning' if time_info['is_morning'] else 'Afternoon' if time_info['is_afternoon'] else 'Evening'}

        User's Request: {user_input}

        CRITICAL INSTRUCTIONS:
        1. You MUST return a PlannerResponse with success=True and a complete DailyPlan object
        2. Break down the user's request into specific tasks (each task needs id, title, description, priority, estimated_duration, scheduled_time, category, status='pending')
        3. Assign realistic time estimates in minutes
        4. Schedule tasks with specific times in HH:MM format
        5. Include appropriate categories: 'work', 'personal', 'health', 'cooking', 'learning', etc.
        6. Set priority as 'high', 'medium', or 'low'
        7. Provide helpful planning notes

        Example format - you must follow this structure exactly:
        daily_plan: {{
            plan_id: "plan_[timestamp]",
            date: "{time_info['current_date']}",
            tasks: [
                {{
                    id: "task-1",
                    title: "Task Name",
                    description: "Brief description",
                    priority: "high",
                    estimated_duration: 30,
                    scheduled_time: "18:00",
                    category: "work",
                    status: "pending"
                }}
            ]
        }}
        """

        logger.debug("🤖 Invoking LLM for plan generation")
        response = structured_llm.invoke(planning_prompt)

        if response.success:
            logger.info("✅ LLM successfully generated plan structure")

            if response.daily_plan:
                response.daily_plan.plan_id = (
                    f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
                )
                response.daily_plan.created_at = datetime.now().isoformat()
                response.daily_plan.current_time = time_info["current_time"]

                # Compute totals if missing
                try:
                    if response.daily_plan.tasks is not None:
                        if not response.daily_plan.total_tasks:
                            response.daily_plan.total_tasks = len(response.daily_plan.tasks)
                        if not response.daily_plan.estimated_total_duration:
                            response.daily_plan.estimated_total_duration = sum(
                                int(
                                    getattr(t, "estimated_duration", 0)
                                )
                                if hasattr(t, "estimated_duration")
                                else int(t.get("estimated_duration", 0))
                                for t in response.daily_plan.tasks
                            )
                except Exception as e:
                    logger.warning(f"⚠️  Could not compute totals: {e}")

                logger.debug(
                    f"💾 Saving structured plan with ID: {response.daily_plan.plan_id}"
                )
                plan_json = save_daily_plan.invoke(
                    {"plan": response.daily_plan.model_dump()}
                )
                logger.info(f"📁 Structured plan saved successfully: {plan_json}")
                return (
                    "✅ Daily plan created successfully!\n\nPlan saved as: "
                    + plan_json
                )
            else:
                logger.info("✅ Generated message-only response")
                return f"✅ {response.message}"
        else:
            logger.warning(
                f"⚠️  LLM failed to create plan: {getattr(response, 'message', 'No message')}"
            )
            return f"❌ Failed to create plan: {response.message}"

    except Exception as e:
        logger.error(f"❌ Error creating daily plan: {str(e)}")
        return f"❌ Error creating daily plan: {str(e)}"


@tool
def save_daily_plan(plan: DailyPlan) -> str:
    """Save a daily plan to JSON file"""
    try:
        plans_dir = Path("plans")
        plans_dir.mkdir(exist_ok=True)

        filename = f"plan_{plan.date}_{datetime.now().strftime('%H%M%S')}.json"
        filepath = plans_dir / filename

        plan_dict = plan.model_dump()

        # Ensure totals exist
        plan_dict["total_tasks"] = plan_dict.get("total_tasks") or len(
            plan_dict.get("tasks", [])
        )
        if not plan_dict.get("estimated_total_duration"):
            plan_dict["estimated_total_duration"] = sum(
                int(t.get("estimated_duration", 0)) for t in plan_dict.get("tasks", [])
            )

        with open(filepath, "w") as f:
            json.dump(plan_dict, f, indent=2)

        return str(filepath)
    except Exception as e:
        return f"Error saving plan: {str(e)}"


@tool
def load_daily_plan(plan_file: str) -> str:
    """Load a daily plan from JSON file"""
    try:
        with open(plan_file, "r") as f:
            plan_data = json.load(f)

        total = plan_data.get("total_tasks") or len(plan_data.get("tasks", []))
        return f"✅ Loaded plan for {plan_data.get('date', 'Unknown')} with {total} tasks"
    except Exception as e:
        return f"❌ Error loading plan: {str(e)}"


@tool
def list_saved_plans() -> str:
    """List all saved daily plans"""
    try:
        plans_dir = Path("plans")
        if not plans_dir.exists():
            return "No plans directory found. Create a plan first!"

        plan_files = list(plans_dir.glob("plan_*.json"))
        if not plan_files:
            return "No saved plans found."

        plans_info = []
        for plan_file in sorted(plan_files, reverse=True):
            try:
                with open(plan_file, "r") as f:
                    plan_data = json.load(f)

                date = plan_data.get("date", "Unknown")
                tasks_count = plan_data.get("total_tasks") or len(
                    plan_data.get("tasks", [])
                )
                created = plan_data.get("created_at", "Unknown")

                created_disp = created[:19] if created and isinstance(created, str) else "Unknown"
                plans_info.append(
                    f"📅 {date} - {tasks_count} tasks (Created: {created_disp}) - File: {plan_file.name}"
                )
            except Exception:
                continue

        return "📋 Saved Plans:\n" + "\n".join(plans_info)
    except Exception as e:
        return f"❌ Error listing plans: {str(e)}"


@tool
def update_task_status(plan_file: str, task_id: str, new_status: str) -> str:
    """Update the status of a specific task in a plan"""
    try:
        with open(plan_file, "r") as f:
            plan_data = json.load(f)

        for task in plan_data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = new_status
                break
        else:
            return f"❌ Task with ID '{task_id}' not found"

        with open(plan_file, "w") as f:
            json.dump(plan_data, f, indent=2)

        return f"✅ Task '{task_id}' status updated to '{new_status}'"
    except Exception as e:
        return f"❌ Error updating task status: {str(e)}"


AGENT_TOOLS = [
    search_web,
    get_current_time_info,
    create_daily_plan,
    save_daily_plan,
    load_daily_plan,
    list_saved_plans,
    update_task_status,
]

