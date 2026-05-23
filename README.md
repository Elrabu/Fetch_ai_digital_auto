# Fetch_ai_digital_auto

a velocitas vehicle app that uses the platform ASI:One to make safety-aware
wiper decisions based on VSS signals (hood state, wiper mode, speed).

## Hierarchy
```
 ├── smartwiper
 ├── SmartWiperApp
```

## Requirements
| Tool             | Version          | Purpose                              |
|------------------|------------------|--------------------------------------|
| Ubuntu / WSL2    | 24.04+           | Host OS                              |
| Python           | 3.12+            | App runtime                          |
| Docker           | 24+              | Kuksa databroker container           |
| Git              | any              | Version control                      |
| Velocitas CLI    | latest           | Velocitas project tooling            |
| ASI:One API key  | —                | LLM access (https://asi1.ai/))       |

## agentverse.ai Setup

create an agent from the **Blank Agent** template at https://agentverse.ai/agents. Use this code in ```agent.py```:

```
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    chat_protocol_spec,
)

# ---------- Structured protocol (for Velocitas bridge) ----------
class WiperSafetyRequest(Model):
    hood_is_open: bool
    current_wiper_mode: str
    vehicle_speed: float

class WiperSafetyResponse(Model):
    risk_level: str           # LOW | MEDIUM | HIGH
    assessment: str
    recommended_action: str   # STOP_WIPER | KEEP_WIPER | REDUCE_WIPER

agent = Agent()  # On Agentverse, name/seed/endpoint are managed by the platform

def assess(hood_open: bool, mode: str, speed: float):
    if hood_open and mode.upper() != "OFF":
        return ("HIGH",
                "Hood is open while wipers are active — mechanical collision risk.",
                "STOP_WIPER")
    if hood_open:
        return ("LOW", "Hood open but wipers off — no immediate risk.", "KEEP_WIPER")
    return ("LOW", "Nominal conditions.", "KEEP_WIPER")

# ---------- Structured endpoint (used by your Velocitas bridge) ----------
safety_proto = Protocol("WiperSafety", version="1.0")

@safety_proto.on_message(model=WiperSafetyRequest, replies=WiperSafetyResponse)
async def handle_safety(ctx: Context, sender: str, msg: WiperSafetyRequest):
    risk, reason, action = assess(msg.hood_is_open, msg.current_wiper_mode, msg.vehicle_speed)
    ctx.logger.info(f"[Safety] {sender} → {risk}: {action}")
    await ctx.send(sender, WiperSafetyResponse(
        risk_level=risk, assessment=reason, recommended_action=action))

# ---------- Chat protocol (makes the agent discoverable on ASI:One) ----------
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent)).lower()
    # naive parse for chat callers
    hood_open = "hood" in text and ("open" in text or "true" in text)
    mode = "MEDIUM" if "wiper" in text or "wiping" in text else "OFF"
    risk, reason, action = assess(hood_open, mode, 0.0)

    reply = f"Risk: {risk}\nReason: {reason}\nRecommended action: {action}"
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=reply)],
    ))

@chat_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(safety_proto, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)
```
press **Start Agent** to publish your agent. The GUI should look like this:

<img width="1352" height="131" alt="image" src="https://github.com/user-attachments/assets/acc9b79d-cda9-4e7c-8997-7e981020e46a" />

copy the agent address starting with ```agent1q...``` for a later step

## Velocitas Runtime Setup (SmartWiperApp)
this creates the Velocitas-Runtime (Kuksa Databroker, MQTT, Mock-Service) that is used by the "vehicle" model inside "SmartWiperAgents"

### 1. Clone the template repo
```
git clone https://github.com/eclipse-velocitas/vehicle-app-python-template.git SmartWiperApp
cd SmartWiperApp
```
/SmartWiperAgents
### 2. pull the packages declared in .velocitas.json
```
velocitas init
```

### 3. Sync devcontainer / scripts / workflows
```
velocitas sync
```

### 4. Start Velocitas Runtime
```
velocitas exec runtime-local up
```

## Agents + Fetch.ai setup

### 1. Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. configure environment variables

Get a ASI:One API key from the website https://asi1.ai/ by creating an account and then go to your profile -> Developer -> API keys

```
cd ~/YOUR_PROJECT_ROOT
cp .env.example .env
nano .env
```

content of .env:
```
ASI1_API_KEY=ASI:One_API_key_here
SAFETY_AGENT_ADDRESS=agentverse_agent_address
```

### 4. fix imports

```
cd ~/YOUR_PROJECT_ROOT/smartwiper/bridge
touch smartwiper/__init__.py
```

### 5. set PYTHONPATH for ```vehicle``` import

```
export PYTHONPATH="/YOUR/HOME/DIRECTORY/PROJECTNAME/SmartWiperApp/gen/vehicle_model:$PYTHONPATH"
```

### 6. start smartwiper app

```
cd ~/YOUR_PROJECT_ROOT/smartwiper
python -m smartwiper.py
```

## KUKSA Databroker

setup Kuksa client
```
pip install kuksa-client
```

start with 
```
kuksa-client grpc://127.0.0.1:55555
```

change mock values with
```
setValue Vehicle.Speed 0
setValue Vehicle.Body.Windshield.Front.Wiping.Mode "MEDIUM"
setValue Vehicle.Body.Hood.IsOpen true
```





