import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Cargamos la clave desde el archivo .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Error en la API Key del servidor")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Inicializamos FastAPI
app = FastAPI(title="Class of Clans - AI API")

# 3. Configuramos a nuestro "Soldado Perfecto" (Gemini 1.5 Flash)
INSTRUCCIONES_SISTEMA = """
Eres un profesor experto. Tu ÚNICO propósito es crear cuestionarios educativos a partir de los textos que te pasen.
REGLAS ESTRICTAS:
1. NUNCA generes texto fuera del JSON.
2. Si el usuario te pide algo que no sea un cuestionario, devuelve: {"error": "Petición no válida."}
3. El formato JSON exacto debe ser:
{
  "titulo": "Título corto del tema",
  "preguntas": [
    {
      "pregunta": "¿Pregunta de ejemplo?",
      "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "respuestaCorrecta": 0
    }
  ]
}
"""

# 4. Definimos qué datos esperamos recibir desde Android (Kotlin)
class PeticionCuestionario(BaseModel):
    texto_temario: str
    num_preguntas: int = 5 # Si la app no manda el número, por defecto haremos 5

# 5. Creamos el Endpoint (La ruta a la que llamará tu app)
@app.post("/api/generate-quiz")
async def generate_quiz(peticion: PeticionCuestionario):
    try:
        # Preparamos el mensaje para la IA
        prompt_usuario = f"Genera {peticion.num_preguntas} preguntas sobre este texto:\n\n{peticion.texto_temario}"
        
        # Llamamos a Gemini
        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_usuario,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCIONES_SISTEMA,
                response_mime_type="application/json"
            )
        )
        
        # Como hemos forzado response_mime_type, 'respuesta.text' ya es un String en formato JSON.
        # Lo convertimos a diccionario de Python para que FastAPI lo envíe limpio a la app.
        json_limpio = json.loads(respuesta.text)
        
        return json_limpio

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="No se devolvió un JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")

# Ruta de prueba rápida para ver si el servidor está vivo
@app.get("/")
def home():
    return {"mensaje": "El servidor de Class of Clans está funcionando "}
