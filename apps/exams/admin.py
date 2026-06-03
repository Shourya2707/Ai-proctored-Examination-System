from django.contrib import admin
from .models import Exam, Question, Option, ExamAttempt, Answer

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'duration_minutes', 'status')
    list_filter = ('status',)
    search_fields = ('title',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'exam', 'question_type', 'marks')
    list_filter = ('exam', 'question_type')

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'status', 'score', 'cheating_risk_score')
    list_filter = ('status', 'exam')

admin.site.register(Answer)
