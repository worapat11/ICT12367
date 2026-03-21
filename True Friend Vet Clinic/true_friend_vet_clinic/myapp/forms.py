from django import forms
from .models_noob import Owner, Pet, Appointment


class OwnerForm(forms.ModelForm):

    class Meta:
        model = Owner
        fields = '__all__'


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'})
        }


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment
        fields = '__all__'