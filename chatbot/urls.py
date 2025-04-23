# chatbot/urls.py
from django.contrib import admin
from django.urls import path
from chatbot_app.views import chat_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("",   chat_view, name="chat"),  # la raíz muestra tu chat
]
