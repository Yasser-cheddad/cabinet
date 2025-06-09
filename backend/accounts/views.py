from rest_framework import generics, permissions
from .serializers import UserSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User

# Registration view
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user (patient, doctor, or secretary)"""
    # Use serializer for validation and creation
    serializer = UserSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Get the password from the request data before it's hashed
            raw_password = request.data.get('password')
            
            # Create the user
            user = serializer.save()
            
            # Send welcome email with login information
            from notifications.email_utils import send_email
            
            # Prepare email content
            subject = "Bienvenue au Cabinet Médical - Vos informations de connexion"
            body = f"""Bonjour {user.first_name} {user.last_name},

Votre compte a été créé avec succès dans notre système de gestion de cabinet médical.

Voici vos informations de connexion:
- Email: {user.email}
- Mot de passe: {raw_password}
- Rôle: {user.get_role_display()}

Veuillez conserver ces informations en lieu sûr. Nous vous recommandons de changer votre mot de passe après votre première connexion.

Cordialement,
L'équipe du Cabinet Médical
"""
            
            # Send the email
            email_sent = send_email(user.email, subject, body)
            
            # Return response
            response_data = {
                'success': _('User registered successfully'),
                'user_id': user.id,
                'email': user.email,
                'role': user.role
            }
            
            if email_sent:
                response_data['email_notification'] = 'Email with login information sent successfully'
            else:
                response_data['email_notification'] = 'Failed to send email notification'
                
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            print(f"Registration error: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Note: The code below is not executed because we're using the serializer approach above
    # This is just kept for reference

# Login view
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login a user and return JWT tokens"""
    print(f"Login request data: {request.data}")
    email = request.data.get('email')
    password = request.data.get('password')
    print(f"Email: {email}, Password provided: {bool(password)}")
    print(f"Request content type: {request.content_type}")
    print(f"Request headers: {request.headers}")
    
    if not email or not password:
        return Response({
            'error': _('Please provide both email and password')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, email=email, password=password)
    
    if user is not None:
        from rest_framework_simplejwt.tokens import RefreshToken
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': _('Login successful'),
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'name': user.get_full_name()
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': _('Invalid email or password')
        }, status=status.HTTP_401_UNAUTHORIZED)

# Logout view
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout the current user"""
    logout(request)
    return Response({
        'success': _('Logged out successfully')
    }, status=status.HTTP_200_OK)

# User profile view
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update the current user's profile"""
    user = request.user
    
    if request.method == 'GET':
        # Return user profile data
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'phone_number': user.phone_number,
            'birth_date': user.birth_date,
        }
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        # Update user profile
        try:
            # Update basic fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.phone_number = request.data.get('phone_number', user.phone_number)
            
            # Handle birth_date if provided
            birth_date = request.data.get('birth_date')
            if birth_date:
                user.birth_date = birth_date
            
            # Save changes
            user.save()
            
            return Response({
                'success': _('Profile updated successfully')
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Password change view
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password"""
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'error': _('Please provide both current and new password')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify current password
    if not user.check_password(current_password):
        return Response({
            'error': _('Current password is incorrect')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Update session auth hash to prevent logout
    login(request, user)
    
    return Response({
        'success': _('Password changed successfully')
    }, status=status.HTTP_200_OK)

# Get doctors endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def get_doctors(request):
    """Get all doctors"""
    doctors = User.objects.filter(role='doctor')
    data = [{
        'id': doctor.id,
        'name': doctor.get_full_name(),
        'email': doctor.email
    } for doctor in doctors]
    return Response(data, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]