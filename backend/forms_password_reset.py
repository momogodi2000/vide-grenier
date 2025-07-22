from django import forms

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Adresse email", max_length=254, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-vgk-green-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white',
        'placeholder': 'Votre adresse email',
        'autocomplete': 'email',
    }))

class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(label="Nouveau mot de passe", widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-vgk-green-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white',
        'placeholder': 'Nouveau mot de passe',
        'autocomplete': 'new-password',
    }))
    new_password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-vgk-green-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white',
        'placeholder': 'Confirmer le mot de passe',
        'autocomplete': 'new-password',
    }))

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "Les mots de passe ne correspondent pas.")
        return cleaned_data
