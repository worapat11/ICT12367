from django.shortcuts import render, redirect
from django.http import HttpResponse
from myapp.models import person

# Create your views here.
def index(request):
    all_person = person.objects.all()
    return render(request, 'index.html',{"all_person":all_person})

def about(request):
    return render(request, 'about.html')

def form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        age = request.POST.get('age')
        if name and age:
            person.objects.create(name=name, age=age)
            return redirect('index')
    return render(request, 'form.html')