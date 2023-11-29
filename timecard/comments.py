# SourceCode: https://github.com/mdn/django-locallibrary-tutorial

# Production ToDo:
# 1) Change SECRET_KEY in the Settings.py file.  Perhaps read from env variable or file.
#   https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/skeleton_website
# 2) Turn off DEBUG in the settings.py file. same link as above
# 3) Consider a different database
#
# Current Progress on Tutorial: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Authentication
#       Do the priority To Dos first
#       https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Authentication#example_%E2%80%94_listing_the_current_users_books
#
# Docker/VSCode/Django:https://backendclub.com/articles/django-dev-environment-vscode-remote-containers/
#   
# Models: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Models
#   Field Arguments: COMMON FIELD ARGUMENTS (https://docs.djangoproject.com/en/4.2/ref/models/fields/#field-options)
#   Field Types: COMMON FIELD TYPES (https://docs.djangoproject.com/en/4.2/ref/models/fields/#field-types)
#   Metadata: Metadata (https://docs.djangoproject.com/en/4.2/ref/models/options/)
#   Methods: Methods ()
#   Creating and modifying records: ()
#   Searching for records: (https://docs.djangoproject.com/en/4.2/ref/models/querysets/#field-lookups)
#   Phone Number: https://stackoverflow.com/questions/19130942/whats-the-best-way-to-store-a-phone-number-in-django-models
#                   See comment "Noting @Forethinker"
#               Phone Number Lite: https://github.com/VeryApt/django-phone-field#readme
#
#   When changing Models, do the following two commands om the terminal
#       python manage.py makemigrations
#       Python manage.py migrate
# Forms:
#   Formsets: https://docs.djangoproject.com/en/4.2/topics/forms/formsets/
#   Model formsets: https://docs.djangoproject.com/en/4.2/topics/forms/modelforms/#model-formsets
#
# Queries:
#   Django Query Documentation: https://docs.djangoproject.com/en/4.2/topics/db/queries/
#
# To Do:
#   - Add logging capability in the website
#   - Set up the backup and restore capability for the database (add to readme.txt)
#   - Add ADMINS and MANAGERS to be notified of 500 errors (see: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
#
#   - Add html for template in place of the create / update user template
#
#   - Table scrollbar: search bootstrap table limit number of rows with scrollbar
#   - Warning row views (https://www.w3schools.com/Bootstrap/tryit.asp?filename=trybs_ref_tr_warning&stacked=h)
#   - fix the css for border-bottom sometime and take out the code in activeuser_detail.html
#   - Implement reminders based on settings
#       - Ok Hours
#       - Ok Adjustments
#       - Dates for hour submission
#       - Date for entering payroll
#   - Go checkout all the %%%% and form and view for .pk
#       - Clean up code
#   - Remove the <style> from the html files to the css files.
#   - Fix first 2025 Period dates when data from Ministry Works is available.
#
#   - Update settings.py when publishing the website
#       - Can use python manage.py check --deploy to see what is needed to deploy
#       - Run python manage.py collectstatic before application is uploaded to gather all the static files in the right place
#       - LOGIN_REDIRECT_URL = '/timecard/' # This goes to the timecard when logging on. May want a logon landing page
#       - EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'    # Remove when real website with email support is there
#       - See: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
#       - Set up Gunicorn on server for Django pure-Python HTTP server
#       - Set the environment variables:
#           - Go into Python on the command prompt
#           - import os
#           - os.environ['DJANGO_DEBUG'] = 'False'
#           - 'DJANGO_DEBUG' = 'False'
#           - 'DJANGO_SECRET_KEY' = <determine what to set the secret key to>
#           - others ALLOWED_HOSTS, STATIC_ROOT, STATIC_URL, EMAIL_BACKEND, MEDIA_ROOT, MEDIA_URL
#           - Turn on https and then set up CSRF_COOKIE_SECURE = True and SESSION_COOKIE_SECURE = True
#       - Set up the web server in front of django (eg, Apachi) (see checklist url above)
#           - Validate the hosts (similar to ALLOWED_HOSTS) and send out a static error page or ignore requests for incorrect hosts.
#                   (eg, server { listen 80 default_server; return 444;})
#       - Set up database connection parameters ala SECRET_KEY.  Also, ensure they accept connections from your application servers only.
#
# URLs
#   - Home URL: http://127.0.0.1:8000/
#   - Admin URL: http://127.0.0.1:8000/admin/
#   - Timecard: http://127.0.0.1:8000/timecard/
#OLD   - Accounts Login: http://127.0.0.1:8000/accounts/login
#OLD   - Accounts Logout: http://127.0.0.1:8000/accounts/logout
#   - Payroll Hours URLs:
#           Create: http://127.0.0.1:8000/timecard/payrollhours/create
#           Update: http://127.0.0.1:8000/timecard/payrollhours/1/update
#           Delete: http://127.0.0.1:8000/timecard/payrollhours/1/delete
# Old URLs
#   - Shortest: http://127.0.0.1:8000/
#   - Home Page: http://127.0.0.1:8000/index/
#
# SQLite3 commands
# sqlite3 to enter "sqlite>" command prompt
# need a ";" at the end of eqch sql command
# Commands:
#   sqlite3 db.sqlite3           # Startup sqlite with the database being used
#   .help                       # List the sqlite commands
#   .exit                       # Exit sqlite3> command prompt
#   ;                           # Exit SQL input ...>
#   .tables <table_name>        # list the tables in the db
#
#   .backup <backup_file_name>  # Backup the same db referenced in the sqlite3 db.sqlite3 startup command
#                               https://www.sqlite.org/backup.html
#   .restore <backup_file_name> # Restore the same db referenced in the sqlite3 db.sqlite3 startup command
#
#   .output <stdout>.sql        # Output stdout to filename (used before the .dump command)
#   .dump <table_name>          # Dump the table contents as SQL to file set in the .output command previously
#   .import <stdout>.sql <table_name>    # Import data previously .dumped
#
