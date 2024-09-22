from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import UserRegisterForm  # Import your user registration form

class SignUpView(CreateView):
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')  # Adjust the redirect URL
    template_name = 'recipes/signup.html'  # Adjust the template name

    def form_valid(self, form):
        user = form.save()  # Save the new user
        auth_login(self.request, user)  # Log the user in immediately
        messages.success(self.request, 'Registration successful.')  # Success message
        return super().form_valid(form)

class UserLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'recipes/login.html'  # Adjust the template name
    success_url = reverse_lazy('home')
    
def home(request):
    return render(request, 'recipes/home.html')