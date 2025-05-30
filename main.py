import streamlit as st
from agents import gemini_sql_agent, optimizer_model, explain_agent_trace, visalize_response
from sidebar_llm_component import sidebar_llm_choice
from sidebar_database_component import sidebar_database_choice
import matplotlib.pyplot as plt


# Streamlit UI config
st.set_page_config(page_title='AI Database Manager')
st.title('🧠 Talk to Your Database')

####################################
# -------- Side Bars ------------ #
####################################

# ------- LLM Choice -------

llm = sidebar_llm_choice()

# --- DATABASE SELECTION ---

db = sidebar_database_choice()

###########################################
# ---------- Main Frame ---------------- #
##########################################

# Initialize session state to store messages
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_table" not in st.session_state:
    st.session_state.last_table = None

# Input from user
user_input = st.chat_input("Ask something about your data...")

# Display chat history
for i, (user, bot) in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.markdown(user)
    with st.chat_message("assistant"):
        st.markdown(bot)

# Handle user input
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response, logs = gemini_sql_agent(user_input, logs=True, llm=llm, db=db)
                final_answer = response

                if response == "I don't know":
                    response = optimizer_model(user_input, response, llm=llm)
                    st.markdown(response)
                else:
                    response = explain_agent_trace(user_input, response, logs, llm=llm)
                    st.markdown(response)
                    # st.markdown('Debug Final Answer')
                    # st.markdown(final_answer)
                    st.session_state.last_table = final_answer

                st.session_state.chat_history.append((user_input, response))

            except Exception as e:
                st.markdown(f"❌ Error: {e}")


# If output looks like a table, offer visualization
if st.session_state.last_table is not None:
    # Visualization
    if st.button("📊 Visualize"):
        with st.chat_message("assistant"):
            with st.spinner("Generating Visuals..."):

                figs = visalize_response(response=st.session_state.last_table, llm=llm)

                for fig in figs:
                    st.pyplot(fig)
                plt.close("all")


###########################
# Clear Messages Button
###########################

with st.sidebar:
    st.markdown("---")
    if st.button("🧹 Clear Messages"):
        st.session_state.chat_history = []
        st.session_state.last_table = None
        st.rerun()

