import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import chatbot_app.routing  # <-- crea esto luego

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chatbot_app.routing.websocket_urlpatterns
        )
    ),
})
