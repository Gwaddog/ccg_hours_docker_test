from django.contrib import admin
from django import forms
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
#from django.contrib.auth.models import User
from .models import ActiveUser, Period, PayrollHours
from .forms import ActiveUserChangeForm, ActiveUserCreationForm

class ActiveUserAdmin(UserAdmin):
    model = ActiveUser
    add_form = ActiveUserCreationForm
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Other Personal info',
            {
                'fields': (
                    'start_date',
                    'end_date',
                    'vacation_hours',
                    'phone_number',
                )
            }
        )
    )

admin.site.register(ActiveUser, ActiveUserAdmin)

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
#class ActiveUserInline(admin.StackedInline):
#    model = ActiveUser
#    can_delete = False
#    verbose_name_plural = "activeusers"
#    
#class UserAdmin(BaseUserAdmin):
#    inlines = [ActiveUserInline]

# Register your models here.
#admin.site.unregister(User)
#admin.site.register(User, UserAdmin)

class HoursInline(admin.TabularInline):
    model = PayrollHours
    #admin.site.register(ActiveUsers, ActiveUsersAdmin)
#@admin.register(ActiveUsers)
#class ActiveUsersAdmin(admin.ModelAdmin):
#    list_display = ('name', 'start_date', 'end_date', 'phone_number')
#    
#    inlines = [HoursInline]
    
#admin.site.register(ActiveUsers)   # ActiveUsers was registered using the @admin.register(ActiveUsers) sequence above
admin.site.register(Period)
admin.site.register(PayrollHours)
