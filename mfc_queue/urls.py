import os
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, Http404
import mimetypes


def frontend_view(request, filename='index.html'):
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    filepath = os.path.join(frontend_dir, filename)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        raise Http404
    mime, _ = mimetypes.guess_type(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type=mime or 'text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('booking.urls')),
    path('', lambda req: frontend_view(req, 'index.html')),
    path('<str:filename>', frontend_view),
]
