from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    return HttpResponse ("ICT12367 SPU")

def about(request):
    return HttpResponse ("<h1>เกี่ยวกับเรา</h1>")

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

def contact(request):
    return HttpResponse ("<h1>รหัสนักศึกษา 6879454 ชื่อนายวรภัทร์ ดินสีวิจิตร</h1>")