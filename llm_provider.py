import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("MODEL_NAME")

llm = ChatGroq(
    api_key=groq_api_key,
    model=model_name,
    temperature=0.0,
    max_retries=2,
)