import streamlit as st
from datetime import date, timedelta

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Electricity Bill Calculator", layout="centered")

# ------------------ CUSTOM CSS ------------------ #
st.markdown("""
<style>
h2, h3, h4 { font-family: 'Segoe UI', sans-serif; color: #007bff; }
p, div, label { font-family: 'Segoe UI', sans-serif; }
.bill-card { background: #f8f9fa; padding: 20px; border-radius: 12px; 
             box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px; }
.metric { font-size: 18px; font-weight: bold; color: #333; }
.value { font-size: 20px; color: #007bff; }
.table-container { border-collapse: collapse; width: 100%; }
.table-container th, .table-container td { border: 1px solid #ddd; padding: 8px; text-align: center; }
.table-container tr:nth-child(even){background-color: #f2f2f2;}
.table-container th { background-color: #007bff; color: white; }
.total-row { font-weight: bold; background-color: #ffc107; color: #000; }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------ #
st.markdown("""
<div style='text-align: center; padding: 15px; background-color: #f0f8ff; border-radius: 10px;'>
    <h2>हरियाणा बिजली वितरण निगम ⚡</h2>
    <p>यहाँ आप घरेलू श्रेणी का बिजली बिल आसानी से कैलकुलेट कर सकते हैं।</p>
</div>
""", unsafe_allow_html=True)

# ------------------ HELPER FUNCTION ------------------ #
def add_working_days(start_date, days):
    current = start_date
    added_days = 0
    while added_days < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added_days += 1
    return current

# ------------------ BILL CALCULATION FUNCTION ------------------ #
def calculate_electricity_bill(units, bill_days, load_kw, bill_date, due_date):
    monthly_units = units / bill_days * 30
    category = None

    # ---------------- CATEGORY 1 ---------------- #
    if load_kw <= 2 and monthly_units <= 100:
        category = "Category 1 (Upto 2 KW & 100 Units)"
        slab1_units = min(units, (50 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (50 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_amounts = [slab1_units*2.20, slab2_units*2.70, 0]
        energy = sum(slab_amounts)
        fixed = 0.0
        fsa = units * 0.47 if monthly_units > 200 else 0.0
        slab_ranges = ["0-50 units", "51-100 units", "101+ units"]

    # ---------------- CATEGORY 2 ---------------- #
    elif load_kw <= 5:
        category = "Category 2 (Upto 5 KW)"
        slab1_units = min(units, (150 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (150 / 30) * bill_days)
        slab3_units = min(max(units - slab1_units - slab2_units, 0), (200 / 30) * bill_days)
        slab4_units = max(units - slab1_units - slab2_units - slab3_units, 0)
        rates = [2.95,5.25,6.45,7.10]
        slab_amounts = [slab1_units*rates[0], slab2_units*rates[1], slab3_units*rates[2], slab4_units*rates[3]]
        energy = sum(slab_amounts)
        # Fixed charge logic only if units >300 (Category 2)
        if units > 300:
            fixed = (load_kw * 50 / 30) * bill_days
        else:
            fixed = 0.0
        fsa = units * 0.47 if monthly_units > 200 else 0.0
        slab_ranges = ["0-150 units", "151-300 units", "301-500 units", "501+ units"]

    # ---------------- CATEGORY 3 ---------------- #
    else:
        category = "Category 3 (Above 5 KW)"
        slab1_units = min(units, (500 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (500 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        rates = [6.50,7.15,7.50]
        slab_amounts = [slab1_units*rates[0], slab2_units*rates[1], slab3_units*rates[2]]
        energy = sum(slab_amounts)
        fixed = (load_kw * 75 / 30) * bill_days
        fsa = units * 0.47 if monthly_units > 200 else 0.0
        slab_ranges = ["0-500 units", "501-1000 units", "1001+ units"]

    # ---------------- OTHER CHARGES ---------------- #
    ed = round(units * 0.10,2)
    mtax = round((energy+fixed+fsa)*0.02,2)
    last_grace_date = due_date  # As per request, grace date = due date
    today = date.today()
    if today <= due_date:
        surcharge_rate = 0.0
        surcharge_note = "No surcharge (Paid Before Due Date)"
    else:
        surcharge_rate = 0.03
        surcharge_note = "Late Payment Surcharge Applied (3%)"
    surcharge = round((energy+fsa+fixed)*surcharge_rate,2)
    total = energy+fixed+fsa+mtax+ed+surcharge

    return {
        "Category": category,
        "Units Consumed": round(units,2),
        "Bill Days": bill_days,
        "Load (KW)": load_kw,
        "Energy Charges": round(energy,2),
        "Fixed Charges": round(fixed,2),
        "FSA": round(fsa,2),
        "M-Tax": mtax,
        "ED": ed,
        "Surcharge": surcharge,
        "Surcharge Note": surcharge_note,
        "Total Bill": round(total,2),
        "Slab Units": [slab1_units, slab2_units, slab3_units] if category!="Category 2" else [slab1_units, slab2_units, slab3_units, slab4_units],
        "Slab Amounts": slab_amounts,
        "Slab Ranges": slab_ranges,
        "Due Date": last_grace_date
    }

# ------------------ STREAMLIT UI ------------------ #
units = st.number_input("Units Consumed", min_value=0.0, step=1.0, format="%.2f")
load = st.number_input("Load (KW)", min_value=1.0, step=0.1, format="%.2f")
days = st.number_input("Bill Days", min_value=1, step=1)
bill_date = st.date_input("Bill Date", value=date.today())
due_date = st.date_input("Due Date", value=date.today())

if st.button("⚡ Calculate Bill"):
    result = calculate_electricity_bill(units, days, load, bill_date, due_date)

    # ---------------- BILL SUMMARY ---------------- #
    st.markdown("<h3>📋 Bill Summary</h3>", unsafe_allow_html=True)
    st.markdown("<div class='bill-card'>", unsafe_allow_html=True)
    st.markdown(f"<h4>{result['Category']}</h4>", unsafe_allow_html=True)
    for key in ["Units Consumed","Bill Days","Load (KW)","Energy Charges","Fixed Charges","FSA","M-Tax","ED","Surcharge","Total Bill"]:
        st.markdown(f"<p class='metric'>{key}: <span class='value'>₹{result[key]:.2f}</span></p>" if key!="Units Consumed" and key!="Bill Days" and key!="Load (KW)" else f"<p class='metric'>{key}: <span class='value'>{result[key]}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='metric'>Surcharge Note: <span class='value'>{result['Surcharge Note']}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='metric'>Due Date: <span class='value'>{result['Due Date'].strftime('%d-%m-%Y')}</span></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- BILL BREAKOUT ---------------- #
    st.markdown("<h3>🔍 Bill Breakout (Slab-wise)</h3>", unsafe_allow_html=True)
    slab_units = result["Slab Units"]
    slab_amounts = result["Slab Amounts"]
    slab_ranges = result["Slab Ranges"]

    table_html = "<table class='table-container'><tr><th>Slab</th><th>Unit Range</th><th>Units Consumed</th><th>Rate (₹/unit)</th><th>Amount (₹)</th></tr>"
    for i in range(len(slab_units)):
        rate = round(slab_amounts[i]/slab_units[i],2) if slab_units[i]>0 else 0
        table_html += f"<tr><td>{i+1}</td><td>{slab_ranges[i]}</td><td>{slab_units[i]:.2f}</td><td>{rate:.2f}</td><td>{slab_amounts[i]:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>Total Energy Charges</td><td>{result['Energy Charges']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>Fixed Charges</td><td>{result['Fixed Charges']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>FSA</td><td>{result['FSA']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>M-Tax</td><td>{result['M-Tax']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>ED</td><td>{result['ED']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>Surcharge</td><td>{result['Surcharge']:.2f}</td></tr>"
    table_html += f"<tr class='total-row'><td colspan='4'>Total Bill</td><td>{result['Total Bill']:.2f}</td></tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # ---------------- FOOTER ---------------- #
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:14px; color:gray;'>Created by <b>ANKIT GAUR</b></div>", unsafe_allow_html=True)






















