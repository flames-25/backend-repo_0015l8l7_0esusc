import os
import asyncio
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from gesture_processor import GestureProcessor, GestureEvent

app = FastAPI(title="Proton Web - Gesture Controlled Virtual Mouse")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Chat command processing
# -----------------------------

class ChatRequest(BaseModel):
    text: str


def greeting() -> str:
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 17:
        return "Good afternoon"
    if 17 <= hour < 22:
        return "Good evening"
    return "Hello night owl"


def handle_command(text: str) -> Dict[str, Any]:
    t = text.lower().strip()
    if t in {"hi", "hello", "hey"}:
        return {"reply": f"{greeting()}! I'm Proton. Say 'launch gestures' to start."}
    if t.startswith("time") or t == "what's the time" or t == "what is the time":
        return {"reply": f"Current time is {datetime.now().strftime('%I:%M %p')}"}
    if t.startswith("date"):
        return {"reply": f"Today's date is {datetime.now().strftime('%A, %d %B %Y')}"}
    if t.startswith("search "):
        q = t.replace("search ", "", 1).strip()
        return {
            "reply": f"Searching the web for '{q}'...",
            "action": {
                "type": "open_url",
                "url": f"https://www.google.com/search?q={q.replace(' ', '+')}"
            }
        }
    if "launch gesture" in t:
        return {"reply": "Launching gesture mode. Raise your hand and use the green pad.", "action": {"type": "enter_gesture_mode"}}
    if t in {"copy", "copy that", "copy text"}:
        return {"reply": "Copying...", "action": {"type": "copy"}}
    if t in {"paste", "paste it"}:
        return {"reply": "Pasting...", "action": {"type": "paste"}}
    if "list files" in t:
        # Simulate files for the web environment
        demo_files = [
            {"name": "Report_Q1.pdf", "size": "1.2 MB"},
            {"name": "presentation.pptx", "size": "8.4 MB"},
            {"name": "notes.txt", "size": "3 KB"},
        ]
        return {"reply": "Here are some sample files:", "files": demo_files}

    return {"reply": "I didn't catch that. Try 'time', 'date', 'search cats', or 'launch gestures'."}


@app.get("/")
async def root():
    return {"message": "Proton Web backend running"}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = handle_command(req.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -----------------------------
# WebSocket for real-time gesture stream
# -----------------------------

processor = GestureProcessor()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            # Expecting: {"type": "gesture", "finger_count": int, "x": float, "y": float, "roi_active": bool}
            if data.get("type") == "gesture":
                evt = GestureEvent(
                    finger_count=int(data.get("finger_count", 0)),
                    x=float(data.get("x", 0.5)),
                    y=float(data.get("y", 0.5)),
                    roi_active=bool(data.get("roi_active", True)),
                )
                out = processor.process(evt)
                await ws.send_json(out)
            else:
                # e.g., ping or misc messages
                await ws.send_json({"type": "ack"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
