import logging
logging.basicConfig(level=logging.INFO)

import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR = os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List, Literal
import operator
from datetime import datetime

from src.validators.agent_validators import *
from src.agent_tools import (
    get_patient_info,
    obtain_specialization_by_doctor,
    check_availability_by_doctor,
    check_availability_by_specialization,
    cancel_appointment,
    get_catalog_specialists,
    retrieve_faq_info,
    set_appointment,
    reminder_appointment,
    check_results,
    reschedule_appointment,
    get_department_location,
)
from src.utils import get_model

logger = logging.getLogger(__name__)

class MessagesState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]

tools = [
    get_patient_info,
    obtain_specialization_by_doctor,
    check_availability_by_doctor,
    check_availability_by_specialization,
    cancel_appointment,
    get_catalog_specialists,
    retrieve_faq_info,
    set_appointment,
    reminder_appointment,
    check_results,
    reschedule_appointment,
    get_department_location,
]

tool_node = ToolNode(tools)
model = get_model("openai").bind_tools(tools=tools)

def should_continue(state: MessagesState) -> Literal["tools", "human_feedback"]:
    last = state["messages"][-1]
    return "tools" if last.tool_calls else "human_feedback"

def call_model(state: MessagesState):
    system_prompt = (
        "You are ZooZoo Hospital’s virtual assistant—think of yourself as the friendly front-desk secretary for a "
        "full-service healthcare center in California, USA.\n"
        f"Current date & time: {datetime.now().strftime('%Y-%m-%d %H:%M, %A')}\n\n"
        "Style\n"
        "• Warm, courteous, professional.\n"
        "• Keep responses concise; avoid unnecessary verbosity.\n\n"
        "Guidelines\n"
        "• NEVER invent parameters when calling a function—use only what the user provides.\n"
        "• Do NOT tell users how to phrase their requests; accommodate any writing style.\n"
        "• Maintain a natural, conversational tone (like a helpful human receptionist).\n"
        "• Call **only ONE tool per turn**.\n\n"
        "Scope & disclaimer\n"
        "• I can help with scheduling, billing, facility details, and other ZooZoo Hospital topics.\n"
        "• For any question about medical definitions, symptoms, or disease overviews, you **must** call "
        "`retrieve_faq_info` tool exactly once.\n"
        "  – After you fetch, append: “⚠️ This information is for reference only and not a substitute for professional medical advice.”\n"
        "• If a request is about hospital logistics (hours, parking, scheduling), use the scheduling or info tools.\n"
        "• If it’s none of the above, politely refuse and steer back to hospital topics.\n"
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")


workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "human_feedback": END},
)

workflow.add_edge("tools", "agent")

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    while True:
        question = input("Put your question: ")
        if question.lower() in {"exit", "quit", "bye", "close", "goodbye"}:
            break

        for event in app.stream(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"thread_id": 42}}
        ):
            
            if "tools" in event:
                tool_payload = event["tools"]
                tm = tool_payload.get("messages", [])[0]
                content = tm.content if hasattr(tm, "content") else str(tm)
                for chunk in content.strip().split("\n\n"):
                    print(chunk.strip())
                    print()
                    print("===")
                break


            elif "agent" in event:
                msgs = event["agent"]["messages"]
                if msgs:
                    reply = msgs[-1].content.strip()
                    if reply:
                        print(reply)
                        break
