from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [

   path('', views.home, name='home'),
   path('rescan/', views.rescan, name='rescan'),

   #path('search/<str:text>/', views.search, name='search'),

   path('search/', views.search, name='search'),

   path('items/', views.items, name='items'),
   path('item/', views.item, name='item'),
   path('item/delete/', views.delete, name='item_delete'),
   path('tags/', views.tags, name='tags'),

   #path('item/<int:pkey>/edit/', item.edit, name='item_edit'),
   #path('item/new/', item.new, name='item_new'),
   #path('item/<int:pkey>/', item.detail, name='item_detail'),

]
