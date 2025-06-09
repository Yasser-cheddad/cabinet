from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.db import models
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import inspect

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication instead of username."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'doctor')  # Default role for superuser
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = 'doctor', _('Doctor')
        PATIENT = 'patient', _('Patient')
        SECRETARY = 'secretary', _('Secretary')
    
    # Remove username field (using email instead)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PATIENT,
        verbose_name=_('Role')
    )
    
    # Additional custom fields
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone Number')
    )
    
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Birth Date')
    )

    # Use email instead of username for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields
    
    # Use our custom manager
    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        swappable = 'AUTH_USER_MODEL'
        
    def _get_admin_user(self):
        """Helper method to determine if the action is being performed by an admin"""
        # Check if this is being called from the admin interface by an admin
        admin_user = None
        for frame in inspect.stack():
            if 'request' in frame.frame.f_locals:
                request = frame.frame.f_locals['request']
                if hasattr(request, 'user') and hasattr(request.user, 'is_superuser'):
                    admin_user = request.user
                    break
        return admin_user
    
    def save(self, *args, **kwargs):
        # Skip validation for superusers (they can create/modify any account)
        if self.is_superuser:
            return super().save(*args, **kwargs)
        
        # If an admin is making the change, allow it
        admin_user = self._get_admin_user()
        if admin_user and admin_user.is_superuser:
            return super().save(*args, **kwargs)
            
        # Enforce single doctor constraint
        if self.role == self.Role.DOCTOR and not self.pk:
            if User.objects.filter(role=self.Role.DOCTOR).exists():
                raise ValidationError(_('The system can only have one doctor. A doctor account already exists.'))
        
        # Enforce single secretary constraint
        if self.role == self.Role.SECRETARY and not self.pk:
            if User.objects.filter(role=self.Role.SECRETARY).exists():
                raise ValidationError(_('The system can only have one secretary. A secretary account already exists.'))
        
        # If changing role to doctor or secretary, check constraints
        if self.pk:
            old_instance = User.objects.get(pk=self.pk)
            if old_instance.role != self.role:
                if self.role == self.Role.DOCTOR and User.objects.filter(role=self.Role.DOCTOR).exists():
                    raise ValidationError(_('The system can only have one doctor. A doctor account already exists.'))
                if self.role == self.Role.SECRETARY and User.objects.filter(role=self.Role.SECRETARY).exists():
                    raise ValidationError(_('The system can only have one secretary. A secretary account already exists.'))
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to allow admins to delete doctor and secretary accounts"""
        # If this is a doctor or secretary, check if admin is making the request
        if self.role in [self.Role.DOCTOR, self.Role.SECRETARY]:
            admin_user = self._get_admin_user()
            
            # Allow deletion if it's an admin or superuser making the request
            if admin_user and admin_user.is_superuser:
                return super().delete(*args, **kwargs)
                
            # Otherwise, prevent deletion of doctor or secretary
            raise ValidationError(_(f'Cannot delete {self.get_role_display()} account. Only administrators can delete this account.'))
        
        # For other roles, proceed with normal deletion
        return super().delete(*args, **kwargs)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_groups",
        related_query_name="user",
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"