from django.db import models
import datetime


class Info(models.Model):
    deadline_of_payment = models.DateField(default=datetime.date.today)
    loan_total = models.FloatField(default=0.0)
    budget = models.FloatField(default=0.0)
    term_AY = models.CharField(max_length=15, default='Term 1, AY17-18')   # Term 1, AY17-18
    start_of_term = models.DateField(default=datetime.date.today)
    end_of_term = models.DateField(default=datetime.date.today)
    application_start = models.DateField(default=datetime.date.today)
    application_end = models.DateField(default=datetime.date.today)
    release_of_results = models.DateField(default=datetime.date.today)
    all_notified = models.BooleanField(default=False)

    def __str__(self):
        return self.term_AY
