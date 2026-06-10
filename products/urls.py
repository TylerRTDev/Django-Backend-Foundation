from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('grid/', views.product_grid, name='product_grid'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]