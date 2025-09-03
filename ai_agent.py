from typing import List, Optional

from agentic_helper.agent.planning import PlanningAgent
from agentic_helper.tools import ALL_TOOLS


# Initialize the global agent instance (backward‑compatible module)
planning_agent = PlanningAgent()


def chat_with_agent(message: str, history: List = None, thread_id: Optional[str] = None) -> str:
    return planning_agent.chat(message, history, thread_id=thread_id)


def create_quick_plan(goals: str, thread_id: Optional[str] = None) -> str:
    return planning_agent.create_plan_from_text(goals)


def get_agent_status() -> str:
    status = planning_agent.get_plan_status()
    tools_info = f"\n\n🛠️ **Agent Ready** with {len(ALL_TOOLS)} tools available"
    return status + tools_info


if __name__ == "__main__":
    agent = PlanningAgent()
    print("🤖 Planning Agent initialized!")
    print(get_agent_status())
    response = agent.chat("Hello! I need help planning my day.")
    print(f"\n💬 Agent Response:\n{response}")
    plan_response = agent.create_plan_from_text(
        "I want to learn Python, exercise, and cook dinner today"
    )
    print(f"\n📋 Plan Response:\n{plan_response}")
