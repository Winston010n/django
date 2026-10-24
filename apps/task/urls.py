from django.urls import path
from .views import GroupedTaskView, TaskView, TaskDetailView

urlpatterns = [
    path('', TaskView.as_view(), name='task-list'),
    path('grouped/', GroupedTaskView.as_view(), name='task-grouped'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]
