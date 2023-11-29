import datetime
from datetime import date, datetime, timedelta

from django import forms
from django.forms import ModelForm
from django.forms.widgets import DateInput, TimeInput, HiddenInput

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q, F, ExpressionWrapper, BigIntegerField, Sum

from .models import PayrollHours, ActiveUser, Period

class ActiveUserCreationForm(UserCreationForm):
    
    class Meta:
        model = ActiveUser
        fields = ('username', 'first_name', 'last_name', 'email',
                  'start_date', 'end_date', 'phone_number')

class ActiveUserChangeForm(UserChangeForm):
    class Meta:
        model = ActiveUser
        fields = ('username', 'email', 'start_date', 'end_date', 'phone_number')

def year_month(year, month):
    """Function to determine the Period year and month which is used in both forms.py and views.py"""
    if (not year or year == 0):
        curr_year = date.today().year
        curr_month = date.today().month
        create_update_ok = True
    else:   # Get the year from the parameter and check if the month has a parameter
        curr_year = year
        curr_month = (1 if not month or month == 0 else month)
        create_update_ok = (True if curr_year == date.today().year and curr_month == date.today().month else False)    
        if (curr_month == 1 and date.today().year < 2024):
            create_update_ok = True     # Allow for testing before 2024    
    if (curr_year < 2024):  # default to Jan 2024 if before 2024 - allows for testing
        curr_year = 2024
        curr_month = 1
        create_update_ok = True
        
    return curr_year, curr_month, create_update_ok
      
class PayrollHoursModelForm(ModelForm):
    """Make a new or update Payroll Hours entry"""

    starting_time = forms.TimeField (
        input_formats=('%I:%M %p', '%I %p', '%H:%M', '%H'), 
        widget=TimeInput(format='%I:%M %p'),
        )
    ending_time = forms.TimeField (
        input_formats=('%I:%M %p', '%I %p', '%H:%M', '%H'), 
        widget=TimeInput(format='%I:%M %p'),
        )
    date_worked = forms.DateField (
        widget=DateInput(format='%m/%d/%Y')
    )

    def time_multiple_5mins(self, time):
        """Truncate the minutes to a multiple of 5."""
        hour = time.hour
        minute = time.minute // 5 * 5
        time_updated = datetime.strptime(f"{hour}:{minute}:00", "%H:%M:%S").time()
        return time_updated
    
    def clean_period(self):
        data = self.cleaned_data['period']
        # Period must be a defined period.
        return data
    
    def clean_user(self):
        data = self.cleaned_data['user']
        #User must be currently logged in user.
        return data
    
    def clean_date_worked(self):    # This will only be called if the admin edits the entry
        data = self.cleaned_data['date_worked']
        # Check if a date is in the future.
