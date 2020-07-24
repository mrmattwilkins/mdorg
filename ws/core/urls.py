from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [

   path('rescan/', views.rescan, name='rescan'),

   path('search/', views.search, name='search'),
   #path('search/<str:text>/', views.search, name='search'),

   path('', views.items, name='items'),
   path('items/<int:tag>/', views.items, name='items'),

   path('item/<int:pkey>/', views.item, name='item'),
   path('item/<int:pkey>/<int:tag>', views.item, name='item'),

   path('zitem/', views.zitem, name='zitem'),
   path('ztags/', views.ztags, name='ztags'),

   #path('item/<int:pkey>/edit/', item.edit, name='item_edit'),
   #path('item/new/', item.new, name='item_new'),
   #path('item/<int:pkey>/delete/', item.delete, name='item_delete'),
   #path('item/<int:pkey>/', item.detail, name='item_detail'),

]
