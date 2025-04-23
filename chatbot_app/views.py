# chatbot_app/views.py
from django.shortcuts import render

def chat_view(request):
    # Renderiza la plantilla chat.html
    return render(request, "chat.html")
