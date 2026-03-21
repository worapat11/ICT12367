from django.contrib import admin
from .models import (
    Owners, Pets, Appointments, Medicines, MedicalRecords, Species, Veterinarians, AppointmentStatus,
    Bills, PaymentMethod, PetAllergies, MedicineStock, Staff, Suppliers, Treatments, Users
)
import uuid

class OwnerAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner_id = str(uuid.uuid4())[:6]
        super().save_model(request, obj, form, change)

admin.site.register(Owners, OwnerAdmin)
admin.site.register(Pets)
admin.site.register(Appointments)
admin.site.register(Medicines)
admin.site.register(MedicalRecords)
admin.site.register(Species)
admin.site.register(Veterinarians)
admin.site.register(AppointmentStatus)
admin.site.register(Bills)
admin.site.register(PaymentMethod)
admin.site.register(PetAllergies)
admin.site.register(MedicineStock)
admin.site.register(Staff)
admin.site.register(Suppliers)
admin.site.register(Treatments)
admin.site.register(Users)