#%%% Include when productizing        if data > date.today():
#            raise ValidationError(_('Invalid date - date in the future'), code='invalid date')
        # more checking in clean
        if not data:
            raise ValidationError(_('Invalid date = None'), code='invalid date')
        return data
    
    def clean_starting_time(self):
        data = self.cleaned_data['starting_time']
        # Starting time must be a multiple of 5
        if ((data.minute % 5) != 0):
            raise ValidationError(_('Starting time not a multiple of 5 minutes'), code='invalid time')

        #data = self.time_multiple_5mins(data)  # Handled as an error above to let user fix

        return data

    def clean_ending_time(self):
        data = self.cleaned_data['ending_time']
        # Starting time must be a multiple of 5
        if ((data.minute % 5) != 0):
            raise ValidationError(_('Ending time not a multiple of 5 minutes'), code='invalid time')
        # Ending time must be > starting time (This is checked in the clean() form method below)
        #data = self.time_multiple_5mins(data)  # Handled as an error above to let user fix
        
        return data

    def clean_vacation_hours(self):    
        data = self.cleaned_data['vacation_hours']

        return data

    def clean_adjustment_mins(self):    
        data = self.cleaned_data['adjustment_mins']
        # Adjustment minutes must be a multiple of 5
        if ((data % 5) != 0):
            raise ValidationError(_('Adjustment minutes not a multiple of 5 minutes'), code='invalid adjustment')
        # Check for starting time and ending time = 0 if adjustment_mins != 0 below in clean()
        return data

    def clean_adjustment_approved(self):
        data = self.cleaned_data['adjustment_approved']
        return data

    def clean_employee_submitted(self):
        data = self.cleaned_data['employee_submitted']
        return data

    def clean(self):
        """
        clean() form method.  Called after all the field clean-ups are done
        This is where the multiple field checks happen and any data substitution
        """
        cleaned_data = super().clean()
        
        # Ensure the user is set at the front here for use throughout this clean routing
        if (not cleaned_data.get('user')):
            # This is the user, not admin, so get the user information
            ph_entry_user = self.user
            self.cleaned_data['user'] = ph_entry_user   # Setting this up will ensure the user is assigned to PH
        else:   
            # Assuming admin set the user correctly
            ph_entry_user = self.cleaned_data['user']

        date_worked = cleaned_data.get('date_worked')

        # Get the period if set by the Admin or set the period if None
        period = cleaned_data.get('period')     # period is None here.  Can I set to something other?
        if (not period):
            curr_year, curr_month, create_update_ok = year_month(0, 0)

            # %%% This doesn't work if the date isn't in the current period
            query = Period.objects.filter(
                        starting_date = date(curr_year, curr_month, 1)
            )
            if query:
                period = query.get()
                self.cleaned_data['period'] = period
                # See: https://stackoverflow.com/questions/25047615/how-to-fill-a-hidden-field-in-a-django-form
                del self.errors['period']   # This is the error because no period was entered.
            else:
                self.add_error('date_worked', ValidationError(_('Invalid Date Worked - date must be within the defined Periods'), code='invalid date'))

        # If any errors already then don't continue
        if (self.errors):
            return
        
        # Check the Payroll Hours entry time related
        starting_time = cleaned_data.get('starting_time')
        ending_time = cleaned_data.get('ending_time')
        adjustment_mins = cleaned_data.get('adjustment_mins')
        # Check the entry date vs. the period date
        try:
            # Try was added before the if (self.errors) code above.  May no longer be needed as all the fields are valid now
            if (self.instance.pk):
                # If modifying an existing entry, leave off the current entry in the query
                query = PayrollHours.objects.filter(    # Check if time overlaps
                    ~Q(id = self.instance.pk),  # See: https://docs.djangoproject.com/en/3.2/topics/db/queries/#complex-lookups-with-q-objects
                    user = ph_entry_user.pk,
                    period = period,            
                    date_worked = date_worked,
                    ending_time__gte = starting_time,
                    starting_time__lte = ending_time,
                )
            else:
                # If creating a new entry
                query = PayrollHours.objects.filter(    # Check if time overlaps
                    user = ph_entry_user.pk,
                    period = period,            
                    date_worked = date_worked,
                    ending_time__gte = starting_time,
                    starting_time__lte = ending_time,
                )
        except:
            raise ValidationError(_('Query failed; invalid Starting time or Ending time = None'), code='invalid time')
            
        if query:
            # If the query found an overlap
            self.add_error('starting_time', ValidationError(_('Invalid time - time overlaps with other entries'), code='invalid time'))
            self.add_error('ending_time', ValidationError(_('Invalid time - time overlaps with other entries'), code='invalid time'))
            return

        if (not adjustment_mins or (adjustment_mins == 0)):
            # Only check if both fields are valid so far
            if (ending_time <= starting_time):
                ve = ValidationError(_('Invalid time - ending time must be after the starting time'), code='invalid time')
                self.add_error('ending_time', ve)
                self.add_error('starting_time', ve)
        else:
            # Starting time and ending time need to be zero
            if (not(starting_time.hour == starting_time.minute == 0)):
                self.add_error('starting_time', ValidationError(_('Starting time must be 0 if Adjustment hours included'), code='invalid time'))
            if (not(ending_time.hour == ending_time.minute == 0)):
                self.add_error('ending_time', ValidationError(_('Ending time must be 0 if Adjustment hours included'), code='invalid time'))

        if ((date_worked < period.starting_date) or (date_worked > period.reporting_date)):
            self.add_error('date_worked', ValidationError(_('Invalid date - date must be within the period'), code='invalid date'))
        
        # Check that the vacation hours don't exceed the alotment
        if (cleaned_data.get('vacation_hours')):
            if (self.instance.pk):
                # If modifying an existing entry, leave off the current entry in the query
                vac_hours_query = PayrollHours.objects.filter(    # Get total FY vacation hours less this entry
                    ~Q(id = self.instance.pk),  # See: https://docs.djangoproject.com/en/3.2/topics/db/queries/#complex-lookups-with-q-objects
                    user = ph_entry_user.pk,
                    period__fiscal_year = period.fiscal_year,
                    vacation_hours=True,
                )
            else:
                # If creating a new entry, can't query self.instance
                vac_hours_query = PayrollHours.objects.filter(    # Get total FY vacation hours less this entry
                    user = ph_entry_user.pk,
                    period__fiscal_year = period.fiscal_year,
                    vacation_hours=True,
                )

            dur_int = vac_hours_query.aggregate(dur=Sum(ExpressionWrapper(F('minutes'), output_field=BigIntegerField())))
            dur_bigint = (dur_int.get('dur') if dur_int.get('dur') else 0)
            vac_secs_new = timedelta(hours=ending_time.hour, minutes=ending_time.minute) -\
                            timedelta(hours=starting_time.hour, minutes=starting_time.minute)
            vac_new_secs_total = int(vac_secs_new.seconds) + (dur_bigint / 10e5)    # ms -> seconds
            # Get the active user entry so will have the allocated vacation hours
            if ( (float(vac_new_secs_total) / (60*60)) > float(ph_entry_user.vacation_hours)):
                # If exceeded allotment for the year
                vac_hours_new = int(vac_new_secs_total / (60*60))
                vac_minutes_new = int((vac_new_secs_total / (60)) - (vac_hours_new * 60))
                self.add_error('vacation_hours', \
                               ValidationError( \
                                    _('Total vacation hours (%(vac_hr)s:%(vac_min)s) exceed alotment of %(allotted_hr)s hours'), \
                                    code='invalid vacation', \
                                    params = {"vac_hr": str(vac_hours_new), "vac_min": str(vac_minutes_new).zfill(2), "allotted_hr": str(ph_entry_user.vacation_hours)}\
                               )
                )

    class Meta:
        model = PayrollHours
        fields = ['user', 'period', 'date_worked', 'starting_time', 'ending_time', 'vacation_hours', 'adjustment_mins', 'employee_submitted', 'adjustment_approved']

    def __init__(self, *args, **kwargs):
        # Done in clean above
        # see: https://stackoverflow.com/questions/68599329/set-initial-value-in-django-model-form
