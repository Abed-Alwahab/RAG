
import os
from dotenv import load_dotenv
from google import genai

# تحميل متغيرات ملف .env
load_dotenv()

# قراءة المفتاح
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# إنشاء الاتصال
client = genai.Client(api_key=GEMINI_API_KEY)

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input="Explain how AI works in a few words"
)

print(interaction.output_text)
