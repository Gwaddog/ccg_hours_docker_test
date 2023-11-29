import datetime
from datetime import date

from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_http_methods   # to enable updating field
from django.db.models import F, ExpressionWrapper, BigIntegerField, IntegerField, Sum
from .models import ActiveUser
from .forms import ActiveUserCreationForm, PayrollHoursModelForm, PeriodModelForm, year_month

from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required()
def auth_logout(request):   # This isn't working, so can delete%%%
    """Logout the user when the browser closes"""
    logout(request)
    return HttpResponseRedirect(reverse('login'))

class SignUpView(PermissionRequiredMixin, CreateView):
    permission_required = [ActiveUser.is_staff, ActiveUser.is_superuser]
    
    form_class = ActiveUserCreationForm
    success_url = reverse_lazy('login-success')
    template_name = 'timecard/signup.html'

def home(request):
    return HttpResponse("Hello, Django!")

from .models import ActiveUser, Period, PayrollHours

@permission_required([ActiveUser.is_staff, ActiveUser.is_superuser])
def adminview(request):
    """View function for home page of site for the admin."""
    num_users = ActiveUser.objects.count()     # 'all()' is implied by default
    num_hour_entries = PayrollHours.objects.all().count()
    num_periods = Period.objects.all().count()
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context = {
        'num_users': num_users,
        'num_periods': num_periods,
        'num_hour_entries': num_hour_entries,
        'num_visits': num_visits,
    }
    
    return render(request, 'timecard/adminview.html', context=context)

@login_required()
def login_success(request):
    """
    Redirect to either the Index or Payroll Hours based on user permissions
    """
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseRedirect(reverse('adminview'))
    else:
        user = request.user
        return HttpResponseRedirect(reverse_lazy('activeuser-home', args=[user.pk, 0, 0]))

@login_required()
def Period_list(request, year=None):
    """Period List for a given year"""
    model = Period
    
    display_year = year if year >= 2024 else date.today().year
    if (display_year < 2024):
        display_year = 2024
    prev_year = display_year-1
    next_year = display_year+1

    queryset = Period.objects.filter(calendar_year=display_year).order_by('starting_date',)
    year_list = sorted(set(Period.objects.values_list('calendar_year', flat=True)))[-5:]
    prev_year_ok = (True if prev_year in year_list else False)
    next_year_ok = (True if next_year in year_list else False)
    
    context = {
        'display_year': display_year,
        'period_list': queryset,
        'year_list': year_list,
        'prev_year_ok': prev_year_ok,
        'next_year_ok': next_year_ok,
        'prev_year': prev_year,
        'next_year': next_year,
    }
    return render(request, 'timecard/period_list.html', context=context)
      
@login_required()
def next_period_yr(request, year=None):
    """Display next period list by year"""
    model = Period
   
    return HttpResponseRedirect(reverse_lazy('period-list', args=[year]))

@login_required()
def prev_period_yr(request, pk=None, year=None, month=None):
    """Display previous period list by year"""
    model = Period
   
    return HttpResponseRedirect(reverse_lazy('period-list', args=[year]))

from django.views import generic

class ActiveuserListView(PermissionRequiredMixin, generic.ListView):
    permission_required = [ActiveUser.is_staff, ActiveUser.is_superuser]

    model = ActiveUser
    
    context_object_name = 'activeuser_list'
    
    template_name = 'activeuser_list.html'
    
