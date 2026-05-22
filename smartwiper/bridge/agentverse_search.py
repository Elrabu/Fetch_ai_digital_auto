"""Optional: discover the smartwiper-safety agent's address at runtime.

Only needed if you don't want to hardcode SAFETY_AGENT_ADDRESS.
"""
import os
import httpx

AGENTVERSE_SEARCH = "https://agentverse.ai/v1/search/agents"


async def find_safety_agent_address(query: str = "smartwiper safety") -> str:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("AGENTVERSE_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"search_text": query, "limit": 5}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(AGENTVERSE_SEARCH, json=payload, headers=headers)
        r.raise_for_status()
        results = r.json()

    items = results.get("agents") or results.get("results") or []
    for item in items:
        name = (item.get("name") or "").lower()
        if "smartwiper" in name or "wiper" in name:
            return item.get("address") or item.get("agent_address")
    raise RuntimeError(f"No agent matched query={query!r}")
