
from langgraph.graph import StateGraph, END
from app.agents.state import ComplaintState
from app.agents.nodes import (
    extract_fields_node,
    completeness_check_node,
    severity_priority_node,
    duplicate_check_node,
    root_cause_node,
    capa_node,
    summary_node,
)


def build_graph():
    graph = StateGraph(ComplaintState)

    graph.add_node("extract", extract_fields_node)
    graph.add_node("completeness_check", completeness_check_node)
    graph.add_node("severity_priority", severity_priority_node)
    graph.add_node("duplicate_check", duplicate_check_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("capa", capa_node)
    graph.add_node("summary", summary_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "completeness_check")
    graph.add_edge("completeness_check", "severity_priority")
    graph.add_edge("severity_priority", "duplicate_check")
    graph.add_edge("duplicate_check", "root_cause")
    graph.add_edge("root_cause", "capa")
    graph.add_edge("capa", "summary")
    graph.add_edge("summary", END)

    return graph.compile()



complaint_graph = build_graph()
