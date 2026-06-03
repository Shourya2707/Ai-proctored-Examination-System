from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from .models import Exam, ExamAttempt, Question, Option, Answer
import json

class PreExamStagingView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        
        # Check if already attempted
        if ExamAttempt.objects.filter(student=request.user, exam=exam, status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']).exists():
            messages.info(request, "You have already completed or were disqualified from this exam.")
            return redirect('student_dashboard')
            
        attempt, created = ExamAttempt.objects.get_or_create(
            student=request.user, 
            exam=exam,
            status='IN_PROGRESS'
        )
        
        if attempt.is_calibrated:
            return redirect('take_exam', exam_id=exam.id)
            
        context = {
            'exam': exam,
            'attempt': attempt,
        }
        return render(request, 'exams/pre_exam.html', context)
        
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        attempt = get_object_or_404(ExamAttempt, student=request.user, exam=exam, status='IN_PROGRESS')
        
        photo_data = request.POST.get('verification_photo_base64')
        if photo_data:
            import base64
            from django.core.files.base import ContentFile
            try:
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f"selfie_{attempt.id}.{ext}")
                attempt.verification_photo = data
            except Exception as e:
                print(f"Error parsing selfie photo: {e}")
                
        attempt.is_calibrated = True
        attempt.save()
        
        return redirect('take_exam', exam_id=exam.id)

