from django.shortcuts import render, redirect
from account.models import Student
from student.models import Loan, Payment
from .models import Info
from .forms import PaymentForm, InfoForm
import datetime
import csv
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from smtplib import SMTPException


def check_user(request):
    if not request.user.is_authenticated:
        return redirect('account:login_url')
    elif Student.objects.filter(user=request.user).count() != 0:
        return redirect('student:index')
    else:
        return None


def get_curr_info():
    try:
        today = datetime.date.today()
        curr_info = Info.objects.get(start_of_term__lte=today, end_of_term__gte=today)
    except Info.DoesNotExist:
        curr_info = None
    return curr_info


def index(request):
    checking = check_user(request)
    # if user is OAS
    if checking is None:
        today = datetime.date.today()

        if Info.objects.filter(start_of_term__gte=today).count() == 0:
            return redirect('oas:create_info')

        # check all loans if addition of 1% is needed
        loans = Loan.objects.filter(balance__gte=0)
        for x in loans:
            # check if today is later than maturity date of that loan
            if today > x.maturity_date:
                x.balance *= 1.01
                # offset the maturity date by one month
                x.maturity_date = x.maturity_date + relativedelta(months=+1)
                x.save()

        # check if emails need to be sent
        # get current term
        try:
            curr_term = Info.objects.get(start_of_term__lte=today, deadline_of_payment__gte=today)
        except Info.DoesNotExist:
            curr_term = None
        except Info.MultipleObjectsReturned:
            curr_term = None

        # if today is within the current term
        if curr_term:
            # all loaners have not yet been notified AND today is a week before deadline
            if (curr_term.all_notified is False) & (today == curr_term.deadline_of_payment + relativedelta(weeks=-1)):
                #   get all active loans for this term which have not been notified yet
                loans = Loan.objects.filter(term_AY=curr_term, balance__gt=0, notif_flag=False)
                for loan in loans:
                    # get the loaner
                    student = Student.objects.get(loan__pk=loan.pk)

                    # send a notification email
                    message = render_to_string('oas/oas_email.html', {
                        'student': student,
                        'message': 'Please pay before ' + curr_term.deadline_of_payment.strftime('%m/%d/%Y')
                                   + ' to avoid incurring extra charges. Thank you!',
                    })
                    mail_subject = 'OAS Student Loan Reminder'
                    to_email = student.user.email
                    email = EmailMessage(mail_subject, message, to=[to_email])
                    try:
                        email.send()
                    except SMTPException:
                        return HttpResponse('There\'s a problem in your connection or our server might be down')
                    except TimeoutError:
                        return HttpResponse('Timeout Error. Check your internet connection')

                    loan.notif_flag = True
                    loan.save()

                unnotified_loans = Loan.objects.filter(notif_flag=False)
                all_loans = Loan.objects.all()

                # if there are existing unnotified loans
                # (put in all loans so that if there are no loans, this will not execute)
                if (all_loans is not None) & (unnotified_loans is not None):
                    # set notif flag in current term to True
                    curr_term.all_notified = True
                    curr_term.save()

        return redirect('oas:view_summary')
    else:
        return checking


