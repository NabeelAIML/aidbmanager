import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_api_key(default_key_env_var: str, custom_key: str | None):
    if custom_key and custom_key.strip():
        return custom_key.strip()
    return os.getenv(default_key_env_var)


def chosen_llm(model_choice: str, custom_key: str | None = None):
    if model_choice == "Gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=get_api_key("GOOGLE_API_KEY", custom_key),
            temperature=0.3
        )

    elif model_choice == "Mistral":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="mistral-saba-24b",
            api_key=get_api_key("GROQ_API_KEY", custom_key),
            temperature=0.3
        )


def sidebar_llm_choice():

    st.sidebar.subheader("🧠 Model Configuration")

    model_choice = st.sidebar.selectbox(
        "Choose a model",
        options=["Gemini", "Mistral"],
        index=0
    )

    use_custom_key = st.sidebar.radio(
        "API Key Source",
        options=["Provide your own"],
        index=0
    )

    custom_api_key = None
    if use_custom_key == "Provide your own":
        custom_api_key = st.sidebar.text_input(
            "Enter your API key",
            type="password"
        )

    llm = chosen_llm(model_choice, custom_key=custom_api_key)

    return llm