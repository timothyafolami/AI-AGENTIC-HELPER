import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from prompts import GENERAL_CHAT_PROMPT
from ai_agent import planning_agent, get_agent_status
from agentic_helper.utils.plans import (
    format_plan_for_display,
    get_latest_plan,
    calculate_plan_progress,
)

# Page configuration
st.set_page_config(
    page_title="AI Assistant Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add the system prompt as the first message (won't be displayed)
    st.session_state.messages.append(SystemMessage(content=GENERAL_CHAT_PROMPT))
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit"
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Sidebar with chat settings and plan viewer
with st.sidebar:
    st.title("🤖 AI Planning Assistant")
    st.markdown("---")
    
    # Agent status
    st.subheader("🚀 Agent Status")
    try:
        status = get_agent_status()
        st.success(status)
    except:
        st.warning("Agent initializing...")
    
    # Plan viewer section
    st.subheader("📋 Current Plan")
    # Show only today's plan in the viewer
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_plan = None
    try:
        today_path = Path("plans") / f"plan_{today_str}.json"
        if today_path.exists():
            with open(today_path, "r") as f:
                today_plan = json.load(f)
    except Exception:
        today_plan = None

    def _is_demo_plan(plan: dict) -> bool:
        try:
            if plan.get("plan_id") == "plan_smoke_test":
                return True
            notes = (plan.get("planning_notes") or "").lower()
            return "storage smoke test" in notes
        except Exception:
            return False

    if today_plan and not _is_demo_plan(today_plan):
        progress = calculate_plan_progress(today_plan)
        
        # Progress metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Completed", f"{progress['completed']}/{progress['total_tasks']}")
        with col2:
            st.metric("Progress", f"{progress['completion_percentage']:.1f}%")
        
        # Progress bar
        if progress['total_tasks'] > 0:
            st.progress(progress['completion_percentage'] / 100)
        
        # Plan details expander
        with st.expander("📅 View Plan Details"):
            st.markdown(format_plan_for_display(today_plan))
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("📊 Show Plan Summary", type="secondary"):
            st.session_state.pending_prompt = "Show me my current plan summary"
            st.rerun()
        if st.button("📝 Create New Plan", type="primary"):
            st.session_state.pending_prompt = "Help me create a new daily plan"
            st.rerun()
            
    else:
        st.info("No plan created for today yet.")
    
    st.markdown("---")
    
    # Chat controls (simplified)
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.messages = [SystemMessage(content=GENERAL_CHAT_PROMPT)]
        st.rerun()

# Main chat interface
st.title("💬 AI Planning Assistant")
st.markdown("🎯 Your intelligent daily planning companion with tools for scheduling, task management, and productivity!")

def _process_prompt(prompt_text: str):
    # Add user message and render
    st.session_state.messages.append(HumanMessage(content=prompt_text))
    with st.chat_message("user"):
        st.markdown(prompt_text)

    # Prepare conversation history (exclude system and the last just-added human)
    conversation_history = st.session_state.messages[1:-1]

    # Resolve thread id on main thread
    local_thread_id = st.session_state.get("thread_id", "streamlit")

    # Generate and display assistant response
    with st.chat_message("assistant"):
        try:
            # Show thinking indicator
            with st.spinner("🤔 Planning and thinking..."):
                import threading, time

                result = {"response": None, "error": False, "completed": False}

                def agent_call():
                    try:
                        result["response"] = planning_agent.chat(
                            prompt_text, conversation_history, thread_id=local_thread_id
                        )
                        result["completed"] = True
                    except Exception as e:
                        result["error"] = True
                        result["response"] = f"I encountered an error: {str(e)}. Please try again."
                        result["completed"] = True

                thread = threading.Thread(target=agent_call)
                thread.daemon = True
                thread.start()

                timeout_seconds = 30
                start_time = time.time()
                while thread.is_alive() and (time.time() - start_time) < timeout_seconds:
                    time.sleep(0.1)

                if thread.is_alive():
                    response_content = "⏰ I'm taking longer than expected to respond. This might be due to a complex planning request. Please try simplifying your message or try again."
                elif result["error"]:
                    st.warning("⚠️ An error occurred while processing your request.")
                    response_content = result["response"]
                else:
                    response_content = result["response"]

            st.markdown(response_content)
            st.session_state.messages.append(AIMessage(content=response_content))
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.error("Please check your environment variables and API key.")
            st.info("💡 Try asking: 'Create a plan for my day' or 'Help me organize my tasks'")

# Display chat messages (excluding system message)
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(message.content)

if st.session_state.pending_prompt:
    pending = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    _process_prompt(pending)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    _process_prompt(prompt)

# Example prompts section
with st.expander("💡 Example Planning Prompts"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Planning Requests:**
        - "Plan my productive day"
        - "I want to exercise, work, and cook today"
        - "Create a study schedule for 4 hours"
        - "Help me organize my weekend"
        """)
    
    with col2:
        st.markdown("""
        **📊 Plan Management:**
        - "Show my current plan"
        - "Mark task as completed"
        - "Update my schedule"
        - "Search for productivity tips"
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🚀 Built with Streamlit, Groq LLM, and LangGraph • AI Planning Assistant v1.0
    </div>
    """, 
    unsafe_allow_html=True
)
