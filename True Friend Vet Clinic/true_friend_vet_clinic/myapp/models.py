from django.db import models


class AppointmentStatus(models.Model):
    status_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    status_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    description = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Appointment_Status'


class Appointments(models.Model):
    appointment_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    pet = models.ForeignKey('Pets', models.DO_NOTHING)
    vet = models.ForeignKey('Veterinarians', models.DO_NOTHING)
    status = models.ForeignKey(AppointmentStatus, models.DO_NOTHING)
    appointment_date = models.DateField(blank=True, null=True)
    appointment_time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Appointments'


class Bills(models.Model):
    bill_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    record = models.ForeignKey('MedicalRecords', models.DO_NOTHING)
    payment_method = models.ForeignKey('PaymentMethod', models.DO_NOTHING, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Bills'


class POSBills(models.Model):
    bill_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    customer = models.ForeignKey('Owners', models.DO_NOTHING)
    payment_method = models.ForeignKey('PaymentMethod', models.DO_NOTHING, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    pre_vat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'POS_Bills'


class MedicalRecords(models.Model):
    record_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    pet = models.ForeignKey('Pets', models.DO_NOTHING)
    vet = models.ForeignKey('Veterinarians', models.DO_NOTHING, blank=True, null=True)
    visit_date = models.DateField(blank=True, null=True)
    symptoms = models.TextField(db_collation='Thai_CI_AS', blank=True, null=True)
    diagnosis = models.TextField(db_collation='Thai_CI_AS', blank=True, null=True)
    treatment = models.TextField(db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Medical_Records'


class MedicineStock(models.Model):
    stock_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    medicine = models.ForeignKey('Medicines', models.DO_NOTHING)
    quantity = models.IntegerField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Medicine_Stock'


class MedicineStockTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    medicine_id = models.CharField(max_length=6, db_collation='Thai_CI_AS')
    transaction_date = models.DateTimeField(auto_now_add=True)
    quantity_change = models.IntegerField()
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Medicine_Stock_Transaction'


class Medicines(models.Model):
    medicine_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    supplier = models.ForeignKey('Suppliers', models.DO_NOTHING)
    medicine_name = models.CharField(max_length=100, db_collation='Thai_CI_AS')
    type = models.CharField(max_length=50, db_collation='Thai_CI_AS', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Medicines'


class POSTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    bill_id = models.CharField(max_length=6, db_collation='Thai_CI_AS', blank=True, null=True)
    customer = models.ForeignKey('Owners', models.DO_NOTHING)
    medicine = models.ForeignKey('Medicines', models.DO_NOTHING)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'POS_Transaction'


class Owners(models.Model):
    owner_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    first_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    last_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    phone = models.CharField(max_length=15, db_collation='Thai_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=100, db_collation='Thai_CI_AS', blank=True, null=True)
    address = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Owners'


class PaymentMethod(models.Model):
    payment_method_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    method_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    description = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Payment_Method'


class PetAllergies(models.Model):
    allergy_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    pet = models.ForeignKey('Pets', models.DO_NOTHING)
    allergy_detail = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)
    note = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Pet_Allergies'


class Pets(models.Model):
    pet_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    owner = models.ForeignKey(Owners, models.DO_NOTHING)
    species = models.ForeignKey('Species', models.DO_NOTHING)
    pet_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    breed = models.CharField(max_length=50, db_collation='Thai_CI_AS', blank=True, null=True)
    gender = models.CharField(max_length=10, db_collation='Thai_CI_AS', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Pets'


class Species(models.Model):
    species_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    species_name = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    description = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Species'


class Staff(models.Model):
    staff_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    staff_name = models.CharField(max_length=100, db_collation='Thai_CI_AS')
    position = models.CharField(max_length=50, db_collation='Thai_CI_AS', blank=True, null=True)
    phone = models.CharField(max_length=15, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Staff'


class Suppliers(models.Model):
    supplier_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    supplier_name = models.CharField(max_length=100, db_collation='Thai_CI_AS')
    contact_name = models.CharField(max_length=100, db_collation='Thai_CI_AS', blank=True, null=True)
    phone = models.CharField(max_length=15, db_collation='Thai_CI_AS', blank=True, null=True)
    address = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=100, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Suppliers'


class Treatments(models.Model):
    treatment_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    record = models.ForeignKey(MedicalRecords, models.DO_NOTHING)
    medicine = models.ForeignKey(Medicines, models.DO_NOTHING)
    quantity = models.IntegerField(blank=True, null=True)
    instruction = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Treatments'


class Users(models.Model):
    user_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    staff = models.ForeignKey(Staff, models.DO_NOTHING)
    username = models.CharField(max_length=50, db_collation='Thai_CI_AS')
    password = models.CharField(max_length=255, db_collation='Thai_CI_AS')
    role = models.CharField(max_length=50, db_collation='Thai_CI_AS', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Users'


class Vaccinations(models.Model):
    vaccination_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    pet = models.ForeignKey(Pets, models.DO_NOTHING)
    vaccine_name = models.CharField(max_length=100, db_collation='Thai_CI_AS', blank=True, null=True)
    vaccination_date = models.DateField(blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)
    note = models.CharField(max_length=255, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Vaccinations'


class Veterinarians(models.Model):
    vet_id = models.CharField(primary_key=True, max_length=6, db_collation='Thai_CI_AS')
    vet_name = models.CharField(max_length=100, db_collation='Thai_CI_AS')
    specialization = models.CharField(max_length=100, db_collation='Thai_CI_AS', blank=True, null=True)
    phone = models.CharField(max_length=15, db_collation='Thai_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Veterinarians'