def view_applicants(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        applicant_list = Student.objects.filter(loan__balance=0).order_by('id_number')
        loan_list = []
        for applicant in applicant_list:
            loan_list.append(Loan.objects.get(id_number=applicant))
        zipped_data = zip(applicant_list, loan_list)
        return render(request, 'oas/applicants.html', {'data': zipped_data, 'curr_info': curr_info})
    else:
        return checking


def view_applicant_detail(request, idnum):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        notif = None
        student = Student.objects.get(id_number=idnum)
        loan = Loan.objects.get(id_number=student)
        return render(request, 'oas/app_details.html', {'student': student, 'loan': loan, 'notif': notif,
                                                        'curr_info': curr_info})
    else:
        return checking


def approve_loan(request, idnum):
    checking = check_user(request)
    if checking is None:
        # get current term/AY
        today = datetime.date.today()
        student = Student.objects.get(id_number=idnum)
        loan = Loan.objects.get(id_number=student)

        try:
            curr_info = Info.objects.get(start_of_term__lte=today, end_of_term__gte=today)

            # check if they'd go overbudget
            if curr_info.budget - curr_info.loan_total - loan.amount < 0:
                notif = 'If you approve this loan, you\'ll go over the term budget!\nBudget left: '\
                        + str(curr_info.budget-curr_info.loan_total)

                return render(request, 'oas/app_details.html', {'student': student, 'loan': loan, 'notif': notif,
                                                                'curr_info': curr_info})
            else:
                loan.status = 'Approved'
                loan.balance = loan.amount
                loan.term_AY = curr_info.term_AY
                # set the maturity date of loan to deadline of payments of current term
                loan.maturity_date = curr_info.deadline_of_payment + relativedelta(months=+3)
                loan.save()

                curr_info.loan_total += loan.amount
                curr_info.save()

                notif = 'Loan application has been approved!'

                # send a notification email
                message = render_to_string('oas/oas_email.html', {
                    'student': student,
                    'message': 'We are pleased to inform you that your loan application has been approved! '
                               'Please log in to your account to view the details.'
                })
                mail_subject = 'OAS Student Loan Application'
                to_email = student.user.email
                email = EmailMessage(mail_subject, message, to=[to_email])
                try:
                    email.send()
                except SMTPException:
                    return HttpResponse('There\'s a problem in your connection or our server might be down')
                except TimeoutError:
                    return HttpResponse('Timeout Error. Check your internet connection')

                return render(request, 'oas/app_details.html', {'student': student, 'loan': loan, 'notif': notif,
                                                                'curr_info': curr_info})

        except Info.DoesNotExist:
            notif = 'You cannot approve/reject loans during this time.'
            return render(request, 'oas/app_details.html', {'student': student, 'loan': loan, 'notif': notif})
    else:
        return checking


def reject_loan(request, idnum):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        if request.method == 'POST':
            if request.POST.get('choice') == 'Yes':
                student = Student.objects.get(pk=idnum)
                loan = Loan.objects.get(id_number=student)
                loan.status = 'Rejected'
                loan.save()
                notif = 'Loan application has been rejected.'

                # send a notification email
                message = render_to_string('oas/oas_email.html', {
                    'student': student,
                    'message': 'We are sorry to inform you that your loan application has been rejected.'
                               'Please log in to your account to reapply.'
                })
                mail_subject = 'OAS Student Loan Application'
                to_email = student.user.email
                email = EmailMessage(mail_subject, message, to=[to_email])
                try:
                    email.send()
                except SMTPException:
                    return HttpResponse('There\'s a problem in your connection or our server might be down')
                except TimeoutError:
                    return HttpResponse('Timeout Error. Check your internet connection')

                return render(request, 'oas/app_details.html', {'student': student, 'loan': loan, 'notif': notif,
                                                                'curr_info': curr_info})
            else:
                return redirect('oas:view_applicant_detail', idnum=idnum)
        else:
            student = Student.objects.get(pk=idnum)
            loan = Loan.objects.get(id_number=student)
            return render(request, 'oas/reject_loan.html', {'student': student, 'loan': loan, 'curr_info': curr_info})
    else:
        return checking


def view_loaners(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        loaners = Student.objects.filter(loan__status="Approved").order_by('id_number')
        loan_list = []
        for loaner in loaners:
            loan_list.append(Loan.objects.get(id_number=loaner))
        zipped_data = zip(loaners, loan_list)
        return render(request, 'oas/loaners.html', {'data': zipped_data, 'curr_info': curr_info})
    else:
        return checking


def view_loaner_detail(request, idnum):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        student = Student.objects.get(id_number=idnum)
        loan = Loan.objects.get(id_number=student)
        payments = Payment.objects.filter(id_number=student)
        return render(request, 'oas/loaner_details.html', {'student': student, 'loan': loan, 'payments': payments,
                                                           'curr_info': curr_info})

    return checking


def view_payments_pending(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        payments = Payment.objects.filter(isApproved=False).order_by('date')
        show_all = False
        return render(request, 'oas/payments.html', {'payments': payments, 'show_all': show_all, 'curr_info': curr_info})
    else:
        return checking


def view_payments_all(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        payments = Payment.objects.all().order_by('date')
        show_all = True
        return render(request, 'oas/payments.html', {'payments': payments, 'show_all': show_all, 'curr_info': curr_info})
    else:
        return checking


def view_payment_detail(request, pk):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        payment = Payment.objects.get(pk=pk)
        student = Student.objects.get(id_number=payment.id_number.id_number)
        loan = Loan.objects.get(id_number=student)
        return render(request, 'oas/payment_details.html',
                      {'student': student, 'payment': payment, 'loan': loan, 'curr_info': curr_info})
    else:
        return checking


def approve_payment(request, pk):
    checking = check_user(request)
    if checking is None:
        payment = Payment.objects.get(pk=pk)
        payment.isApproved = True
        payment.save()
        student = Student.objects.get(id_number=payment.id_number.id_number)
        loan = Loan.objects.get(id_number=student)
        loan.balance -= payment.amount
        if loan.balance < 0:
            loan.balance = 0
        loan.save()

        # send a notification email
        message = render_to_string('oas/oas_email.html', {
            'student': student,
            'message': 'Your payment with the following details has been approved. '
                       '\nOR Number: ' + payment.orNum
                       + '\nAmount: ' + str(payment.amount)
                       + '\nDate: ' + str(payment.date)
                       + '\n\nYour remaining balance is now: ' + str(loan.balance)
                       + '\nPlease log in to your account to view the details.'
        })
        mail_subject = 'Student Loan Payment'
        to_email = student.user.email
        email = EmailMessage(mail_subject, message, to=[to_email])
        try:
            email.send()
        except SMTPException:
            return HttpResponse('There\'s a problem in your connection or our server might be down')
        except TimeoutError:
            return HttpResponse('Timeout Error. Check your internet connection')

        return redirect('oas:view_payment_detail', pk=pk)
    else:
        return checking


def reject_payment(request, pk):
    checking = check_user(request)
    if checking is None:
        payment = Payment.objects.get(pk=pk)
        student = payment.id_number

        # send a notification email
        message = render_to_string('oas/oas_email.html', {
            'student': student,
            'message': 'Your payment with the following details has been rejected. '
                       '\nOR Number: ' + payment.orNum
                       + '\nAmount: ' + str(payment.amount)
                       + '\nDate: ' + str(payment.date)
                       + '\nPlease log in to your account to view the details.'
        })
        mail_subject = 'Student Loan Payment'
        to_email = student.user.email
        email = EmailMessage(mail_subject, message, to=[to_email])
        try:
            email.send()
        except SMTPException:
            return HttpResponse('There\'s a problem in your connection or our server might be down')
        except TimeoutError:
            return HttpResponse('Timeout Error. Check your internet connection')

        Payment.objects.get(pk=pk).delete()

        return redirect('oas:all_payments')
    else:
        return checking


def edit_payment(request, pk):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        payment = Payment.objects.get(pk=pk)
        student = Student.objects.get(id_number=payment.id_number.id_number)
        loan = Loan.objects.get(id_number=student)

        if request.method == 'POST':
            form = PaymentForm(request.POST)
            if form.is_valid():
                paymentf = form.save(commit=False)
                paymentf.id_number = student
                paymentf.isApproved = False
                temp = payment.pk
                payment.delete()
                paymentf.pk = temp
                paymentf.save()

                # send a notification email
                message = render_to_string('oas/oas_email.html', {
                    'student': student,
                    'message': 'Your payment has been edited into the following information. '
                               + '\nOR Number: ' + payment.orNum
                               + '\nAmount: ' + str(payment.amount)
                               + '\nDate: ' + str(payment.date)
                               + '\nPlease log in to your account to view the details.'
                })
                mail_subject = 'Student Loan Payment'
                to_email = student.user.email
                email = EmailMessage(mail_subject, message, to=[to_email])
                try:
                    email.send()
                except SMTPException:
                    return HttpResponse('There\'s a problem in your connection or our server might be down')
                except TimeoutError:
                    return HttpResponse('Timeout Error. Check your internet connection')

                return redirect('oas:view_payment_detail', pk=paymentf.pk)
        else:
            form = PaymentForm(None, initial={'orNum': payment.orNum, 'amount': payment.amount, 'date': payment.date})

        return render(request, 'oas/payment_edit.html',
                      {'form': form, 'student': student, 'payment': payment, 'loan': loan, 'curr_info': curr_info})
    else:
        return checking


def view_summary(request):
    checking = check_user(request)
    if checking is None:
        # find out current term
        today = datetime.date.today()
        try:
            curr_info = Info.objects.get(start_of_term__lte=today, end_of_term__gte=today)
            # get loaners for this term
            loaners = Student.objects.filter(loan__status='Approved', loan__term_AY=curr_info.term_AY)
            # get applicants for this term
            applicants = Student.objects.filter(loan__status='In Process')
            # calculate budget left
            budget = curr_info.budget - curr_info.loan_total

            context = {'curr_info': curr_info, 'budget': budget, 'loaners': loaners, 'applicants': applicants}
            return render(request, 'oas/summary.html', context)
        except Info.DoesNotExist:
            return render(request, 'oas/summary.html', {'notif': 'Today is not within an academic term.'
                                                                 'Please view term details in the term'
                                                                 'information page.'})
    else:
        return checking


def create_info(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        notif = None
        if request.method == 'POST':
            form = InfoForm(request.POST)
            try:
                if form.is_valid():
                    # check if an entry with same term/AY already exists
                    try:
                        new_term = form.cleaned_data['term_AY']
                        term_info = Info.objects.get(term_AY=new_term)
                        if term_info:
                            form.add_error('term_AY', 'An entry with the same term/AY already exists!')
                    except Info.DoesNotExist:
                        form.save(commit=True)
                        notif = 'Term information saved!'
            except TypeError:
                notif = 'You did not enter valid information.'
        else:
            today = datetime.date.today()
            # if no information for next term in the database
            if Info.objects.filter(start_of_term__gte=today).count() == 0:
                notif = 'Please set up information for the next term.'
            form = InfoForm(None)

        return render(request, 'oas/create_info.html', {'form': form, 'notif': notif, 'curr_info': curr_info})
    else:
        return checking


def view_info(request):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        info = Info.objects.all().order_by('term_AY')
        return render(request, 'oas/infos.html', {'info': info, 'curr_info': curr_info})
    else:
        return checking


def edit_info(request, pk):
    checking = check_user(request)
    if checking is None:
        curr_info = get_curr_info()

        info = Info.objects.get(pk=pk)
        notif = None

        if request.method == 'POST':
            form = InfoForm(request.POST)
            try:
                if form.is_valid():
                    info_new = form.save(commit=False)
                    temp = info.pk
                    info.delete()
                    info_new.pk = temp
                    info_new.save()
                    notif = 'Information has been saved!'
            except TypeError:
                notif = 'You did not enter valid information.'
        else:
            initial = {'budget': info.budget, 'term_AY': info.term_AY,
                       'start_of_term': info.start_of_term, 'end_of_term': info.end_of_term,
                       'application_start': info.application_start, 'application_end': info.application_end,
                       'release_of_results': info.release_of_results, 'deadline_of_payment': info.deadline_of_payment}
            form = InfoForm(None, initial=initial)

        return render(request, 'oas/info_details.html', {'form': form, 'info': info, 'notif': notif,
                                                         'curr_info': curr_info})
    else:
        return checking


def export_loaners(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loaners.csv"'

    writer = csv.writer(response)
    writer.writerow(['#', 'ID Number', 'First name', 'Last name', 'Email', 'College', 'Course', 'Level',
                     'Cellphone Number', 'Loan Amount', 'Loan Balance left', 'Term/AY of Loan Applied'])

    students = Student.objects.all().order_by('id_number')

    ctr = 1
    for student in students:
        row = [str(ctr), student.id_number, student.first_name, student.last_name, student.user.email, student.college,
               student.course, student.level, student.cellphone_number]
        try:
            loan = Loan.objects.get(id_number=student, status='Approved')
            row.extend([loan.amount, loan.balance, loan.term_AY])
        except Loan.DoesNotExist:
            row.extend(['N/A', 'N/A', 'N/A'])

        writer.writerow(row)
        ctr += 1

    return response
