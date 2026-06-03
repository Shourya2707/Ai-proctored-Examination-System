from django.contrib import admin
from .models import ViolationLog

@admin.register(ViolationLog)
class ViolationLogAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'violation_type', 'timestamp')
    list_filter = ('violation_type', 'timestamp')
