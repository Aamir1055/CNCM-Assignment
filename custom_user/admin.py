from django.contrib import admin
from django_use_email_as_username.admin import BaseUserAdmin

from .models import User,Task

admin.site.register(User)
admin.site.register(Task)