@login_required()
def ActiveUser_home(request, pk=None, year=None, month=None):
    """Active User Main Home Screen with Payroll Hours as well"""
    model = ActiveUser
    
    if (pk):
        activeuser = ActiveUser.objects.filter(pk=pk).get()

    curr_year, curr_month, create_update_ok = year_month(year, month)
        
    curr_period = Period.objects.filter(starting_date = date(curr_year, curr_month, 1)).get()
    value = curr_period.pk
    period_list = Period.objects.filter(calendar_year = curr_year)
    total_hours = 0
    total_minutes= 0
    if curr_period:
        # Get the Total Hours worked in the period.
        # See: https://docs.djangoproject.com/en/4.2/topics/db/aggregation/
        # and: https://stackoverflow.com/questions/33237819/aggregate-in-django-with-duration-field
        # and: https://stackoverflow.com/questions/32305800/why-does-django-queryset-say-typeerror-complex-aggregates-require-an-alias
        payrollhours_per_period = PayrollHours.objects.filter(user = activeuser, period__starting_date = date(curr_year, curr_month, 1))
        dur_int = payrollhours_per_period.aggregate(dur=Sum(ExpressionWrapper(F('minutes'), output_field=BigIntegerField())))
        dur_bigint = (dur_int.get('dur') if dur_int.get('dur') else 0)
        total_hours = int(dur_bigint / (10e5*60*60))
        total_minutes = int((dur_bigint / (10e5*60)) - (total_hours * 60))
        
        # Get the Total Vacation hours taken in the period.
        vac_hours_query = PayrollHours.objects.filter(user = activeuser, period__fiscal_year = curr_period.fiscal_year, vacation_hours=True)
        dur_int = vac_hours_query.aggregate(dur=Sum(ExpressionWrapper(F('minutes'), output_field=BigIntegerField())))
        dur_bigint = (dur_int.get('dur') if dur_int.get('dur') else 0)
        vac_hours_taken = int(dur_bigint / (10e5*60*60))
        vac_minutes_taken = int((dur_bigint / (10e5*60)) - (vac_hours_taken * 60))
        
        # Get the Total Adjustment hours taken in the period.
        payrollhours_per_period = PayrollHours.objects.filter(user = activeuser, period__starting_date = date(curr_year, curr_month, 1))
        dur_int = payrollhours_per_period.aggregate(dur=Sum(ExpressionWrapper(F('adjustment_mins'), output_field=IntegerField())))
        total_adjustment_mins = (dur_int.get('dur') if dur_int.get('dur') else 0)
        
        # Determine if all of the entries for the month are submitted
        all_sub = payrollhours_per_period.aggregate(Sum("employee_submitted"))
        if ('employee_submitted__sum' in all_sub and all_sub['employee_submitted__sum']):
            sub_yes = int(all_sub.get('employee_submitted__sum'))
            all_hours_submitted = (True if sub_yes == payrollhours_per_period.count() else False)
        else:
            all_hours_submitted = True  # No entries means don't enable the Submit All Hours button

    # See: https://stackoverflow.com/questions/4424435/how-to-convert-a-django-queryset-to-a-list
    #    ... and: https://docs.djangoproject.com/en/4.2/ref/models/querysets/
    # note user is in the filter due to the get_queryset overload below
    # sort the list and get the limit to last 5
    year_list = sorted(set(Period.objects.values_list('calendar_year', flat=True)))[-5:]
    prev_period_ok = (False if curr_year == year_list[0] and curr_month == 1 else True)
    next_period_ok = (False if curr_year == year_list[-1] and curr_month == 12 else True)

    context = {
        'activeuser': activeuser,
        'curr_year': curr_year,
        'curr_month': curr_month,
        'curr_period': curr_period,
        'payrollhours_per_period': payrollhours_per_period,
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'year_list': year_list,
        'period_list': period_list,
        'all_hours_submitted':all_hours_submitted,
        'prev_period_ok': prev_period_ok,
        'next_period_ok': next_period_ok,
        'create_update_ok': create_update_ok,
        'vac_user_has': activeuser.vacation_hours,
        'vac_hours_total': activeuser.vacation_hours,
        'vac_hours_taken': vac_hours_taken,
        'vac_minutes_taken': vac_minutes_taken,
        'total_adjustment_mins': total_adjustment_mins,
    }
# "minutes" bigint NULL
    return render(request, 'timecard/activeuser_detail.html', context=context)

    # See https://docs.djangoproject.com/en/4.2/topics/class-based-views/generic-display/
#    def get_queryset(self, *args, **kwargs):
#        return (
#            PayrollHours.objects.filter(user=self.request.user)
#            .filter(status_exact='o')
#            .order_by('date_worked', 'starting_time', 'ending_time')
#        )

# See: https://stackoverflow.com/questions/65452345/how-to-change-status-by-a-link-or-a-button-in-django
@require_http_methods(['POST'])
@login_required()
def submit_hours(request, pk=None, pk_per=None, ):
    """Employee submits all the hours for a period"""
    model = ActiveUser
    
    if (pk):
        activeuser = ActiveUser.objects.filter(pk=pk).get()

    curr_period = Period.objects.filter(pk=pk_per).get()
    if pk and curr_period:
        PayrollHours.objects.filter(user = activeuser, period = curr_period.pk).update(employee_submitted=True)
        
    return HttpResponseRedirect(reverse_lazy('activeuser-home', args=[pk, 0, 0]))
      
@login_required()
def next_period_mo(request, pk=None, year=None, month=None):
    """Display next period"""
    model = ActiveUser

    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    
    return HttpResponseRedirect(reverse_lazy('activeuser-home', args=[pk, year, month]))

@login_required()
def prev_period_mo(request, pk=None, year=None, month=None):
    """Display previous period"""
    model = ActiveUser

    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    
    return HttpResponseRedirect(reverse_lazy('activeuser-home', args=[pk, year, month]))

# Form views
from django.forms import ModelForm, Form

# Generic Form Views for Payroll Hours
from django.views.generic.edit import CreateView, UpdateView, DeleteView

