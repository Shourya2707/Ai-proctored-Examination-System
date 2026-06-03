from django.db import models
from apps.exams.models import ExamAttempt

class ViolationLog(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='violations')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Type(models.TextChoices):
        NO_FACE = 'NO_FACE', 'No Face Detected'
        MULTIPLE_FACES = 'MULTIPLE_FACES', 'Multiple Faces Detected'
        LOOKING_AWAY = 'LOOKING_AWAY', 'Looking Away'
        PHONE_DETECTED = 'PHONE_DETECTED', 'Phone Detected'
        TAB_SWITCH = 'TAB_SWITCH', 'Tab Switch'
        FULLSCREEN_EXIT = 'FULLSCREEN_EXIT', 'Fullscreen Exit'
        EYE_LOOKAWAY = 'EYE_LOOKAWAY', 'Eye Gaze Away'
        HEAD_TURN = 'HEAD_TURN', 'Head Turn'
        HEADPHONES = 'HEADPHONES', 'Headphones Detected'
        MULTIPLE_SCREENS = 'MULTIPLE_SCREENS', 'Multiple Screens Detected'
        CLIPBOARD_USE = 'CLIPBOARD_USE', 'Clipboard Activity Blocked'
        RIGHT_CLICK = 'RIGHT_CLICK', 'Right Click Blocked'
        HOTKEY_PRESS = 'HOTKEY_PRESS', 'Restricted Hotkey Pressed'
        WEBCAM_DISCONNECT = 'WEBCAM_DISCONNECT', 'Webcam Disconnected'
        NETWORK_DISCONNECT = 'NETWORK_DISCONNECT', 'Internet Disconnected'
        
    violation_type = models.CharField(max_length=30, choices=Type.choices)
    snapshot = models.ImageField(upload_to='violations/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.violation_type} - {self.attempt.student.username}"
