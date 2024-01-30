from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_image, name='upload_image'),
    path('upload-page/', views.upload_page, name='upload_page'),
    path('summary/', views.summary, name='summary'),
]

