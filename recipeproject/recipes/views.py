from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import * 
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Recipe
from django.contrib.auth.decorators import login_required
## -- Authen -- ##
class SignUpView(CreateView):
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')  
    template_name = 'recipes/signup.html'  

    def form_valid(self, form):
        user = form.save(commit=False)  # Create user instance
        user.save()  # Save the user to the database
        auth_login(self.request, user)  # Log the user in
        messages.success(self.request, 'Registration successful.')  
        return super().form_valid(form)

class UserLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'recipes/login.html'  
    success_url = reverse_lazy('home')
    
def home(request):
    appetizers = Recipe.objects.filter(category='Appetizer')
    main_dishes = Recipe.objects.filter(category='Main dish')
    desserts = Recipe.objects.filter(category='Dessert')
    return render(request, 'recipes/home.html', {'appetizers': appetizers,
                                                 'main_dishes': main_dishes,
                                                 'desserts': desserts})

## -- Handle Request -- ##

# Detail view for a specific recipe
def recipeDetail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    ingredients = recipe.ingredients.all() 
    return render(request, 'recipes/recipeDetail.html', {'recipe': recipe, 'ingredients': ingredients})

# Create a new recipe
def recipeCreate(request):
    if request.method == 'POST':
        # ฟอร์มจะต้องรองรับการอัปโหลดไฟล์โดยใช้ request.FILES
        recipe_form = RecipeForm(request.POST, request.FILES)
        if recipe_form.is_valid():
            # บันทึกข้อมูลฟอร์มลงในฐานข้อมูล
            recipe = recipe_form.save(commit=False)
            recipe.user = request.user  # กำหนดผู้ใช้ที่เพิ่มสูตร
            recipe.save()
            return redirect('myRecipes')  # หลังจากบันทึกสำเร็จแล้วจะกลับไปหน้ารายการสูตรของฉัน
    else:
        recipe_form = RecipeForm()
    
    # แสดงฟอร์มสำหรับเพิ่มสูตรใหม่
    return render(request, 'recipes/recipe_form.html', {'form': recipe_form})


# Update an existing recipe
def recipeUpdate(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST, instance=recipe)
        if recipe_form.is_valid():
            recipe_form.save()
            return redirect('myRecipes')  # Redirect to the recipe list
    else:
        recipe_form = RecipeForm(instance=recipe)
    return render(request, 'recipes/recipe_form.html', {'form': recipe_form})


# Delete a recipe
def recipeDelete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        recipe.delete()
        return redirect('myRecipes')  # Redirect to the recipe list
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

@login_required
def myRecipes(request):
    # ใช้ request.user ซึ่งเป็น instance ของ User ไม่ใช่ username
    user_recipes = Recipe.objects.filter(user_id=request.user)
    return render(request, 'recipes/my_recipes.html', {'recipes': user_recipes})



    
    