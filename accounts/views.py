from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm, ProfileForm
from .models import Player

class SignUpView(CreateView):
    """
    View for user registration
    """
    template_name = 'accounts/signup.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Save the user
        response = super().form_valid(form)
        
        # Create player profile
        Player.objects.create(user=self.object)
        
        # Log the user in
        login(self.request, self.object)
        
        # Show success message
        messages.success(self.request, 'Account created successfully! Welcome to Panda Match!')
        
        return response

class CustomLoginView(LoginView):
    """
    Custom login view
    """
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Redirect to home page after login
        return reverse_lazy('home')
    
    def form_valid(self, form):
        # Show welcome message
        messages.info(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    """
    Custom logout view
    """
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out. Come back soon!')
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset request view
    """
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Custom password reset done view
    """
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirmation view
    """
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Custom password reset complete view
    """
    template_name = 'accounts/password_reset_complete.html'

class ProfileView(LoginRequiredMixin, UpdateView):
    """
    View for user profile management
    """
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player'] = self.request.user.player
        return context