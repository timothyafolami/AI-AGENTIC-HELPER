import json
from typing import List, Dict, Any, Optional, Annotated
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel
from loguru import logger

from llm_provider import llm
from agent_tools import AGENT_TOOLS
from prompts import PLANNING_AGENT_PROMPT, GENERAL_CHAT_PROMPT
from helper import format_plan_for_display, get_latest_plan, create_plan_summary

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    "ai_agent.log", 
    rotation="10 MB", 
    retention="7 days", 
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
logger.add(
    lambda msg: print(msg), 
    level="INFO",
    format="🤖 {time:HH:mm:ss} | {level} | {message}"
)


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
        
        # Build the graph with increased recursion limit
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the langgraph state graph for the agent"""
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
            }
        )
        workflow.add_conditional_edges(
            "tools",
            self._should_continue,
            {
                "continue": "agent",
                "__end__": END,
            }
        )
        
        # Compile with increased recursion limit and debugging
        compiled_graph = workflow.compile(
            debug=True
        )
        
        logger.info("✅ LangGraph workflow compiled successfully")
        return compiled_graph

    def _should_continue(self, state: AgentState) -> str:
        """Determine if the agent should continue after tool execution"""
        messages = state.messages
        if not messages:
            return "continue"
            
        # Check if the last tool call was save_daily_plan and succeeded
        last_message = messages[-1]
        if hasattr(last_message, 'name') and last_message.name == 'save_daily_plan':
            # If save was successful (no error message), we can end
            if not last_message.content.startswith('❌'):
                logger.info("🎯 Plan saved successfully, ending conversation")
                return "__end__"
        
        return "continue"
    
    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Main agent reasoning node"""
        logger.debug(f"🧠 Agent node called with {len(state.messages)} messages")
        
        messages = state.messages
        
        # Log current state
        logger.debug(f"📝 Current mode: {state.mode}")
        logger.debug(f"💬 Messages count: {len(messages)}")
        
        # Determine if this is a planning request
        latest_message = messages[-1] if messages else None
        is_planning_request = self._is_planning_request(latest_message)
        
        logger.debug(f"🎯 Is planning request: {is_planning_request}")
        
        # Choose appropriate system prompt
        if is_planning_request or state.mode == "planning":
            system_prompt = PLANNING_AGENT_PROMPT
            state.mode = "planning"
            logger.info("📋 Switching to PLANNING mode")
        else:
            system_prompt = GENERAL_CHAT_PROMPT
            state.mode = "chat"
            logger.info("💬 Using CHAT mode")
        
        # Prepare messages with system prompt
        system_message = SystemMessage(content=system_prompt)
        
        # Add context about current plans if available
        context_message = self._get_context_message(state)
        
        full_messages = [system_message]
        if context_message:
            full_messages.append(context_message)
            logger.debug("📌 Added context message")
        full_messages.extend(messages)
        
        logger.debug(f"📨 Invoking LLM with {len(full_messages)} total messages")
        
        # Get response from LLM
        try:
            response = self.llm_with_tools.invoke(full_messages)
            
            # Log response details
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"🔧 LLM wants to call {len(response.tool_calls)} tools: {[tc['name'] for tc in response.tool_calls]}")
            else:
                logger.info("💭 LLM responded with text (no tool calls)")
            
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"❌ Error in agent node: {str(e)}")
            error_message = AIMessage(content=f"❌ I encountered an error: {str(e)}")
            return {"messages": [error_message]}
    
    def _is_planning_request(self, message) -> bool:
        """Detect if the message is requesting actual planning (not just conversation about planning)"""
        if not message or not hasattr(message, 'content'):
            return False
            
        content = message.content.lower().strip()
        
        # Explicit planning requests with details
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
            "organize my time"
        ]
        
        # Check for explicit planning requests
        has_explicit_request = any(indicator in content for indicator in explicit_planning_indicators)
        
        # Must also contain specific activities or time details
        activity_indicators = [
            "hour", "hours", "minutes", "am", "pm", "morning", "afternoon", "evening",
            "code", "coding", "exercise", "work", "study", "cook", "clean", "read", 
            "meeting", "call", "project", "task", "break", "lunch", "dinner"
        ]
        
        has_activities = any(activity in content for activity in activity_indicators)
        
        # Length check - detailed requests are usually longer
        is_detailed = len(content.split()) >= 6
        
        # Exclude conversational inquiries - these should stay in chat mode
        conversational_phrases = [
            "can you help", "do you help", "are you able", "what can you do",
            "how do you", "tell me about", "explain", "what is", "can i",
            "is it possible", "would you", "could you help", "can you plan"
        ]
        
        is_conversational = any(phrase in content for phrase in conversational_phrases)
        
        # Strong indicators that user wants a concrete scheduled plan NOW
        concrete_scheduling_phrases = [
            "schedule my", "create a detailed schedule", "specific times", 
            "from 9am", "at 10am", "until 5pm", "9:00", "10:30", ":00", ":30",
            "am ", "pm ", "o'clock", "divide the time", "time properly", 
            "split the time", "organize the time", "time block", "time allocation"
        ]
        
        wants_concrete_schedule = any(phrase in content for phrase in concrete_scheduling_phrases)
        
        # Only trigger planning mode if:
        # 1. Wants concrete schedule AND has activities 
        # 2. OR has explicit planning request AND activities AND is detailed AND NOT conversational
        should_plan = (
            (wants_concrete_schedule and has_activities) or
            (has_explicit_request and has_activities and is_detailed and not is_conversational)
        )
        
        logger.debug(f"Intent analysis: explicit={has_explicit_request}, activities={has_activities}, detailed={is_detailed}, conversational={is_conversational}, should_plan={should_plan}")
        
        return should_plan
    
    def _get_context_message(self, state: AgentState) -> Optional[AIMessage]:
        """Get context about current plans"""
        if state.mode != "planning":
            return None
            
        latest_plan = get_latest_plan()
        if not latest_plan:
            return AIMessage(content="📋 No previous plans found. Ready to create your first daily plan!")
        
        summary = create_plan_summary(latest_plan)
        formatted_plan = format_plan_for_display(latest_plan)
        
        context = f"""📊 **Current Plan Context:**

{summary}

**Latest Plan Details:**
{formatted_plan}

You can reference this plan or create a new one based on the user's request."""
        
        return AIMessage(content=context)
    
    def chat(self, message: str, conversation_history: List = None) -> str:
        """Main chat interface for the agent"""
        logger.info(f"💬 Chat started: '{message[:50]}{'...' if len(message) > 50 else ''}'")
        
        try:
            # Prepare initial state
            messages = conversation_history or []
            messages.append(HumanMessage(content=message))
            
            initial_state = AgentState(
                messages=messages,
                current_plan=get_latest_plan(),
                mode="chat"
            )
            
            logger.debug(f"🚀 Starting graph execution with initial state")
            logger.debug(f"📋 Current plan available: {initial_state.current_plan is not None}")
            
            # Run the graph with configuration
            config = {
                "recursion_limit": 10,  # Reduced from default 25
                "max_iterations": 5     # Additional safety
            }
            
            logger.info(f"⚙️  Running graph with config: {config}")
            result = self.graph.invoke(initial_state, config)
            
            logger.debug(f"✅ Graph execution completed")
            logger.debug(f"📤 Result messages count: {len(result.get('messages', []))}")
            
            # Extract the final response
            final_message = result["messages"][-1]
            
            if hasattr(final_message, 'content'):
                logger.info(f"📝 Returning response: '{final_message.content[:100]}{'...' if len(final_message.content) > 100 else ''}'")
                return final_message.content
            else:
                logger.warning("⚠️  Final message has no content attribute")
                return "I apologize, but I encountered an issue processing your request."
                
        except Exception as e:
            logger.error(f"❌ Chat error: {str(e)}")
            logger.exception("Full error traceback:")
            return f"❌ Error: {str(e)}"
    
    def create_plan_from_text(self, user_input: str) -> str:
        """Shortcut method to directly create a plan"""
        try:
            # Force planning mode
            messages = [HumanMessage(content=f"Create a daily plan for: {user_input}")]
            
            initial_state = AgentState(
                messages=messages,
                mode="planning",
                user_goals=user_input
            )
            
            result = self.graph.invoke(initial_state)
            final_message = result["messages"][-1]
            
            return final_message.content if hasattr(final_message, 'content') else "Plan creation failed"
            
        except Exception as e:
            return f"❌ Error creating plan: {str(e)}"
    
    def get_plan_status(self) -> str:
        """Get status of the current plan"""
        latest_plan = get_latest_plan()
        if not latest_plan:
            return "📋 No active plans found. Create your first plan!"
        
        summary = create_plan_summary(latest_plan)
        return summary
    
    def list_available_tools(self) -> str:
        """List all available tools"""
        tool_descriptions = []
        for tool in self.tools:
            name = tool.name
            description = tool.description
            tool_descriptions.append(f"🔧 **{name}**: {description}")
        
        return "🛠️ **Available Tools:**\n\n" + "\n".join(tool_descriptions)


# Initialize the global agent instance
planning_agent = PlanningAgent()


def chat_with_agent(message: str, history: List = None) -> str:
    """Convenient function to chat with the planning agent"""
    return planning_agent.chat(message, history)


def create_quick_plan(goals: str) -> str:
    """Quick function to create a plan"""
    return planning_agent.create_plan_from_text(goals)


def get_agent_status() -> str:
    """Get current agent and plan status"""
    status = planning_agent.get_plan_status()
    tools_info = f"\n\n🛠️ **Agent Ready** with {len(AGENT_TOOLS)} tools available"
    return status + tools_info


# Example usage and testing
if __name__ == "__main__":
    # Test the agent
    agent = PlanningAgent()
    
    print("🤖 Planning Agent initialized!")
    print(get_agent_status())
    
    # Test basic chat
    response = agent.chat("Hello! I need help planning my day.")
    print(f"\n💬 Agent Response:\n{response}")
    
    # Test planning
    plan_response = agent.create_plan_from_text("I want to learn Python, exercise, and cook dinner today")
    print(f"\n📋 Plan Response:\n{plan_response}")
