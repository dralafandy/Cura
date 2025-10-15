import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from database import Session
from models import Payment

def generate_report(start_date, end_date):
    session = Session()
    payments = session.query(Payment).filter(Payment.date_paid.between(start_date, end_date + pd.Timedelta(days=1))).all()  # ليشمل اليوم كاملاً
    data = [{'موعد': p.appointment_id, 'إجمالي': p.total_amount, 'نصيب العيادة': p.clinic_share, 'نصيب الطبيب': p.doctor_share} for p in payments]
    df = pd.DataFrame(data)
    session.close()
    return df

def export_to_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "تقرير المحاسبة")
    y = 700
    # رسم العناوين
    x_positions = [100, 200, 300, 400]
    for i, col in enumerate(df.columns):
        c.drawString(x_positions[i], y, col)
    y -= 20
    # رسم البيانات (بسيط، يمكن تحسينه)
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