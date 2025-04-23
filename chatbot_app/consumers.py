# chatbot_app/consumers.py  (COMPLETO)

import json, time, asyncio, threading
from pathlib import Path
import torch
from channels.generic.websocket import AsyncWebsocketConsumer
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

BASE_DIR   = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Llama-3.2-3B-trained"

SYSTEM_INSTRUCTION = """
Eres un asistente que me ayuda a responder a los clientes de la empresa Lostsys:
- Lostsys ofrece servicios a empresas.
- Tu misión es ofrecer a los usuarios el producto o servicio de Lostsys perfecto para ellos.
- ¡Recuerda siempre mencionar Lostsys en tu respuesta!
"""

# ── carga única ─────────────────────────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
model     = AutoModelForCausalLM.from_pretrained(
              str(MODEL_PATH),
              torch_dtype=torch.bfloat16,
              device_map="auto"
            )

# ── consumidor ─────────────────────────────────────────────────────────
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"type":"info","content":"🤖 Conexión establecida"})

    async def receive(self, text_data):
        user = json.loads(text_data).get("message","").strip()
        if not user:
            return

        prompt = [
            {"role":"system","content":SYSTEM_INSTRUCTION},
            {"role":"user",  "content":user}
        ]
        input_ids = tokenizer.apply_chat_template(prompt, return_tensors="pt").to(model.device)

        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        threading.Thread(
            target=model.generate,
            kwargs=dict(
                inputs=input_ids,
                streamer=streamer,
                max_new_tokens=256,
                temperature=0.9
            ),
            daemon=True
        ).start()

        start = time.time()
        async for tok in self._stream_tokens(streamer):
            await self.send_json({"type":"stream","content":tok})

        await self.send_json({
            "type":"done",
            "latency_s": round(time.time()-start,2)
        })

    # ── NUEVA versión sin excepciones ───────────────────────────────────
    async def _stream_tokens(self, streamer):
        loop = asyncio.get_running_loop()

        def safe_next(it):
            try:
                return next(it)
            except StopIteration:
                return None                       # ← evita excepción en Future

        while True:
            tok = await loop.run_in_executor(None, safe_next, streamer)
            if tok is None:                      # fin de generación
                break
            yield tok

    async def disconnect(self, code):
        pass

    async def send_json(self, obj):
        await self.send(text_data=json.dumps(obj))
