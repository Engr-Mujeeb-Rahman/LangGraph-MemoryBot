from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Checkpointer
conn = sqlite3.connect(database='chatbot.db' , check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():

    threads = {}

    for checkpoint in checkpointer.list(None):
        tid = checkpoint.config['configurable']['thread_id']
        tid = str(tid)  # normalize

        if tid not in threads:

            threads[tid] = {
                "id": tid,
                "title": "New Chat"
            }
            
    return list(threads.values())
