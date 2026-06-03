from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]
