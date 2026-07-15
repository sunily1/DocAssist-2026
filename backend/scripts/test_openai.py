import asyncio
import os
import sys
from openai import AsyncOpenAI

# Add project root to path to load config
sys.path.append(os.getcwd())

from app.core.config import settings

async def test_openai():
    print("DEBUG: API key loaded" if settings.OPENAI_API_KEY else "DEBUG: No API key loaded")
    client_options = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        client_options["base_url"] = settings.OPENAI_BASE_URL
    client = AsyncOpenAI(**client_options)
    
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": "Hello, is this working?"}],
            max_tokens=10
        )
        print(f"SUCCESS: OpenAI Response: {response.choices[0].message.content}")
    except Exception as e:
        status = getattr(e, "status_code", None)
        code = getattr(e, "code", None)
        print(f"ERROR: LLM API call failed ({type(e).__name__}, status={status}, code={code})")

if __name__ == "__main__":
    asyncio.run(test_openai())


