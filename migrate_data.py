from app import app, db, User, Patient, MedicalStaff, Appointment, MedicalRecord
from datetime import datetime
from werkzeug.security import generate_password_hash

def migrate_patient_data():
    """Script to migrate existing patient data into the application's schema"""
    with app.app_context():
        print("Starting data migration...")
        
        # Check if we already have migrated data
        existing_patients = Patient.query.count()
        if existing_patients > 1:  # Allow for the test patient
            print(f"Found {existing_patients} patients already in the system. Skipping migration.")
            return
            
        # Create user accounts for the patients with your data
        patients_data = [
            {
                'username': 'kwame_n',
                'email': 'kwame.n@email.com',
                'first_name': 'Kwame',
                'last_name': 'Nkrumah',
                'date_of_birth': '1980-05-15',
                'gender': 'Male',
                'phone': '+233-541-234567',
                'address': '123 Independence Ave, Accra'
            },
            {
                'username': 'amina_s',
                'email': 'amina.s@email.com',
                'first_name': 'Amina',
                'last_name': 'Sow',
                'date_of_birth': '1992-08-22',
                'gender': 'Female',
                'phone': '+233-551-987654',
                'address': '456 Liberation Rd, Kumasi'
            },
            {
                'username': 'tafari_m',
                'email': 'tafari.m@email.com',
                'first_name': 'Tafari',
                'last_name': 'Makonen',
                'date_of_birth': '1975-11-30',
                'gender': 'Male',
                'phone': '+233-561-456789',
                'address': '789 Unity St, Tamale'
            },
            {
                'username': 'zainab_m',
                'email': 'zainab.m@email.com',
                'first_name': 'Zainab',
                'last_name': 'Mensah',
                'date_of_birth': '1988-04-12',
                'gender': 'Female',
                'phone': '+233-571-345678',
                'address': '321 Harmony Blvd, Cape Coast'
            },
            {
                'username': 'kofi_o',
                'email': 'kofi.o@email.com',
                'first_name': 'Kofi',
                'last_name': 'Osei',
                'date_of_birth': '1995-07-08',
                'gender': 'Male',
                'phone': '+233-581-234567',
                'address': '654 Progress Dr, Takoradi'
            }
        ]
        
        # Create staff user accounts
        staff_data = [
            {
                'username': 'dr_addo',
                'email': 'dr.addo@africanhealthhub.com',
                'first_name': 'Abena',
                'last_name': 'Addo',
                'specialization': 'General Medicine',
                'qualification': 'MD, University of Ghana',
                'phone': '+233560123456',
                'years_of_experience': 6
            },
            {
                'username': 'dr_boateng',
                'email': 'dr.boateng@africanhealthhub.com',
                'first_name': 'Kwesi',
                'last_name': 'Boateng',
                'specialization': 'Pediatrics',
                'qualification': 'MD, KNUST',
                'phone': '+233561234567',
                'years_of_experience': 5
            },
            {
                'username': 'nurse_osei',
                'email': 'nurse.osei@africanhealthhub.com',
                'first_name': 'Gifty',
                'last_name': 'Osei',
                'specialization': 'General Nursing',
                'qualification': 'BSN, University of Cape Coast',
                'phone': '+233562345678',
                'years_of_experience': 4
            },
            {
                'username': 'dr_nkrumah',
                'email': 'dr.nkrumah@africanhealthhub.com',
                'first_name': 'Emmanuel',
                'last_name': 'Nkrumah',
                'specialization': 'Cardiology',
                'qualification': 'MD, Johns Hopkins University',
                'phone': '+233563456789',
                'years_of_experience': 7
            },
            {
                'username': 'nurse_asamoah',
                'email': 'nurse.asamoah@africanhealthhub.com',
                'first_name': 'David',
                'last_name': 'Asamoah',
                'specialization': 'Emergency Care',
                'qualification': 'BSN, University of Ghana',
                'phone': '+233564567890',
                'years_of_experience': 3
            }
        ]
        
        created_patients = []
        created_staff = []
        
        # Create patients
        for idx, patient_data in enumerate(patients_data):
            try:
                # Create user account
                user = User(
                    username=patient_data['username'],
                    email=patient_data['email'],
                    role='patient',
                    is_active=True
                )
                # Set a standard password they can change later
                user.set_password(f"{patient_data['username']}123")
                db.session.add(user)
                db.session.commit()
                
                # Create patient profile
                dob = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d').date()
                patient = Patient(
                    user_id=user.id,
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    date_of_birth=dob,
                    gender=patient_data['gender'],
                    phone=patient_data['phone'],
                    email=patient_data['email'],
                    address=patient_data['address']
                )
                db.session.add(patient)
                db.session.commit()
                created_patients.append(patient)
                print(f"Created patient: {patient.first_name} {patient.last_name}")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating patient {patient_data['first_name']} {patient_data['last_name']}: {str(e)}")
        
        # Create staff
        for idx, staff_data in enumerate(staff_data):
            try:
                # Create user account
                user = User(
                    username=staff_data['username'],
                    email=staff_data['email'],
                    role='staff',
                    is_active=True
                )
                # Set a standard password they can change later
                user.set_password(f"{staff_data['username']}123")
                db.session.add(user)
                db.session.commit()
                
                # Create staff profile
                staff = MedicalStaff(
                    user_id=user.id,
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    email=staff_data['email'],
                    phone=staff_data['phone'],
                    specialization=staff_data['specialization'],
                    qualification=staff_data['qualification'],
                    years_of_experience=staff_data['years_of_experience']
                )
                db.session.add(staff)
                db.session.commit()
                created_staff.append(staff)
                print(f"Created staff: Dr. {staff.first_name} {staff.last_name}")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating staff {staff_data['first_name']} {staff_data['last_name']}: {str(e)}")
        
        # Create some appointments and medical records
        if created_patients and created_staff:
            # Appointments
            appointments_data = [
                {
                    'patient_idx': 0,
                    'staff_idx': 0,
                    'appointment_date': '2025-02-20 10:00:00',
                    'appointment_type': 'Annual check-up',
                    'status': 'Completed',
                    'notes': 'Patient reported feeling well'
                },
                {
                    'patient_idx': 1,
                    'staff_idx': 1,
                    'appointment_date': '2025-02-22 14:30:00',
                    'appointment_type': 'Asthma follow-up',
                    'status': 'Completed',
                    'notes': 'Prescription renewed'
                },
                {
                    'patient_idx': 2,
                    'staff_idx': 3,
                    'appointment_date': '2025-02-25 09:15:00',
                    'appointment_type': 'Blood pressure monitoring',
                    'status': 'Completed',
                    'notes': 'BP readings: 140/90'
                },
                {
                    'patient_idx': 3,
                    'staff_idx': 0,
                    'appointment_date': '2025-03-05 11:00:00',
                    'appointment_type': 'Diabetes management',
                    'status': 'Scheduled',
                    'notes': 'Review latest lab results'
                },
                {
                    'patient_idx': 4,
                    'staff_idx': 2,
                    'appointment_date': '2025-03-10 15:45:00',
                    'appointment_type': 'Post-surgery follow-up',
                    'status': 'Scheduled',
                    'notes': 'Evaluate healing progress'
                }
            ]
            
            created_appointments = []
            
            for appt_data in appointments_data:
                try:
                    appointment_date = datetime.strptime(appt_data['appointment_date'], '%Y-%m-%d %H:%M:%S')
                    appointment = Appointment(
                        patient_id=created_patients[appt_data['patient_idx']].id,
                        staff_id=created_staff[appt_data['staff_idx']].id,
                        appointment_date=appointment_date,
                        appointment_type=appt_data['appointment_type'],
                        status=appt_data['status'],
                        notes=appt_data['notes']
                    )
                    db.session.add(appointment)
                    db.session.commit()
                    created_appointments.append(appointment)
                    print(f"Created appointment: {appointment.appointment_type} on {appointment.appointment_date}")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating appointment: {str(e)}")
            
            # Medical Records
            if created_appointments:
                medical_records_data = [
                    {
                        'patient_idx': 0,
                        'staff_idx': 0,
                        'appointment_idx': 0,
                        'diagnosis': 'Healthy, no concerns',
                        'treatment': 'Routine preventive advice',
                        'prescription': 'Vitamin D supplements',
                        'notes': 'Continue annual check-ups'
                    },
                    {
                        'patient_idx': 1,
                        'staff_idx': 1,
                        'appointment_idx': 1,
                        'diagnosis': 'Well-controlled asthma',
                        'treatment': 'Continue current management plan',
                        'prescription': 'Albuterol inhaler as needed',
                        'notes': 'Patient shows good response to therapy'
                    },
                    {
                        'patient_idx': 2,
                        'staff_idx': 3,
                        'appointment_idx': 2,
                        'diagnosis': 'Stage 1 Hypertension',
                        'treatment': 'Diet modification, exercise regimen',
                        'prescription': 'Lisinopril 10mg daily',
                        'notes': 'Schedule follow-up in 1 month'
                    }
                ]
                
                for record_data in medical_records_data:
                    try:
                        record = MedicalRecord(
                            patient_id=created_patients[record_data['patient_idx']].id,
                            staff_id=created_staff[record_data['staff_idx']].id,
                            diagnosis=record_data['diagnosis'],
                            treatment=record_data['treatment'],
                            prescription=record_data['prescription'],
                            notes=record_data['notes'],
                            record_date=datetime.now()
                        )
                        db.session.add(record)
                        db.session.commit()
                        print(f"Created medical record: {record.diagnosis}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error creating medical record: {str(e)}")
        
        print("Data migration completed!")

if __name__ == "__main__":
    migrate_patient_data() 