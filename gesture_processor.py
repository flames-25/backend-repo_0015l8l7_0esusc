from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class GestureEvent:
    finger_count: int
    x: float  # normalized 0..1
    y: float  # normalized 0..1
    roi_active: bool = True

class GestureProcessor:
    """
    Lightweight processor that mirrors the intent of the original Gesture_Controller_Gloved.py
    but for a browser environment. We don't control OS mouse here; instead, we translate
    gestures into semantic actions that the frontend can simulate on a virtual canvas.
    """

    def __init__(self) -> None:
        self.last_action: Optional[str] = None

    def process(self, evt: GestureEvent) -> Dict:
        # Map finger counts to actions (example mapping):
        # 0 -> click, 1 -> right-click, 2 -> scroll, 3/4 -> move cursor, 5+ -> idle
        action = "idle"
        payload: Dict = {}
        if not evt.roi_active:
            action = "out_of_roi"
        else:
            if evt.finger_count == 0:
                action = "click"
            elif evt.finger_count == 1:
                action = "right_click"
            elif evt.finger_count == 2:
                action = "scroll"
                # positive y -> scroll down, negative -> up (frontend normalizes)
                payload["dy"] = (0.5 - evt.y) * 2
            elif evt.finger_count in (3, 4):
                action = "move"
                payload["x"] = evt.x
                payload["y"] = evt.y
            else:
                action = "idle"

        self.last_action = action
        return {
            "type": "gesture_action",
            "action": action,
            "payload": payload,
        }
