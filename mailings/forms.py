from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Mailing


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'owner', 'status', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Задаем минимально допустимую дату для календаря в браузере (в локальном часовом поясе)
        now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')
        if not self.instance.pk:
            self.fields['start_time'].widget.attrs['min'] = now_str
        self.fields['end_time'].widget.attrs['min'] = now_str

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if not self.instance.pk and start_time and start_time < timezone.now():
            raise ValidationError("Дата и время начала рассылки не могут быть в прошлом.")
        return start_time

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', "Дата окончания рассылки должна быть позже даты начала.")

        return cleaned_data
