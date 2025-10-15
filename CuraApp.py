# Combined single file: dental_clinic_app.py
# This includes all components: database, models, functions, reports, and the Streamlit app.
# Run with: streamlit run dental_clinic_app.py
# Fixed DetachedInstanceError by using joinedload for relationships in get_appointments

import streamlit as st
import pandas as pd
import datetime
import os
import io
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Database setup
engine = create_engine('sqlite:///dental_clinic.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Models
class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    address = Column(String)
    medical_history = Column(Text)
    image_path = Column(String)

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)
    phone = Column(String)
    email = Column(String)

class Treatment(Base):
    __tablename__ = 'treatments'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    base_cost = Column(Float)

class TreatmentPercentage(Base):
    __tablename__ = 'treatment_percentages'
    id = Column(Integer, primary_key=True)
    treatment_id = Column(Integer, ForeignKey('treatments.id'))
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    clinic_percentage = Column(Float)  # نسبة العيادة
    doctor_percentage = Column(Float)  # نسبة الطبيب
    treatment = relationship("Treatment")
    doctor = relationship("Doctor")

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    treatment_id = Column(Integer, ForeignKey('treatments.id'))
    date = Column(DateTime)
    status = Column(String)
    notes = Column(Text)
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    treatment = relationship("Treatment")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    total_amount = Column(Float)
    paid_amount = Column(Float)
    clinic_share = Column(Float)
    doctor_share = Column(Float)
    payment_method = Column(String)
    discounts = Column(Float)
    taxes = Column(Float)
    date_paid = Column(DateTime)
    appointment = relationship("Appointment")

Base.metadata.create_all(engine)

# Functions
def add_patient(name, age, gender, phone, address, medical_history, image):
    session = Session()
    patient = Patient(name=name, age=age, gender=gender, phone=phone, address=address, medical_history=medical_history)
    if image:
        image_path = f"images/{name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        os.makedirs('images', exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(image.getvalue())
        patient.image_path = image_path
    session.add(patient)
    session.commit()
    session.close()

def get_patients():
    session = Session()
    patients = session.query(Patient).all()
    session.close()
    return patients

def add_doctor(name, specialty, phone, email):
    session = Session()
    doctor = Doctor(name=name, specialty=specialty, phone=phone, email=email)
    session.add(doctor)
    session.commit()
    session.close()

def get_doctors():
    session = Session()
    doctors = session.query(Doctor).all()
    session.close()
    return doctors

def add_treatment(name, base_cost):
    session = Session()
    treatment = Treatment(name=name, base_cost=base_cost)
    session.add(treatment)
    session.commit()
    session.close()

def get_treatments():
    session = Session()
    treatments = session.query(Treatment).all()
    session.close()
    return treatments

def add_treatment_percentage(treatment_id, doctor_id, clinic_percentage, doctor_percentage):
    session = Session()
    perc = TreatmentPercentage(treatment_id=treatment_id, doctor_id=doctor_id, 
                                clinic_percentage=clinic_percentage, doctor_percentage=doctor_percentage)
    session.add(perc)
    session.commit()
    session.close()

def add_appointment(patient_id, doctor_id, treatment_id, date, status, notes):
    session = Session()
    appointment = Appointment(patient_id=patient_id, doctor_id=doctor_id, treatment_id=treatment_id, 
                              date=date, status=status, notes=notes)
    session.add(appointment)
    session.commit()
    session.close()

def get_appointments():
    session = Session()
    appointments = session.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.doctor),
        joinedload(Appointment.treatment)
    ).all()
    session.close()
    return appointments

def calculate_shares(appointment_id, total_amount, discounts=0, taxes=0):
    session = Session()
    appointment = session.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.doctor),
        joinedload(Appointment.treatment)
    ).get(appointment_id)
    perc = session.query(TreatmentPercentage).filter_by(treatment_id=appointment.treatment_id, doctor_id=appointment.doctor_id).first()
    if not perc:
        clinic_perc = 50.0
        doctor_perc = 50.0
    else:
        clinic_perc = perc.clinic_percentage
        doctor_perc = perc.doctor_percentage
    net_amount = total_amount - discounts + taxes
    clinic_share = net_amount * (clinic_perc / 100)
    doctor_share = net_amount * (doctor_perc / 100)
    session.close()
    return clinic_share, doctor_share

def add_payment(appointment_id, total_amount, paid_amount, payment_method, discounts, taxes):
    session = Session()
    clinic_share, doctor_share = calculate_shares(appointment_id, total_amount, discounts, taxes)
    payment = Payment(appointment_id=appointment_id, total_amount=total_amount, paid_amount=paid_amount,
                      clinic_share=clinic_share, doctor_share=doctor_share, payment_method=payment_method,
                      discounts=discounts, taxes=taxes, date_paid=datetime.datetime.now())
    session.add(payment)
    session.commit()
    session.close()

# Reports
def generate_report(start_date, end_date):
    session = Session()
    payments = session.query(Payment).filter(Payment.date_paid.between(start_date, end_date + pd.Timedelta(days=1))).all()
    data = [{'موعد': p.appointment_id, 'إجمالي': p.total_amount, 'نصيب العيادة': p.clinic_share, 'نصيب الطبيب': p.doctor_share} for p in payments]
    df = pd.DataFrame(data)
    session.close()
    return df

def export_to_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "تقرير المحاسبة")
    y = 700
    x_positions = [100, 200, 300, 400]
    for i, col in enumerate(df.columns):
        c.drawString(x_positions[i], y, col)
    y -= 20
    for index, row in df.iterrows():
        for i, value in enumerate(row):
            c.drawString(x_positions[i], y, str(value))
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    buffer.seek(0)
    return buffer

def export_to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

