from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.response import TemplateResponse

from .models import User


class UserAdmin(BaseUserAdmin):
    # The fields to be used in displaying the User model.
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'admin_actions')
    list_filter = ('role', 'is_staff', 'is_active')
    actions = ['make_doctor', 'make_secretary', 'make_patient']
    
    def changelist_view(self, request, extra_context=None):
        """Override to add a button to manage special roles"""
        extra_context = extra_context or {}
        extra_context['special_roles_url'] = reverse('admin:manage-special-roles')
        return super().changelist_view(request, extra_context=extra_context)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'birth_date')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'manage-special-roles/',
                self.admin_site.admin_view(self.manage_special_roles_view),
                name='manage-special-roles',
            ),
            path(
                'change-role/<int:user_id>/<str:new_role>/',
                self.admin_site.admin_view(self.change_role_view),
                name='change-user-role',
            ),
            path(
                'delete-special-role/<int:user_id>/',
                self.admin_site.admin_view(self.delete_special_role_view),
                name='delete-special-role',
            ),
        ]
        return custom_urls + urls
    
    def admin_actions(self, obj):
        """Add links to special actions in the list view"""
        if obj.role == 'doctor':
            buttons = [
                f'<a href="{reverse("admin:change-user-role", args=[obj.pk, "patient"])}" class="button">Change to Patient</a>',
                f'<a href="{reverse("admin:delete-special-role", args=[obj.pk])}" class="button" style="background-color: #ba2121;">Delete Doctor</a>'
            ]
            return ' '.join(buttons)
        elif obj.role == 'secretary':
            buttons = [
                f'<a href="{reverse("admin:change-user-role", args=[obj.pk, "patient"])}" class="button">Change to Patient</a>',
                f'<a href="{reverse("admin:delete-special-role", args=[obj.pk])}" class="button" style="background-color: #ba2121;">Delete Secretary</a>'
            ]
            return ' '.join(buttons)
        elif obj.role == 'patient':
            # Check if we already have a doctor and secretary
            has_doctor = User.objects.filter(role='doctor').exists()
            has_secretary = User.objects.filter(role='secretary').exists()
            
            buttons = []
            if not has_doctor:
                buttons.append(f'<a href="{reverse("admin:change-user-role", args=[obj.pk, "doctor"])}" class="button">Make Doctor</a>')
            if not has_secretary:
                buttons.append(f'<a href="{reverse("admin:change-user-role", args=[obj.pk, "secretary"])}" class="button">Make Secretary</a>')
                
            return ' '.join(buttons) if buttons else '-'
        return '-'
    admin_actions.short_description = 'Actions'
    admin_actions.allow_tags = True
    
    def manage_special_roles_view(self, request):
        """Custom admin view to manage doctor and secretary roles"""
        # Get current doctor and secretary if they exist
        doctor = User.objects.filter(role='doctor').first()
        secretary = User.objects.filter(role='secretary').first()
        
        # Get all patients that could be promoted
        patients = User.objects.filter(role='patient')
        
        context = {
            'title': 'Manage Special Roles',
            'doctor': doctor,
            'secretary': secretary,
            'patients': patients,
            'opts': self.model._meta,
        }
        
        # Display the template
        return TemplateResponse(request, 'admin/accounts/manage_special_roles.html', context)
    
    def change_role_view(self, request, user_id, new_role):
        """Change a user's role and handle constraints"""
        try:
            user = User.objects.get(pk=user_id)
            old_role = user.role
            
            # Check constraints
            if new_role == 'doctor' and User.objects.filter(role='doctor').exists():
                messages.error(request, 'Cannot create another doctor. The system already has a doctor.')
            elif new_role == 'secretary' and User.objects.filter(role='secretary').exists():
                messages.error(request, 'Cannot create another secretary. The system already has a secretary.')
            else:
                # Update the role
                user.role = new_role
                user.save()
                messages.success(request, f'User {user.email} has been changed from {old_role} to {new_role}.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except Exception as e:
            messages.error(request, f'Error changing role: {str(e)}')
            
        # Redirect back to the user list
        return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
    
    def delete_special_role_view(self, request, user_id):
        """Handle deletion of doctor or secretary accounts"""
        try:
            user = User.objects.get(pk=user_id)
            role = user.get_role_display()
            
            if user.role not in ['doctor', 'secretary']:
                messages.error(request, f'This action is only for doctor or secretary accounts. {user.email} is a {role}.')
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
            
            # Confirm deletion or handle POST request for confirmed deletion
            if request.method == 'POST':
                # The admin has confirmed the deletion
                email = user.email
                user.delete()
                messages.success(request, f'The {role} account for {email} has been successfully deleted.')
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
            else:
                # Show confirmation page
                context = {
                    'title': f'Delete {role} Account',
                    'user_to_delete': user,
                    'role': role,
                    'opts': self.model._meta,
                }
                return TemplateResponse(request, 'admin/accounts/delete_special_role.html', context)
                
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
    
    def make_doctor(self, request, queryset):
        # Check if there's already a doctor
        if User.objects.filter(role='doctor').exists():
            doctor = User.objects.get(role='doctor')
            # If the doctor is in the queryset, we're trying to change another user to doctor
            if doctor not in queryset:
                self.message_user(request, 
                                 _('Cannot make user a doctor. There is already a doctor in the system.'),
                                 level='error')
                return
        
        # Update the selected user to be a doctor
        queryset.update(role='doctor')
        self.message_user(request, _('User has been updated to doctor role.'))
    make_doctor.short_description = _('Change selected user to doctor')
    
    def make_secretary(self, request, queryset):
        # Check if there's already a secretary
        if User.objects.filter(role='secretary').exists():
            secretary = User.objects.get(role='secretary')
            # If the secretary is in the queryset, we're trying to change another user to secretary
            if secretary not in queryset:
                self.message_user(request, 
                                 _('Cannot make user a secretary. There is already a secretary in the system.'),
                                 level='error')
                return
        
        # Update the selected user to be a secretary
        queryset.update(role='secretary')
        self.message_user(request, _('User has been updated to secretary role.'))
    make_secretary.short_description = _('Change selected user to secretary')
    
    def make_patient(self, request, queryset):
        # Update the selected users to be patients
        queryset.update(role='patient')
        self.message_user(request, _('Selected users have been updated to patient role.'))
    make_patient.short_description = _('Change selected users to patients')


# Custom admin site to override index template
class MedicalCabinetAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        # Check if there's a doctor and secretary
        has_doctor = User.objects.filter(role='doctor').exists()
        has_secretary = User.objects.filter(role='secretary').exists()
        
        # Prepare notifications
        notifications = []
        if not has_doctor:
            notifications.append({
                'message': 'There is no doctor account in the system. Please assign a doctor.',
                'url': reverse('admin:manage-special-roles'),
                'level': 'warning'
            })
        if not has_secretary:
            notifications.append({
                'message': 'There is no secretary account in the system. Please assign a secretary.',
                'url': reverse('admin:manage-special-roles'),
                'level': 'warning'
            })
        
        # Add to context
        extra_context = extra_context or {}
        extra_context['notifications'] = notifications
        
        return super().index(request, extra_context=extra_context)

# Create an instance of the custom admin site
admin_site = MedicalCabinetAdminSite(name='admin')

# Register the User model with the custom admin class
admin_site.register(User, UserAdmin)

# Replace the default admin site with our custom one
admin.site = admin_site

# Re-register all other models with the custom admin site
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Get all models from all apps except User which we already registered
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        try:
            # Skip User model as we already registered it with a custom admin class
            if model.__name__ != 'User':
                admin_site.register(model)
        except AlreadyRegistered:
            pass
