from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from apps.exams.models import Exam, ExamAttempt
from apps.proctoring.models import ViolationLog

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_admin():
                return redirect('admin_dashboard')
            return redirect('student_dashboard')
        return render(request, 'auth/login.html')
        
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_admin():
                return redirect('admin_dashboard')
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'auth/login.html')

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('student_dashboard')
        return render(request, 'auth/register.html')
        
    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
            
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('student_dashboard')

def logout_view(request):
    logout(request)
    return redirect('login')

class StudentDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_admin():
            return redirect('admin_dashboard')
            
        upcoming_exams = Exam.objects.filter(status__in=['UPCOMING', 'ONGOING']).order_by('start_time')
        # Filter out exams already attempted
        attempted_exam_ids = request.user.attempts.values_list('exam_id', flat=True)
        upcoming_exams = upcoming_exams.exclude(id__in=attempted_exam_ids)
        
        completed_count = request.user.attempts.filter(status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']).count()
        
        # Calculate average score
        attempts = request.user.attempts.filter(score__isnull=False)
        avg_score = attempts.aggregate(models.Avg('score'))['score__avg'] or 0
        
        # Get historical attempts with related exam and violations
        history_attempts = request.user.attempts.select_related('exam').prefetch_related('violations').order_by('-start_time')
        
        context = {
            'upcoming_exams': upcoming_exams,
            'upcoming_count': upcoming_exams.count(),
            'completed_count': completed_count,
            'avg_score': round(avg_score, 2),
            'history_attempts': history_attempts,
        }
        return render(request, 'student/dashboard.html', context)

class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_admin():
            return redirect('student_dashboard')
            
        context = {
            'active_exams_count': Exam.objects.filter(status__in=['ONGOING', 'UPCOMING']).count(),
            'total_students_count': User.objects.filter(role='STUDENT').count(),
            'total_violations_count': ViolationLog.objects.count(),
            'completed_exams_count': ExamAttempt.objects.filter(status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']).count(),
            'recent_violations': ViolationLog.objects.select_related('attempt__student', 'attempt__exam').order_by('-timestamp')[:10],
            'exams': Exam.objects.all().order_by('-start_time'),
        }
        return render(request, 'admin/dashboard.html', context)
