from django.urls import path
from . import views

urlpatterns = [
    path('<int:exam_id>/pre/', views.PreExamStagingView.as_view(), name='pre_exam'),
    path('<int:exam_id>/take/', views.TakeExamView.as_view(), name='take_exam'),
    path('<int:exam_id>/submit/', views.SubmitExamView.as_view(), name='submit_exam'),
    path('<int:exam_id>/submitted/', views.ExamSubmittedView.as_view(), name='exam_submitted'),
    path('create/', views.CreateExamView.as_view(), name='admin_create_exam'),
    path('<int:exam_id>/export/csv/', views.ExportExamCSVReportView.as_view(), name='export_exam_csv'),
    path('<int:exam_id>/export/pdf/', views.ExportExamPDFReportView.as_view(), name='export_exam_pdf'),
]
