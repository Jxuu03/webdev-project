from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.conf import settings
from django.contrib import messages
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

## -- Authen -- ##
class SignUpView(CreateView):
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")
    template_name = "recipes/signup.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()
        User.objects.create(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            username=user.username,
            password=make_password(user.password),
        )
        auth_login(self.request, user)
        messages.success(self.request, "Registration successful.")
        return super().form_valid(form)


class UserLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = "recipes/login.html"
    success_url = reverse_lazy("home")


def home(request):
    appetizers = Recipe.objects.filter(category="Appetizer")
    main_dishes = Recipe.objects.filter(category="Main dish")
    desserts = Recipe.objects.filter(category="Dessert")
    
    return render(
        request,
        "recipes/home.html",
        {
            "appetizers": appetizers,
            "main_dishes": main_dishes,
            "desserts": desserts,
            "MEDIA_URL": settings.MEDIA_URL  
        },
    )


## -- Handle Request -- ##
# Detail view for a specific recipe
class recipeDetailView(LoginRequiredMixin, DetailView):
    model = Recipe
    template_name = "recipes/recipeDetail.html"
    context_object_name = "recipe"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        context['title'] = recipe.title  
        context['user'] = recipe.user.username  
        context['picture_url'] = recipe.picture_url
        context['MEDIA_URL'] = settings.MEDIA_URL  
        context['category'] = recipe.category
        context['difficulty'] = recipe.difficulty
        context['instructions'] = recipe.instructions
        context['ingredients'] = recipe.ingredients.all()  

        return context

# Create a new recipe
@login_required
def recipeCreate(request):
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST, request.FILES)
        
        if recipe_form.is_valid():
            recipe = recipe_form.save(commit=False)  # Don't save yet
            user_instance = User.objects.get(pk=request.user.pk)  # Ensure a User instance
            recipe.user = user_instance  # Assign the user
            recipe.save()  # Now save to the database

            # Process ingredients if applicable
            ingredient_names = request.POST.getlist('ingredient')
            ingredient_amounts = request.POST.getlist('amount')
            ingredient_units = request.POST.getlist('unit')

            for name, amount, unit in zip(ingredient_names, ingredient_amounts, ingredient_units):
                if name:  # Ensure the ingredient name is not empty
                    Ingredient.objects.create(recipe=recipe, name=name, amount=amount, unit=unit)

            print("Successfully saved new recipe")
            return redirect('myRecipes')
        else:
            print("Form is not valid:", recipe_form.errors)
    else:
        recipe_form = RecipeForm()

    return render(request, 'recipes/recipe_form.html', {'form': recipe_form})


# Update an existing recipe
@login_required
def recipeUpdate(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe_form = RecipeForm(request.POST, instance=recipe)
        if recipe_form.is_valid():
            recipe.user = request.user
            recipe_form.save()
            return redirect("myRecipes")  # Redirect to the recipe list
    else:
        recipe_form = RecipeForm(instance=recipe)
    return render(request, "recipes/recipe_form.html", {"form": recipe_form})

# Delete a recipe
@login_required
def recipeDelete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.delete()
        return redirect('myRecipes')  # Redirect to the recipe list
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

# Display all user' recipes
@login_required
def myRecipes(request):
    # ใช้ request.user ซึ่งเป็น instance ของ User ไม่ใช่ username
    user_recipes = Recipe.objects.filter(user=request.user.id)
    return render(request, 'recipes/my_recipes.html', {'recipes': user_recipes})

# Search bar with suggestion
def search_view(request):
    query = request.GET.get('query', '')
    if query:
        suggestions = Recipe.objects.filter(title__istartswith=query)[:5]  # Get up to 5 suggestions
        results = [{'title': recipe.title, 'url': reverse('recipe-detail', args=[recipe.pk])} for recipe in suggestions]
        return JsonResponse({'suggestions': results})
    return JsonResponse({'suggestions': []})


# Reset password
verification_codes = {}
def resetPassword(request):
    if request.method == "POST":
        step = request.POST.get('step')

        if step == '1':  # Step 1: Email submission
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
                code = get_random_string(6, allowed_chars='0123456789')  # Generate a 6-digit code
                verification_codes[email] = code

                # Send code via email
                send_mail(
                    'Password Reset Code',
                    f'Your password reset code is: {code}',
                    'noreply@example.com',
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({'status': 'success', 'message': 'Code sent successfully.'})
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Email not found.'})

        elif step == '2':  # Step 2: Code verification
            email = request.POST.get('email')
            code = request.POST.get('code')

            if verification_codes.get(email) == code:
                return JsonResponse({'status': 'success', 'message': 'Code verified successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid code.'})

        elif step == '3':  # Step 3: Password reset
            email = request.POST.get('email')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user = get_object_or_404(User, email=email)
                user.password = make_password(new_password)
                user.save()
                del verification_codes[email]  # Remove the code after successful password reset
                return JsonResponse({'status': 'success', 'message': 'Password reset successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Passwords do not match.'})

    return render(request, 'recipes/resetPW.html')