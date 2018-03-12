from django import forms


class MyForm(forms.Form):
    my_field = forms.CharField()

    def process(self):
      # Assumes .cleaned_data exists because this method is always invoked after .is_valid(), otherwise will raise AttributeError
      cd = self.cleaned_data
