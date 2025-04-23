# chatbot_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Conectado al WebSocket"}))

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Aquí luego se integrará Meta LLaMA
        response = f"Echo: {message}"

        await self.send(text_data=json.dumps({
            "message": response
        }))

    async def disconnect(self, close_code):
        pass
