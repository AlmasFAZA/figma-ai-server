from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import openai
import os

# Получаем ключ из переменной окружения
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY не найден! Установите переменную окружения.")
openai.api_key = api_key

app = FastAPI()

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    image: str  # base64 строка

@app.post("/analyze")
async def analyze(request: ImageRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY не задан. Добавьте его в Render → Environment Variables.")

    image_data = request.image.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
    image_bytes = base64.b64decode(image_data)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — UI-дизайнер. На основе изображения создай JSON с блоками, текстами и кнопками для макета в Figma."
                },
                {
                    "role": "user",
                    "content": [
                        { "type": "text", "text": "Создай JSON-макет интерфейса по изображению." },
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
            return { "error": "Не удалось распарсить ответ от OpenAI", "raw": content }
        return json_data
    except Exception as e:
        return { "error": "Ошибка при обращении к OpenAI", "detail": str(e) }