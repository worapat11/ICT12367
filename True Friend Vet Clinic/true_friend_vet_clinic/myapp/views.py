from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q, Count
from .models import Bills, Owners, Pets, Appointments, Treatments, Veterinarians, Species, MedicalRecords, Medicines, MedicineStock, PaymentMethod, AppointmentStatus, Suppliers, MedicineStockTransaction, POSTransaction
from datetime import date
from dateutil.relativedelta import relativedelta
import uuid
import os
from django.conf import settings


def get_next_id(model, field_name, prefix, width=3):
    latest = model.objects.filter(**{f"{field_name}__startswith": prefix}).order_by(f"-{field_name}").first()
    if not latest:
        num = 1
    else:
        current = getattr(latest, field_name) or ""
        try:
            num = int(current.replace(prefix, "")) + 1
        except Exception:
            num = 1
    return f"{prefix}{num:0{width}d}"


def get_next_bill_id(prefix='B', width=3):
    latest_bill = Bills.objects.filter(bill_id__startswith=prefix).order_by('-bill_id').first()
    latest_pos_bill = POSTransaction.objects.filter(bill_id__startswith=prefix).order_by('-bill_id').first()

    candidates = []
    if latest_bill:
        candidates.append(latest_bill.bill_id)
    if latest_pos_bill:
        candidates.append(latest_pos_bill.bill_id)

    if not candidates:
        num = 1
    else:
        latest = max(candidates)
        try:
            num = int(latest.replace(prefix, '')) + 1
        except Exception:
            num = 1

    return f"{prefix}{num:0{width}d}"


def reconcile_stock_from_transactions():
    # Sync MedicineStock quantity with sum of MedicineStockTransaction
    tx_sums = MedicineStockTransaction.objects.values('medicine_id').annotate(total=Sum('quantity_change'))
    for row in tx_sums:
        med_id = row['medicine_id']
        qty = row['total'] or 0
        stock = MedicineStock.objects.filter(medicine_id=med_id).first()
        if stock:
            if stock.quantity != qty:
                stock.quantity = qty
                stock.save()
        else:
            MedicineStock.objects.create(
                stock_id=str(uuid.uuid4())[:6],
                medicine_id=med_id,
                quantity=qty
            )


def dashboard(request):
    total_revenue = Bills.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    # Show only active scheduled appointments (not completed/cancelled)
    scheduled = Appointments.objects.filter(status__status_name='Scheduled').count()
    active_appointments = Appointments.objects.exclude(status__status_name__in=['Completed', 'Cancelled']).count()
    completed = Appointments.objects.filter(status__status_name='Completed').count()
    cancelled = Appointments.objects.filter(status__status_name='Cancelled').count()

    # Most used medicines (shifted from report to dashboard as requested)
    most_used = Treatments.objects.values('medicine__medicine_name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    # Stock summary for dashboard
    stock_rows = MedicineStock.objects.select_related('medicine').all()
    total_stock = stock_rows.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0
    low_count = stock_rows.filter(quantity__lt=10).count()
    ok_count = stock_rows.filter(quantity__gte=10).count()

    return render(request, 'dashboard.html', {
        'total_owners': Owners.objects.count(),
        'total_pet': Pets.objects.count(),
        'scheduled_appointments': scheduled,
        'active_appointments': active_appointments,
        'completed_appointments': completed,
        'cancelled_appointments': cancelled,
        'total_revenue': total_revenue,
        'most_used': most_used,
        'total_stock': total_stock,
        'stock_low_count': low_count,
        'stock_ok_count': ok_count,
    })


# OWNER
def owner_list(request):
    q = request.GET.get('q')
    if q:
        owners = Owners.objects.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q) |
            Q(address__icontains=q)
        )
    else:
        owners = Owners.objects.all()
    return render(request, 'owners.html', {'owners': owners, 'q': q})


def add_owner(request):
    if request.method == 'POST':
        Owners.objects.create(
            owner_id=get_next_id(Owners, 'owner_id', 'OWN'),
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address')
        )
        return redirect('owner_list')
    return render(request, 'add_owner.html')


def edit_owner(request, id):
    owner = get_object_or_404(Owners, pk=id)
    if request.method == 'POST':
        owner.first_name = request.POST.get('first_name')
        owner.last_name = request.POST.get('last_name')
        owner.phone = request.POST.get('phone')
        owner.email = request.POST.get('email')
        owner.address = request.POST.get('address')
        owner.save()
        return redirect('owner_list')
    return render(request, 'edit_owner.html', {'owner': owner})


def delete_owner(request, id):
    get_object_or_404(Owners, pk=id).delete()
    return redirect('owner_list')


# PET
def get_pet_image_url(pet_id):
    image_dir = os.path.join(settings.MEDIA_ROOT, 'pet_images')
    if not os.path.exists(image_dir):
        return None
    for ext in ['.jpg', '.jpeg', '.png', '.gif']:
        candidate = os.path.join(image_dir, f"{pet_id}{ext}")
        if os.path.exists(candidate):
            return settings.MEDIA_URL + f"pet_images/{pet_id}{ext}"
    return None


