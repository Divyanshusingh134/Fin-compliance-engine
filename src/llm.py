import os 
import asyncio
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client()

logger = logging.getLogger(__name__)


async def embed(texts: list[str], max_retries: int = 3):
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        logger.error("Input texts must not be empty strings")
        raise ValueError("Input texts must not be empty strings")

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.embed_content(
                model="gemini-embedding-2",
                contents= texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=768
                )
            )
            if response.embeddings is None:
                logger.error(f"The API returned no embeddings")
                raise RuntimeError
            
            embeddings = []
            for embedding in response.embeddings:
                if embedding.values is None:
                    logger.error(f"An embedding has no vector values")
                    raise RuntimeError
                embeddings.append(embedding.values)
            return embeddings

        except errors.APIError as e:
            if e.code != 429 or attempt == max_retries - 1:
                logger.error(f"API Error: {e}")
                raise
            wait_time = 2 ** attempt
            logger.info(f"Rate limit reached...Retrying in {wait_time}")
            await asyncio.sleep(wait_time)

    logger.warning(f"Max retries reached...")
    return None

