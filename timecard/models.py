from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.urls import reverse
from phone_field import PhoneField
from django.utils import timezone
from django.utils.timezone import localtime
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from datetime import date, datetime, timedelta

# Create your models here.
class MyUserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self, start_date, end_date, phone_number, password, **extra_fields):
        """ Creates and saves a User with additional fields"""
        if not start_date:
            raise ValueError('Users must have an employment start date')
        if not phone_number:
            raise ValueError('Users must have a mobile phone number')
        
        user = self.model(
            start_date = start_date,
            end_date = end_date,
            phone_number=phone_number,            
            **extra_fields)
        
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, start_date, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not start_date:
            raise ValueError('Users must have an employment start date')
        if not phone_number:
            raise ValueError('Users must have a mobile phone number')
        
        user = self.model(
            start_date = start_date,
            end_date = None,
            phone_number=phone_number,            
            **extra_fields)
        
        user.is_admin = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user        

class ActiveUser(AbstractUser):
    """ActiveUser model is an Abstract based on the built in Django User."""
    # Changed to AbstractUser as documented in: https://learndjango.com/tutorials/django-custom-user-model
    # other docs: https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project

    pass
    # Add other needed fields
    start_date = models.DateField(null=False, blank=False, help_text='Start Date')
    end_date = models.DateField(default=None, null=True, blank=True, help_text='End Date')
    vacation_hours = models.IntegerField(default=0, null=False, help_text='Vacation hours alloted per year')
    phone_number = PhoneField(null=False, blank=False, unique=True, E164_only=False, help_text='Mobile phone number')
    #   See: https://github.com/VeryApt/django-phone-field#readme 
    #     https://stackoverflow.com/questions/19130942/whats-the-best-way-to-store-a-phone-number-in-django-models for more details

    objects = MyUserManager()
    
    REQUIRED_FIELDS = ['email', 'start_date', 'vacation_hours', 'phone_number']
    
    def __str__(self):
        """String for representing the ActiveUser object."""
        return f'{self.first_name} {self.last_name}, Started:{self.start_date}, Phone:{self.phone_number}'
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this ActiveUser."""
        return reverse('activeuser-home', args=[str(self.id), str(0), str(0)])
    
class Period(models.Model):
    """Period model represents a payroll period"""
    period = models.AutoField(primary_key=True, help_text='Period Primary Key')
    period_no = models.IntegerField(choices=((i,i) for i in range(1, 13)), help_text='Period No within the calendar year')
    calendar_year = models.IntegerField(validators=[MinValueValidator(2023), MaxValueValidator(9999)], help_text='Calendar year')
    fiscal_year = models.CharField(max_length=4, help_text='Fiscal Year in the format FYyy')
    starting_date = models.DateField(help_text='Starting Date of the Period')
    reporting_date = models.DateField(help_text='Date/Hour when employee needs to report hours')
    submission_date = models.DateField(help_text='Date when manager needs to submit for paycheck processing')
    submission_time = models.TimeField(default='13:00:00', help_text='Time when manager needs to submit for paycheck processing')
    pay_date = models.DateField(help_text='Date paycheck is to be received by Employee')
    pay_time = models.TimeField(default = datetime.strptime(f"09:00:00", "%H:%M:%S").time(), help_text = 'Time of day Paycheck is expected')
        
    # Metadata
    class Meta:
        ordering = ['starting_date']
        
    def __str__(self):
        """String for representing the Period table"""
#        return f'Period:{self.period_no}, Start:{self.starting_date}, Submit:{localtime(self.submission_time)}'
        return f'Period:{self.period_no}, Start:{self.starting_date}, Submit:{self.submission_date}/{self.submission_time}'
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this Period."""
        return reverse('period-list', args=[str(self.period)])    

class PayrollHours(models.Model):
    """Model represents a Payroll Hour entry"""
    period = models.ForeignKey(Period, default=None, on_delete=models.RESTRICT, null=False)
    user = models.ForeignKey(ActiveUser, null = False, blank = False, on_delete=models.RESTRICT)
    date_worked = models.DateField(default=date.today().strftime('%m/%d/%Y'))
    starting_time = models.TimeField(help_text='Starting Time for date_worked')
    ending_time = models.TimeField(help_text='Ending Time + starting_time')  # Must be >starting time
    minutes = models.DurationField(blank = True, null = True, help_text='Set to Timedelta (hours, minutes) ending_time - starting_time')
    vacation_hours = models.BooleanField(default=False, help_text='Are these vacation hours')
    adjustment_mins = models.IntegerField(default=0, help_text='Adjustment to minutes from previous month')
        # Starting_time and ending time are ignored if adjument_hours is non-zero
    adjustment_approved = models.BooleanField(default=False, help_text='Manager must approve the adjustment')
    employee_submitted = models.BooleanField(default=False, help_text='Employee must review the entry and check submit box')
        # All hours for the period must be submitted.

# Moved the following code to forms.py
#def time_multiple_5mins(self, time):
#        hour = time.hour
#        minute = time.minute // 5 * 5
#        time_updated = datetime.strptime(f"{hour}:{minute}:00", "%H:%M:%S").time()
#        return time_updated
    

    def save(self, *args, **kwargs):
# Moved the following code to forms.py
#        self.starting_time = self.time_multiple_5mins(self.starting_time)
#        self.ending_time = self.time_multiple_5mins(self.ending_time)
        self.minutes = timedelta(hours=self.ending_time.hour, minutes=self.ending_time.minute) -\
                                timedelta(hours=self.starting_time.hour, minutes=self.starting_time.minute)
        super().save(*args, **kwargs)
        
    def __str__(self):
        """String representing the PayrollHours table"""
#        return f'Payroll Hours for:{self.user}, Time:{localtime(self.starting_time)}--{localtime(self.ending_time)}'
        return f'Payroll Hours for:{self.user} -- Date:{self.date_worked}  Time:{self.starting_time}--{self.ending_time}'
        
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this PayrollHours."""
        return reverse('payrollhours-update', args=[str(self.id)])    

    # Metadata
    class Meta:
        ordering = ['date_worked','starting_time']
    
