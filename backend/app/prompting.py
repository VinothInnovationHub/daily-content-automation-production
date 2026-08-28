def build_generation_prompt(topic: str, perspective: str, instructions: str, research: str = "") -> str:
    return f"""
You are an expert technology content strategist.

TOPIC:
{topic}

PERSPECTIVE:
{perspective}

INSTRUCTIONS:
{instructions}

CURRENT RESEARCH / SIGNALS:
{research}

Create TWO independent pieces of content.

1) LINKEDIN
- Professional and credible.
- Strong opening hook.
- Useful insight for technology professionals/software architects.
- 700-1300 characters where practical.
- Natural, not clickbait.
- 3-6 relevant hashtags.
- Do not mention that AI wrote it.

2) MEDIUM ARTICLE
- A standalone long-form article.
- Clear title.
- Strong introduction.
- Practical sections and examples.
- Technology-professional audience.
- Do not include the LinkedIn post inside the article.

Return ONLY valid JSON:
{{
  "linkedin": {{
    "title": "",
    "body": ""
  }},
  "medium": {{
    "title": "",
    "body": ""
  }}
}}
""".strip()
