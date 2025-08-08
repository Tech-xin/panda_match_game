from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with additional fields
    """
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field appearance
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[field_name].label
            })

class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field appearance
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[field_name].label
            })

class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset request form
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field appearance
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[field_name].label
            })

class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom form for setting a new password
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field appearance
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[field_name].label
            })

class ProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field appearance
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control'
            })