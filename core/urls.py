from django.urls import path
from . import views

urlpatterns = [
    path('', views.batch_pdf_to_epub, name='batch'),   
    path('progress/<str:task_id>/', views.progress_status),
]