class TakeExamView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        
        # Check if already attempted
        if ExamAttempt.objects.filter(student=request.user, exam=exam, status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']).exists():
            messages.info(request, "You have already completed or were disqualified from this exam.")
            return redirect('student_dashboard')
            
        attempt, created = ExamAttempt.objects.get_or_create(
            student=request.user, 
            exam=exam,
            status='IN_PROGRESS'
        )
        
        if not attempt.is_calibrated:
            messages.warning(request, "Please complete identity verification and device calibration before starting the exam.")
            return redirect('pre_exam', exam_id=exam.id)
        
        # Fetch questions with options
        questions = exam.questions.all().prefetch_related('options')
        
        context = {
            'exam': exam,
            'attempt': attempt,
            'questions': questions,
        }
        return render(request, 'exams/take_exam.html', context)

class SubmitExamView(LoginRequiredMixin, View):
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        
        try:
            attempt = ExamAttempt.objects.get(student=request.user, exam=exam, status='IN_PROGRESS')
        except ExamAttempt.DoesNotExist:
            # If the attempt is already submitted (e.g. double-click or auto-submit race condition)
            if ExamAttempt.objects.filter(student=request.user, exam=exam, status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']).exists():
                return redirect('exam_submitted', exam_id=exam.id)
            messages.error(request, "No active exam attempt found.")
            return redirect('student_dashboard')
        
        # Check auto-disqualification
        if request.POST.get('auto_disqualified') == 'true':
            attempt.status = 'DISQUALIFIED'
            attempt.score = 0.0
            attempt.save()
            messages.error(request, "Your exam was terminated and disqualified due to proctor violations.")
            return redirect('exam_submitted', exam_id=exam.id)

        # Process answers
        questions = exam.questions.all()
        score = 0.0
        
        for q in questions:
            if q.question_type == 'MCQ':
                option_id = request.POST.get(f'q{q.id}')
                if option_id:
                    option = get_object_or_404(Option, id=option_id)
                    Answer.objects.create(attempt=attempt, question=q, selected_option=option)
                    if option.is_correct:
                        score += q.marks
                    elif exam.negative_marking:
                        score -= exam.negative_mark_value
            elif q.question_type == 'SUBJECTIVE':
                text = request.POST.get(f'q{q.id}')
                if text:
                    Answer.objects.create(attempt=attempt, question=q, subjective_text=text)
                    
        # Score shouldn't go below 0
        attempt.score = max(0.0, score)
        attempt.status = 'SUBMITTED'
        attempt.save()
        
        messages.success(request, f"Exam submitted successfully! Your score: {attempt.score}")
        return redirect('exam_submitted', exam_id=exam.id)


class ExamSubmittedView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        attempt = ExamAttempt.objects.filter(
            student=request.user,
            exam=exam,
            status__in=['SUBMITTED', 'AUTO_SUBMITTED', 'DISQUALIFIED']
        ).order_by('-start_time').first()

        if not attempt:
            messages.info(request, "No submitted attempt found for this exam.")
            return redirect('student_dashboard')

        total_questions = exam.questions.count()
        answered_count = attempt.answers.count()
        has_subjective = exam.questions.filter(question_type='SUBJECTIVE').exists()

        context = {
            'exam': exam,
            'attempt': attempt,
            'total_questions': total_questions,
            'answered_count': answered_count,
            'has_subjective': has_subjective,
        }
        return render(request, 'exams/exam_submitted.html', context)

class CreateExamView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_admin():
            return redirect('student_dashboard')
        return render(request, 'admin/create_exam.html')
        
    def post(self, request):
        if not request.user.is_admin():
            return redirect('student_dashboard')
            
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_time = request.POST.get('start_time')
        duration = request.POST.get('duration')
        
        # New: Questions data from hidden input (JSON)
        questions_data = request.POST.get('questions_json')
        
        exam = Exam.objects.create(
            title=title,
            description=description,
            start_time=start_time,
            duration_minutes=duration,
            status='UPCOMING'
        )
        
        if questions_data:
            try:
                questions = json.loads(questions_data)
                for q_data in questions:
                    q = Question.objects.create(
                        exam=exam,
                        text=q_data['text'],
                        question_type=q_data['type'],
                        marks=q_data.get('marks', 1)
                    )
                    if q_data['type'] == 'MCQ' and 'options' in q_data:
                        for opt_data in q_data['options']:
                            Option.objects.create(
                                question=q,
                                text=opt_data['text'],
                                is_correct=opt_data.get('is_correct', False)
                            )
            except Exception as e:
                messages.error(request, f"Error processing questions: {str(e)}")
        
        messages.success(request, f"Exam '{title}' created successfully with {exam.questions.count()} questions.")
        return redirect('admin_dashboard')

import csv
from django.http import HttpResponse

class ExportExamCSVReportView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        if not request.user.is_admin():
            return redirect('student_dashboard')
            
        exam = get_object_or_404(Exam, id=exam_id)
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('student').prefetch_related('violations')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="exam_{exam_id}_proctoring_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student Username', 
            'Email', 
            'Start Time', 
            'End Time', 
            'Attempt Status', 
            'Warnings Logged', 
            'Cheating Risk Score (%)', 
            'Score / Grade', 
            'Violations Highlight'
        ])
        
        for attempt in attempts:
            violations_summary = ", ".join([v.get_violation_type_display() for v in attempt.violations.all()])
            writer.writerow([
                attempt.student.username,
                attempt.student.email,
                attempt.start_time.strftime('%Y-%m-%d %H:%M:%S') if attempt.start_time else 'N/A',
                attempt.end_time.strftime('%Y-%m-%d %H:%M:%S') if attempt.end_time else 'N/A',
                attempt.get_status_display(),
                attempt.warning_count,
                f"{attempt.cheating_risk_score:.1f}%",
                attempt.score if attempt.score is not None else 'N/A',
                violations_summary or 'No violations'
            ])
            
        return response

class ExportExamPDFReportView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        if not request.user.is_admin():
            return redirect('student_dashboard')
            
        exam = get_object_or_404(Exam, id=exam_id)
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('student').prefetch_related('violations').order_by('-cheating_risk_score')
        
        # Calculate summary statistics
        total_attempts = attempts.count()
        disqualified_count = attempts.filter(status='DISQUALIFIED').count()
        auto_submitted_count = attempts.filter(status='AUTO_SUBMITTED').count()
        clean_attempts_count = attempts.filter(warning_count=0).count()
        
        context = {
            'exam': exam,
            'attempts': attempts,
            'total_attempts': total_attempts,
            'disqualified_count': disqualified_count,
            'auto_submitted_count': auto_submitted_count,
            'clean_attempts_count': clean_attempts_count,
        }
        return render(request, 'admin/exam_pdf_report.html', context)