# Streamlit App
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        text-align: right;
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("مرحباً بك في نظام إدارة العيادة")

page = st.sidebar.selectbox("اختر القسم", ["إدارة المرضى", "إدارة الأطباء", "إدارة خطط العلاج", "إدارة المواعيد", "المحاسبة", "التقارير"])

if page == "إدارة المرضى":
    st.title("إدارة المرضى")
    with st.form("إضافة مريض"):
        name = st.text_input("الاسم")
        age = st.number_input("العمر", min_value=0)
        gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
        phone = st.text_input("الهاتف")
        address = st.text_input("العنوان")
        medical_history = st.text_area("التاريخ الطبي")
        image = st.file_uploader("رفع صورة (أشعة أسنان)", type=["png", "jpg"])
        if st.form_submit_button("إضافة"):
            add_patient(name, age, gender, phone, address, medical_history, image)
            st.success("تم إضافة المريض")
    
    patients = get_patients()
    df = pd.DataFrame([{'id': p.id, 'name': p.name, 'age': p.age, 'phone': p.phone} for p in patients])
    st.dataframe(df)

if page == "إدارة الأطباء":
    st.title("إدارة الأطباء")
    with st.form("إضافة طبيب"):
        name = st.text_input("الاسم")
        specialty = st.text_input("التخصص")
        phone = st.text_input("الهاتف")
        email = st.text_input("البريد الإلكتروني")
        if st.form_submit_button("إضافة"):
            add_doctor(name, specialty, phone, email)
            st.success("تم إضافة الطبيب")
    
    doctors = get_doctors()
    df = pd.DataFrame([{'id': d.id, 'name': d.name, 'specialty': d.specialty} for d in doctors])
    st.dataframe(df)

if page == "إدارة خطط العلاج":
    st.title("إدارة خطط العلاج")
    with st.form("إضافة علاج"):
        name = st.text_input("اسم العلاج")
        base_cost = st.number_input("التكلفة الأساسية", min_value=0.0)
        if st.form_submit_button("إضافة"):
            add_treatment(name, base_cost)
            st.success("تم إضافة العلاج")
    
    st.subheader("تخصيص النسب المئوية")
    treatments = get_treatments()
    doctors = get_doctors()
    with st.form("إضافة نسب"):
        treatment_opt = st.selectbox("العلاج", options=[(t.name, t.id) for t in treatments], format_func=lambda x: x[0])
        doctor_opt = st.selectbox("الطبيب", options=[(d.name, d.id) for d in doctors], format_func=lambda x: x[0])
        clinic_perc = st.number_input("نسبة العيادة (%)", 0.0, 100.0, value=50.0)
        doctor_perc = st.number_input("نسبة الطبيب (%)", 0.0, 100.0, value=50.0)
        if st.form_submit_button("إضافة"):
            add_treatment_percentage(treatment_opt[1], doctor_opt[1], clinic_perc, doctor_perc)
            st.success("تم إضافة النسب")

if page == "إدارة المواعيد":
    st.title("إدارة المواعيد")
    with st.form("إضافة موعد"):
        patients = get_patients()
        doctors = get_doctors()
        treatments = get_treatments()
        patient_opt = st.selectbox("المريض", options=[(p.name, p.id) for p in patients], format_func=lambda x: x[0])
        doctor_opt = st.selectbox("الطبيب", options=[(d.name, d.id) for d in doctors], format_func=lambda x: x[0])
        treatment_opt = st.selectbox("العلاج", options=[(t.name, t.id) for t in treatments], format_func=lambda x: x[0])
        date = st.date_input("التاريخ")
        time = st.time_input("الوقت")
        status = st.selectbox("الحالة", ["مؤكد", "ملغى", "قيد الانتظار"])
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("إضافة"):
            full_date = datetime.datetime.combine(date, time)
            add_appointment(patient_opt[1], doctor_opt[1], treatment_opt[1], full_date, status, notes)
            st.success("تم إضافة الموعد")
    
    appointments = get_appointments()
    df = pd.DataFrame([{'id': a.id, 'patient': a.patient.name if a.patient else '', 'doctor': a.doctor.name if a.doctor else '', 'treatment': a.treatment.name if a.treatment else '', 'date': a.date} for a in appointments])
    st.dataframe(df)

if page == "المحاسبة":
    st.title("المحاسبة")
    appointments = get_appointments()
    with st.form("إنشاء فاتورة"):
        appointment_opt = st.selectbox("اختر الموعد", options=[(f"{a.id} - {a.patient.name if a.patient else 'غير معروف'}", a.id) for a in appointments], format_func=lambda x: x[0])
        total_amount = st.number_input("المبلغ الإجمالي", min_value=0.0)
        paid_amount = st.number_input("المبلغ المدفوع", min_value=0.0)
        discounts = st.number_input("الخصومات", min_value=0.0)
        taxes = st.number_input("الضرائب", min_value=0.0)
        payment_method = st.selectbox("طريقة الدفع", ["نقدي", "بطاقة", "تحويل"])
        if st.form_submit_button("إنشاء"):
            add_payment(appointment_opt[1], total_amount, paid_amount, payment_method, discounts, taxes)
            st.success("تم إنشاء الفاتورة مع حساب النسب")

if page == "التقارير":
    st.title("التقارير")
    start_date = st.date_input("من تاريخ")
    end_date = st.date_input("إلى تاريخ")
    if st.button("إنشاء تقرير"):
        df = generate_report(start_date, end_date)
        st.dataframe(df)
        
        excel_buffer = export_to_excel(df)
        st.download_button("تصدير إلى Excel", data=excel_buffer, file_name="report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        pdf_buffer = export_to_pdf(df)
        st.download_button("تصدير إلى PDF", data=pdf_buffer, file_name="report.pdf", mime="application/pdf")
