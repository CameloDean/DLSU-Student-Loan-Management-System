from account.models import Student
from student.models import Payment, Loan
from oas.models import Info
from django.shortcuts import render, redirect
from student.forms import PaymentForm, LoanForm
from django.utils.dateparse import parse_date
from django.contrib.auth import authenticate
from calendar import monthrange
from datetime import datetime, timedelta
import calendar
import datetime
from django.http import HttpResponse


# Check if user is authenticated
def check_user(request):
    if not request.user.is_authenticated:
        return redirect('account:login_url')
    else:
        return None


# Get current term information
def get_curr_info():
    try:
        today = datetime.date.today()
        curr_info = Info.objects.get(start_of_term__lte=today, end_of_term__gte=today)
    except Info.DoesNotExist:
        curr_info = None
    return curr_info


# Student Homepage
def index_view(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        s = Student.objects.get(user=request.user)
        return render(request, 'student/index.html', {'id': s.id_number, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# View User Profile
def user_profile(request, pk):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        student = Student.objects.get(pk=pk)
        array = ["", student.first_name, student.last_name, student.id_number, student.college, student.level,
                 student.course, student.cellphone_number, student.user.email]
        if request.method == 'POST':
            college = request.POST.get('College')
            course = request.POST.get('Course')
            cellphone_number = request.POST.get('Cellphone Number')
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            user = authenticate(username=student.user.username, password=current_password)
            if user:
                user = student.user
                student.college = college
                student.course = course
                student.cellphone_number = cellphone_number
                if new_password1 != "" and new_password1 == new_password2:
                    user.set_password(new_password1)
                elif new_password1 != new_password2:
                    array[0] = " Password Mismatch "
                    s = Student.objects.get(user=request.user)
                    return render(request, 'student/profile.html', {'array': array, 'curr_info': curr_info, 'pk': s.pk})
                user.save()
                student.save()
                return redirect('student:profile_url', pk=student.id_number)
            else:
                array[0] = " Wrong Password "
                s = Student.objects.get(user=request.user)
                return render(request, 'student/profile.html', {'array': array, 'curr_info': curr_info, 'pk': s.pk})
        else:
            s = Student.objects.get(user=request.user)
            return render(request, 'student/profile.html', {'array': array, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# View payments already made by the student
def payments_list(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        s = Student.objects.get(user=request.user)
        object_list = Payment.objects.filter(id_number=s)
        return render(request, 'student/view_payments.html', {'object_list': object_list, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# View payment details
def payment_detail(request, pk):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        s = Student.objects.get(user=request.user)
        payment = Payment.objects.get(pk=pk)
        return render(request, 'student/view_payment_details.html', {'payment': payment, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# Create a payment
def payment_create(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        try:
            # Check if student already has a loan
            s = Student.objects.get(user=request.user)
            Loan.objects.get(id_number=s)

            if request.method == 'POST':
                form = PaymentForm(request.POST)
                if form.is_valid():
                    temp = form.save(commit=False)
                    temp.id_number = Student.objects.get(user=request.user)
                    temp.save()
                    return redirect('student:view_payment_details', pk=temp.pk)
                else:
                    error = "Amount is not valid!"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            # Return blank form
            else:
                form = PaymentForm(None)
            return render(request, 'student/payment_form.html', {'form': form, 'curr_info': curr_info, 'pk': s.pk})
        except Loan.DoesNotExist:
            error = "You have not applied for a Loan yet!"
            s = Student.objects.get(user=request.user)
            return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# View status of application
def view_status(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        s = Student.objects.get(user=request.user)
        try:
            l = Loan.objects.get(id_number=s)
            return render(request, 'student/view_status.html', {'loan': l, 'curr_info': curr_info, 'pk': s.pk})
        except Loan.DoesNotExist:
            error = "You have not applied for a Loan yet!"
            return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# Create a loan application
def loan_create(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        # Check if student is logged in
        s = Student.objects.get(user=request.user)
        try:
            # Check if student has a loan for this term already
            l = Loan.objects.get(id_number=s)
            if (l.balance == 0) & (not l.status == 'In Process'):
                # Check if Loan application is open
                today = datetime.date.today()
                try:
                    current_term = Info.objects.get(start_of_term__lte=today, end_of_term__gte=today)
                    if (today < current_term.application_end) & (today > current_term.application_start):
                        if request.method == 'POST':
                            form = LoanForm(request.POST)
                            if form.is_valid():
                                form.save(commit=False)
                                temp = form
                                temp.id_number = Student.objects.get(user=request.user)
                                temp.save()
                                return redirect('student:view_status')
                    else:
                        error = "You are not allowed to apply for a loan at this point in time."
                        return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
                except Info.DoesNotExist:
                    error = "Current term applications have not been set"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            else:
                error = "You already have a loan"
                return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})

        except Loan.DoesNotExist:
            if request.method == 'POST':
                form = LoanForm(request.POST)
                if form.is_valid():
                    temp = form.save(commit=False)
                    temp.id_number = Student.objects.get(user=request.user)
                    temp.save()
                    return redirect('student:view_status')
                else:
                    error = "Amount is not valid!"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            else:
                form = LoanForm(None)
            return render(request, 'student/loan_form.html', {'form': form, 'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking


# Loan calculator
def loan_calc(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        if request.method == 'POST':
            s = Student.objects.get(user=request.user)

            # Get end date from input
            amount = float(request.POST.get('amount_field', None))
            if amount <= 0:
                error = "Amount must be greater than 0!"
                return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})

            price = 0
            date_str1 = request.POST.get('sdate')
            start_date = parse_date(date_str1)
            date_str2 = request.POST.get('edate')
            end_date = parse_date(date_str2)

            # Error if start date is after end date
            try:
                if start_date > end_date:
                    error = "Start date cannot be before the end date!"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            except TypeError:
                error = "You have not entered a valid date range!"
                return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})

            # Get month difference + populate month and year table
            length = 0
            while True:
                mdays = monthrange(start_date.year, start_date.month)[1]
                try:
                    start_date += timedelta(days=mdays)
                except OverflowError:
                    error = "Overflow"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})

                if start_date <= end_date:
                    length += 1
                else:
                    break

            # Calculations here
            for i in range(0, length):
                if i > 2:
                    amount += amount * 0.01
                price = amount

            return render(request, 'student/calculate_result.html', {'data': price, 'curr_info': curr_info, 'pk': s.pk})

        else:
            s = Student.objects.get(user=request.user)
            return render(request, 'student/calculator_form.html', {'curr_info': curr_info, 'pk': s.pk})


# Loan projection view
def loan_projection(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()
        s = Student.objects.get(user=request.user)
        if request.method == 'POST':
            loan = Loan.objects.get(id_number=s)
            if Info.objects.filter(term_AY=loan.term_AY).count() > 0:
                info = Info.objects.get(term_AY=loan.term_AY)
            else:
                error = "Loan not found"
                return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            start_date = info.deadline_of_payment

            # Get end date from input
            date_str = request.POST.get('edate_field')
            end_date = parse_date(date_str)

            try:
                if start_date > end_date:
                    error = "Start date cannot be before the end date!"
                    return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})
            except TypeError:
                error = "You have not entered a valid date range!"
                return render(request, 'student/error.html', {'error': error, 'curr_info': curr_info, 'pk': s.pk})

            monthlist = []
            yearlist = []

            # get month difference + populate month and year table
            length = 0
            while True:
                mdays = monthrange(start_date.year, start_date.month)[1]
                start_date += timedelta(days=mdays)
                if start_date <= end_date:
                    monthlist.append(calendar.month_name[start_date.month])
                    yearlist.append(start_date.year)
                    length += 1
                else:
                    break

            # Declare empty array
            price = [0] * length

            # Get balance
            current = loan.balance

            # Calculations here
            for i in range(0, length):
                if i > 2:
                    current += current * 0.01
                price[i] = current
                zipped_data = zip(monthlist, yearlist, price)

            return render(request, 'student/loan_projection.html', {'data': zipped_data, 'curr_info': curr_info, 'pk': s.pk})
        else:
            return render(request, 'student/loan_projection_form.html', {'curr_info': curr_info, 'pk': s.pk})
    else:
        return checking
