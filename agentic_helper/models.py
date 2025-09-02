from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TodoTask(BaseModel):
    """A single todo task with time planning"""

    id: str = Field(description="Unique identifier for the task")
    title: str = Field(description="Brief title of the task")
    description: str = Field(description="Detailed description of what needs to be done")
    priority: str = Field(description="Priority level: high, medium, low")
    estimated_duration: int = Field(description="Estimated duration in minutes")
    scheduled_time: str = Field(description="Suggested time to start the task (HH:MM format)")
    category: str = Field(description="Category of the task (work, personal, health, etc.)")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")


class DailyPlan(BaseModel):
    """A complete daily plan with multiple todo tasks"""

    plan_id: str = Field(description="Unique identifier for this plan")
    date: str = Field(description="Date for this plan (YYYY-MM-DD format)")
    tasks: List[TodoTask] = Field(description="List of todo tasks")
    created_at: Optional[str] = Field(default=None, description="When this plan was created (ISO timestamp)")
    current_time: Optional[str] = Field(default=None, description="Current time when plan was created")
    total_tasks: Optional[int] = Field(default=None, description="Total number of tasks in the plan")
    estimated_total_duration: Optional[int] = Field(
        default=None, description="Total estimated duration in minutes"
    )
    planning_notes: Optional[str] = Field(
        default=None, description="AI's reasoning and notes about the planning decisions"
    )


class PlannerResponse(BaseModel):
    """Response from the AI planner with structured output"""

    success: bool = Field(description="Whether planning was successful")
    daily_plan: Optional[DailyPlan] = Field(default=None, description="The generated daily plan")
    message: str = Field(description="Human-readable message about the planning result")
    suggestions: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional suggestions or recommendations as a flexible object"
    )

