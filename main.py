from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import openai
import os
import traceback

# Получаем ключ
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY не задан в Render Environment.")
openai.api_key = api_key

app = FastAPI()

# Разрешаем CORS для Figma
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    image: str

@app.post("/analyze")
async def analyze(request: ImageRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY не задан. Добавьте его в Render → Environment Variables.")

    try:
        # Обработка изображения
        image_data = request.image.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
        image_bytes = base64.b64decode(image_data)

        # Запрос к OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — UI-дизайнер. На основе изображения создай JSON с блоками, текстами и кнопками для макета в Figma. Игнорируй фотографии. Верни только JSON."
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
        except Exception as parse_err:
            print("Ошибка парсинга ответа от OpenAI:")
            print(content)
            print(traceback.format_exc())
            return {
                "error": "Ошибка парсинга JSON",
                "raw_response": content,
                "exception": str(parse_err)
            }

        return json_data

    except Exception as e:
        print("❌ Ошибка при обращении к OpenAI:")
        print(traceback.format_exc())
        return {
            "error": "Ошибка при обращении к OpenAI",
            "exception": str(e),
            "traceback": traceback.format_exc()
        }