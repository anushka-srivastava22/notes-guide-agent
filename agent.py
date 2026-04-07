import os
import logging
import datetime
import google.cloud.logging
from google.cloud import datastore
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from mcp.server.fastmcp import FastMCP 

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

import google.generativeai as genai

# ================= 1. SETUP =================

# Logging
try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)

# Datastore (your custom DB)
db = datastore.Client(project=PROJECT_ID, database="genainotes")

# MCP
mcp = FastMCP("NotesGuideAgent")

# ================= 2. TOOLS =================

@mcp.tool()
def add_note(title: str, content: str) -> str:
    """Create a note"""
    try:
        key = db.key("Note")
        note = datastore.Entity(key=key)
        note.update({
            "title": title,
            "content": content,
            "created_at": datetime.datetime.utcnow()
        })
        db.put(note)
        return f"✅ Note '{title}' saved"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def list_notes() -> str:
    """List all notes"""
    try:
        query = db.query(kind="Note")
        notes = list(query.fetch())

        if not notes:
            return "No notes found"

        result = ["📝 Notes:"]
        for n in notes:
            result.append(f"- {n['title']} (ID: {n.key.id})")

        return "\n".join(result)
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_latest_note() -> str:
    """Get latest note"""
    try:
        query = db.query(kind="Note")
        query.order = ["-created_at"]
        notes = list(query.fetch(limit=1))

        if not notes:
            return "No notes available"

        return notes[0]["content"]
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def add_task(title: str) -> str:
    """Create task"""
    try:
        key = db.key("Task")
        task = datastore.Entity(key=key)
        task.update({
            "title": title,
            "completed": False,
            "created_at": datetime.datetime.utcnow()
        })
        db.put(task)
        return f"✅ Task '{title}' added"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def list_tasks() -> str:
    """List all tasks"""
    try:
        query = db.query(kind="Task")
        tasks = list(query.fetch())

        if not tasks:
            return "No tasks found"

        result = ["📋 Tasks:"]
        for t in tasks:
            status = "✅" if t["completed"] else "⏳"
            result.append(f"{status} {t['title']} (ID: {t.key.id})")

        return "\n".join(result)
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ================= 3. AI FUNCTIONS =================

def summarize_text(text: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(f"Summarize this:\n{text}")
    return response.text


def extract_tasks(text: str):
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        f"Extract tasks as bullet points:\n{text}"
    )
    return [t.strip("- ").strip() for t in response.text.split("\n") if t.strip()]


# ================= 4. AGENTS =================

def add_prompt_to_state(tool_context: ToolContext, prompt: str):
    tool_context.state["PROMPT"] = prompt
    return {"status": "ok"}


def workspace_instruction(ctx):
    prompt = ctx.state.get("PROMPT", "")

    return f"""
You are an AI Notes Assistant.

Follow instructions:

- Create note → use add_note
- Show notes → use list_notes
- Summarize → get_latest_note then summarize
- Create tasks → extract tasks from note and save using add_task
- Show tasks → use list_tasks

User input:
{prompt}
"""


def root_instruction(ctx):
    raw_input = ctx.state.get("user_input", "")
    return f"""
1. Save user input using add_prompt_to_state: {raw_input}
2. Pass to workspace agent
"""


workspace_agent = Agent(
    name="workspace_agent",
    model=MODEL_NAME,
    instruction=workspace_instruction,
    tools=[add_note, list_notes, get_latest_note, add_task, list_tasks]
)

workflow = SequentialAgent(
    name="workflow",
    sub_agents=[workspace_agent]
)

root_agent = Agent(
    name="root_agent",
    model=MODEL_NAME,
    instruction=root_instruction,
    tools=[add_prompt_to_state],
    sub_agents=[workflow]
)

# ================= 5. API =================

app = FastAPI()


class UserRequest(BaseModel):
    prompt: str


@app.post("/chat")
async def chat(request: UserRequest):
    try:
        final_reply = ""

        async for event in root_agent.run_async({"user_input": request.prompt}):
            if hasattr(event, "text") and event.text:
                final_reply = event.text

        return {
            "status": "success",
            "reply": final_reply or "Done"
        }

    except Exception as e:
        logging.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ================= 6. RUN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
