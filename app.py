import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد قاعدة بيانات SQLite
conn = sqlite3.connect('dental_clinic.db')
c = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
c.execute('''CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    phone TEXT,
    notes TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    date TEXT,
    time TEXT,
    reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    amount REAL,
    service TEXT,
    paid BOOLEAN,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
)''')
conn.commit()

# واجهة Streamlit
st.set_page_config(page_title="إدارة عيادة الأسنان", layout="wide")
st.title("نظام إدارة عيادة الأسنان 🦷")

# شريط جانبي للتنقل
page = st.sidebar.selectbox("اختر الصفحة", ["الرئيسية", "إدارة المرضى", "المواعيد", "الفواتير"])

# الصفحة الرئيسية
if page == "الرئيسية":
    st.header("مرحبًا بك في نظام إدارة عيادة الأسنان")
    st.write("استخدم القائمة الجانبية للتنقل بين إدارة المرضى، المواعيد، والفواتير.")

# إدارة المرضى
elif page == "إدارة المرضى":
    st.header("إدارة المرضى")
    
    with st.form("patient_form"):
        name = st.text_input("اسم المريض")
        age = st.number_input("العمر", min_value=1, max_value=120, step=1)
        phone = st.text_input("رقم الهاتف")
        notes = st.text_area("ملاحظات")
        submit = st.form_submit_button("إضافة مريض")
        
        if submit:
            c.execute("INSERT INTO patients (name, age, phone, notes) VALUES (?, ?, ?, ?)",
                      (name, age, phone, notes))
            conn.commit()
            st.success("تم إضافة المريض بنجاح!")
    
    # عرض قائمة المرضى
    st.subheader("قائمة المرضى")
    patients = pd.read_sql("SELECT * FROM patients", conn)
    st.dataframe(patients)

# إدارة المواعيد
elif page == "المواعيد":
    st.header("إدارة المواعيد")
    
    with st.form("appointment_form"):
        patient_id = st.number_input("معرف المريض", min_value=1, step=1)
        date = st.date_input("تاريخ الموعد")
        time = st.time_input("وقت الموعد")
        reason = st.text_input("سبب الموعد")
        submit = st.form_submit_button("إضافة موعد")
        
        if submit:
            c.execute("INSERT INTO appointments (patient_id, date, time, reason) VALUES (?, ?, ?, ?)",
                      (patient_id, str(date), str(time), reason))
            conn.commit()
            st.success("تم إضافة الموعد بنجاح!")
    
    # عرض قائمة المواعيد
    st.subheader("قائمة المواعيد")
    appointments = pd.read_sql("SELECT a.id, p.name, a.date, a.time, a.reason FROM appointments a JOIN patients p ON a.patient_id = p.id", conn)
    st.dataframe(appointments)

# إدارة الفواتير
elif page == "الفواتير":
    st.header("إدارة الفواتير")
    
    with st.form("invoice_form"):
        patient_id = st.number_input("معرف المريض", min_value=1, step=1)
        amount = st.number_input("المبلغ", min_value=0.01, step=0.01)
        service = st.text_input("الخدمة")
        paid = st.checkbox("مدفوع؟")
        submit = st.form_submit_button("إضافة فاتورة")
        
        if submit:
            c.execute("INSERT INTO invoices (patient_id, amount, service, paid) VALUES (?, ?, ?, ?)",
                      (patient_id, amount, service, paid))
            conn.commit()
            st.success("تم إضافة الفاتورة بنجاح!")
    
    # عرض قائمة الفواتير
    st.subheader("قائمة الفواتير")
    invoices = pd.read_sql("SELECT i.id, p.name, i.amount, i.service, i.paid FROM invoices i JOIN patients p ON i.patient_id = p.id", conn)
    st.dataframe(invoices)

# إغلاق الاتصال بقاعدة البيانات
conn.close()
