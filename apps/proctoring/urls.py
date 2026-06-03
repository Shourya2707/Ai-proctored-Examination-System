from django.urls import path
from . import views

urlpatterns = [
    path('exam/<int:exam_id>/monitor/', views.LiveMonitoringView.as_view(), name='live_monitoring'),
]
