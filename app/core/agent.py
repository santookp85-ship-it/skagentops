"""
Core Agent Logic.
This mocks an "Advanced" agent to focus on the operational wrapping.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .prompts import SYSTEM_PROMPT
from .memory import memory_store

# Use the same OpenAI-compatible endpoint configuration as the Week 15 demos.
# On Vocareum, OPENAI_BASE_URL points to the Vocareum endpoint; with a direct
# OpenAI key it can be omitted.
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.getenv("OPENAI_BASE_URL") or None,
)

def get_agent_response(session_id: str, query: str) -> str:
    """
    Executes the agent logic with history awareness.
    """
    # 1. Retrieve History
    history_dicts = memory_store.get_history(session_id)
    history_messages = []
    
    for msg in history_dicts:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))

    # 2. Construct Chain
    # System Prompt -> History -> New Query
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + history_messages + [HumanMessage(content=query)]
    
    # 3. Execute
    # In a real scenario, this might involve tools, retrieval, etc.
    # We stick to a simple chain for reliability in this demo.
    response = llm.invoke(messages)
    
    # 4. Update Memory
    memory_store.add_message(session_id, "user", query)
    memory_store.add_message(session_id, "assistant", response.content)
    
    return response.content
