from django.db import models

class Population(models.Model):
    pid = models.IntegerField()
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    created_date = models.DateField(auto_now_add=True)