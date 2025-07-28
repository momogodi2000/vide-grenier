# backend/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Row, Column, Field
from crispy_forms.bootstrap import FormActions
import re
from .models import User, Product, Order, Review, Message, Category, GroupChat, GroupChatMessage


class CustomSignupForm(UserCreationForm):
    """Formulaire d'inscription personnalisé"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre.email@exemple.com'
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX',
            'pattern': r'\+237[0-9]{9}'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        })
    )
    
    city = forms.ChoiceField(
        choices=User.CITIES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name', 'city', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('email', css_class='form-group mb-3'),
            Field('phone', css_class='form-group mb-3'),
            Field('city', css_class='form-group mb-3'),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('terms_accepted', css_class='form-check mb-3'),
            FormActions(
                Submit('submit', 'Créer mon compte', css_class='btn btn-primary btn-lg w-100')
            )
        )
        
        # Personnaliser les widgets de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe (min. 12 caractères)'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Cette adresse email est déjà utilisée.')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Valider le format camerounais
        if not re.match(r'^\+237[0-9]{9}$', phone):
            raise ValidationError('Format téléphone invalide. Utilisez: +237XXXXXXXXX')
        
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Ce numéro de téléphone est déjà utilisé.')
        
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.city = self.cleaned_data['city']
        user.user_type = 'CLIENT'
        # Set username to None since we use email as USERNAME_FIELD
        user.username = None
        
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre adresse email',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre mot de passe'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='form-group mb-3'),
            Field('password', css_class='form-group mb-3'),
            Field('remember_me', css_class='form-check mb-3'),
            FormActions(
                Submit('submit', 'Se connecter', css_class='btn btn-primary btn-lg w-100')
            )
        )


class ProductForm(forms.ModelForm):
    """Formulaire de création/modification de produit"""
    
    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        help_text="Vous pouvez sélectionner jusqu'à 5 images (max 5MB chacune)"
    )
    
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'category', 'price', 
            'condition', 'city', 'is_negotiable'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre produit (10-100 caractères)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez votre produit en détail (50-2000 caractères)'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': settings.VGK_SETTINGS['MIN_PRODUCT_PRICE'],
                'max': settings.VGK_SETTINGS['MAX_PRODUCT_PRICE'],
                'placeholder': 'Prix en FCFA'
            }),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'is_negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='form-group mb-3'),
            Field('category', css_class='form-group mb-3'),
            Row(
                Column('price', css_class='form-group col-md-6 mb-3'),
                Column('condition', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('city', css_class='form-group col-md-6 mb-3'),
                Column('is_negotiable', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('description', css_class='form-group mb-3'),
            Field('images', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Publier le produit', css_class='btn btn-success btn-lg')
            )
        )
        
        # Filtrer les catégories pour n'afficher que les feuilles
        self.fields['category'].queryset = Category.objects.filter(
            children=None, is_active=True
        ).order_by('parent__name', 'name')
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise ValidationError('Le titre doit contenir au moins 10 caractères.')
        if len(title) > 100:
            raise ValidationError('Le titre ne peut pas dépasser 100 caractères.')
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 50:
            raise ValidationError('La description doit contenir au moins 50 caractères.')
        if len(description) > 2000:
            raise ValidationError('La description ne peut pas dépasser 2000 caractères.')
        return description
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        min_price = settings.VGK_SETTINGS['MIN_PRODUCT_PRICE']
        max_price = settings.VGK_SETTINGS['MAX_PRODUCT_PRICE']
        
        if price < min_price:
            raise ValidationError(f'Le prix minimum est de {min_price} FCFA.')
        if price > max_price:
            raise ValidationError(f'Le prix maximum est de {max_price:,} FCFA.')
        
        return price


class OrderForm(forms.ModelForm):
    """Formulaire de création de commande"""
    
    class Meta:
        model = Order
        fields = ['payment_method', 'delivery_method', 'delivery_address', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'delivery_method': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète pour la livraison'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Instructions spéciales (optionnel)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('payment_method', css_class='form-group mb-3'),
            Field('delivery_method', css_class='form-group mb-3'),
            Field('delivery_address', css_class='form-group mb-3'),
            Field('notes', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Passer la commande', css_class='btn btn-primary btn-lg w-100')
            )
        )
    
    def clean_delivery_address(self):
        delivery_method = self.cleaned_data.get('delivery_method')
        delivery_address = self.cleaned_data.get('delivery_address')
        
        if delivery_method == 'DELIVERY' and not delivery_address:
            raise ValidationError('Une adresse de livraison est requise pour la livraison à domicile.')
        
        return delivery_address


class ReviewForm(forms.ModelForm):
    """Formulaire d'avis client"""
    
    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        help_text='Photos du produit reçu (optionnel)'
    )
    # To support multiple images, handle request.FILES.getlist('images') in your view.
    
    class Meta:
        model = Review
        fields = [
            'product_quality', 'seller_communication', 'delivery_speed',
            'packaging', 'overall_rating', 'comment'
        ]
        widgets = {
            'product_quality': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'seller_communication': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'delivery_speed': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'packaging': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'overall_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Partagez votre expérience en détail...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser les labels
        self.fields['product_quality'].label = 'Qualité du produit'
        self.fields['seller_communication'].label = 'Communication vendeur'
        self.fields['delivery_speed'].label = 'Rapidité de livraison'
        self.fields['packaging'].label = 'Qualité emballage'
        self.fields['overall_rating'].label = 'Note globale'
        self.fields['comment'].label = 'Votre avis détaillé'
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('product_quality', css_class='rating-field'),
                Field('seller_communication', css_class='rating-field'),
                Field('delivery_speed', css_class='rating-field'),
                Field('packaging', css_class='rating-field'),
                Field('overall_rating', css_class='rating-field'),
                css_class='ratings-section mb-4'
            ),
            Field('comment', css_class='form-group mb-3'),
            Field('images', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Publier mon avis', css_class='btn btn-primary btn-lg')
            )
        )
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if len(comment) < 20:
            raise ValidationError('Votre commentaire doit contenir au moins 20 caractères.')
        return comment


