from django import forms


class GameForm(forms.Form):
    title = forms.CharField(label='Game title', max_length=100)
