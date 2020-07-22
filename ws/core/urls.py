from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [

   path('', views.item, name='items'),
   #path('items/<slug:tag>/', views.item, name='items'),
   #path('item/<int:pkey>/edit/', item.edit, name='item_edit'),
   #path('item/new/', item.new, name='item_new'),
   #path('item/<int:pkey>/delete/', item.delete, name='item_delete'),
   #path('item/<int:pkey>/', item.detail, name='item_detail'),

]
