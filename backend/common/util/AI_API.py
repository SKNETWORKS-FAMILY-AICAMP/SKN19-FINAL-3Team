import os
import logging
from dotenv import load_dotenv

from google import genai
import google.generativeai as embedding_genai

class GeminiApi() :
    def __init__(self) :
       self.GEMINI_KEY=os.environ.get("GEMINI_API_KEY")

    async def create_sentence_vector(self, essence) :
        embedding_genai.configure(api_key=self.GEMINI_KEY)

        result = embedding_genai.embed_content(
            model="models/gemini-embedding-001",
            content=essence,
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=768
        )

        return result['embedding']