from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Member(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.username} : {self.email}'

class Recipe(models.Model):
    user = models.ForeignKey(Member, related_name='recipes', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=50)
    picture_url = models.ImageField(upload_to='recipes/images/', blank=True, null=True)
    instructions = models.TextField()
    
    def __str__(self):
        return f'{self.title} : {self.category}'
    
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    unit = models.CharField(max_length=50, choices=[
        ('tsp', 'ช้อนชา'),
        ('tbs', 'ช้อนโต๊ะ'),
        ('oz', 'ออนซ์'),
        ('g', 'กรัม'),
        ('lb', 'ปอนด์ (lb)'),
        ('cup', 'ถ้วยตวง'),
    ])
    
    def __str__(self):
        return f'{self.name} : {self.amount} : {self.unit}'