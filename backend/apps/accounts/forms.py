from django import forms
from django.core.exceptions import ValidationError

from apps.churches.models import Departement, RoleEglise
from .models import Utilisateur
from .services_sms import normaliser_telephone


class InscriptionMembreForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            "nom", "prenom", "sexe", "date_naissance", "telephone", "email", "nationalite",
            "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise", "eglise",
            "departement", "role_eglise", "photo",
        ]
        widgets = {
            "telephone": forms.TextInput(attrs={"class":"form-control","placeholder":"+224626483701","autocomplete":"tel","inputmode":"tel"}),
            "photo": forms.ClearableFileInput(attrs={"class":"form-control","accept":"image/*"}),
        }

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name in ["email","date_naissance","date_bapteme_eau","date_bapteme_saint_esprit","photo","departement","role_eglise"]:
            self.fields[name].required=False

    def clean_telephone(self):
        try:
            numero=normaliser_telephone(self.cleaned_data.get("telephone"))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        qs=Utilisateur.objects.filter(telephone=numero)
        if self.instance and self.instance.pk: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise ValidationError("Ce numéro de téléphone est déjà associé à un compte EESAG.")
        return numero

    def clean(self):
        cleaned=super().clean(); eglise=cleaned.get("eglise"); departement=cleaned.get("departement"); role_eglise=cleaned.get("role_eglise")
        if eglise and departement and departement.eglise_id != eglise.id: self.add_error("departement","Le département sélectionné n'appartient pas à cette église.")
        if eglise and role_eglise and role_eglise.eglise_id != eglise.id: self.add_error("role_eglise","Le rôle sélectionné n'appartient pas à cette église.")
        return cleaned


class VerificationTelephoneForm(forms.Form):
    telephone=forms.CharField(max_length=30,label="Numéro de téléphone",widget=forms.TextInput(attrs={"class":"form-control","readonly":"readonly"}))
    code=forms.CharField(min_length=6,max_length=6,label="Code de confirmation",widget=forms.TextInput(attrs={"class":"form-control text-center","placeholder":"000000","autocomplete":"one-time-code","inputmode":"numeric"}))
    def clean_telephone(self):
        try:return normaliser_telephone(self.cleaned_data.get("telephone"))
        except ValueError as exc:raise ValidationError(str(exc)) from exc
    def clean_code(self):
        code=str(self.cleaned_data.get("code") or "").strip()
        if not code.isdigit() or len(code)!=6:raise ValidationError("Le code doit contenir exactement 6 chiffres.")
        return code


class RenvoyerCodeTelephoneForm(forms.Form):
    telephone=forms.CharField(max_length=30,label="Numéro de téléphone",widget=forms.TextInput(attrs={"class":"form-control","placeholder":"+224626483701","inputmode":"tel"}))
    def clean_telephone(self):
        try:return normaliser_telephone(self.cleaned_data.get("telephone"))
        except ValueError as exc:raise ValidationError(str(exc)) from exc


class ConfirmationOTPForm(forms.Form):
    code=forms.CharField(min_length=6,max_length=6,label="Code reçu",widget=forms.TextInput(attrs={"class":"form-control text-center","placeholder":"123456","autocomplete":"one-time-code","inputmode":"numeric"}))
    def clean_code(self):
        code=str(self.cleaned_data.get("code") or "").strip()
        if not code.isdigit() or len(code)!=6:raise ValidationError("Le code doit contenir exactement 6 chiffres.")
        return code
