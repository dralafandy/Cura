import streamlit as st
import pandas as pd
import datetime
from database import engine, Base, Session
from models import *  # Import all models to create tables
from functions import *
from reports import generate_report, export_to_pdf, export_to_excel

# Create tables if not exist
Base.metadata.create_all(engine)

# CSS لدعم RTL (العربية)
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        text-align: right;
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

# No authentication - direct access
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
    
    # عرض المرضى
    patients = get_patients()
    df = pd.DataFrame([{'id': p.id, 'name': p.name, 'age': p.age, 'phone': p.phone} for p in patients])
    st.dataframe(df)
    
    # يمكن إضافة تعديل/حذف هنا

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
        treatment_id = st.selectbox("العلاج", options=[(t.name, t.id) for t in treatments], format_func=lambda x: x[0])
        doctor_id = st.selectbox("الطبيب", options=[(d.name, d.id) for d in doctors], format_func=lambda x: x[0])
        clinic_perc = st.number_input("نسبة العيادة (%)", 0.0, 100.0, value=50.0)
        doctor_perc = st.number_input("نسبة الطبيب (%)", 0.0, 100.0, value=50.0)
        if st.form_submit_button("إضافة"):
            add_treatment_percentage(treatment_id[1], doctor_id[1], clinic_perc, doctor_perc)
            st.success("تم إضافة النسب")

if page == "إدارة المواعيد":
    st.title("إدارة المواعيد")
    with st.form("إضافة موعد"):
        patients = get_patients()
        doctors = get_doctors()
        treatments = get_treatments()
        patient_id = st.selectbox("المريض", options=[(p.name, p.id) for p in patients], format_func=lambda x: x[0])
        doctor_id = st.selectbox("الطبيب", options=[(d.name, d.id) for d in doctors], format_func=lambda x: x[0])
        treatment_id = st.selectbox("العلاج", options=[(t.name, t.id) for t in treatments], format_func=lambda x: x[0])
        date = st.date_input("التاريخ")
        time = st.time_input("الوقت")
        status = st.selectbox("الحالة", ["مؤكد", "ملغى", "قيد الانتظار"])
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("إضافة"):
            full_date = datetime.datetime.combine(date, time)
            add_appointment(patient_id[1], doctor_id[1], treatment_id[1], full_date, status, notes)
            st.success("تم إضافة الموعد")
    
    appointments = get_appointments()
    df = pd.DataFrame([{'id': a.id, 'patient': a.patient.name, 'doctor': a.doctor.name, 'treatment': a.treatment.name, 'date': a.date} for a in appointments])
    st.dataframe(df)

if page == "المحاسبة":
    st.title("المحاسبة")
    appointments = get_appointments()
    with st.form("إنشاء فاتورة"):
        appointment_opt = st.selectbox("اختر الموعد", options=[(f"{a.id} - {a.patient.name}", a.id) for a in appointments], format_func=lambda x: x[0])
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
