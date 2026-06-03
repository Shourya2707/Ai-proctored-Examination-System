from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.exams.models import Exam, ExamAttempt, Question, Option, Answer
from apps.proctoring.models import ViolationLog

User = get_user_model()

class ProctoringTestCase(TestCase):
    def setUp(self):
        # Create standard and admin users
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpassword123',
            role='STUDENT'
        )
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpassword123',
            role='ADMIN'
        )
        
        # Create an exam with negative marking enabled
        self.exam = Exam.objects.create(
            title='Proctored AI Midterm',
            description='Test description',
            start_time='2026-05-20T10:00:00Z',
            duration_minutes=60,
            total_marks=10,
            negative_marking=True,
            negative_mark_value=0.5,
            allowed_warnings=3
        )
        
        # Create questions and options
        self.q1 = Question.objects.create(
            exam=self.exam,
            text='What is 2 + 2?',
            question_type='MCQ',
            marks=5
        )
        self.opt_correct_1 = Option.objects.create(
            question=self.q1,
            text='4',
            is_correct=True
        )
        self.opt_wrong_1 = Option.objects.create(
            question=self.q1,
            text='5',
            is_correct=False
        )
        
        self.q2 = Question.objects.create(
            exam=self.exam,
            text='What is 3 * 3?',
            question_type='MCQ',
            marks=5
        )
        self.opt_correct_2 = Option.objects.create(
            question=self.q2,
            text='9',
            is_correct=True
        )
        self.opt_wrong_2 = Option.objects.create(
            question=self.q2,
            text='8',
            is_correct=False
        )

    def test_user_role_helpers(self):
        """Test that user role helpers work correctly."""
        self.assertFalse(self.student.is_admin())
        self.assertTrue(self.admin.is_admin())

    def test_exam_attempt_creation(self):
        """Test creating an exam attempt with default settings."""
        attempt = ExamAttempt.objects.create(
            student=self.student,
            exam=self.exam,
            status='IN_PROGRESS'
        )
        self.assertEqual(attempt.status, 'IN_PROGRESS')
        self.assertEqual(attempt.warning_count, 0)
        self.assertEqual(attempt.cheating_risk_score, 0.0)
        self.assertFalse(attempt.is_calibrated)

    def test_violation_logging(self):
        """Test logging violations and tracking warning count."""
        attempt = ExamAttempt.objects.create(
            student=self.student,
            exam=self.exam,
            status='IN_PROGRESS'
        )
        
        # Log a tab switch violation
        v1 = ViolationLog.objects.create(
            attempt=attempt,
            violation_type=ViolationLog.Type.TAB_SWITCH,
            description="Student switched tab"
        )
        
        self.assertEqual(v1.violation_type, ViolationLog.Type.TAB_SWITCH)
        self.assertEqual(attempt.violations.count(), 1)

    def test_score_calculation_with_negative_marking(self):
        """Test score calculation including negative marking deductions."""
        attempt = ExamAttempt.objects.create(
            student=self.student,
            exam=self.exam,
            status='IN_PROGRESS'
        )
        
        # 1 correct answer (5 marks), 1 incorrect answer (-0.5 marks deduction)
        Answer.objects.create(attempt=attempt, question=self.q1, selected_option=self.opt_correct_1)
        Answer.objects.create(attempt=attempt, question=self.q2, selected_option=self.opt_wrong_2)
        
        # Mimic grading from view logic
        score = 0.0
        for ans in attempt.answers.all():
            if ans.selected_option and ans.selected_option.is_correct:
                score += ans.question.marks
            elif self.exam.negative_marking:
                score -= self.exam.negative_mark_value
                
        attempt.score = max(0.0, score)
        attempt.status = 'SUBMITTED'
        attempt.save()
        
        # 5 - 0.5 = 4.5 marks
        self.assertEqual(attempt.score, 4.5)
        self.assertEqual(attempt.status, 'SUBMITTED')
