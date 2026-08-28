import httpx
from .config import settings


async def research(topic: str) -> str:
    if not settings.tavily_api_key:
        return "No external research provider configured. Use the topic and perspective as the research basis."

    payload = {
        "api_key": settings.tavily_api_key,
        "query": topic,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 6,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()

    answer = data.get("answer") or ""
    results = data.get("results") or []
    lines = [answer] if answer else []
    for item in results:
        title = item.get("title", "")
        url = item.get("url", "")
        content = item.get("content", "")
        lines.append(f"- {title}\n  {url}\n  {content}")
    return "\n".join(lines)[:12000]
