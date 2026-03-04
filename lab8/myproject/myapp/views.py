from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    return render(request, "index.html")

def about(request):
    return render(request, "about.html")

from django.shortcuts import render
from django.http import HttpResponse

def form(request):
    if request.method == "POST":
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        email = request.POST.get("email")
        role = request.POST.get("role")

        return HttpResponse(f"""
            <h1>บันทึกข้อมูลเรียบร้อย</h1>
            <p>ชื่อ: {fname}</p>
            <p>นามสกุล: {lname}</p>
            <p>อีเมล: {email}</p>
            <p>ระดับผู้ใช้: {role}</p>
        """)

    return render(request, "form.html")
