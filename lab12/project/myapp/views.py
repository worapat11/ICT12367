from django.shortcuts import render, redirect, get_object_or_404
from .models import Population

def index(request):
    people = Population.objects.all()
    return render(request, 'index.html', {'people': people})

def register(request):
    if request.method == 'POST':
        pid = request.POST.get('pid')
        name = request.POST.get('name')
        age = request.POST.get('age')
        
        if pid and name and age:
            Population.objects.create(pid=pid, name=name, age=age)
            return redirect('home')
    
    return render(request, 'form.html')

def edit(request, id):
    person = get_object_or_404(Population, id=id)
    
    if request.method == 'POST':
        person.pid = request.POST.get('pid')
        person.name = request.POST.get('name')
        person.age = request.POST.get('age')
        person.save()
        return redirect('home')
    
    return render(request, 'edit.html', {'person': person})

def delete(request, id):
    person = get_object_or_404(Population, id=id)
    person.delete()
    return redirect('home')

def about(request):
    return render(request, 'about.html')