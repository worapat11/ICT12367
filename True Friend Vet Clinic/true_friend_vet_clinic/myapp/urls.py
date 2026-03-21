from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),

    # OWNER
    path('owners/', views.owner_list, name='owner_list'),
    path('owners/add/', views.add_owner, name='add_owner'),
    path('owners/edit/<str:id>/', views.edit_owner, name='edit_owner'),
    path('owners/delete/<str:id>/', views.delete_owner, name='delete_owner'),

    # PET
    path('pets/', views.pet_list, name='pet_list'),
    path('pets/add/', views.add_pet, name='add_pet'),
    path('pets/edit/<str:id>/', views.edit_pet, name='edit_pet'),
    path('pets/delete/<str:id>/', views.delete_pet, name='delete_pet'),

    # APPOINTMENT
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/add/', views.add_appointment, name='add_appointment'),
    path('appointments/edit/<str:id>/', views.edit_appointment, name='edit_appointment'),
    path('appointments/delete/<str:id>/', views.delete_appointment, name='delete_appointment'),

    # MEDICAL RECORD
    path('medical_records/', views.medical_records, name='medical_records'),
    path('medical_records/add/', views.add_medical_record, name='add_medical_record'),
    path('medical_records/edit/<str:id>/', views.edit_medical_record, name='edit_medical_record'),
    path('medical_records/delete/<str:id>/', views.delete_medical_record, name='delete_medical_record'),
    path('medical_records/<str:id>/remove_treatment/<str:treatment_id>/', views.remove_treatment, name='remove_treatment'),
    path('bills/pay/<str:id>/', views.pay_bill, name='pay_bill'),
    path('bills/paid/<str:id>/', views.paid_bill, name='paid_bill'),
    path('bills/paid/', views.paid_bills, name='paid_bills'),
    path('bills/unpaid/', views.unpaid_bills, name='unpaid_bills'),
    path('bills/<str:id>/', views.bill_detail, name='bill_detail'),

    # MEDICINE
    path('medicines/', views.medicines, name='medicines'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('medicines/edit/<str:id>/', views.edit_medicine, name='edit_medicine'),
    path('medicines/delete/<str:id>/', views.delete_medicine, name='delete_medicine'),

    # REPORTS
    path('reports/', views.reports, name='reports'),
    path('reports/stock_status/', views.report_stock_status, name='report_stock_status'),
    path('reports/stock_ledger/', views.report_stock_ledger, name='report_stock_ledger'),
    path('reports/payments/', views.report_payments, name='report_payments'),
    path('reports/appointments/', views.report_appointments, name='report_appointments'),
    path('reports/animals/', views.report_animals, name='report_animals'),
    path('reports/most_used_medicines/', views.report_most_used_medicines, name='report_most_used_medicines'),
    path('reports/pos/', views.report_pos, name='report_pos'),

    # POS
    path('pos/', views.pos, name='pos'),
    path('pos/receipt/<str:bill_id>/', views.pos_receipt, name='pos_receipt'),
    path('pos/receipts/', views.pos_receipts_list, name='pos_receipts_list'),
    # AUTH
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]