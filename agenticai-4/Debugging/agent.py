from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import START, END
from langgraph.graph.state import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage
from langchain.tools import tool
from langchain_groq import ChatGroq

import os
from dotenv import load_dotenv
load_dotenv()

# Environment setup
os.environ["LANGSMITH_PROJECT"] = "langchainLearning"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"

# Model
llm = ChatGroq(model_name="qwen/qwen3-32b")

# State definition
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Graph factory
def make_tool_graph():
    @tool
    def add_numbers(a: float, b: float) -> float:
        """Add two numbers"""
        return a + b

    tools = [add_numbers]
    llm_with_tool = llm.bind_tools(tools)

    def call_llm_model(state: State):
        return {"messages": [llm_with_tool.invoke(state["messages"])]}

    builder = StateGraph(State)
    builder.add_node("tool_calling_llm", call_llm_model)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "tool_calling_llm")
    builder.add_conditional_edges("tool_calling_llm", tools_condition)
    builder.add_edge("tools", "tool_calling_llm")

    graph = builder.compile()

    # Optional: render in notebook only
    try:
        from IPython.display import display, Image
        display(Image(graph.get_graph().draw_mermaid_png()))
    except:
        pass

    return graph

tool_agent = make_tool_graph()
