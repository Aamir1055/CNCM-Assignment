from django_use_email_as_username.models import BaseUser
from django.db import models

class User(BaseUser):
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return self.email

class Task(models.Model):
    title = models.CharField(max_length=400)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


