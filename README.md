# SmartWiper

Velocitas vehicle app that uses ASI:One (Fetch.ai) to make safety-aware
wiper decisions based on VSS signals (hood state, wiper mode, speed).

## Setup
\`\`\`bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your ASI_ONE_API_KEY
python -m app.SmartWiper
\`\`\`