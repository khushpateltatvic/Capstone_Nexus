import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv("backend/.env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Available Models on Groq:")
models = client.models.list()
for model in models.data:
    print(model.id)
