# ADR: Agentic AI Architecture & LangGraph StateGraph Standards

## 1. Context & Architectural Rationale
When designing autonomous or semi-autonomous multi-agent systems, monolithic agent loops (single prompt with continuous tool calling) fail on complex multi-step reasoning due to context drift and prompt pollution.

## 2. Decision: LangGraph StateGraph Architecture
All agentic workflows must be modeled as a directed `StateGraph`:
1. **Explicit Typed State**: Use `TypedDict` or `Pydantic` models to define state keys (`query`, `contexts`, `confidence`, `verdict`, `patch`).
2. **Deterministic Routing**: Conditional edges must inspect explicit state fields rather than relying on unstructured LLM output text.
3. **Tool Calling Encapsulation**: Tools must use `@tool` decorators with strict Pydantic v2 schemas and isolated execution sandboxes.
4. **Human-in-the-Loop & Memory**: Use checkpointers (e.g., `MemorySaver` or SQLite checkpointer) for persistence across agent turns.

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    task: str
    code_diff: str
    test_passed: bool
    iterations: int

def node_synthesize(state: AgentState) -> dict:
    return {"code_diff": "--- a/file.py...", "iterations": state["iterations"] + 1}

def route_next(state: AgentState) -> Literal["synthesize", "finish"]:
    if state["test_passed"] or state["iterations"] >= 3:
        return "finish"
    return "synthesize"

builder = StateGraph(AgentState)
builder.add_node("synthesize", node_synthesize)
builder.add_conditional_edges("synthesize", route_next, {"synthesize": "synthesize", "finish": END})
builder.add_edge(START, "synthesize")
graph = builder.compile()
```
