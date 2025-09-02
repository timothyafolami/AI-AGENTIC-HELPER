import json
from typing import List, Dict, Any, Optional, Annotated

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel

from agentic_helper.logging_config import setup_logger
from agentic_helper.llm import llm
from agentic_helper.tools import AGENT_TOOLS
from prompts import PLANNING_AGENT_PROMPT, GENERAL_CHAT_PROMPT
from agentic_helper.utils.plans import (
    format_plan_for_display,
    get_latest_plan,
    create_plan_summary,
)


logger = setup_logger()


class AgentState(BaseModel):
    """State for the planning agent"""

    messages: Annotated[List, add_messages]
    current_plan: Optional[Dict[str, Any]] = None
    user_goals: Optional[str] = None
    mode: str = "chat"  # "chat" or "planning"


class PlanningAgent:
    """AI Agent for daily planning and task management"""

    def __init__(self):
        logger.info("🚀 Initializing PlanningAgent")
        self.llm = llm
        self.tools = AGENT_TOOLS
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)

        logger.info(f"📋 Loaded {len(self.tools)} tools: {[tool.name for tool in self.tools]}")

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        logger.info("🏗️  Building LangGraph workflow")

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                "__end__": END,
            },
        )
        workflow.add_conditional_edges(
            "tools",
            self._should_continue,
            {
                "continue": "agent",
                "__end__": END,
            },
        )

        compiled_graph = workflow.compile(debug=True)

        logger.info("✅ LangGraph workflow compiled successfully")
        return compiled_graph

    def _should_continue(self, state: AgentState) -> str:
        messages = state.messages
        if not messages:
            return "continue"

        last_message = messages[-1]
        if hasattr(last_message, "name") and last_message.name == "save_daily_plan":
            if not last_message.content.startswith("❌"):
                logger.info("🎯 Plan saved successfully, ending conversation")
                return "__end__"

        return "continue"

    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        logger.debug(f"🧠 Agent node called with {len(state.messages)} messages")

        messages = state.messages
        logger.debug(f"📝 Current mode: {state.mode}")
        logger.debug(f"💬 Messages count: {len(messages)}")

        latest_message = messages[-1] if messages else None
        is_planning_request = self._is_planning_request(latest_message)
        logger.debug(f"🎯 Is planning request: {is_planning_request}")

        if is_planning_request or state.mode == "planning":
            system_prompt = PLANNING_AGENT_PROMPT
            state.mode = "planning"
            logger.info("📋 Switching to PLANNING mode")
        else:
            system_prompt = GENERAL_CHAT_PROMPT
            state.mode = "chat"
            logger.info("💬 Using CHAT mode")

        system_message = SystemMessage(content=system_prompt)
        context_message = self._get_context_message(state)

        full_messages = [system_message]
        if context_message:
            full_messages.append(context_message)
            logger.debug("📌 Added context message")
        full_messages.extend(messages)

        logger.debug(f"📨 Invoking LLM with {len(full_messages)} total messages")

        try:
            response = self.llm_with_tools.invoke(full_messages)

            if hasattr(response, "tool_calls") and response.tool_calls:
                logger.info(
                    f"🔧 LLM wants to call {len(response.tool_calls)} tools: {[tc['name'] for tc in response.tool_calls]}"
                )
            else:
                logger.info("💭 LLM responded with text (no tool calls)")

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"❌ Error in agent node: {str(e)}")
            error_message = AIMessage(content=f"❌ I encountered an error: {str(e)}")
            return {"messages": [error_message]}

    def _is_planning_request(self, message) -> bool:
        if not message or not hasattr(message, "content"):
            return False

        content = message.content.lower().strip()

        explicit_planning_indicators = [
            "create a plan for",
            "make a plan for",
            "schedule my",
            "plan my day",
            "organize my day",
            "i need a schedule",
            "help me schedule",
            "i want to plan",
            "create my schedule",
            "divide the time",
            "help me divide",
            "split my time",
            "organize my time",
        ]

        has_explicit_request = any(indicator in content for indicator in explicit_planning_indicators)

        activity_indicators = [
            "hour",
            "hours",
            "minutes",
            "am",
            "pm",
            "morning",
            "afternoon",
            "evening",
            "code",
            "coding",
            "exercise",
            "work",
            "study",
            "cook",
            "clean",
            "read",
            "meeting",
            "call",
            "project",
            "task",
            "break",
            "lunch",
            "dinner",
        ]

        has_activities = any(activity in content for activity in activity_indicators)
        is_detailed = len(content.split()) >= 6

        conversational_phrases = [
            "can you help",
            "do you help",
            "are you able",
            "what can you do",
            "how do you",
            "tell me about",
            "explain",
            "what is",
            "can i",
            "is it possible",
            "would you",
            "could you help",
            "can you plan",
        ]
        is_conversational = any(phrase in content for phrase in conversational_phrases)

        concrete_scheduling_phrases = [
            "schedule my",
            "create a detailed schedule",
            "specific times",
            "from 9am",
            "at 10am",
            "until 5pm",
            "9:00",
            "10:30",
            ":00",
            ":30",
            "am ",
            "pm ",
            "o'clock",
            "divide the time",
            "time properly",
            "split the time",
            "organize the time",
            "time block",
            "time allocation",
        ]
        wants_concrete_schedule = any(phrase in content for phrase in concrete_scheduling_phrases)

        should_plan = (wants_concrete_schedule and has_activities) or (
            has_explicit_request and has_activities and is_detailed and not is_conversational
        )

        logger.debug(
            f"Intent analysis: explicit={has_explicit_request}, activities={has_activities}, detailed={is_detailed}, conversational={is_conversational}, should_plan={should_plan}"
        )

        return should_plan

    def _get_context_message(self, state: AgentState) -> Optional[AIMessage]:
        if state.mode != "planning":
            return None

        latest_plan = get_latest_plan()
        if not latest_plan:
            return AIMessage(
                content="📋 No previous plans found. Ready to create your first daily plan!"
            )

        summary = create_plan_summary(latest_plan)
        formatted_plan = format_plan_for_display(latest_plan)

        context = f"""📊 **Current Plan Context:**

{summary}

**Latest Plan Details:**
{formatted_plan}

You can reference this plan or create a new one based on the user's request."""

        return AIMessage(content=context)

    def chat(self, message: str, conversation_history: List = None) -> str:
        logger.info(
            f"💬 Chat started: '{message[:50]}{'...' if len(message) > 50 else ''}'"
        )

        try:
            messages = conversation_history or []
            # If history elements are dicts, coerce to LC messages for safety
            if messages and isinstance(messages[0], dict):
                coerced: List = []
                for m in messages:
                    role = m.get("role")
                    content = m.get("content")
                    if role == "human":
                        coerced.append(HumanMessage(content=content))
                    elif role == "assistant":
                        coerced.append(AIMessage(content=content))
                messages = coerced

            messages.append(HumanMessage(content=message))

            initial_state = AgentState(
                messages=messages, current_plan=get_latest_plan(), mode="chat"
            )

            config = {"recursion_limit": 10, "max_iterations": 5}
            logger.info(f"⚙️  Running graph with config: {config}")
            result = self.graph.invoke(initial_state, config)

            final_message = result["messages"][-1]

            if hasattr(final_message, "content"):
                logger.info(
                    f"📝 Returning response: '{final_message.content[:100]}{'...' if len(final_message.content) > 100 else ''}'"
                )
                return final_message.content
            else:
                return "I apologize, but I encountered an issue processing your request."

        except Exception as e:
            logger.error(f"❌ Chat error: {str(e)}")
            return f"❌ Error: {str(e)}"

    def create_plan_from_text(self, user_input: str) -> str:
        try:
            messages = [HumanMessage(content=f"Create a daily plan for: {user_input}")]

            initial_state = AgentState(
                messages=messages, mode="planning", user_goals=user_input
            )

            result = self.graph.invoke(initial_state)
            final_message = result["messages"][-1]

            return (
                final_message.content
                if hasattr(final_message, "content")
                else "Plan creation failed"
            )

        except Exception as e:
            return f"❌ Error creating plan: {str(e)}"

    def get_plan_status(self) -> str:
        latest_plan = get_latest_plan()
        if not latest_plan:
            return "📋 No active plans found. Create your first plan!"

        summary = create_plan_summary(latest_plan)
        return summary

    def list_available_tools(self) -> str:
        tool_descriptions = []
        for tool in self.tools:
            name = tool.name
            description = tool.description
            tool_descriptions.append(f"🔧 **{name}**: {description}")

        return "🛠️ **Available Tools:**\n\n" + "\n".join(tool_descriptions)