class PayrollHoursCreate(LoginRequiredMixin, CreateView):
    """View to create a Payroll Hours entry"""
    model = PayrollHours
    form_class = PayrollHoursModelForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curr_period'] = Period.objects.get(period=self.kwargs['pk'])
       
        return context
    
    # https://stackoverflow.com/questions/49455797/how-to-use-django-forms-get-initial-for-field-method
    # This didn't work %%%
    def get_initial_for_field(self, field, field_name):
        if field_name == 'period':
            return self.kwargs['pk']
        return super(PayrollHoursCreate, self).get_initial_for_field(field, field_name)
        
    # See: https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform
    def get_form_kwargs(self):
        """
        This update to get_form_kwargs, runs the function for this class and base classes, then adds the user to the kwargs
        The user is then popped off in the form before the __init__ is run.
        """
        kwargs = super(PayrollHoursCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        
        return kwargs
   
    def form_valid(self, form):
        # Add logged-in user as PayrollHours user
        # See:https://stackoverflow.com/questions/2414473/how-to-assign-currently-logged-in-user-as-default-value-for-a-model-field
        # Not needed anymore.  Did this in the CreateView form
        #if (not(self.request.user.is_staff or self.request.user.is_superuser)):
        #    form.instance.user = self.request.user
            
#        if not form.instance.period:
#            form.instance.period = self.kwargs['pk']
            #self.get_context_data('curr_period')

        # See: https://stackoverflow.com/questions/48595913/how-to-access-form-data-in-formview-get-success-url
        self.form = form
        
        return super(PayrollHoursCreate, self).form_valid(form)
   
    def get_success_url(self):
        # See: https://stackoverflow.com/questions/48595913/how-to-access-form-data-in-formview-get-success-url
        user = self.form.instance.user
        return reverse_lazy('activeuser-home', args=[user.pk, 0, 0])

        # user = self.request.user Not needed anymore
        #return reverse_lazy('activeuser-home', args=[user.pk, 0, 0])
    
#    def __init__(self, **kwargs):
#        """Add code to the init to set up the period default"""
#        super().__init__(**kwargs)
        
        # See: https://stackoverflow.com/questions/604266/django-set-default-form-values
#        kwargs = super(PayrollHoursCreate, self).get_form_kwargs()
#%%%        self.initial['period'] = kwargs['pk']   # len = 0
      
class PayrollHoursUpdate(LoginRequiredMixin, UpdateView):
    model = PayrollHours
    form_class = PayrollHoursModelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curr_period'] = Period.objects.get(period=self.kwargs['pk_per'])
       
        return context

    # See: https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform
    def get_form_kwargs(self):
       kwargs = super(PayrollHoursUpdate, self).get_form_kwargs()
       kwargs.update({'user': self.request.user})
       return kwargs

    def form_valid(self, form):
        # See: PayrollHoursCreate above for why
        self.form = form
        
        return super(PayrollHoursUpdate, self).form_valid(form)
    
    def get_success_url(self):
        # See: PayrollHoursCreate above for why
        user = self.form.instance.user
        return reverse_lazy('activeuser-home', args=[user.pk, 0, 0])

#    # See: https://stackoverflow.com/questions/42065922/django-dynamic-success-url-in-updateview  
#    def get_success_url(self):
#        user = self.request.user
#        return reverse_lazy('activeuser-home', args=[user.pk, 0, 0])
    
class PayrollHoursDelete(LoginRequiredMixin, DeleteView):
    model = PayrollHours
    fields = ['user', 'period', 'date_worked', 'starting_time', 'ending_time', 'vacation_hours', 'adjustment_mins', 'employee_submitted']
    
    def get_success_url(self):  # This isn't getting called for some reason
        return reverse_lazy('activeuser-home', args=[self.object.user.pk, 0, 0])
    
    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(reverse_lazy('activeuser-home', args=[self.object.user.pk, 0, 0]))
        except Exception as e:
            return HttpResponseRedirect(
                reverse_lazy("payrollhours-delete", kwargs={"pk": self.object.pk})
            )
    

# Generic Views for creating / deleting a period    
class PeriodCreate(PermissionRequiredMixin, CreateView):
    """View to create a Period entry"""
    model = Period
    form_class = PeriodModelForm    # Use a Model Form to verify the fields
    #initial = {'date_of_death': '11/11/2023'}
    permission_required = [ActiveUser.is_staff, ActiveUser.is_superuser]
    
    def get_success_url(self):
        return reverse_lazy('period-list', args = [self.object.calendar_year])

    
class PeriodUpdate(PermissionRequiredMixin, UpdateView):
    """Update a Period entry"""
    model = Period
    form_class = PeriodModelForm    # Use a Model Form to verify the fields
    permission_required = [ActiveUser.is_staff, ActiveUser.is_superuser]
    
    def get_success_url(self):
        scheck = self.object.calendar_year
        return reverse_lazy('period-list', args=[str(self.object.calendar_year)])

class PeriodDelete(PermissionRequiredMixin, DeleteView):
    """Delete a Period entry"""
    model = Period
    fields = ['period', 'period_no', 'calendar_year', 'fiscal_year', 'starting_date', 'reporting_date', 'submission_date',
              'submission_time', 'pay_date', 'pay_time']
    permission_required = [ActiveUser.is_staff, ActiveUser.is_superuser]

    def get_success_url(self):  # This isn't getting called for some reason, likely because of the form_valid below
        return reverse_lazy('period-list', args = [self.object.pk])

    # See: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Forms
    def form_valid(self, form):
        try:
            self.object.delete()
            url =reverse_lazy('period-list', args = [self.object.calendar_year])
            return HttpResponseRedirect(reverse_lazy('period-list', args = [self.object.calendar_year]))
        except Exception as e:
            return HttpResponseRedirect(
                reverse_lazy("period-delete", args=[self.object.calendar_year])
            )
        