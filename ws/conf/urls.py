from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("recipes/", include("core.urls")),
    path("admin/", admin.site.urls),
]