#%%%        initial = kwargs.get("initial", {})
#%%%        initial = ['period'] = %%%%
                
        #see: https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform        
        if kwargs:
            self.user = kwargs.pop('user')
        
            super().__init__(*args, **kwargs)
        
            if (not(self.user.is_staff or self.user.is_superuser)): # Check the logged in user
                del self.fields['user']
                del self.fields['adjustment_approved']
                # See: https://stackoverflow.com/questions/6862250/change-a-django-form-field-to-a-hidden-field
                # See: https://pyquestions.com/change-a-django-form-field-to-a-hidden-field
                # tried to use del self.fields['period'], but get an error message in the clean above when trying to remove the 'period' error
    #            del self.fields['period']      # Don't want user to see this, but set it up
                self.fields['period'].widget = HiddenInput()
                self.fields['period'].disabled = True
                if (self.user.vacation_hours == 0): # Check selected user vacation hour allotment
                    #%%% Wrong user if superuser is the one.
                    del self.fields['vacation_hours']
        
class PeriodModelForm(ModelForm):
    """Make a new or update a Period entry"""

    submission_time = forms.TimeField (
        input_formats=('%I:%M %p', '%I %p', '%H:%M', '%H'), 
        widget=TimeInput(format='%I:%M %p'),
        )
    pay_time = forms.TimeField (
        input_formats=('%I:%M %p', '%I %p', '%H:%M', '%H'), 
        widget=TimeInput(format='%I:%M %p'),
        )
    starting_date = forms.DateField (
        widget=DateInput(format='%m/%d/%Y')
    )
    reporting_date = forms.DateField (
        widget=DateInput(format='%m/%d/%Y')
    )
    submission_date = forms.DateField (
        widget=DateInput(format='%m/%d/%Y')
    )
    pay_date = forms.DateField (
        widget=DateInput(format='%m/%d/%Y')
    )
    
  
    def clean_period(self):
        data = self.cleaned_data['period']
        # Create by the system, so should be ok
        return data
    
    def clean_period_no(self):
        data = self.cleaned_data['period_no']
        # period_no must be the same as the month; see clean(self) below for the code
        return data
    
    def clean_calendar_year(self):
        data = self.cleaned_data['calendar_year']
        # calendar_year ensure not a duplicate of calendar_year and starting_date.month with another entry; see clean(self) below for the code
        return data

    def clean_fiscal_year(self):
        data = self.cleaned_data['fiscal_year']
        # fiscal_year check that it is correct with the starting_date; see clean(self) below for the code 
        return data

    def clean_starting_date(self):
        data = self.cleaned_data['starting_date']
        # starting_date ensure the year is the same as the calendar year; see clean(self) below for the code
        if (data.day != 1):
            raise ValidationError(_('Starting date must begin on the 1st day of the month'), code='invalid date')
        return data

    def clean_reporting_date(self):    
        data = self.cleaned_data['reporting_date']
        # reporting_date check that the year is the same as the starting_date; see clean(self) below for the code 
        return data

    def clean_submission_date(self):    
        data = self.cleaned_data['submission_date']
        # submission_date check that it is greater than the reporting_date; see clean(self) below for the code
        return data

    def clean_submission_time(self):
        data = self.cleaned_data['submission_time']
        # submission_time will typically be the default time, so don't check
        return data

    def clean_pay_date(self):
        data = self.cleaned_data['pay_date']
        # pay_date_date check that it is greater than the submission_date; see clean(self) below for the code
        return data
    
    def clean_pay_time(self):
        data = self.cleaned_data['pay_time']
        # pay_time will typically be the default time, so don't check
        return data

    def clean(self):
        """
        clean() form method.  Called after all the field clean-ups are done
        This is where the multiple field checks happen and any data substitution
        """
        cleaned_data = super().clean()      # Execute the super version of clean first
        
        # period_no must be the same as the month
        p_period_no = cleaned_data.get('period_no')
        p_starting_date = cleaned_data.get('starting_date')
        if (not p_starting_date):
            return  # Leave if there is already a starting date error
        if (p_period_no != p_starting_date.month):
            raise ValidationError(_('Period no must be the same as the starting date month'), code='invalid period no')

        # calendar_year ensure not a duplicate of calendar_year and month with another entry
        p_calendar_year = cleaned_data.get('calendar_year')
        if (self.instance.pk):
            # If modifying an existing entry, leave off the current entry in the query
            query = Period.objects.filter(    # Check if time overlaps
                ~Q(period = self.instance.pk),  # See: https://docs.djangoproject.com/en/3.2/topics/db/queries/#complex-lookups-with-q-objects
                calendar_year = p_calendar_year,
                starting_date = p_starting_date,
            )
        else:
            # If creating a new entry
            query = PayrollHours.objects.filter(    # Check if time overlaps
                calendar_year = p_calendar_year,
                starting_date = p_starting_date,
            )
        if (query):
            raise ValidationError(_('Calendar year and starting date duplicate entry'), code='duplicate entry')

        # fiscal_year check that it is correct with the starting_date 
        p_fiscal_year = cleaned_data.get('fiscal_year')
        if (
            (p_starting_date.month >= 9) and (p_fiscal_year != "FY"+str(p_calendar_year-1)[-2:])     #%%% Should make the FY start date a variable in database somewhere
            or
            (p_fiscal_year != ("FY"+str(p_calendar_year)[-2:]))
        ):
            raise ValidationError(_('Calendar year or fiscal year incorrect'), code='invalid date')
        
        # starting_date ensure the year is the same as the calendar year
        if (p_starting_date.year != p_calendar_year):
            raise ValidationError(_('Calendar year or fiscal year incorrect'), code='invalid date')

        # reporting_date check that the year is the same as the starting_date
        p_reporting_date = cleaned_data.get('reporting_date')
        if (p_reporting_date.year != p_starting_date.year):
            raise ValidationError(_('Reporting date and starting date need to be in the same year'), code='invalid date')
            
        # submission_date check that it is greater than the reporting_date
        p_submission_date = cleaned_data.get('submission_date')
        if (p_submission_date < p_reporting_date):
            raise ValidationError(_('Submission date must be greater than or equal to submission date'), code='invalid date')
        
        # pay_date_date check that it is greater than the submission_date
        p_pay_date = cleaned_data.get('pay_date')
        if (p_pay_date < p_submission_date): 
            raise ValidationError(_('Pay date must be greater than or equal to submission date'), code='invalid date')

    class Meta:
        model = Period
        fields = ['period', 'period_no', 'calendar_year', 'fiscal_year', 'starting_date', 'reporting_date', 'submission_date',
                'submission_time', 'pay_date', 'pay_time']
