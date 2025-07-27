from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import openai
import os

# 🔐 Получаем ключ из переменной окружения (не вставлять прямо в код)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# ✅ CORS для Figma Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    image: str  # base64 PNG или JPG

@app.post("/analyze")
async def analyze(request: ImageRequest):
    image_data = request.image.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
    image_bytes = base64.b64decode(image_data)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Ты — UI-дизайнер. На основе изображения создай JSON с блоками, текстами и кнопками для макета в Figma. Игнорируй фотографии. Структурируй как JSON: blocks, texts, buttons, sections."
            },
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": "Создай JSON-макет из интерфейса на изображении." },
                    {
                        "type": "image_url",
                        "image_url": { "url": "data:image/png;base64," + image_data }
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=2000
    )

    content = response.choices[0].message.content
    try:
        json_data = eval(content)
    except:
        return { "error": "Ошибка парсинга JSON", "raw": content }

    return json_data