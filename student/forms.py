from django import forms
from student.models import Payment, Loan
from django.core.exceptions import ValidationError


class DateInput(forms.DateInput):
    input_type = 'date'


class PaymentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['orNum'].label = 'OR Number'

    class Meta:
        model = Payment
        fields = ['orNum', 'amount', 'date']

        widgets = {
            'date': DateInput(),
        }

    def clean_amount(self):
        data = super(PaymentForm, self).clean()

        amount = data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount should be more than 0!')

        return amount


class LoanForm(forms.ModelForm):

    class Meta:
        model = Loan
        fields = ['amount']

    def clean_amount(self):
        data = super(LoanForm, self).clean()

        amount = data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount should  be greater than 0!')
        return amount
