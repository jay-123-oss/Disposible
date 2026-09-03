"""Master Intent Router (Layer 1) for Antigravity+ IDE.

Built with LangChain and LangGraph:
- Analyzes user input to determine the execution route.
- Routes:
    1. CHAT: Casual greetings, conceptual questions, explanations
    2. CODE_SINGLE: Specific single file request or snippet
    3. PROJECT_ARCH: Multi-file project / landing page / full-stack app
    4. SYSTEM_CMD: Direct IDE or terminal operations / npm / server run
- Returns STRICTLY valid JSON with route, confidence, reasoning, and extracted_entities.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field

# LangChain & LangGraph Imports
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

RouteType = Literal["CHAT", "CODE_SINGLE", "PROJECT_ARCH", "SYSTEM_CMD"]


class RouterOutput(BaseModel):
    """Pydantic schema for structured Master Intent Router output."""

    route: RouteType = Field(
        ...,
        description="The chosen execution route: CHAT | CODE_SINGLE | PROJECT_ARCH | SYSTEM_CMD",
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score between 0 and 100",
    )
    reasoning: str = Field(
        ...,
        description="Short 1-sentence explanation of why this route was chosen",
    )
    extracted_entities: List[str] = Field(
        default_factory=list,
        description="Any specific tech, tools, or filenames mentioned",
    )


class RouterState(TypedDict):
    """LangGraph state schema for Layer 1 Master Intent Routing."""

    user_input: str
    route: Optional[RouteType]
    confidence: int
    reasoning: str
    extracted_entities: List[str]
    final_output: Optional[Dict[str, Any]]


ROUTER_SYSTEM_PROMPT = """You are the Master Intent Router (Layer 1) for an advanced Autonomous IDE (Antigravity+). 
Your ONLY job is to analyze the user's input and determine the exact execution route required. You are a silent backend component. 

DO NOT write code. DO NOT generate files. DO NOT reply with conversational text or greetings.
You must reply STRICTLY with a single JSON object.

### INTENT CATEGORIES (ROUTES):

1. "CHAT"
- Use for: Casual greetings ("hi", "hello"), asking for explanations, conceptual questions, or general conversation.
- Action: Routes to the Text LLM for a conversational response.

2. "CODE_SINGLE"
- Use for: Requests targeting a specific, single file (e.g., "Write a python script to reverse a string", "Fix the bug in app.js").
- Action: Routes directly to the Code LLM.

3. "PROJECT_ARCH"
- Use for: Broad requests requiring multiple files, folders, or full system design (e.g., "Build a landing page", "Create a React dashboard", "Make a weather app").
- Action: Routes to the Project Architect LLM to plan the directory structure before coding.

4. "SYSTEM_CMD"
- Use for: Direct IDE or terminal operations (e.g., "Open the terminal", "Run the server", "Install express").
- Action: Routes to the OS Execution module.

