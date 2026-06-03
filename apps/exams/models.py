from django.db import models
from django.conf import settings

class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    total_marks = models.IntegerField(default=100)
    pass_percentage = models.FloatField(default=50.0)
    randomize_questions = models.BooleanField(default=False)
    negative_marking = models.BooleanField(default=False)
    negative_mark_value = models.FloatField(default=0.0)
    allowed_warnings = models.IntegerField(default=3)
    
    class Status(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
        
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.UPCOMING)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    
    class Type(models.TextChoices):
        MCQ = 'MCQ', 'Multiple Choice'
        SUBJECTIVE = 'SUBJECTIVE', 'Subjective'
        CODING = 'CODING', 'Coding'
        
    question_type = models.CharField(max_length=15, choices=Type.choices, default=Type.MCQ)
    marks = models.IntegerField(default=1)
    
    def __str__(self):
        return self.text[:50]

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text

class ExamAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        AUTO_SUBMITTED = 'AUTO_SUBMITTED', 'Auto Submitted'
        DISQUALIFIED = 'DISQUALIFIED', 'Disqualified'
        
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    score = models.FloatField(null=True, blank=True)
    cheating_risk_score = models.FloatField(default=0.0)
    warning_count = models.IntegerField(default=0)
    is_calibrated = models.BooleanField(default=False)
    verification_photo = models.ImageField(upload_to='verifications/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

class Answer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, null=True, blank=True, on_delete=models.SET_NULL)
    subjective_text = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.attempt} - Q: {self.question.id}"
