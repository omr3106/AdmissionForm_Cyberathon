from django.contrib import admin
from django.urls import path
from admissions import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('delete/<str:doc_id>/', views.delete_record, name='delete'),
    path('update/<str:doc_id>/', views.update_record, name='update'), ]