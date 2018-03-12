from django.shortcuts import render, redirect, render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
from .models import Student
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from smtplib import SMTPException


def home_page(request):
    return render_to_response('account/home.html')


def prompt1(request):
    return render_to_response('account/prompt1.html')


def prompt2(request):
    return render_to_response('account/prompt2.html')


def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        array = ["", email]
        if user:
            login(request, user)
            count = Student.objects.filter(user=user).count()
            if count:
                return redirect('student:index')
            else:
                return redirect('oas:index')
        else:
            array[0] = " Invalid Email or Password/Account not activated "
            return render(request, 'account/login.html', {'array': array})
    else:
        return render(request, 'account/login.html')


def user_signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('First Name')
        last_name = request.POST.get('Last Name')
        id_number = request.POST.get('ID Number')
        college = request.POST.get('College')
        level = request.POST.get('Level')
        course = request.POST.get('Course')
        cellphone_number = request.POST.get('Cellphone Number')
        email = request.POST.get('Email')
        array = ["", first_name, last_name, id_number, college, level, course, cellphone_number, email]
        pass_1 = request.POST.get('password1')
        pass_2 = request.POST.get('password2')
        if (not Student.objects.filter(id_number=id_number).exists()) and (not User.objects.filter(username=email).exists()):
            if email.find("@dlsu.edu.ph") > 0:
                if pass_1 == pass_2:
                    user = User.objects.create_user(username=email, email=email, password=pass_1)
                    user.is_active = False
                    user.save()
                    student = Student.objects.create(user=user, first_name=first_name, last_name=last_name, id_number=id_number, college=college, course=course, cellphone_number=cellphone_number, level=level)
                    student.save()
                    current_site = get_current_site(request)
                    message = render_to_string('account/acc_active_email.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': account_activation_token.make_token(user),
                    })
                    mail_subject = 'Activate your account.'
                    to_email = user.email
                    email = EmailMessage(mail_subject, message, to=[to_email])
                    try:
                        email.send()
                    except SMTPException:
                        user.delete()
                        return HttpResponse('There\'s a problem in your connection or our server might be down')
                    except TimeoutError:
                        user.delete()
                        return HttpResponse('Timeout Error. Check your internet connection')

                    return redirect('account:prompt1')
                else:
                    array[0] = " Password Mismatch "
                    return render(request, 'account/signup.html', {'array': array})
            else:
                array[0] = "Please use DLSU email"
                return render(request, 'account/signup.html', {'array': array})
        else:
            array[0] = " Account already exists "
            return render(request, 'account/signup.html', {'array': array})
    else:
        return render(request, 'account/signup.html')


def user_logout(request):
    logout(request)
    return redirect('account:home_page')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        count = Student.objects.filter(user=user).count()
        if count:
            return redirect('student:index')
        else:
            return redirect('oas:index')
    else:
        return HttpResponse('Activation link is invalid!')


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.is_active:
                current_site = get_current_site(request)
                message = render_to_string('account/forgot_pass_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                mail_subject = 'Reset Your Password.'
                to_email = user.email
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
                return redirect('account:prompt2')
            else:
                error = "This Account Is Not Yet Activated, Please try again"
                return render(request, 'account/forgot_password.html', {'error': error})
        else:
            error = "Email Doesn't Exist, Please try again"
            return render(request, 'account/forgot_password.html', {'error': error})
    else:
        return render(request, 'account/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if password1 == password2:
                user.set_password(password1)
                user.save()
                login(request, user)
                count = Student.objects.filter(user=user).count()
                if count:
                    return redirect('student:index')
                else:
                    return redirect('oas:index')
            else:
                error = " Password Mismatch "
                return render(request, 'account/reset_password.html', {'error': error})
        else:
            return render(request, 'account/reset_password.html')
    else:
        return HttpResponse('Reset Password link is invalid!')
