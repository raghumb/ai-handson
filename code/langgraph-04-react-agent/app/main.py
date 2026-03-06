import streamlit as st
import io
from PIL import Image
from agent import run_streaming, run

st.set_page_config(page_title="AI Blog Agent", layout="wide")
st.title("📝 ReAct Blog Generator")

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "current_draft" not in st.session_state:
    st.session_state.current_draft = ""
with st.sidebar:
    st.header("Agent Architecture")

   
    st.text_input("Enter a blog topic:", key="current_topic")

    if st.button("Generate Blog Post"):
        # 1. Create a placeholder for the draft so it updates in real-time
        draft_placeholder = st.empty() 
        
        with st.status("Agent is working...", expanded=True) as status:
            for step in run_streaming(st.session_state.current_topic):
                for node_name, state_update in step.items():
                    st.write(f"Entering Node: `{node_name}`")
                    
                    # Check if the writer produced a new draft
                    if node_name == "writer" and "draft" in state_update:
                        new_draft = state_update["draft"]
                        st.session_state.current_draft = new_draft
                        # Update the placeholder immediately
                        draft_placeholder.markdown(f"### Current Draft\n\n{new_draft}")
                    
                    # Handle validator feedback
                    if node_name == "validator":
                        if state_update.get("is_valid"):
                            st.success("✅ Validation Passed!")
                        else:
                            st.warning(f"❌ Revision Needed: {state_update.get('feedback')}")
    
        st.divider()
        st.subheader("Final Result")
        st.markdown(st.session_state.get("current_draft", "No draft generated yet."))