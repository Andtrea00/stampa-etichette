from django import forms
from .models import Prodotto


class EtichettaBaseForm(forms.Form):
    data_scadenza = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    codice_animale = forms.CharField(max_length=100)






class ProdottoForm(forms.ModelForm):
    class Meta:
        model = Prodotto
        fields = ['nome', 'peso_default', 'categoria']
