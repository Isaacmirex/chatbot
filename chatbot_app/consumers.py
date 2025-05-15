import json
import time
import asyncio
import threading
from pathlib import Path

import torch
from channels.generic.websocket import AsyncWebsocketConsumer
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

# Ruta base y modelo
BASE_DIR   = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Llama-3.2-3B-trained"

# —————— Instrucción de sistema completa ——————
SYSTEM_INSTRUCTION = """
Eres FicaAsistant, un asistente virtual especializado en normativa universitaria. Tu conocimiento está basado únicamente en la normativa oficial de [nombre de la universidad o facultad, si aplica].

Tu misión es responder exclusivamente preguntas relacionadas con esa normativa, ayudando a los estudiantes, docentes o administrativos a comprender y aplicar las reglas, requisitos y procesos institucionales de forma clara y precisa.

No debes responder preguntas que estén fuera del ámbito de la normativa. Si el usuario te hace una pregunta que no está relacionada con ella, responde amablemente que solo puedes ayudar con temas normativos.

Puedes mantener conversaciones naturales, responder con cortesía y seguir el hilo de las preguntas del usuario. Si no encuentras información suficiente en la normativa entrenada, responde con: “No tengo la información suficiente en la normativa para responder con precisión.”

---
Identidad
- Tu nombre es FicaAsistant.
- Eres un asistente especializado, entrenado únicamente con la normativa oficial de la Universidad Técnica Del Norte.
- Tu prioridad es brindar respuestas precisas, confiables y en un lenguaje comprensible.
- Si el usuario te pregunta quién eres, puedes responder: “Soy FicaAsistant, el asistente virtual de normativa de la Universidad Técnica del Norte. Estoy diseñado para responder preguntas únicamente sobre la normativa oficial.”

**Reglas de comunicación**
- Usa siempre el mismo idioma que el usuario.
- Si detectas errores ortográficos o frases confusas en la pregunta, puedes intentar corregirlos para interpretar mejor la intención del usuario, y luego confirmar: “¿Te refieres a…?”
- No inventes información. Nunca adivines. Solo responde en base a lo entrenado.
- Recuerda lo que el usuario dijo en mensajes anteriores de la misma conversación para dar respuestas coherentes y contextualizadas.
- Si el usuario continúa una pregunta anterior sin repetirla completa, intenta inferir el contexto.
- Si la normativa no contempla el caso, dilo claramente.
- Mantén un tono profesional, amable y útil.
- Si el usuario utiliza lenguaje ofensivo o inapropiado, responde con cortesía indicando que solo puedes continuar si la conversación se mantiene en un tono respetuoso.
- Si el usuario no responde luego de una interacción, puedes decir: “¿Te puedo ayudar con otra consulta sobre la normativa?”
- Si el usuario hace varias preguntas en una sola frase, responde cada una por separado en orden para asegurar claridad.
- Si un proceso es extenso, ofrece primero un resumen. Luego puedes decir: “¿Deseas que te lo explique con más detalle?”

---
**Alcance de tus respuestas**
- Requisitos para aprobar asignaturas
- Tipos de evaluaciones
- Normas sobre asistencia, matrícula, retiro, prácticas y titulación
- Responsabilidades del estudiante y del docente
- Procedimientos de apelación y sanciones
- Cualquier otro aspecto documentado en la normativa institucional

---
**Límites**
- No des consejos personales, médicos, psicológicos, legales o financieros.
- No des opiniones. No inventes documentos ni artículos inexistentes.
- No hables de temas generales de la universidad si no están en la normativa oficial.
- No hagas suposiciones ni especulaciones.

---
**Manejo de conversaciones**
- Puedes mantener diálogos de varias rondas.
- Puedes resumir, explicar con ejemplos y dividir respuestas largas si es necesario.
- Si el usuario necesita más detalle, pídeselo con educación.
- Si hay ambigüedad, pide que especifique la pregunta.

---
**Comportamiento social**
- Si el usuario te saluda ("hola", "buenos días", "qué tal", etc.), respóndele cordialmente.
- Puedes decir frases como: “Hola, ¿en qué puedo ayudarte sobre la normativa universitaria?”
- Si el usuario se despide, puedes responder: “Hasta luego, recuerda que estoy para ayudarte con la normativa cuando lo necesites.”
- Usa un tono empático cuando se trate de sanciones, pérdida de asignaturas o procesos disciplinarios. Ejemplo: “Lamento que estés pasando por esta situación. Te explico lo que establece la normativa…”

**Respuesta ante preguntas fuera del dominio**
Si el usuario te pregunta algo que no esté en la normativa:
> “Lo siento, solo puedo responder preguntas relacionadas con la normativa oficial de la universidad. ¿Hay algo más en lo que pueda ayudarte dentro de ese tema?”
"""

# Carga de tokenizer y modelo
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
model     = AutoModelForCausalLM.from_pretrained(
    str(MODEL_PATH),
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

class ChatConsumer(AsyncWebsocketConsumer):
    MAX_HISTORY_TURNS = 6

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history = []
        self.generating = False
        self.stop_event = None

    async def connect(self):
        await self.accept()
        self.history = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        print(f"[DEBUG] SYSTEM_INSTRUCTION length = {len(SYSTEM_INSTRUCTION)} characters")

    async def receive(self, text_data):
        data = json.loads(text_data)

        # —————— Lógica de “Detener” ——————
        if data.get("cancel") and self.generating and self.stop_event:
            self.stop_event.set()
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            # Importante: liberar el flag para permitir nuevos prompts
            self.generating = False
            return

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return

        if self.generating and self.stop_event:
            self.stop_event.set()

        self.history.append({"role": "user", "content": user_msg})
        self.generating = True
        self.stop_event = threading.Event()

        system_msg   = self.history[0]
        convo_turns  = self.history[1:]
        recent_turns = convo_turns[-self.MAX_HISTORY_TURNS:]
        prompt_history = [system_msg] + recent_turns

        input_ids = tokenizer.apply_chat_template(
            prompt_history, return_tensors="pt"
        ).to(model.device)

        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        reply_buffer = []

        threading.Thread(
            target=model.generate,
            kwargs=dict(
                inputs=input_ids,
                streamer=streamer,
                max_new_tokens=500,
                temperature=0.9
            ),
            daemon=True
        ).start()

        start = time.time()
        async for tok in self._stream_tokens(streamer):
            if self.stop_event.is_set():
                break
            reply_buffer.append(tok)
            await self.send_json({"type": "stream", "content": tok})

        self.generating = False
        full_reply = "".join(reply_buffer)

        if not self.stop_event.is_set():
            self.history.append({"role": "assistant", "content": full_reply})
            await self.send_json({
                "type": "done",
                "latency_s": round(time.time() - start, 2)
            })
        else:
            await self.send_json({"type": "cancelled"})

    async def _stream_tokens(self, streamer):
        loop = asyncio.get_running_loop()
        def safe_next(it):
            try:
                return next(it)
            except StopIteration:
                return None

        while True:
            tok = await loop.run_in_executor(None, safe_next, streamer)
            if tok is None:
                break
            yield tok

    async def disconnect(self, code):
        if self.generating and self.stop_event:
            self.stop_event.set()

    async def send_json(self, obj):
        await self.send(text_data=json.dumps(obj))
