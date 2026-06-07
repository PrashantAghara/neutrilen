from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    vision_node,
    nutrition_node,
    memory_node,
    goal_node,
    streak_node,
)

load_dotenv()


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("vision", vision_node)
    builder.add_node("nutrition", nutrition_node)
    builder.add_node("memory", memory_node)
    builder.add_node("goals", goal_node)
    builder.add_node("streak", streak_node)
    builder.set_entry_point("vision")
    builder.add_edge("vision", "nutrition")
    builder.add_edge("nutrition", "memory")
    builder.add_edge("memory", "goals")
    builder.add_edge("goals", "streak")
    builder.add_edge("streak", END)
    return builder.compile()


nutrilens_graph = build_graph()
