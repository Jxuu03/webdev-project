"""
URL configuration for recipeproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from recipes.views import *
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from recipes import views
from .views import myRecipes
from .views import recipeCreate


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', home, name='home'),
    path('recipe/<int:pk>/', recipeDetail, name='recipe_detail'),
    path('recipes/new/', recipeCreate, name='recipe_create'),
    path('recipes/edit/<int:pk>/', recipeUpdate, name='recipe_update'),
    path('recipes/delete/<int:pk>/', recipeDelete, name='recipe_delete'),
    path('my-recipes/', views.myRecipes, name='myRecipes'),
    path('my-recipes/', myRecipes, name='myRecipes'),  # URL สำหรับหน้าสูตรของฉัน
    path('recipes/new/', recipeCreate, name='recipe_create'), # เชื่อมโยงกับฟังก์ชันเพิ่มสูตร
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

   