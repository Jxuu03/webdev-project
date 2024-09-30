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
from .models import Recipe, Ingredient
from .forms import RecipeForm, IngredientFormSet


## -- Authen -- ##
class SignUpView(CreateView):
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")
    template_name = "recipes/signup.html"

    def form_valid(self, form):
        member = form.save(commit=False)
        member.save()
        Member.objects.create(
            first_name=member.first_name,
            last_name=member.last_name,
            email=member.email,
            username=member,
        )
        auth_login(self.request, member)
        return super().form_valid(form)


class UserLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = "recipes/login.html"
    success_url = reverse_lazy("home")
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)


def home(request):
    appetizers = Recipe.objects.filter(category="Appetizer")
    main_dishes = Recipe.objects.filter(category="Main Dish")
    desserts = Recipe.objects.filter(category="Dessert")
    
    appetizer_count = appetizers.count()
    main_dish_count = main_dishes.count()
    dessert_count = desserts.count()

    # Pass the counts to the template
    return render(
        request,
        "recipes/home.html",
        {
            "appetizers": appetizers,
            "main_dishes": main_dishes,
            "desserts": desserts,
            "appetizer_count": appetizer_count,
            "main_dish_count": main_dish_count,
            "dessert_count": dessert_count,
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
            recipe.user = Member.objects.get(username=request.user)
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
    
    # สร้างฟอร์ม Recipe และ IngredientFormSet
    if request.method == "POST":
        recipe_form = RecipeForm(request.POST, request.FILES, instance=recipe)
        formset = IngredientFormSet(request.POST, queryset=recipe.ingredients.all())

        if recipe_form.is_valid() and formset.is_valid():
            recipe = recipe_form.save(commit=False)
            recipe.user = request.user  # เชื่อมโยงกับผู้ใช้ที่กำลังล็อกอิน
            recipe.save()

            # บันทึกส่วนผสมจาก formset
            ingredients = formset.save(commit=False)
            for ingredient in ingredients:
                ingredient.recipe = recipe
                ingredient.save()

            # ลบส่วนผสมที่ทำเครื่องหมายว่าลบ
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect("myRecipes")
    else:
        recipe_form = RecipeForm(instance=recipe)
        formset = IngredientFormSet(queryset=recipe.ingredients.all())

    return render(request, "recipes/recipe_edit.html", {
        "form": recipe_form,
        "formset": formset,
        "recipe": recipe
    })
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
    user_recipes = Recipe.objects.filter(user__username=request.user)
    return render(request, 'recipes/my_recipes.html', {'recipes': user_recipes})

# Search bar with suggestion
def search_view(request):
    query = request.GET.get('query', '')
    if query:
        suggestions = Recipe.objects.filter(title__istartswith=query)[:5]  # Get up to 5 suggestions
        results = [{'title': recipe.title, 'url': reverse('recipe-detail', args=[recipe.pk])} for recipe in suggestions]
        return JsonResponse({'suggestions': results})
    return JsonResponse({'suggestions': []})

import json
# Reset password
def resetPassword(request):
    verification_codes = request.session.get('verification_codes', {})

    if request.method == "POST":
        data = json.loads(request.body)
        step = data.get('step')

        # Step 1: Send the code to user's email
        if step == '1':
            email = data.get('email')
            try:
                user = User.objects.get(email=email)
                
                # Generate a 6-digit code
                code = get_random_string(6, allowed_chars='0123456789')
                verification_codes[email] = code
                request.session['verification_codes'] = verification_codes

                # Send code via email
                send_mail(
                    'Password Reset Code',
                    f'Your password reset code is: {code}',
                    settings.DEFAULT_FROM_EMAIL,  # e.g., 'noreply@example.com'
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({'status': 'success', 'message': 'Code sent successfully.'})
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Email not found.'})
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                return JsonResponse({'status': 'error', 'message': 'Failed to send email'})

        # Step 2: Verify the code
        elif step == '2':
            email = data.get('email')
            code = data.get('code')

            if verification_codes.get(email) == code:
                return JsonResponse({'status': 'success', 'message': 'Code verified successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid code.'})

        # Step 3: Reset the password
        elif step == '3':
            email = data.get('email')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if new_password == confirm_password:
                user = get_object_or_404(Member, email=email)
                user.password = make_password(new_password)
                user.save()
                auth_user = get_object_or_404(User, email=email)
                auth_user.password = make_password(new_password)
                auth_user.save()

                # Remove the code from the session after successful password reset
                verification_codes.pop(email, None)
                request.session['verification_codes'] = verification_codes

                return JsonResponse({'status': 'success', 'message': 'Password reset successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Passwords do not match.'})

    return render(request, 'recipes/resetPW.html')