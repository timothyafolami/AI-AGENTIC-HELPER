from datetime import datetime
import sys
import os

# Ensure package root on path when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agentic_helper.models import DailyPlan, TodoTask
from agentic_helper.tools.planning import save_daily_plan, list_saved_plans


def build_sample_plan() -> DailyPlan:
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = [
        TodoTask(
            id="task_1",
            title="Sample Coding",
            description="Work on sample feature",
            priority="high",
            estimated_duration=60,
            scheduled_time="09:00",
            category="work",
            status="pending",
        ),
        TodoTask(
            id="task_2",
            title="Sample Exercise",
            description="30-min run",
            priority="medium",
            estimated_duration=30,
            scheduled_time="10:30",
            category="health",
            status="pending",
        ),
    ]
    return DailyPlan(
        plan_id="plan_smoke_test",
        date=today,
        tasks=tasks,
        created_at=datetime.now().isoformat(),
        current_time=datetime.now().strftime("%H:%M"),
        total_tasks=len(tasks),
        estimated_total_duration=sum(t.estimated_duration for t in tasks),
        planning_notes="Storage smoke test plan",
    )


def main():
    plan = build_sample_plan()
    path = save_daily_plan.invoke({"plan": plan.model_dump()})
    print("Saved:", path)
    print()
    print(list_saved_plans.invoke({}))


if __name__ == "__main__":
    main()
