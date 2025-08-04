import streamlit as st
import pandas as pd
import sqlite3
import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime

# إعدادات Streamlit
st.set_page_config(page_title="MATRIX 2050 ESG Intelligence", layout="wide")
st.title("🌍 MATRIX 2050 - ESG Digital Twin Dashboard")

# ------ تكامل MQTT ------
live_data = {"E_co2": 0, "E_water": 0, "S_training": 0}

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        live_data.update(data)
        # حفظ البيانات في قاعدة البيانات
        save_to_db(data)
    except Exception as e:
        st.error(f"خطأ في معالجة بيانات MQTT: {str(e)}")

def init_mqtt():
    client = mqtt.Client()
    client.connect("broker.hivemq.com", 1883)
    client.subscribe("matrix2050/esg_data")
    client.on_message = on_message
    client.loop_start()
    return client

mqtt_client = init_mqtt()

# ------ تكامل قاعدة البيانات SQLite ------
DB_FILE = "network_data.db"

def create_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS esg_metrics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  unit TEXT,
                  e_co2_emissions REAL,
                  e_water_usage REAL,
                  s_training_rate REAL,
                  s_community_initiatives INTEGER,
                  g_compliance_rate REAL)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO esg_metrics 
                    (unit, e_co2_emissions, e_water_usage, s_training_rate) 
                    VALUES (?, ?, ?, ?)''',
                 ('الطاقة', data.get('E_co2', 0), data.get('E_water', 0), data.get('S_training', 0)))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {str(e)}")

@st.cache_data(ttl=60)
def load_historical_data():
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM esg_metrics ORDER BY date DESC LIMIT 1000", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"خطأ في قاعدة البيانات: {str(e)}")
        return pd.DataFrame()

# إنشاء قاعدة البيانات عند التشغيل الأول
create_db()

# ------ واجهة المستخدم ------
st.sidebar.header("⚙️ لوحة التحكم الحيَّة")
st.sidebar.metric("انبعاثات CO₂ اللحظية", f"{live_data['E_co2']} g/kWh")
st.sidebar.metric("استهلاك المياه", f"{live_data['E_water']} m³")
st.sidebar.metric("معدل التدريب", f"{live_data['S_training']}%")

tab1, tab2, tab3 = st.tabs(["📈 المؤشرات الحيَّة", "📊 التحليل التاريخي", "🧠 التوصيات الذكية"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("الأداء البيئي (E)")
        fig = px.bar(x=["CO₂", "المياه"], y=[live_data["E_co2"], live_data["E_water"]],
                     labels={"x": "المؤشر", "y": "القيمة"})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("المؤشرات المجتمعية (S)")
        fig = px.pie(values=[live_data["S_training"], 100 - live_data["S_training"]], 
                     names=["معدل التدريب", "معدل التحسين المطلوب"])
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    df = load_historical_data()
    if not df.empty:
        st.subheader("تحليل اتجاهات ESG")
        
        # تحويل العمود الزمني
        df['date'] = pd.to_datetime(df['date'])
        
        selected_unit = st.selectbox("اختر الوحدة:", df['unit'].unique())
        unit_data = df[df['unit'] == selected_unit]
        
        fig = px.line(unit_data, x='date', y=['e_co2_emissions', 'e_water_usage'],
                      title="الاتجاه البيئي", labels={"value": "القيمة", "date": "التاريخ"})
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.scatter(unit_data, x='s_training_rate', y='e_co2_emissions',
                         size='e_water_usage', color='unit',
                         title="العلاقة بين التدريب والانبعاثات",
                         labels={"s_training_rate": "معدل التدريب (%)", "e_co2_emissions": "انبعاثات CO₂"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("لا توجد بيانات تاريخية متاحة. سيتم ملء البيانات تلقائيًا عند استقبال بيانات MQTT.")

with tab3:
    st.subheader("توصيات التحسين الفورية")
    if live_data['E_co2'] > 150:
        st.error("🚨 ارتفاع انبعاثات الكربون: تنشيط خطة خفض الانبعاثات الفورية")
    if live_data['S_training'] < 70:
        st.warning("⚠️ انخفاض معدل التدريب: مقترح برامج تطوير مهارات عاجلة")
    if live_data['E_water'] > 1000:
        st.info("💧 استهلاك مياه مرتفع: تفعيل نظام إعادة التدوير الآلي")
    
    st.subheader("خطة التحسين الاستراتيجي")
    st.markdown("""
    1. **تطوير نظام مراقبة ذكي للطاقة**
        - تركيب أجهزة استشعار IoT
        - تحليل البيانات في الوقت الفعلي
    2. **برامج تدريبية متخصصة**
        - ورش عمل في الاستدامة
        - شهادات مهنية معتمدة
    3. **تحديث البنية التحتية**
        - أنظمة إعادة تدوير المياه
        - تحسين كفاءة الطاقة
    """)

# ------ إدارة البيانات ------
st.sidebar.divider()
st.sidebar.header("🔗 إدارة النظام")
if st.sidebar.button("🔄 تحديث البيانات اللحظية"):
    st.rerun()
    
if st.sidebar.button("🧹 مسح البيانات التاريخية"):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM esg_metrics")
        conn.commit()
        conn.close()
        st.sidebar.success("تم مسح البيانات التاريخية بنجاح!")
        st.cache_data.clear()
    except:
        st.sidebar.error("فشل في مسح البيانات")

st.sidebar.download_button(
    label="📥 تنزيل البيانات",
    data=open(DB_FILE, "rb").read(),
    file_name="esg_data.db",
    mime="application/octet-stream"
)

st.sidebar.markdown("""
---
**MATRIX 2050 ESG System**  
v2.1 | Blue Ocean Intelligence  
© 2025 All Rights Reserved
""")
