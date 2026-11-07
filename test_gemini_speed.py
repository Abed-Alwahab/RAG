
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = "gemini-3.6-flash"

tests = [
    ("Short prompt", "أجب بكلمة واحدة: ما عاصمة فلسطين؟"),
    ("Medium prompt", "اشرح مفهوم RAG في ثلاث جمل فقط.")
]

for name, prompt in tests:
    print(f"\nTesting: {name}", flush=True)

    start = time.perf_counter()

    try:
        response = client.interactions.create(
            model=model,
            input=prompt
        )

        elapsed = time.perf_counter() - start

        print(f"Time: {elapsed:.2f}s")
        print("Answer:", response.output_text)

    except Exception as error:
        print("Error:", error)
