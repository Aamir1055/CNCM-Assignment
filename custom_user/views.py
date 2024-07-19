import re
from django.contrib.auth import get_user_model,authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from custom_user.serializers import UserSerializer, TaskSerializer
from rest_framework.request import Request
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from custom_user.models import User, Task
from django.contrib.auth.models import User
from django.core.mail import send_mail
# from django.core.mail import EmailMessage
from elevate.settings import EMAIL_HOST_USER
from django.contrib.auth import get_user_model  


CustomUser = get_user_model()

@api_view(['POST'])
def register_view(request):
    data = request.data
    
    email = data.get('email')
    if not email:
        return Response('Email field should not be blank', status=status.HTTP_400_BAD_REQUEST)
    
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.search(regex, email):
        return Response('Invalid Email', status=status.HTTP_400_BAD_REQUEST)
    
    password = data.get('password')
    if not password:
        return Response('Password field should not be blank', status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 8:
        return Response('This password is too short. It must contain at least 8 characters.', status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r'[A-Z]', password):
        return Response('This password must contain at least one uppercase letter.', status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r'\d', password):
        return Response('This password must contain at least one digit.', status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return Response('This password must contain at least one special character.', status=status.HTTP_400_BAD_REQUEST)
    
    first_name = data.get('first_name')
    if not first_name:
        return Response('First name field should not be blank', status=status.HTTP_400_BAD_REQUEST)
    
    last_name = data.get('last_name')
    if not last_name:
        return Response('Last name field should not be blank', status=status.HTTP_400_BAD_REQUEST)
    
    if not CustomUser.objects.filter(email=email).exists():
        user = CustomUser(first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        user.save()
        
        
        group, created = Group.objects.get_or_create(name='Customer')
        user.groups.add(group)
        
        return Response("User Created", status=status.HTTP_201_CREATED)
    else:
        return Response("User Already Exists", status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response('Please provide both email and password', status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(email=email, password=password)

    if not user:
        return Response('Invalid Credentials', status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })



@api_view(['GET'])
def task_all(request: Request):
    authenticated_user = JWTAuthentication().authenticate(request)
    if authenticated_user is None:
        return Response("Given token not valid for any token type", status = status.HTTP_401_UNAUTHORIZED)

    if request.method == "GET":
        user_list = Task.objects.all()
        serializer = TaskSerializer(user_list, many = True, context = {'request': None})
        return Response(serializer.data, status = status.HTTP_200_OK)

    return Response("Request Failed", status = status.HTTP_400_BAD_REQUEST)




User = get_user_model()

@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def task_view(request: Request):
    req_data = request.data
    authenticated_user = JWTAuthentication().authenticate(request)
    
    if authenticated_user is not None:
        USER, TOKEN = authenticated_user
    else:
        return Response("Given token not valid for any token type", status=status.HTTP_401_UNAUTHORIZED)

    
    if request.method == "POST":
        
        title = req_data.get('title')
        description = req_data.get('description')
        due_date = req_data.get('due_date')
        assigned_to_email = req_data.get('assigned_to')  
        
        try:
            assigned_to_user = User.objects.get(email=assigned_to_email)
        except User.DoesNotExist:
            return Response(f"User with email '{assigned_to_email}' does not exist", status=status.HTTP_404_NOT_FOUND)
        
        
        req_data['assigned_to'] = assigned_to_user.pk
        
        serializer = TaskSerializer(data=req_data)
        if serializer.is_valid():

            serializer.save()
            # Send email notification
            subject = 'New Task Assigned'
            message = f'A new task "{title}" has been assigned to you.'
            from_email = 'shaikhaamir2206@gmail.com'  
            to_email = assigned_to_email
            
            send_mail(subject, message, from_email, [to_email])

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       

    elif request.method == "PATCH":
        task_id = req_data.get('id')
        try:
            task = Task.objects.get(pk=task_id, assigned_to=USER)
        except Task.DoesNotExist:
            return Response(f"Task with id '{task_id}' does not exist for user '{USER.email}'", status=status.HTTP_404_NOT_FOUND)
        
    
        if 'title' in req_data:
            task.title = req_data['title']
        if 'description' in req_data:
            task.description = req_data['description']
        if 'due_date' in req_data:
            task.due_date = req_data['due_date']
        if 'assigned_to' in req_data:
            try:
                assigned_to_user = User.objects.get(email=req_data['assigned_to'])
                task.assigned_to = assigned_to_user
            except User.DoesNotExist:
                return Response(f"User with email '{req_data['assigned_to']}' does not exist", status=status.HTTP_404_NOT_FOUND)
        if 'completed' in req_data:
            task.completed = req_data['completed']

        task.save()
        serializer = TaskSerializer(task, context={'request': None})
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "DELETE":
        task_id = req_data.get('id')
        try:
            task = Task.objects.get(pk=task_id, assigned_to=USER)
            task.delete()
            return Response("Task Deleted", status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response(f"Task with id '{task_id}' does not exist for user '{USER.email}'", status=status.HTTP_404_NOT_FOUND)

    return Response("Request Failed", status=status.HTTP_400_BAD_REQUEST)


