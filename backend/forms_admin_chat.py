from django import forms
from .models_admin_chat import AdminChat, AdminMessage, AdminChatTemplate


class AdminMessageForm(forms.ModelForm):
    """Form for sending admin messages"""
    
    class Meta:
        model = AdminMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none',
                'rows': 4,
                'placeholder': 'Tapez votre message...'
            })
        }


class AdminChatForm(forms.ModelForm):
    """Form for creating admin chats"""
    
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Décrivez votre problème ou question...'
        }),
        required=True,
        help_text="Décrivez votre problème ou question en détail"
    )
    
    class Meta:
        model = AdminChat
        fields = ['subject', 'category', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'placeholder': 'Sujet de votre demande'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            })
        }


class AdminChatFilterForm(forms.Form):
    """Form for filtering admin chats"""
    
    STATUS_CHOICES = [('', 'Tous les statuts')] + AdminChat.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'Toutes les priorités')] + AdminChat.PRIORITY_CHOICES
    CATEGORY_CHOICES = [('', 'Toutes les catégories')] + AdminChat.CATEGORY_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    )
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Rechercher dans les sujets...'
        })
    )


class AdminChatTemplateForm(forms.ModelForm):
    """Form for admin chat templates"""
    
    class Meta:
        model = AdminChatTemplate
        fields = ['name', 'category', 'subject', 'content', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'placeholder': 'Nom du template'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'placeholder': 'Sujet du template'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none',
                'rows': 8,
                'placeholder': 'Contenu du template...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 focus:ring-2'
            })
        }


class AdminChatAssignmentForm(forms.Form):
    """Form for assigning chats to staff members"""
    
    def __init__(self, *args, **kwargs):
        staff_users = kwargs.pop('staff_users', None)
        super().__init__(*args, **kwargs)
        
        if staff_users:
            self.fields['assigned_to'] = forms.ModelChoiceField(
                queryset=staff_users,
                required=False,
                empty_label="Non assigné",
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
                })
            )
    
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Non assigné",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    )
    
    priority = forms.ChoiceField(
        choices=AdminChat.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    )
    
    status = forms.ChoiceField(
        choices=AdminChat.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500'
        })
    ) 