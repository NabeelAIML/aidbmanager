from langchain_community.agent_toolkits import create_sql_agent
from prompts import optimizer_prompt, explanation_prompt, df_parse_prompt, code_prompt
from contextlib import redirect_stdout
import streamlit as st
import numpy as np
from io import StringIO
import pandas as pd
import matplotlib.pyplot as plt
import re
import io

# Gemini SQL Agent

def gemini_sql_agent(user_input: str, llm, db, logs: bool = False):

    # No need for SQLAgentLogger here since callbacks not used by agent internally
    callbacks = []

    agent = create_sql_agent(
        llm,
        db=db,
        agent_type="zero-shot-react-description",
        verbose=True,
        callbacks=callbacks,
    )

    if logs:
        f = io.StringIO()
        with redirect_stdout(f):
            result = agent.invoke(user_input)
        logs_output = f.getvalue()
        response = result["output"]
        return response, logs_output
    else:
        result = agent.invoke(user_input)
        response = result["output"]
        return response

# Explainer Model

def extract_sql_query_from_logs(logs: str) -> str:
    # Looks for SQL-looking lines in the logs
    matches = re.findall(r"(SELECT|WITH).*?;", logs, re.DOTALL | re.IGNORECASE)
    return matches[0].strip() if matches else "SQL query not found."

def explain_agent_trace(user_input: str, response: str, logs: str, llm) -> str:
    sql_query = extract_sql_query_from_logs(logs)

    explanation_prompt_filled = explanation_prompt.format(
        user_input=user_input,
        logs=logs,
        sql_query=sql_query,
        response=response
    )

    explanation = llm.invoke(explanation_prompt_filled)

    return explanation.content



# Optimizer
def optimizer_model(user_query, sql_response, llm):
    optimizer_response = llm.invoke(
        optimizer_prompt.format(
            input=user_query,
            sql_response=sql_response
        )
    )
    return optimizer_response.content


# Visualizer

def visalize_response(response, llm):
    format_request = df_parse_prompt.format(response=response)
    formatted_table = llm.invoke(format_request).content.strip()

    # st.code(formatted_table, language="csv")

    df = pd.read_csv(StringIO(formatted_table))
    # st.write(df)

    # 2. Pass to Pandas agent

    # Ask LLM to generate plotting code
    llm_response = llm.invoke(code_prompt.format(df_head=df.head().to_markdown()))
    # st.write(llm_response)

    code_match = re.search(r"```python\n(.*?)```", llm_response.content, re.DOTALL)
    # st.write(code_match)

    code = code_match.group(1)
    # st.code(code, language="python")

    # Replace hardcoded df creation if present
    code = re.sub(r"(?s)data\s*=.*?df\s*=\s*pd\.DataFrame\(data\)", "# removed hardcoded df assignment",
                  code)

    # Safe exec context
    safe_globals = {
        "df": df,  # actual df from user input
        "plt": plt,
        "np": np,
        "pd": pd,
        "sns": __import__('seaborn'),
        "st": st  # optional, if you want to pass st into LLM code
    }

    # Execute safely and render plots

    exec(code, safe_globals)

    # Ensure we render every open figure
    figs = [plt.figure(n) for n in plt.get_fignums()]

    return figs
