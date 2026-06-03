from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        ADMIN = 'ADMIN', 'Admin'
        
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    
    def is_student(self):
        return self.role == self.Role.STUDENT
        
    def is_admin(self):
        return self.role == self.Role.ADMIN
