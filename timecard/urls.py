from django.urls import path
from timecard import views
from .views import SignUpView

urlpatterns = [
#    path("", views.home, name="home"),      # comment this guy out when ready to turn on the other page
    path('', views.login_success, name='login-success'),
    path('adminview/', views.adminview, name='adminview'),
    path('logout/', views.auth_logout, name='auth_logout'),
    path("signup/", SignUpView.as_view(), name="signup"),
#    path('period/<int:pk>', views.PeriodDetailView.as_view(), name='period-detail'),
    path('activeuser/', views.ActiveuserListView.as_view(), name='activeuser'),
    path('activeuser/<int:pk>/<int:year>/<int:month>', views.ActiveUser_home, name='activeuser-home'),
#    path('activeuser/<int:pk>', views.ActiveuserDetailView.as_view(), name='activeuser-detail'), # not used
    path('submithours/<int:pk>/<int:pk_per>', views.submit_hours, name='submit-hours'),
    path('nextperiodmo/<int:pk>/<int:year>/<int:month>', views.next_period_mo, name='next-period-mo'),
    path('prevperiodmo/<int:pk>/<int:year>/<int:month>', views.prev_period_mo, name='prev-period-mo'),
    path('nextperiodyr/<int:year>', views.next_period_yr, name='next-period-yr'),
    path('prevperiodyr/<int:year>', views.prev_period_yr, name='prev-period-yr'),
    #path('mypayrollhours/', views.PayrollHoursByUserListView.as_view(), name='my-hours'),
    path('payrollhours/<int:pk>/create/', views.PayrollHoursCreate.as_view(), name='payrollhours-create'),
    path('payrollhours/<int:pk><int:pk_per>/update/', views.PayrollHoursUpdate.as_view(), name='payrollhours-update'),
    path('payrollhours/<int:pk>/delete', views.PayrollHoursDelete.as_view(), name='payrollhours-delete'),
    path('period/<int:year>', views.Period_list, name='period-list'),
    path('period/create', views.PeriodCreate.as_view(), name='period-create'),
    path('period/<int:pk>/update/', views.PeriodUpdate.as_view(), name='period-update'),
    path('period/<int:pk>/delete/', views.PeriodDelete.as_view(), name='period-delete'),
#    path('payrollhours/', views.PayrollHoursDetailView.as_view(), name='payrollhours-detail'),
    #path('payrollhours/<int:pk>', views.login_success, name='login-success'),
    #path('payrollhours/<int:pk>', views.enter_payrollhoursdate, name='enter-payrollhoursdate'),
    ]
