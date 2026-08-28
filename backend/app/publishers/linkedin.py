import httpx
from ..config import settings


class LinkedInPublisher:
    async def publish(self, body: str) -> str:
        if not settings.linkedin_access_token or not settings.linkedin_author_urn:
            raise RuntimeError("LinkedIn credentials are not configured")

        payload = {
            "author": settings.linkedin_author_urn,
            "commentary": body,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        headers = {
            "Authorization": f"Bearer {settings.linkedin_access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": settings.linkedin_version,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.linkedin.com/rest/posts",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            post_id = response.headers.get("x-restli-id", "")
            return f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""
