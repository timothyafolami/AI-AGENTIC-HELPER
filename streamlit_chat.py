import streamlit as st
import json
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
    latest_plan = get_latest_plan()
    
    if latest_plan:
        progress = calculate_plan_progress(latest_plan)
        
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
            st.markdown(format_plan_for_display(latest_plan))
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("📊 Show Plan Summary", type="secondary"):
            st.session_state.show_plan_summary = True
        if st.button("📝 Create New Plan", type="primary"):
            st.session_state.create_new_plan = True
            
    else:
        st.info("No plans created yet. Ask me to create your first daily plan!")
    
    st.markdown("---")
    
    # Chat controls (simplified)
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.messages = [SystemMessage(content=GENERAL_CHAT_PROMPT)]
        st.rerun()

# Main chat interface
st.title("💬 AI Planning Assistant")
st.markdown("🎯 Your intelligent daily planning companion with tools for scheduling, task management, and productivity!")

# Handle quick actions
if hasattr(st.session_state, 'show_plan_summary') and st.session_state.show_plan_summary:
    if latest_plan:
        st.info("📊 Displaying plan summary in chat...")
        st.session_state.messages.append(HumanMessage(content="Show me my current plan summary"))
        st.session_state.show_plan_summary = False
        st.rerun()

if hasattr(st.session_state, 'create_new_plan') and st.session_state.create_new_plan:
    st.info("📝 Starting new plan creation...")
    st.session_state.messages.append(HumanMessage(content="Help me create a new daily plan"))
    st.session_state.create_new_plan = False
    st.rerun()

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

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        try:
            # Show thinking indicator
            with st.spinner("🤔 Planning and thinking..."):
                # Convert messages to simple format for the agent
                # Pass actual LangChain message objects (excluding system and the current prompt)
                conversation_history = st.session_state.messages[1:-1]
                
                # Get response from planning agent with timeout handling
                import threading
                import time
                
                # Use a simple shared container to avoid nonlocal issues
                result = {"response": None, "error": False, "completed": False}
                
                def agent_call():
                    try:
                        result["response"] = planning_agent.chat(prompt, conversation_history)
                        result["completed"] = True
                    except Exception as e:
                        result["error"] = True
                        result["response"] = f"I encountered an error: {str(e)}. Please try again."
                        result["completed"] = True
                
                # Run agent call in thread with timeout
                thread = threading.Thread(target=agent_call)
                thread.daemon = True
                thread.start()
                
                # Wait for completion with timeout
                timeout_seconds = 30
                start_time = time.time()
                while thread.is_alive() and (time.time() - start_time) < timeout_seconds:
                    time.sleep(0.1)
                
                # Check results
                if thread.is_alive():
                    response_content = "⏰ I'm taking longer than expected to respond. This might be due to a complex planning request. Please try simplifying your message or try again."
                elif result["error"]:
                    st.warning("⚠️ An error occurred while processing your request.")
                    response_content = result["response"]
                elif result["completed"]:
                    response_content = result["response"]
                else:
                    response_content = "I'm having trouble processing your request right now. Please try again."
            
            # Display the response
            st.markdown(response_content)
            
            # Add assistant response to chat history
            st.session_state.messages.append(AIMessage(content=response_content))
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.error("Please check your environment variables and API key.")
            st.info("💡 Try asking: 'Create a plan for my day' or 'Help me organize my tasks'")

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
