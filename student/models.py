from django.db import models
from account.models import Student


class Payment(models.Model):
    orNum = models.CharField(max_length=20)
    amount = models.FloatField()
    date = models.DateField()
    id_number = models.ForeignKey(Student, on_delete=models.CASCADE)
    isApproved = models.BooleanField(default=False)

    def __str__(self):
        return self.orNum


class Loan(models.Model):
    id_number = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='In Process')
    balance = models.FloatField(default=0)
    term_AY = models.CharField(max_length=15)
    maturity_date = models.DateField(default='2017-01-01')
    notif_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.pk.__str__()
