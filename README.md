# Fetch_ai_digital_auto

a velocitas vehicle app that uses the platform ASI:One to make safety-aware
wiper decisions based on VSS signals (hood state, wiper mode, speed).

## Hierarchy
```
 ├── smartwiper
 ├── SmartWiperApp
```

| Tool             | Version          | Purpose                              |
|------------------|------------------|--------------------------------------|
| Ubuntu / WSL2    | 22.04+           | Host OS                              |
| Python           | 3.10+            | App runtime                          |
| Docker           | 24+              | Kuksa databroker container           |
| Git              | any              | Version control                      |
| Velocitas CLI    | latest           | Velocitas project tooling            |
| ASI:One API key  | —                | LLM access (https://asi1.ai/))       |

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

### Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Install Dependencies

```
pip install -r requirements.txt
```

### configure environment variables

Get a ASI:One API key from the website https://asi1.ai/ by creating an account and then go to dashboard -> API keys

```
cd ~/YOUR_PROJECT_ROOT
cp .env.example .env
nano .env
```

content of .env:
```
ASI1_API_KEY
```



