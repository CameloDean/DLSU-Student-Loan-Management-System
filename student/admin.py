from django.contrib import admin
from .models import Payment, Loan

# Register your models here.
admin.site.register(Payment)
admin.site.register(Loan)