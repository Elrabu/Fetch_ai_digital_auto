# ASI-One_digital_auto

a velocitas vehicle app that uses the ASI:One LLM on the ASI:One platform to make safety-aware
wiper decisions based on VSS signals (hood state, wiper mode, speed).

## Hierarchy
```
 ├── smartwiper <- fetch.ai agent logic and bridge to ASI:One and Velocitas
 ├── SmartWiperApp <- Velocitas Runtime 
```

## Requirements
| Tool             | Version          | Purpose                              |
|------------------|------------------|--------------------------------------|
| Ubuntu / WSL2    | 24.04+           | Host OS                              |
| Python           | 3.12+            | App runtime                          |
| Docker           | 24+              | Kuksa databroker container           |
| ASI:One API key  | —                | LLM access (https://asi1.ai/))       |


## Velocitas Runtime Setup (SmartWiperApp)
this creates the Velocitas-Runtime (Kuksa Databroker, MQTT, Mock-Service) that is used by the "vehicle" model inside "SmartWiperAgents"

### 1. Clone the template repo
```
git clone https://github.com/eclipse-velocitas/vehicle-app-python-template.git SmartWiperApp
cd SmartWiperApp
```

### 2. pull the packages declared in velocitas.json
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





