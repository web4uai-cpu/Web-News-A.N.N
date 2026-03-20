import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")

async def test_llm():
    client = AsyncOpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )
    
    try:
        response = await client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            messages=[{"role": "user", "content": "Hello! Reply with 1 word."}],
        )
        print("Success!", response.choices[0].message.content)
    except Exception as e:
        with open("error.txt", "w", encoding="utf-8") as f:
            f.write(str(e))

if __name__ == "__main__":
    asyncio.run(test_llm())