class ChatMessageForm(forms.ModelForm):
    """Formulaire de message dans le chat"""
    
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'offer_amount', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tapez votre message...'
            }),
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'offer_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant en FCFA',
                'min': 1000
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'message-form'
        self.helper.layout = Layout(
            Field('message_type', css_class='d-none', id='message-type'),
            Field('content', css_class='form-group'),
            Field('offer_amount', css_class='form-group d-none', id='offer-amount-field'),
            Field('image', css_class='form-group d-none', id='image-field'),
            FormActions(
                Submit('submit', 'Envoyer', css_class='btn btn-primary')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        content = cleaned_data.get('content')
        offer_amount = cleaned_data.get('offer_amount')
        
        if message_type == 'OFFER' and not offer_amount:
            raise ValidationError('Un montant est requis pour une offre de prix.')
        
        if message_type == 'TEXT' and not content:
            raise ValidationError('Le message ne peut pas être vide.')
        
        return cleaned_data


class GroupChatForm(forms.ModelForm):
    """Formulaire de création de groupe de discussion"""
    
    selected_participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'participant-checkbox'
        }),
        label="Participants"
    )
    
    class Meta:
        model = GroupChat
        fields = ['name', 'type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du groupe'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter users based on the current user's type
            if user.user_type == 'ADMIN':
                # Admins can add any user
                self.fields['selected_participants'].queryset = User.objects.exclude(id=user.id)
            elif user.user_type == 'STAFF':
                # Staff can add clients and other staff
                self.fields['selected_participants'].queryset = User.objects.filter(
                    user_type__in=['CLIENT', 'STAFF']
                ).exclude(id=user.id)
            else:
                # Clients can only add other clients
                self.fields['selected_participants'].queryset = User.objects.filter(
                    user_type='CLIENT'
                ).exclude(id=user.id)
            
            # Set initial type based on user type
            if user.user_type == 'ADMIN':
                self.fields['type'].initial = 'ADMIN_CLIENT'
            elif user.user_type == 'STAFF':
                self.fields['type'].initial = 'CLIENT_STAFF'
            else:
                self.fields['type'].initial = 'GENERAL'
        
        self.helper = FormHelper()
        self.helper.form_class = 'group-chat-form'
        self.helper.layout = Layout(
            Field('name', css_class='form-group'),
            Field('type', css_class='form-group'),
            Field('selected_participants', css_class='form-group'),
            FormActions(
                Submit('submit', 'Créer le groupe', css_class='btn btn-primary')
            )
        )
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError('Le nom du groupe doit comporter au moins 3 caractères.')
        return name


class GroupChatMessageForm(forms.ModelForm):
    """Formulaire de message dans un groupe de discussion"""
    
    class Meta:
        model = GroupChatMessage
        fields = ['content', 'message_type', 'image', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tapez votre message...'
            }),
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'group-message-form'
        self.helper.layout = Layout(
            Field('message_type', css_class='d-none', id='message-type'),
            Field('content', css_class='form-group'),
            Field('image', css_class='form-group d-none', id='image-field'),
            Field('file', css_class='form-group d-none', id='file-field'),
            FormActions(
                Submit('submit', 'Envoyer', css_class='btn btn-primary')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        file = cleaned_data.get('file')
        
        if message_type == 'TEXT' and not content:
            raise ValidationError('Le message ne peut pas être vide.')
        
        if message_type == 'IMAGE' and not image:
            raise ValidationError('Une image est requise pour ce type de message.')
        
        if message_type == 'FILE' and not file:
            raise ValidationError('Un fichier est requis pour ce type de message.')
        
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """Formulaire de modification du profil utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'city', 
            'address', 'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 6XX XXX XXX'
            }),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-3'),
                Column('city', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('address', css_class='form-group mb-3'),
            Field('profile_picture', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Mettre à jour', css_class='btn btn-primary btn-lg')
            )
        )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Valider le format camerounais
        if not re.match(r'^\+237[0-9]{9}$', phone):
            raise ValidationError('Format téléphone invalide. Utilisez: +237XXXXXXXXX')
        
        # Vérifier l'unicité (sauf pour l'utilisateur actuel)
        existing_user = User.objects.filter(phone=phone).exclude(id=self.instance.id).first()
        if existing_user:
            raise ValidationError('Ce numéro de téléphone est déjà utilisé.')
        
        return phone


class SearchForm(forms.Form):
    """Formulaire de recherche avancée"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Que recherchez-vous ?',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True, parent=None),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    city = forms.ChoiceField(
        choices=[('', 'Toutes les villes')] + User.CITIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_price = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix min',
            'min': 0
        })
    )
    
    max_price = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix max',
            'min': 0
        })
    )
    
    condition = forms.ChoiceField(
        choices=[('', 'Tous états')] + Product.CONDITIONS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Plus récents'),
            ('price', 'Prix croissant'),
            ('-price', 'Prix décroissant'),
            ('-views_count', 'Plus populaires'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('q', css_class='search-main mb-3'),
            Row(
                Column('category', css_class='form-group col-md-4'),
                Column('city', css_class='form-group col-md-4'),
                Column('condition', css_class='form-group col-md-4'),
                css_class='form-row mb-3'
            ),
            Row(
                Column('min_price', css_class='form-group col-md-4'),
                Column('max_price', css_class='form-group col-md-4'),
                Column('sort', css_class='form-group col-md-4'),
                css_class='form-row mb-3'
            ),
            FormActions(
                Submit('submit', 'Rechercher', css_class='btn btn-primary btn-lg w-100')
            )
        )


class AdminStockForm(forms.ModelForm):
    """Formulaire pour ajouter du stock admin"""
    
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'category', 'price', 'condition', 'city'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du produit'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix de vente en FCFA'
            }),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'})
        }
    
    # Champs additionnels pour AdminStock
    sku = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code produit unique'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantité en stock'
        })
    )
    
    purchase_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix d\'achat en FCFA'
        })
    )
    
    shelf_location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emplacement physique (ex: A1-B2)'
        })
    )
    
    warranty_info = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Informations garantie'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='form-group mb-3'),
            Field('category', css_class='form-group mb-3'),
            Row(
                Column('sku', css_class='form-group col-md-6 mb-3'),
                Column('quantity', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('purchase_price', css_class='form-group col-md-6 mb-3'),
                Column('price', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('condition', css_class='form-group col-md-6 mb-3'),
                Column('city', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('shelf_location', css_class='form-group mb-3'),
            Field('description', css_class='form-group mb-3'),
            Field('warranty_info', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Ajouter au stock', css_class='btn btn-success btn-lg')
            )
        )


class ContactForm(forms.Form):
    """Formulaire de contact"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom complet'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sujet de votre message'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Votre message détaillé...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('subject', css_class='form-group mb-3'),
            Field('message', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Envoyer le message', css_class='btn btn-primary btn-lg')
            )
        )