def save_pet_image(pet_id, uploaded_file):
    image_dir = os.path.join(settings.MEDIA_ROOT, 'pet_images')
    os.makedirs(image_dir, exist_ok=True)
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        ext = '.jpg'
    filename = f"{pet_id}{ext}"
    path = os.path.join(image_dir, filename)
    with open(path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return f"{settings.MEDIA_URL}pet_images/{filename}"


def pet_list(request):
    q = request.GET.get('q')
    pets = Pets.objects.select_related('owner', 'species')
    if q:
        pets = pets.filter(
            Q(pet_id__icontains=q) |
            Q(pet_name__icontains=q) |
            Q(owner__first_name__icontains=q) |
            Q(owner__last_name__icontains=q) |
            Q(species__species_name__icontains=q) |
            Q(breed__icontains=q) |
            Q(gender__icontains=q) |
            Q(weight__icontains=q)
        )
    pets = pets.all()
    pet_rows = []
    for pet in pets:
        age_year = age_month = None
        if pet.birth_date:
            diff = relativedelta(date.today(), pet.birth_date)
            age_year = diff.years
            age_month = diff.months
        pet_rows.append({
            'pet': pet,
            'age_year': age_year,
            'age_month': age_month,
            'image_url': get_pet_image_url(pet.pet_id)
        })
    return render(request, 'pet.html', {
        'pet': pet_rows,
        'q': q
    })


def add_pet(request):
    owners = Owners.objects.all()
    species = Species.objects.all()

    if request.method == "POST":
        age_year = int(request.POST.get('age_year') or 0)
        age_month = int(request.POST.get('age_month') or 0)
        birth_date = date.today() - relativedelta(years=age_year, months=age_month)
        owner_id = request.POST.get('owner')
        species_id = request.POST.get('species')

        if not owner_id or not species_id:
            error = "Owner and species are required."
            years = list(range(0, 25))
            months = list(range(0, 12))
            return render(request, 'add_pet.html', {
                'owners': owners,
                'species': species,
                'years': years,
                'months': months,
                'error': error
            })

        try:
            owner = Owners.objects.get(owner_id=owner_id)
            species_obj = Species.objects.get(species_id=species_id)
        except (Owners.DoesNotExist, Species.DoesNotExist):
            error = "Selected owner or species does not exist."
            years = list(range(0, 25))
            months = list(range(0, 12))
            return render(request, 'add_pet.html', {
                'owners': owners,
                'species': species,
                'years': years,
                'months': months,
                'error': error
            })

        pet = Pets.objects.create(
            pet_id=get_next_id(Pets, 'pet_id', 'PET'),
            owner=owner,
            species=species_obj,
            pet_name=request.POST.get('pet_name'),
            breed=request.POST.get('breed'),
            gender=request.POST.get('gender'),
            birth_date=birth_date,
            weight=request.POST.get('weight')
        )
        if 'pet_image' in request.FILES:
            save_pet_image(pet.pet_id, request.FILES['pet_image'])
        return redirect('pet_list')

    years = list(range(0, 25))
    months = list(range(0, 12))
    return render(request, 'add_pet.html', {'owners': owners, 'species': species, 'years': years, 'months': months})


def edit_pet(request, id):
    pet = get_object_or_404(Pets, pk=id)
    owners = Owners.objects.all()
    species = Species.objects.all()

    if request.method == "POST":
        age_year = int(request.POST.get('age_year') or 0)
        age_month = int(request.POST.get('age_month') or 0)
        birth_date = date.today() - relativedelta(years=age_year, months=age_month)

        owner_id = request.POST.get('owner')
        species_id = request.POST.get('species')

        if not owner_id or not species_id:
            error = "Owner and species are required."
            years = list(range(0, 25))
            months = list(range(0, 12))
            return render(request, 'edit_pet.html', {
                'pet': pet,
                'owners': owners,
                'species': species,
                'years': years,
                'months': months,
                'age_year': age_year,
                'age_month': age_month,
                'error': error
            })

        try:
            owner = Owners.objects.get(owner_id=owner_id)
            species_obj = Species.objects.get(species_id=species_id)
        except (Owners.DoesNotExist, Species.DoesNotExist):
            error = "Selected owner or species does not exist."
            years = list(range(0, 25))
            months = list(range(0, 12))
            return render(request, 'edit_pet.html', {
                'pet': pet,
                'owners': owners,
                'species': species,
                'years': years,
                'months': months,
                'age_year': age_year,
                'age_month': age_month,
                'error': error
            })

        pet.owner = owner
        pet.species = species_obj
        pet.pet_name = request.POST.get('pet_name')
        pet.breed = request.POST.get('breed')
        pet.gender = request.POST.get('gender')
        pet.birth_date = birth_date
        pet.weight = request.POST.get('weight')
        pet.save()
        if 'pet_image' in request.FILES:
            save_pet_image(pet.pet_id, request.FILES['pet_image'])
        return redirect('pet_list')

    years = list(range(0, 25))
    months = list(range(0, 12))
    age_year = 0
    age_month = 0
    if pet.birth_date:
        diff = relativedelta(date.today(), pet.birth_date)
        age_year = diff.years
        age_month = diff.months
    return render(request, 'edit_pet.html', {
        'pet': pet,
        'owners': owners,
        'species': species,
        'years': years,
        'months': months,
        'age_year': age_year,
        'age_month': age_month,
        'image_url': get_pet_image_url(pet.pet_id)
    })


def delete_pet(request, id):
    get_object_or_404(Pets, pk=id).delete()
    return redirect('pet_list')


# APPOINTMENT
def appointment_list(request):
    q = request.GET.get('q')
    appointments = Appointments.objects.select_related('pet', 'vet', 'status')
    if q:
        appointments = appointments.filter(
            Q(appointment_id__icontains=q) |
            Q(pet__pet_name__icontains=q) |
            Q(vet__vet_name__icontains=q) |
            Q(status__status_name__icontains=q) |
            Q(reason__icontains=q)
        )
    return render(request, 'appointments.html', {
        'appointments': appointments,
        'q': q
    })


def add_appointment(request):
    if request.method == "POST":
        Appointments.objects.create(
            appointment_id=get_next_id(Appointments, 'appointment_id', 'APT'),
            pet_id=request.POST.get('pet'),
            vet_id=request.POST.get('veterinarian'),
            status_id=request.POST.get('status'),
            appointment_date=request.POST.get('appointment_date'),
            appointment_time=request.POST.get('appointment_time'),
            reason=request.POST.get('reason')
        )
        return redirect('appointment_list')

    return render(request, 'add_appointment.html', {
        'pet': Pets.objects.all(),
        'vets': Veterinarians.objects.all(),
        'statuses': AppointmentStatus.objects.all()
    })


def edit_appointment(request, id):
    appointment = get_object_or_404(Appointments, pk=id)

    if request.method == "POST":
        appointment.pet_id = request.POST.get('pet')
        appointment.vet_id = request.POST.get('veterinarian')
        appointment.status_id = request.POST.get('status')
        appointment.appointment_date = request.POST.get('appointment_date')
        appointment.appointment_time = request.POST.get('appointment_time')
        appointment.reason = request.POST.get('reason')
        appointment.save()
        return redirect('appointment_list')

    return render(request, 'edit_appointment.html', {
        'appointment': appointment,
        'pet': Pets.objects.all(),
        'vets': Veterinarians.objects.all(),
        'statuses': AppointmentStatus.objects.all()
    })


def delete_appointment(request, id):
    get_object_or_404(Appointments, pk=id).delete()
    return redirect('appointment_list')


# MEDICAL
def medical_records(request):
    q = request.GET.get('q')
    pet_id = request.GET.get('pet')
    records = MedicalRecords.objects.select_related('pet', 'vet')
    if pet_id:
        records = records.filter(pet_id=pet_id)
    if q:
        records = records.filter(
            Q(record_id__icontains=q) |
            Q(pet__pet_name__icontains=q) |
            Q(vet__vet_name__icontains=q) |
            Q(symptoms__icontains=q) |
            Q(diagnosis__icontains=q) |
            Q(treatment__icontains=q)
        )
    bills = {b.record_id: b for b in Bills.objects.select_related('record').all()}
    return render(request, 'medical_records.html', {
        'records': records,
        'bills': bills,
        'q': q,
        'pet_id': pet_id
    })


def add_medical_record(request):
    error = None
    if request.method == "POST":
        pet_id = request.POST.get('pet')
        vet_id = request.POST.get('veterinarian')
        diagnosis = request.POST.get('diagnosis')
        treatment_text = request.POST.get('treatment')
        medicines = request.POST.getlist('medicine')
        quantities = request.POST.getlist('quantity')

        valid_items = []
        for med_id, qty_str in zip(medicines, quantities):
            if not med_id:
                continue
            try:
                qty = int(qty_str or 0)
            except ValueError:
                qty = 0
            if qty > 0:
                valid_items.append((med_id, qty))

        if not pet_id or not diagnosis or not valid_items:
            error = 'Please fill pet, diagnosis, and at least one medicine/quantity.'
        else:
            record = MedicalRecords.objects.create(
                record_id=get_next_id(MedicalRecords, 'record_id', 'MR'),
                pet_id=pet_id,
                vet_id=vet_id,
                visit_date=request.POST.get('visit_date') or date.today(),
                diagnosis=diagnosis,
                treatment=treatment_text
            )

            total = 0
            for med_id, qty in valid_items:
                med = Medicines.objects.get(pk=med_id)
                stock = MedicineStock.objects.filter(medicine_id=med_id).first()
                if not stock or stock.quantity is None or stock.quantity < qty:
                    record.delete()
                    error = f'Insufficient stock for {med.medicine_name}. Available: {stock.quantity if stock else 0}.'
                    break

                Treatments.objects.create(
                    treatment_id=str(uuid.uuid4())[:6],
                    record=record,
                    medicine=med,
                    quantity=qty
                )
                # deduct stock
                stock.quantity = stock.quantity - qty
                stock.save()
                MedicineStockTransaction.objects.create(
                    medicine_id=med_id,
                    quantity_change=-qty,
                    note=f"Treatment {record.record_id}"
                )
                total += (med.price or 0) * qty

            if not error:
                Bills.objects.create(
                    bill_id=get_next_id(Bills, 'bill_id', 'B', width=5),
                    record=record,
                    total_amount=total,
                    bill_date=date.today()
                )
                return redirect('medical_records')

    return render(request, 'add_medical_record.html', {
        'pet': Pets.objects.all(),
        'vets': Veterinarians.objects.all(),
        'medicines': Medicines.objects.all(),
        'error': error
    })


def edit_medical_record(request, id):
    record = get_object_or_404(MedicalRecords, pk=id)
    error = None

    if request.method == "POST":
        record.pet_id = request.POST.get('pet')
        record.vet_id = request.POST.get('veterinarian')
        record.diagnosis = request.POST.get('diagnosis')
        record.treatment = request.POST.get('treatment')
        record.save()

        med_id = request.POST.get('medicine')
        qty = int(request.POST.get('quantity') or 0)
        if med_id and qty > 0:
            med = Medicines.objects.get(pk=med_id)
            stock = MedicineStock.objects.filter(medicine_id=med_id).first()
            if not stock or stock.quantity is None or stock.quantity < qty:
                error = f'Insufficient stock for {med.medicine_name}. Available: {stock.quantity if stock else 0}.'
            else:
                treatment = Treatments.objects.filter(record=record, medicine=med).first()
                if treatment:
                    treatment.quantity += qty
                    treatment.save()
                else:
                    Treatments.objects.create(
                        treatment_id=str(uuid.uuid4())[:6],
                        record=record,
                        medicine=med,
                        quantity=qty
                    )
                stock.quantity -= qty
                stock.save()
                MedicineStockTransaction.objects.create(
                    medicine_id=med_id,
                    quantity_change=-qty,
                    note=f"Treatment update {record.record_id}"
                )

        # recalc bill total
        treatments = Treatments.objects.filter(record=record).select_related('medicine')
        total = sum((t.quantity or 0) * (t.medicine.price or 0) for t in treatments)
        bill = Bills.objects.filter(record=record).first()
        if bill:
            bill.total_amount = total
            bill.save()
        else:
            bill = Bills.objects.create(
                bill_id=get_next_id(Bills, 'bill_id', 'B', width=5),
                record=record,
                total_amount=total,
                bill_date=date.today()
            )

        if not error:
            return redirect('medical_records')

    bill = Bills.objects.filter(record=record).first()
    treatments = Treatments.objects.filter(record=record).select_related('medicine')
    return render(request, 'edit_medical_record.html', {
        'record': record,
        'pet': Pets.objects.all(),
        'vets': Veterinarians.objects.all(),
        'medicines': Medicines.objects.all(),
        'bill': bill,
        'treatments': treatments,
        'error': error
    })


def remove_treatment(request, id, treatment_id):
    record = get_object_or_404(MedicalRecords, pk=id)
    treatment = get_object_or_404(Treatments, pk=treatment_id, record=record)
    stock = MedicineStock.objects.filter(medicine_id=treatment.medicine_id).first()
    if stock:
        stock.quantity = (stock.quantity or 0) + (treatment.quantity or 0)
        stock.save()
        MedicineStockTransaction.objects.create(
            medicine_id=treatment.medicine_id,
            quantity_change=treatment.quantity,
            note=f"Treatment removed {record.record_id}"
        )
    treatment.delete()

    treatments = Treatments.objects.filter(record=record).select_related('medicine')
    total = sum((t.quantity or 0) * (t.medicine.price or 0) for t in treatments)
    bill = Bills.objects.filter(record=record).first()
    if bill:
        bill.total_amount = total
        bill.save()
    return redirect('edit_medical_record', id=record.record_id)


def delete_medical_record(request, id):
    record = get_object_or_404(MedicalRecords, pk=id)

    # คืนสต็อกจากทรีตเมนต์และ log transaction
    treatments = Treatments.objects.filter(record=record).select_related('medicine')
    for t in treatments:
        stock = MedicineStock.objects.filter(medicine_id=t.medicine_id).first()
        if stock:
            stock.quantity = (stock.quantity or 0) + (t.quantity or 0)
            stock.save()
        MedicineStockTransaction.objects.create(
            medicine_id=t.medicine_id,
            quantity_change=(t.quantity or 0),
            note=f"Delete Medical Record {record.record_id}"
        )

    # ลบ Bills ก่อน
    Bills.objects.filter(record=record).delete()

    # ลบ Treatments ก่อน
    treatments.delete()

    # แล้วค่อยลบ record
    record.delete()

    return redirect('medical_records')


def pos(request):
    # POS cart state in session
    cart = request.session.get('pos_cart', [])
    selected_customer_id = request.session.get('pos_customer_id')
    message = ''
    error = ''

    owners = Owners.objects.all()
    medicines = Medicines.objects.select_related('supplier').filter(type='อาหารสัตว์')

    if request.method == 'POST':
        action = request.POST.get('action')

        # Add an item to cart
        if action == 'add_item':
            selected_customer_id = request.POST.get('customer') or selected_customer_id
            medicine_id = request.POST.get('medicine')
            qty = int(request.POST.get('quantity') or 0)

            if not selected_customer_id:
                error = 'กรุณาเลือกลูกค้าก่อนเพิ่มรายการ'
            elif not medicine_id or qty <= 0:
                error = 'กรุณาเลือกอาหารสัตว์และจำนวนอย่างน้อย 1'
            else:
                try:
                    med = Medicines.objects.get(pk=medicine_id)
                    stock = MedicineStock.objects.filter(medicine_id=medicine_id).first()
                    if not stock or (stock.quantity or 0) < qty:
                        error = f'สต็อกไม่พอสำหรับ {med.medicine_name} (คงเหลือ {stock.quantity if stock else 0})'
                    else:
                        # add or update cart
                        item = next((i for i in cart if i['medicine_id'] == medicine_id), None)
                        if item:
                            item['quantity'] += qty
                            item['subtotal'] = float(item['quantity']) * float(med.price or 0)
                        else:
                            cart.append({
                                'medicine_id': medicine_id,
                                'medicine_name': med.medicine_name,
                                'unit_price': float(med.price or 0),
                                'quantity': qty,
                                'subtotal': float(qty) * float(med.price or 0)
                            })
                        request.session['pos_cart'] = cart
                        request.session['pos_customer_id'] = selected_customer_id
                        message = f'เพิ่ม {med.medicine_name} ({qty}) เรียบร้อยแล้ว'
                except Medicines.DoesNotExist:
                    error = 'ไม่พบรายการอาหารสัตว์'

        # Remove line item
        elif action == 'remove_item':
            item_id = request.POST.get('medicine_id')
            cart = [i for i in cart if i['medicine_id'] != item_id]
            request.session['pos_cart'] = cart
            message = 'ลบรายการสินค้าเรียบร้อยแล้ว'

        # Checkout and create POS transactions
        elif action == 'checkout':
            selected_customer_id = request.POST.get('customer') or selected_customer_id
            if not selected_customer_id:
                error = 'กรุณาเลือกลูกค้าก่อนชำระเงิน'
            elif not cart:
                error = 'ไม่มีรายการสินค้าในรถเข็น'
            else:
                try:
                    customer_id = selected_customer_id
                    total_amount = 0
                    
                    # Generate bill number from both Bills + POSBills (จะไม่ซ้ำอีก)
                    bill_id = get_next_bill_id('B')

                    total_amount = 0
                    for item in cart:
                        med = Medicines.objects.get(pk=item['medicine_id'])
                        qty = int(item['quantity'])
                        unit_price = float(item['unit_price'])
                        subtotal = unit_price * qty

                        if qty <= 0:
                            continue

                        # stock check
                        stock = MedicineStock.objects.filter(medicine_id=med.medicine_id).first()
                        if not stock or (stock.quantity or 0) < qty:
                            error = f'สต็อกไม่พอสำหรับ {med.medicine_name} (คงเหลือ {stock.quantity if stock else 0})'
                            break

                        # Create POS transaction with bill_id
                        POSTransaction.objects.create(
                            bill_id=bill_id,
                            customer_id=customer_id,
                            medicine_id=med.medicine_id,
                            quantity=qty,
                            unit_price=unit_price,
                            total_amount=subtotal
                        )

                        # Update stock
                        stock.quantity = (stock.quantity or 0) - qty
                        stock.save()
                        
                        # Create stock transaction record
                        MedicineStockTransaction.objects.create(
                            medicine_id=med.medicine_id,
                            quantity_change=-qty,
                            note=f'POS Sale to customer {customer_id} (Bill {bill_id})'
                        )

                        total_amount += subtotal

                    if not error:
                        pre_vat = round(total_amount, 2)
                        vat_amount = round(pre_vat * 0.07, 2)
                        total_with_vat = round(pre_vat + vat_amount, 2)

                        request.session['pos_cart'] = []
                        request.session['pos_customer_id'] = None
                        message = f'บันทึกการขายสำเร็จ บิล {bill_id} ยอดรวมก่อน VAT {pre_vat:.2f} VAT {vat_amount:.2f} รวม {total_with_vat:.2f} บาท'
                        
                        # redirect to receipt page immediately
                        return redirect('pos_receipt', bill_id=bill_id)

                except Owners.DoesNotExist:
                    error = 'ลูกค้าที่เลือกไม่มีอยู่'

    total = round(sum(i['subtotal'] for i in cart), 2)

    # Get POS receipts grouped by bill_id
    pos_transactions = POSTransaction.objects.select_related('customer').order_by('-transaction_date')
    
    # Group transactions by bill_id and get summary
    from collections import defaultdict
    bill_groups = defaultdict(lambda: {'bill_id': None, 'customer_name': '', 'item_count': 0, 'total_amount': 0.0})
    
    for tx in pos_transactions:
        bill_id = tx.bill_id
        if bill_id not in bill_groups:
            customer = tx.customer
            customer_name = f'{customer.first_name} {customer.last_name}' if customer else 'ไม่ทราบ'
            bill_groups[bill_id] = {
                'bill_id': bill_id,
                'customer_name': customer_name,
                'item_count': 0,
                'total_amount': 0.0
            }
        bill_groups[bill_id]['item_count'] += tx.quantity
        bill_groups[bill_id]['total_amount'] += float(tx.total_amount or 0)
    
    pos_receipts = list(bill_groups.values())[:10]  # Get latest 10 bills
    latest_receipt = pos_receipts[0] if pos_receipts else None

    return render(request, 'pos.html', {
        'owners': owners,
        'medicines': medicines,
        'cart': cart,
        'selected_customer_id': selected_customer_id,
        'total': total,
        'message': message,
        'error': error,
        'pos_receipts': pos_receipts,
        'latest_receipt': latest_receipt,
    })


def bill_detail(request, id):
    bill = get_object_or_404(Bills, pk=id)
    record = bill.record
    pet = record.pet
    owner = pet.owner
    treatments_qs = Treatments.objects.filter(record=record).select_related('medicine')
    treatments = []
    total_calc = 0
    total_items = 0
    for t in treatments_qs:
        subtotal = (t.quantity or 0) * (t.medicine.price or 0)
        treatments.append({
            'medicine': t.medicine,
            'quantity': t.quantity,
            'unit_price': t.medicine.price,
            'subtotal': subtotal
        })
        total_calc += subtotal
        total_items += (t.quantity or 0)
    
    pre_vat = float(total_calc)
    vat = round(pre_vat * 0.07, 2)
    total_with_vat = round(pre_vat + vat, 2)
    
    return render(request, 'bill_detail.html', {
        'bill': bill,
        'pet': pet,
        'owner': owner,
        'treatments': treatments,
        'total': total_with_vat,
        'pre_vat': pre_vat,
        'vat': vat,
        'total_items': total_items
    })


def pay_bill(request, id):
    bill = get_object_or_404(Bills, pk=id)
    method_names = ['เงินสด', 'QR code']
    error = None
    
    # Calculate pre-VAT and VAT
    pre_vat = float(bill.total_amount or 0)
    vat = round(pre_vat * 0.07, 2)

    if request.method == 'POST':
        method_name = request.POST.get('payment_method')
        paid_amount = request.POST.get('paid_amount')
        bill_date = request.POST.get('payment_date')

        if not method_name:
            error = 'Please select a payment method.'
        elif method_name not in method_names:
            error = 'Payment method invalid.'
        elif not paid_amount:
            error = 'Please enter paid amount.'
        else:
            # Get payment method by name; if missing create fallback id
            method, _ = PaymentMethod.objects.get_or_create(
                method_name=method_name,
                defaults={'payment_method_id': get_next_id(PaymentMethod, 'payment_method_id', 'PM')}
            )

        qr_image = request.POST.get('qr_image', '').strip()
        if not error:
            bill.payment_method = method
            bill.total_amount = float(paid_amount)
            bill.bill_date = bill_date or bill.bill_date or date.today()
            bill.save()
            return redirect('paid_bill', id=bill.bill_id)

    else:
        qr_image = ''

    return render(request, 'pay_bill.html', {
        'bill': bill,
        'method_names': method_names,
        'error': error,
        'qr_image': qr_image,
        'pre_vat': pre_vat,
        'vat': vat
    })


def paid_bill(request, id):
    bill = get_object_or_404(Bills, pk=id)
    if not bill.payment_method:
        return redirect('bill_detail', id=bill.bill_id)

    record = bill.record
    pet = record.pet
    owner = pet.owner
    treatment_qs = Treatments.objects.filter(record=record).select_related('medicine')
    treatments = []
    total = 0
    for t in treatment_qs:
        subtotal = (t.quantity or 0) * (t.medicine.price or 0)
        treatments.append({'medicine': t.medicine, 'quantity': t.quantity, 'unit_price': t.medicine.price, 'subtotal': subtotal})
        total += subtotal

    return render(request, 'paid_bill.html', {
        'bill': bill,
        'pet': pet,
        'owner': owner,
        'treatments': treatments,
        'total': total
    })


def paid_bills(request):
    bills = Bills.objects.filter(payment_method__isnull=False).select_related('record__pet__owner', 'payment_method')
    return render(request, 'paid_bills.html', {
        'bills': bills
    })


def unpaid_bills(request):
    bills = Bills.objects.filter(payment_method__isnull=True).select_related('record__pet__owner')
    return render(request, 'unpaid_bills.html', {
        'bills': bills
    })



# MEDICINE
def medicines(request):
    q = request.GET.get('q')
    med_data = Medicines.objects.select_related('supplier')
    if q:
        med_data = med_data.filter(
            Q(medicine_id__icontains=q) |
            Q(medicine_name__icontains=q) |
            Q(type__icontains=q) |
            Q(supplier__supplier_name__icontains=q)
        )
    med_data = med_data.all()
    stock = MedicineStock.objects.select_related('medicine')
    stock_by_med = {s.medicine_id: s for s in stock}
    medicines = []
    for m in med_data:
        s = stock_by_med.get(m.medicine_id)
        medicines.append({
            'medicine': m,
            'stock': s.quantity if s else 0,
            'is_low': (s.quantity if s else 0) < 10
        })
    return render(request, 'medicines.html', {
        'medicines': medicines,
        'q': q
    })


def add_medicine(request):
    error = None
    if request.method == "POST":
        supplier_id = request.POST.get('supplier')
        if not supplier_id:
            error = 'Please select supplier.'
        else:
            medicine_id = get_next_id(Medicines, 'medicine_id', 'MED')
            med = Medicines.objects.create(
                medicine_id=medicine_id,
                supplier_id=supplier_id,
                medicine_name=request.POST.get('medicine_name'),
                type=request.POST.get('medicine_type'),
                price=request.POST.get('price')
            )
            stock_qty = int(request.POST.get('stock') or 0)
            if stock_qty > 0:
                MedicineStock.objects.create(
                    stock_id=str(uuid.uuid4())[:6],
                    medicine_id=medicine_id,
                    quantity=stock_qty
                )
                MedicineStockTransaction.objects.create(
                    medicine_id=medicine_id,
                    quantity_change=stock_qty,
                    note=f"Initial stock from add medicine {medicine_id}"
                )
            return redirect('medicines')
    return render(request, 'add_medicine.html', {
        'error': error,
        'suppliers': Suppliers.objects.all()
    })


def edit_medicine(request, id):
    m = get_object_or_404(Medicines, pk=id)
    stock = MedicineStock.objects.filter(medicine_id=m.medicine_id).first()
    error = None
    if request.method == "POST":
        supplier_id = request.POST.get('supplier')
        if not supplier_id:
            error = 'Please select supplier.'
        else:
            m.supplier_id = supplier_id
            m.medicine_name = request.POST.get('medicine_name')
            m.type = request.POST.get('medicine_type')
            m.price = request.POST.get('price')
            m.save()
            stock_qty = int(request.POST.get('stock') or 0)
            if stock:
                old_qty = stock.quantity or 0
                stock.quantity = stock_qty
                stock.save()
                diff = stock_qty - old_qty
                if diff != 0:
                    MedicineStockTransaction.objects.create(
                        medicine_id=m.medicine_id,
                        quantity_change=diff,
                        note=f"Stock adjustment in edit medicine {m.medicine_id}"
                    )
            else:
                MedicineStock.objects.create(
                    stock_id=str(uuid.uuid4())[:6],
                    medicine_id=m.medicine_id,
                    quantity=stock_qty
                )
                if stock_qty != 0:
                    MedicineStockTransaction.objects.create(
                        medicine_id=m.medicine_id,
                        quantity_change=stock_qty,
                        note=f"Stock created in edit medicine {m.medicine_id}"
                    )
            return redirect('medicines')
    return render(request, 'edit_medicine.html', {
        'medicine': m,
        'stock': stock,
        'suppliers': Suppliers.objects.all(),
        'error': error
    })


def delete_medicine(request, id):
    get_object_or_404(Medicines, pk=id).delete()
    return redirect('medicines')


def reports(request):
    return render(request, 'reports.html')


def report_appointments(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    qs = Appointments.objects.select_related('pet', 'status')
    if start_date:
        qs = qs.filter(appointment_date__gte=start_date)
    if end_date:
        qs = qs.filter(appointment_date__lte=end_date)
    if status and status != 'all':
        qs = qs.filter(status__status_name=status)

    total = qs.count()
    scheduled = qs.filter(status__status_name='Scheduled').count()
    completed = qs.filter(status__status_name='Completed').count()
    cancelled = qs.filter(status__status_name='Cancelled').count()
    return render(request, 'report_appointments.html', {
        'appointments': qs.order_by('-appointment_date', '-appointment_time'),
        'total': total,
        'scheduled': scheduled,
        'completed': completed,
        'cancelled': cancelled,
        'start_date': start_date,
        'end_date': end_date,
        'status': status or 'all'
    })


def report_stock_status(request):
    med_data = Medicines.objects.select_related('supplier').all()
    stock_data = MedicineStock.objects.select_related('medicine')
    stock_by_med = {s.medicine_id: s for s in stock_data}
    rows = []
    for med in med_data:
        stock = stock_by_med.get(med.medicine_id)
        qty = stock.quantity if stock else 0
        status = 'Low' if qty < 10 else 'OK'
        rows.append({
            'medicine': med,
            'stock': qty,
            'status': status,
            'supplier': med.supplier
        })
    total_stock = sum(r['stock'] for r in rows)
    low_count = sum(1 for r in rows if r['status'] == 'Low')
    ok_count = sum(1 for r in rows if r['status'] != 'Low')
    return render(request, 'report_stock_status.html', {
        'rows': rows,
        'total_stock': total_stock,
        'low_count': low_count,
        'ok_count': ok_count
    })


def report_stock_ledger(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    medicine_id = request.GET.get('medicine')

    # keep stock and ledger consistent
    reconcile_stock_from_transactions()
    txns = MedicineStockTransaction.objects.all().order_by('-transaction_date')
    if start_date:
        txns = txns.filter(transaction_date__date__gte=start_date)
    if end_date:
        txns = txns.filter(transaction_date__date__lte=end_date)
    if medicine_id:
        txns = txns.filter(medicine_id=medicine_id)

    medicines = Medicines.objects.all()

    ledger = []
    balance_by_med = {}
    total_inbound = 0
    total_outbound = 0
    medicine_names = {m.medicine_id: m.medicine_name for m in medicines}
    for t in txns.order_by('transaction_date'):
        mid = t.medicine_id
        balance_by_med[mid] = balance_by_med.get(mid, 0) + (t.quantity_change or 0)
        inbound = t.quantity_change if t.quantity_change > 0 else 0
        outbound = abs(t.quantity_change) if t.quantity_change < 0 else 0
        total_inbound += inbound
        total_outbound += outbound
        ledger.append({
            'date': t.transaction_date,
            'medicine': medicine_names.get(mid, mid),
            'inbound': inbound,
            'outbound': outbound,
            'balance': balance_by_med[mid],
            'note': t.note
        })

    current_balance_rows = []
    # Reconcile stock values before rendering
    reconcile_stock_from_transactions()
    for stock in MedicineStock.objects.select_related('medicine').all():
        current_balance_rows.append({
            'medicine': stock.medicine.medicine_name,
            'qty': stock.quantity or 0
        })

    return render(request, 'report_stock_ledger.html', {
        'ledger': ledger,
        'medicines': medicines,
        'start_date': start_date,
        'end_date': end_date,
        'medicine_id': medicine_id,
        'current_balance_rows': current_balance_rows,
        'total_inbound': total_inbound,
        'total_outbound': total_outbound
    })


def report_payments(request):
    report_type = request.GET.get('type', 'daily')
    bills = Bills.objects.filter(payment_method__isnull=False)
    if report_type == 'daily':
        bills = bills.filter(bill_date=date.today())
    elif report_type == 'monthly':
        bills = bills.filter(bill_date__year=date.today().year, bill_date__month=date.today().month)
    elif report_type == 'yearly':
        bills = bills.filter(bill_date__year=date.today().year)

    total = bills.aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0
    vat_rate = 0.07
    total_before_vat = float(total) / (1 + vat_rate) if total else 0
    total_vat = float(total) - total_before_vat

    # จำนวนรวมสินค้าที่ขาย
    treat_qs = Treatments.objects.filter(record__bills__in=bills)
    total_item_qty = treat_qs.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
    total_item_price = treat_qs.aggregate(total_price=Sum(F('quantity') * F('medicine__price')))['total_price'] or 0

    return render(request, 'report_payments.html', {
        'report_type': report_type,
        'bills': bills.select_related('record__pet__owner', 'payment_method'),
        'total_amount': total,
        'total_before_vat': total_before_vat,
        'total_vat': total_vat,
        'total_item_qty': total_item_qty,
        'total_item_price': total_item_price,
    })


def report_animals(request):
    total_pets = Pets.objects.count()
    pets_by_species = Pets.objects.values('species__species_name').annotate(count=Count('pet_id')).order_by('-count')
    pets_by_owner = Pets.objects.values('owner__first_name', 'owner__last_name').annotate(count=Count('pet_id')).order_by('-count')[:10]
    return render(request, 'report_animals.html', {
        'total_pets': total_pets,
        'pets_by_species': pets_by_species,
        'pets_by_owner': pets_by_owner,
    })


def report_most_used_medicines(request):
    most_used = Treatments.objects.values('medicine__medicine_name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:20]
    total_qty = sum(item['total_qty'] for item in most_used)
    return render(request, 'report_most_used_medicines.html', {
        'most_used': most_used,
        'total_qty': total_qty
    })


def pos_receipt(request, bill_id):
    transactions = POSTransaction.objects.filter(bill_id=bill_id).order_by('transaction_date')
    if not transactions:
        return render(request, 'pos_receipt.html', {
            'error': f'ไม่พบใบเสร็จ POS ที่มีรหัส {bill_id}'
        })

    customer_name = 'ไม่ทราบ'
    if transactions:
        customer = Owners.objects.filter(owner_id=transactions[0].customer_id).first()
        if customer:
            customer_name = f'{customer.first_name} {customer.last_name}'

    from decimal import Decimal

    pre_vat = sum(t.total_amount for t in transactions)
    vat = (pre_vat * Decimal('0.07')).quantize(Decimal('0.01'))
    total = (pre_vat + vat).quantize(Decimal('0.01'))

    # ใส่ชื่อยาให้บิล POS
    transactions_with_names = []
    for t in transactions:
        med = Medicines.objects.filter(medicine_id=t.medicine_id).first()
        medicine_name = med.medicine_name if med else t.medicine_id
        transactions_with_names.append({
            'transaction_id': t.transaction_id,
            'medicine_name': medicine_name,
            'quantity': t.quantity,
            'unit_price': t.unit_price,
            'total_amount': t.total_amount,
            'transaction_date': t.transaction_date
        })

    return render(request, 'pos_receipt.html', {
        'bill_id': bill_id,
        'transactions': transactions_with_names,
        'customer_name': customer_name,
        'pre_vat': pre_vat,
        'vat_amount': vat,
        'total': total
    })

def pos_receipts_list(request):
    # Get all POS receipts grouped by bill_id
    pos_transactions = POSTransaction.objects.select_related('customer').order_by('-transaction_date')
    
    from collections import defaultdict
    bill_groups = defaultdict(lambda: {'bill_id': None, 'customer_name': '', 'item_count': 0, 'total_amount': 0.0})
    
    for tx in pos_transactions:
        bill_id = tx.bill_id
        if bill_id not in bill_groups:
            customer = tx.customer
            customer_name = f'{customer.first_name} {customer.last_name}' if customer else 'ไม่ทราบ'
            bill_groups[bill_id] = {
                'bill_id': bill_id,
                'customer_name': customer_name,
                'item_count': 0,
                'total_amount': 0.0
            }
        bill_groups[bill_id]['item_count'] += tx.quantity
        bill_groups[bill_id]['total_amount'] += float(tx.total_amount or 0)
    
    pos_receipts = list(bill_groups.values())
    
    return render(request, 'pos_receipts_list.html', {
        'pos_receipts': pos_receipts,
    })

def report_pos(request):
    # Get all POS transactions with customer and medicine names
    pos_transactions = POSTransaction.objects.select_related().order_by('-transaction_date')
    
    # Add customer and medicine names to each transaction
    transactions_with_names = []
    for transaction in pos_transactions:
        try:
            customer = Owners.objects.get(owner_id=transaction.customer_id)
            customer_name = f"{customer.first_name} {customer.last_name}"
        except Owners.DoesNotExist:
            customer_name = f"Customer ID: {transaction.customer_id}"
        
        try:
            medicine = Medicines.objects.get(medicine_id=transaction.medicine_id)
            medicine_name = medicine.medicine_name
        except Medicines.DoesNotExist:
            medicine_name = f"Medicine ID: {transaction.medicine_id}"
        
        transactions_with_names.append({
            'transaction_id': transaction.transaction_id,
            'customer_name': customer_name,
            'medicine_name': medicine_name,
            'quantity': transaction.quantity,
            'unit_price': transaction.unit_price,
            'total_amount': transaction.total_amount,
            'transaction_date': transaction.transaction_date
        })
    
    # Calculate totals
    total_sales = sum(t['total_amount'] for t in transactions_with_names)
    total_quantity = sum(t['quantity'] for t in transactions_with_names)
    
    return render(request, 'report_pos.html', {
        'transactions': transactions_with_names,
        'total_sales': total_sales,
        'total_quantity': total_quantity
    })