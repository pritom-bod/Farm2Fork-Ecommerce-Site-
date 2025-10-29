# shop/forms.py
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, 
    AuthenticationForm, 
    UsernameField, 
    PasswordChangeForm, 
    PasswordResetForm, 
    SetPasswordForm
)
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import ProductQuestion, UserProfile
import re


# ============================================================
# AUTHENTICATION FORMS
# ============================================================

class UserRegForm(UserCreationForm):
    """User registration form with email validation"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        """Validate that the email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('This email address is already registered.'))
        return email

    def clean_username(self):
        """Validate username contains only alphanumeric characters and underscores"""
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w]+$', username):
            raise ValidationError(_('Username can only contain letters, numbers, and underscores.'))
        return username


class LoginForm(AuthenticationForm):
    """User login form"""
    username = UsernameField(
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class PassChangeForm(PasswordChangeForm):
    """Password change form"""
    old_password = forms.CharField(
        label=_('Old Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
    )
    new_password1 = forms.CharField(
        label=_('New Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': 'New Password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    )


class MyPasswordResetForm(PasswordResetForm):
    """Password reset form"""
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )


class MySetPasswordForm(SetPasswordForm):
    """Set new password form"""
    new_password1 = forms.CharField(
        label=_('New Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': 'New Password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    )


# ============================================================
# USER PROFILE FORM
# ============================================================

class UserProfileForm(forms.ModelForm):
    """User profile form with validation"""
    # Additional fields from User model
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'address', 'city', 'country', 'postcode', 'profile_image'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postcode/ZIP'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'phone': _('Phone Number'),
            'address': _('Address'),
            'city': _('City'),
            'country': _('Country'),
            'postcode': _('Postcode/ZIP'),
            'profile_image': _('Profile Picture')
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with user data"""
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # Pre-populate first_name, last_name, email from User model
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and dashes
            phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
            # Check if it contains only digits and + (for country code)
            if not re.match(r'^\+?[\d]+$', phone_clean):
                raise ValidationError(_('Please enter a valid phone number.'))
            # Check length (between 10 and 15 digits)
            if len(phone_clean) < 10 or len(phone_clean) > 15:
                raise ValidationError(_('Phone number must be between 10 and 15 digits.'))
        return phone

    def clean_postcode(self):
        """Validate postcode"""
        postcode = self.cleaned_data.get('postcode')
        if postcode:
            # Remove spaces
            postcode_clean = postcode.replace(' ', '')
            if len(postcode_clean) < 3 or len(postcode_clean) > 10:
                raise ValidationError(_('Please enter a valid postcode.'))
        return postcode

    def clean_profile_image(self):
        """Validate uploaded image"""
        image = self.cleaned_data.get('profile_image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(_('Image file size cannot exceed 5MB.'))
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError(_('Please upload a valid image file (JPG, PNG, or GIF).'))
        return image

    def save(self, commit=True):
        """Save the profile and update the associated User model"""
        profile = super(UserProfileForm, self).save(commit=False)
        
        # Update the associated User model with first_name, last_name, email
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name')
            profile.user.last_name = self.cleaned_data.get('last_name')
            profile.user.email = self.cleaned_data.get('email')
            if commit:
                profile.user.save()
        
        # Update profile fields
        profile.first_name = self.cleaned_data.get('first_name')
        profile.last_name = self.cleaned_data.get('last_name')
        profile.email = self.cleaned_data.get('email')
        
        if commit:
            profile.save()
        
        return profile

class ProductQuestionForm(forms.ModelForm):
    class Meta:
        model = ProductQuestion
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ask your question about this product...'
            }),
        }
