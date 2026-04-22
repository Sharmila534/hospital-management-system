from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from ..utils.decorators import roles_required
from bson.objectid import ObjectId
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__, template_folder='../templates')
# ---------------- Dashboard ---------------- #
@doctor_bp.route('/')
@login_required
@roles_required('doctor')
def dashboard():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())
    appts = list(db.appointments.find({'doctor_id': doctor_id}))
    return render_template('doctor/dashboard.html', appointments=appts)

# ---------------- Appointments ---------------- #
@doctor_bp.route('/appointments')
@login_required
@roles_required('doctor')
def appointments():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())
    appts = list(db.appointments.find({'doctor_id': doctor_id}).sort('datetime', 1))
    for a in appts:
        # convert _id so template forms/links work
        a['_id'] = str(a['_id'])
        # convert patient_id to string for display if it's ObjectId
        pid = a.get('patient_id')
        try:
            # if patient stored as ObjectId, lookup patient doc
            patient_doc = db.patients.find_one({'_id': ObjectId(pid)}) if pid else None
        except Exception:
            patient_doc = None
        if patient_doc:
            a['patient_name'] = patient_doc.get('name')
        else:
            # fallback: if patient_id already string or name missing
            a['patient_name'] = a.get('patient_id')
    return render_template('doctor/appointments.html', appointments=appts)

@doctor_bp.route('/appointments/add', methods=['GET', 'POST'])
@login_required
@roles_required('doctor')
def add_appointment():
    db = current_app.db
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        dt = request.form['datetime']
        notes = request.form.get('notes', '')

        try:
            appt_dt = datetime.fromisoformat(dt)
        except Exception:
            appt_dt = datetime.strptime(dt.replace("T", " "), "%Y-%m-%d %H:%M")

        db.appointments.insert_one({
            'doctor_id': ObjectId(current_user.get_id()),
            'patient_id': ObjectId(patient_id),        # store ObjectId
            'datetime': appt_dt,
            'status': 'Scheduled',
            'notes': notes
        })
        flash('Appointment added successfully ✅', 'success')
        return redirect(url_for('doctor.appointments'))

    return render_template('doctor/add_appointment.html')

@doctor_bp.route('/appointments/delete/<appt_id>', methods=['POST'])
@login_required
@roles_required('doctor')
def delete_appointment(appt_id):
    db = current_app.db
    db.appointments.delete_one({'_id': ObjectId(appt_id), 'doctor_id': ObjectId(current_user.get_id())})
    flash('Appointment deleted ❌', 'info')
    return redirect(url_for('doctor.appointments'))

# ---------------- Patients ---------------- #
@doctor_bp.route('/patients')
@login_required
@roles_required('doctor')
def patients():
    db = current_app.db
    doctor_name = getattr(current_user, 'username', getattr(current_user, 'name', ''))
    patients = list(db.patients.find({'assigned_doctor': doctor_name}))

    # Convert ObjectId -> string and provide a stable 'id' property used in templates
    for p in patients:
        # keep original _id string for debugging; ensure template-friendly id
        p['_id'] = str(p['_id'])
        p['id'] = p['_id']               # <--- add this line: templates will use patient.id

    return render_template('doctor/patients.html', patients=patients)

@doctor_bp.route('/patients/add', methods=['GET', 'POST'])
@login_required
@roles_required('doctor')
def add_patient():
    db = current_app.db
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        condition = request.form['condition']

        db.patients.insert_one({
            'name': name,
            'age': age,
            'condition': condition,
            'assigned_doctor': current_user.username
        })
        flash('Patient added successfully ✅', 'success')
        return redirect(url_for('doctor.patients'))

    return render_template('doctor/add_patient.html')

@doctor_bp.route('/patients/delete/<patient_id>', methods=['POST'])
@login_required
@roles_required('doctor')
def delete_patient(patient_id):
    db = current_app.db
    db.patients.delete_one({'_id': ObjectId(patient_id), 'assigned_doctor': current_user.username})
    flash('Patient deleted ❌', 'info')
    return redirect(url_for('doctor.patients'))

# ---------------- Profile ---------------- #
@doctor_bp.route('/profile', methods=['GET','POST'])
@login_required
@roles_required('doctor')
def profile():
    db = current_app.db
    if request.method == 'POST':
        profile_data = dict(request.form)
        db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'profile': profile_data}})
        flash('Profile updated ✅', 'success')

    user = db.users.find_one({'_id': ObjectId(current_user.get_id())}, {'password':0})
    return render_template('doctor/profile.html', user=user)

# ---------------- Salary ---------------- #
@doctor_bp.route('/salary')
@login_required
@roles_required('doctor')
def salary():
    db = current_app.db
    doctor = db.users.find_one({'_id': ObjectId(current_user.get_id())})
    salary = doctor.get('salary', 'Not set')
    return render_template('doctor/salary.html', salary=salary)

# ---------------- Prescriptions ---------------- #
@doctor_bp.route('/prescribe/<patient_id>', methods=['GET', 'POST'])
@login_required
@roles_required('doctor')
def prescribe(patient_id):
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())

    # Find the patient
    patient = db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        flash("Patient not found ❌", "danger")
        return redirect(url_for('doctor.patients'))

    # Handle form submission
    if request.method == 'POST':
        details = request.form.get('details')
        date = datetime.utcnow()

        # Insert into prescriptions collection
        db.prescriptions.insert_one({
            'doctor_id': doctor_id,
            'doctor_name': getattr(current_user, 'username', getattr(current_user, 'name', '')),
            'patient_id': ObjectId(patient_id),
            'patient_name': patient.get('name', ''),
            'details': details,
            'date': date
        })

        flash("Prescription added successfully ✅", "success")
        return redirect(url_for('doctor.patients'))

    return render_template('doctor/prescribe.html', patient=patient)


# ---------------- View Precriptions ---------------- #
@doctor_bp.route('/prescriptions')
@login_required
@roles_required('doctor')
def view_prescriptions():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())

    prescriptions = list(db.prescriptions.find({'doctor_id': doctor_id}).sort('date', -1))
    for p in prescriptions:
        p['_id'] = str(p['_id'])
        # convert patient_id for display
        try:
            p['patient_name'] = db.patients.find_one({'_id': ObjectId(p['patient_id'])}).get('name')
        except Exception:
            pass

    return render_template('doctor/prescriptions.html', prescriptions=prescriptions)



# ---------------- Logout ---------------- #
@doctor_bp.route('/logout')
@login_required
@roles_required('doctor')
def logout():
    logout_user()
    flash("You have been logged out 👋", "info")
    return redirect(url_for('auth.login'))
