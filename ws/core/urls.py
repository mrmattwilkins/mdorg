from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("rescan/", views.rescan, name="rescan"),
    path("search/", views.search, name="search"),
    path("items/", views.items, name="items"),
    path("item/", views.item, name="item"),
    path("item/delete/", views.delete, name="item_delete"),
    path("tags/", views.tags, name="tags"),
    path("login/", auth_views.LoginView.as_view()),
]
