from django import forms
from django.core.exceptions import ValidationError
from student.models import Payment
from .models import Info
import re


class DateInput(forms.DateInput):
    input_type = 'date'


class PaymentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['orNum'].label = 'OR Number'

    class Meta:
        model = Payment
        fields = ['orNum', 'amount', 'date']

    def clean_amount(self):
        data = super(PaymentForm, self).clean()

        amount = data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount should be more than 0')

        return amount


class InfoForm(forms.ModelForm):

    class Meta:
        model = Info
        fields = ['term_AY', 'budget', 'start_of_term', 'end_of_term', 'application_start',
                  'application_end', 'release_of_results', 'deadline_of_payment']
        widgets = {
            'start_of_term': DateInput(),
            'end_of_term': DateInput(),
            'application_start': DateInput(),
            'application_end': DateInput(),
            'release_of_results': DateInput(),
            'deadline_of_payment': DateInput(),
        }

    def clean_budget(self):
        data = super(InfoForm, self).clean()

        budget = data.get('budget')
        if budget <= 0:
            raise ValidationError('Budget should be more than 0')

        return budget

    def clean_term_AY(self):
        data = super(InfoForm, self).clean()

        term = data.get('term_AY')

        # check if term_AY follows the pattern
        match = re.match('^Term [123], AY[0-9][0-9]-[0-9][0-9]', term)
        if not match:
            raise ValidationError('Invalid format! Please follow: Term x, AYxx-xx')

        return term

    def clean(self):
        data = super(InfoForm, self).clean()

        application_start = data.get('application_start')
        application_end = data.get('application_end')
        end_of_term = data.get('end_of_term')
        start_of_term = data.get('start_of_term')
        deadline_of_payment = data.get('deadline_of_payment')
        release_of_results = data.get('release_of_results')

        if start_of_term >= end_of_term:
            self.add_error('end_of_term', 'End of term should be later than start of term')

        if application_start >= application_end:
            self.add_error('application_end', 'End of application should be later than start of application')

        if release_of_results >= deadline_of_payment:
            self.add_error('deadline_of_payment', 'Deadline of payment should be later than release of results')

        return data
