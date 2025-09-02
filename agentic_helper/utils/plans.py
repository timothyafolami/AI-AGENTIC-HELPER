import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def format_plan_for_display(plan_data: Dict[str, Any]) -> str:
    """Format a daily plan for nice display in the chat interface"""
    try:
        tasks = plan_data.get("tasks", [])
        date = plan_data.get("date", "Unknown")
        total_duration = plan_data.get("estimated_total_duration", 0)
        planning_notes = plan_data.get("planning_notes", "")

        formatted = f"""
📅 **Daily Plan for {date}**
⏱️ **Total estimated time:** {total_duration} minutes ({total_duration // 60}h {total_duration % 60}m)
📝 **Total tasks:** {len(tasks)}

**Tasks Schedule:**
"""

        for i, task in enumerate(tasks, 1):
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
            }.get(task.get("status", "pending"), "⏳")

            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(task.get("priority", "medium"), "🟡")

            formatted += f"""
{i}. {status_emoji} **{task.get('title', 'Untitled')}** {priority_emoji}
   ⏰ **Time:** {task.get('scheduled_time', 'TBD')} ({task.get('estimated_duration', 0)} min)
   📂 **Category:** {task.get('category', 'General')}
   📝 **Description:** {task.get('description', 'No description')}
"""

        if planning_notes:
            formatted += f"\n💡 **Planning Notes:**\n{planning_notes}"

        return formatted
    except Exception as e:
        return f"❌ Error formatting plan: {str(e)}"


def get_latest_plan() -> Optional[Dict[str, Any]]:
    """Get the most recently created plan"""
    try:
        plans_dir = Path("plans")
        if not plans_dir.exists():
            return None

        plan_files = list(plans_dir.glob("plan_*.json"))
        if not plan_files:
            return None

        latest_file = max(plan_files, key=lambda x: x.stat().st_mtime)

        with open(latest_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def create_plan_summary(plan_data: Dict[str, Any]) -> str:
    """Create a brief summary of a plan"""
    try:
        total_tasks = len(plan_data.get("tasks", []))
        completed_tasks = len(
            [t for t in plan_data.get("tasks", []) if t.get("status") == "completed"]
        )
        date = plan_data.get("date", "Unknown")

        return f"📊 Plan Summary for {date}: {completed_tasks}/{total_tasks} tasks completed"
    except Exception as e:
        return f"Error creating summary: {str(e)}"


def validate_time_format(time_str: str) -> bool:
    """Validate if a time string is in HH:MM format"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def get_task_by_id(plan_data: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """Find a specific task by ID in a plan"""
    for task in plan_data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def calculate_plan_progress(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate progress statistics for a plan"""
    tasks = plan_data.get("tasks", [])
    total_tasks = len(tasks)

    if total_tasks == 0:
        return {
            "total_tasks": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "completion_percentage": 0,
            "estimated_remaining_time": 0,
        }

    completed = len([t for t in tasks if t.get("status") == "completed"])
    in_progress = len([t for t in tasks if t.get("status") == "in_progress"])
    pending = len([t for t in tasks if t.get("status") == "pending"])

    completion_percentage = (completed / total_tasks) * 100

    remaining_time = sum(
        t.get("estimated_duration", 0) for t in tasks if t.get("status") != "completed"
    )

    return {
        "total_tasks": total_tasks,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "completion_percentage": round(completion_percentage, 1),
        "estimated_remaining_time": remaining_time,
    }


def export_plan_to_markdown(plan_data: Dict[str, Any]) -> str:
    """Export a plan to markdown format"""
    try:
        date = plan_data.get("date", "Unknown")
        total_duration = plan_data.get("estimated_total_duration", 0)
        planning_notes = plan_data.get("planning_notes", "")
        tasks = plan_data.get("tasks", [])

        markdown = f"""# Daily Plan - {date}

**Total Estimated Time:** {total_duration // 60}h {total_duration % 60}m
**Total Tasks:** {len(tasks)}

## Tasks

"""

        for i, task in enumerate(tasks, 1):
            status = "- [x]" if task.get("status") == "completed" else "- [ ]"
            priority = task.get("priority", "medium").upper()

            markdown += f"""{status} **{task.get('title', 'Untitled')}** ({priority})
   - **Time:** {task.get('scheduled_time', 'TBD')} ({task.get('estimated_duration', 0)} min)
   - **Category:** {task.get('category', 'General')}
   - **Description:** {task.get('description', 'No description')}

"""

        if planning_notes:
            markdown += f"""## Planning Notes

{planning_notes}
"""

        return markdown
    except Exception as e:
        return f"Error creating markdown: {str(e)}"

