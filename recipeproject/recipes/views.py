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
def recipeDelete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        recipe.delete()
        return redirect('myRecipes')  # Redirect to the recipe list
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

@login_required
def myRecipes(request):
    # ใช้ request.user ซึ่งเป็น instance ของ User ไม่ใช่ username
    user_recipes = Recipe.objects.filter(user=request.user.id)
    return render(request, 'recipes/my_recipes.html', {'recipes': user_recipes})