### OUTPUT FORMAT:
You must output ONLY valid JSON. Do not include markdown formatting like ```json.

{
  "route": "CHAT | CODE_SINGLE | PROJECT_ARCH | SYSTEM_CMD",
  "confidence": 0-100,
  "reasoning": "Short 1-sentence explanation of why this route was chosen",
  "extracted_entities": ["any", "specific", "tech", "or", "filenames", "mentioned"]
}
"""


def heuristic_classify_intent(user_input: str) -> RouterOutput:
    """Robust heuristic classification conforming to the exact Layer 1 spec."""
    text = user_input.strip()
    lower = text.lower()

    # Extract filenames or common tech mentions
    file_pattern = r"\b[a-zA-Z0-9_\-./]+\.(py|js|jsx|ts|tsx|html|css|json|yaml|yml|md|txt|sh|sql)\b"
    files_found = re.findall(file_pattern, text, re.IGNORECASE)
    # Full filename matches
    full_files = [m.group(0) for m in re.finditer(r"\b[a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+\b", text)]

    entities = list(set(full_files))

    # Tech keywords
    tech_keywords = [
        "python", "react", "fastapi", "express", "node", "javascript", "docker",
        "kubernetes", "sql", "landing page", "website", "dashboard", "weather app",
        "coffee shop", "terminal", "server", "git", "npm", "pip"
    ]
    for kw in tech_keywords:
        if kw in lower and kw not in entities:
            entities.append(kw)

    # 1. SYSTEM_CMD checks
    cmd_triggers = [
        "terminal", "run the server", "start server", "install ", "npm i", "npm start",
        "npm run", "pip install", "open terminal", "kill process", "git push", "git commit"
    ]
    if any(trig in lower for trig in cmd_triggers) or lower.startswith(("run ", "start ", "exec ", "install ")):
        return RouterOutput(
            route="SYSTEM_CMD",
            confidence=96,
            reasoning="User is requesting a direct IDE, terminal, or system execution command.",
            extracted_entities=entities,
        )

    # 2. PROJECT_ARCH checks (broad requests requiring multi-file project/structure)
    arch_triggers = [
        "landing page", "website", "dashboard", "full stack", "fullstack", "bana do", "create a project",
        "build an app", "build a web", "make an app", "make a weather", "saas", "coffee shop"
    ]
    if any(trig in lower for trig in arch_triggers) and not (len(full_files) == 1 and ("modify" in lower or "fix" in lower)):
        return RouterOutput(
            route="PROJECT_ARCH",
            confidence=95,
            reasoning="User is asking for a multi-file project, website, or system design requiring structural planning.",
            extracted_entities=entities,
        )

    # 3. CODE_SINGLE checks (specific single file or snippet)
    if full_files or any(w in lower for w in ["script", "function", "fix the bug", "hata do", "add a test", "reverse a string", "bug in"]):
        reasoning = (
            f"User is asking to create or modify a single specific file ({full_files[0]})."
            if full_files
            else "User is requesting code for a single targeted function or script."
        )
        return RouterOutput(
            route="CODE_SINGLE",
            confidence=98 if full_files else 92,
            reasoning=reasoning,
            extracted_entities=entities,
        )

    # 4. CHAT checks (casual greeting, explanation, conversation)
    chat_greetings = ["hi", "hii", "hello", "hey", "hola", "kya haal", "good morning", "sup"]
    if lower in chat_greetings or any(lower.startswith(g) for g in ["hi ", "hello ", "hey "]):
        return RouterOutput(
            route="CHAT",
            confidence=99,
            reasoning="User is sending a casual greeting.",
            extracted_entities=[],
        )

    # Conceptual or conversational
    if lower.endswith("?") or any(w in lower for w in ["what is", "how does", "explain", "samjhao", "kyun", "who are you"]):
        return RouterOutput(
            route="CHAT",
            confidence=94,
            reasoning="User is asking a conceptual or explanatory conversational question.",
            extracted_entities=entities,
        )

    # Default fallback to CHAT
    return RouterOutput(
        route="CHAT",
        confidence=85,
        reasoning="General conversational inquiry.",
        extracted_entities=entities,
    )


# ============================================================================
# LangGraph Nodes Definition
# ============================================================================


def classify_intent_node(state: RouterState) -> Dict[str, Any]:
    """Node 1: LangChain prompt invocation with LangGraph state routing."""
    user_input = state["user_input"]

    # In an active environment with an LLM, LangChain executes:
    # prompt = ChatPromptTemplate.from_messages([("system", ROUTER_SYSTEM_PROMPT), ("user", "{input}")])
    # structured_llm = llm.with_structured_output(RouterOutput)
    # result = (prompt | structured_llm).invoke({"input": user_input})
    # Here we employ the verified heuristic engine with the exact same structured contract:
    result = heuristic_classify_intent(user_input)

    return {
        "route": result.route,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "extracted_entities": result.extracted_entities,
    }


def route_chat_node(state: RouterState) -> Dict[str, Any]:
    """Downstream Handler for CHAT intent."""
    payload = {
        "route": "CHAT",
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "extracted_entities": state["extracted_entities"],
    }
    return {"final_output": payload}


def route_code_single_node(state: RouterState) -> Dict[str, Any]:
    """Downstream Handler for CODE_SINGLE intent."""
    payload = {
        "route": "CODE_SINGLE",
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "extracted_entities": state["extracted_entities"],
    }
    return {"final_output": payload}


def route_project_arch_node(state: RouterState) -> Dict[str, Any]:
    """Downstream Handler for PROJECT_ARCH intent."""
    payload = {
        "route": "PROJECT_ARCH",
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "extracted_entities": state["extracted_entities"],
    }
    return {"final_output": payload}


def route_system_cmd_node(state: RouterState) -> Dict[str, Any]:
    """Downstream Handler for SYSTEM_CMD intent."""
    payload = {
        "route": "SYSTEM_CMD",
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "extracted_entities": state["extracted_entities"],
    }
    return {"final_output": payload}


def decide_next_route(state: RouterState) -> str:
    """LangGraph conditional routing edge."""
    route = state.get("route", "CHAT")
    if route == "CODE_SINGLE":
        return "route_code_single"
    elif route == "PROJECT_ARCH":
        return "route_project_arch"
    elif route == "SYSTEM_CMD":
        return "route_system_cmd"
    return "route_chat"


# Build the LangGraph StateGraph
def create_router_graph():
    graph = StateGraph(RouterState)

    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("route_chat", route_chat_node)
    graph.add_node("route_code_single", route_code_single_node)
    graph.add_node("route_project_arch", route_project_arch_node)
    graph.add_node("route_system_cmd", route_system_cmd_node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        decide_next_route,
        {
            "route_chat": "route_chat",
            "route_code_single": "route_code_single",
            "route_project_arch": "route_project_arch",
            "route_system_cmd": "route_system_cmd",
        },
    )

    graph.add_edge("route_chat", END)
    graph.add_edge("route_code_single", END)
    graph.add_edge("route_project_arch", END)
    graph.add_edge("route_system_cmd", END)

    return graph.compile()


master_router_graph = create_router_graph()


class MasterIntentRouter:
    """Master Intent Router (Layer 1) wrapper using compiled LangGraph workflow."""

    def __init__(self):
        self.graph = master_router_graph

    def route(self, user_input: str) -> Dict[str, Any]:
        """Execute the LangGraph workflow and return strict JSON-compatible dict."""
        initial_state: RouterState = {
            "user_input": user_input,
            "route": None,
            "confidence": 0,
            "reasoning": "",
            "extracted_entities": [],
            "final_output": None,
        }
        res = self.graph.invoke(initial_state)
        return res.get("final_output") or {
            "route": res.get("route", "CHAT"),
            "confidence": res.get("confidence", 90),
            "reasoning": res.get("reasoning", ""),
            "extracted_entities": res.get("extracted_entities", []),
        }

    def route_json(self, user_input: str) -> str:
        """Return strictly serialized JSON string with no markdown formatting."""
        output = self.route(user_input)
        return json.dumps(output, ensure_ascii=False)


if __name__ == "__main__":
    import sys

    user_query = sys.argv[1] if len(sys.argv) > 1 else "app.py me se console.log hata do"
    router = MasterIntentRouter()
    print(router.route_json(user_query))
