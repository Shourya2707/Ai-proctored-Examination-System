from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.exams.models import Exam, ExamAttempt
from apps.proctoring.models import ViolationLog

class LiveMonitoringView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        if not request.user.is_admin():
            return redirect('student_dashboard')
            
        exam = get_object_or_404(Exam, id=exam_id)
        # Fetch active attempts
        active_attempts = ExamAttempt.objects.filter(exam=exam, status='IN_PROGRESS').select_related('student')
        
        # Fetch violation history
        violation_logs = ViolationLog.objects.filter(attempt__exam=exam).select_related('attempt__student').order_by('-timestamp')[:50]
        
        context = {
            'exam': exam,
            'active_attempts': active_attempts,
            'active_count': active_attempts.count(),
            'violation_logs': violation_logs,
        }
        return render(request, 'admin/live_monitoring.html', context)
