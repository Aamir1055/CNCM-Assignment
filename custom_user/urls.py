from django.urls import path
from .views import register_view,login_view,task_all,task_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('all_task/',task_all,name='all_task'),
    path('task/',task_view,name='task'),
]
