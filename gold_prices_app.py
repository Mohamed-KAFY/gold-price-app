import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  # مهم جداً
import altair as alt

# إعداد الصفحة
st.set_page_config(page_title="أسعار الذهب", layout="centered", page_icon="💰")

# اختيار الوضع (عادي أو ليلي)
mode = st.selectbox("🎨 اختر وضع العرض", ["☀️ الوضع العادي", "🌙 الوضع الليلي"])

# CSS حسب الوضع
if mode == "🌙 الوضع الليلي":
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .title { color: #f1c40f; text-align: center; font-size: 32px; font-weight: bold; }
        .subtitle { color: #ccc; text-align: center; font-size: 16px; }
        .footer { color: #999; text-align: center; font-size: 13px; margin-top: 40px; }
        .block-container, .css-1d391kg, .css-18ni7ap {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #fdfcfb;
            color: #000000;
        }
        .title { color: #b8860b; text-align: center; font-size: 32px; font-weight: bold; }
        .subtitle { color: #555; text-align: center; font-size: 16px; }
        .footer { color: #888; text-align: center; font-size: 13px; margin-top: 40px; }
        </style>
    """, unsafe_allow_html=True)

# العنوان
st.markdown('<div class="title">💰 أسعار الذهب في مصر</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">يتم التحديث مباشرةً من موقع: egypt.gold-price-today.com</div>', unsafe_allow_html=True)
st.write("")

# زر التحديث اليدوي
if st.button("🔄 اضغط لتحديث الصفحة"):
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)

# ---- جلب البيانات ----
url = "https://egypt.gold-price-today.com/"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # --- جدول الأسعار اللحظية ---
    table = soup.find("table", class_="prices-table")
    rows = table.find("tbody").find_all("tr")

    data = []
    for row in rows:
        cols = row.find_all(["th", "td"])
        if len(cols) == 3:
            data.append([cols[0].text.strip(), cols[1].text.strip(), cols[2].text.strip()])
        elif len(cols) == 2:
            data.append([cols[0].text.strip(), cols[1].text.strip(), ""])

    df = pd.DataFrame(data, columns=["الصنف", "سعر البيع", "سعر الشراء"])

    # التوقيت المحلي لمصر
    cairo_time = datetime.now(ZoneInfo("Africa/Cairo"))
    timestamp = cairo_time.strftime('%Y-%m-%d %H:%M:%S')
    st.success(f"📅 تم جلب البيانات من الموقع في: {timestamp} (هذا ليس وقت التحديث الفعلي لأسعار الذهب)")

    st.dataframe(df, use_container_width=True)

    # --- آلة حاسبة ---
    st.subheader("🧮 احسب تكلفة الذهب بالجرام")
    available_items = df[df["سعر البيع"].str.contains("جنيه", na=False)]["الصنف"].tolist()
    selected_type = st.selectbox("اختر العيار:", available_items)
    selected_price_str = df[df["الصنف"] == selected_type]["سعر البيع"].values[0]
    price_per_gram = int(selected_price_str.replace("جنيه", "").strip())
    grams = st.number_input("أدخل عدد الجرامات:", min_value=0.0, value=1.0, step=0.1)
    st.info(f"💸 التكلفة = {grams * price_per_gram:,.0f} جنيه")

    # --- تغير الأسعار في الأيام السابقة ---
    st.subheader("📊 تغير أسعار الذهب في الأيام السابقة")

    caption_tag = soup.find("caption", string=lambda text: "الأيام السابقة" in text)
    historical_table = caption_tag.find_parent("table")
    historical_rows = historical_table.find("tbody").find_all("tr")

    hist_data = []
    for row in historical_rows:
        cols = row.find_all("td")
        day = row.find("th").text.strip()
        if len(cols) >= 5:
            gold_24 = int(cols[0].text.strip())
            gold_21 = int(cols[2].text.strip())
            gold_18 = int(cols[3].text.strip())
            ounce = int(cols[4].text.strip())
            hist_data.append([day, gold_24, gold_21, gold_18, ounce])

    df_hist = pd.DataFrame(hist_data, columns=["اليوم", "ذهب 24", "ذهب 21", "ذهب 18", "الأوقية"])
    df_long = df_hist.melt(id_vars="اليوم", var_name="النوع", value_name="السعر")

    min_price = df_long["السعر"].min()
    max_price = df_long["السعر"].max()

    chart = alt.Chart(df_long).mark_line(point=True).encode(
        x=alt.X("اليوم:N", sort=None, title="اليوم"),
        y=alt.Y("السعر:Q", title="السعر بالجنيه", scale=alt.Scale(domain=[min_price * 0.98, max_price * 1.02])),
        color=alt.Color("النوع:N", title="العيار")
    ).properties(width="container", height=400)

    st.altair_chart(chart, use_container_width=True)

except Exception as e:
    st.error("❌ حدث خطأ أثناء تحميل البيانات.")
    st.text(f"{e}")

# --- التذييل ---
st.markdown('<div class="footer">© محمد أحمد سيد - 2025</div>', unsafe_allow_html=True)
