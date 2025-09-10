import streamlit as st
from datetime import date, timedelta

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Electricity Bill Calculator", layout="centered")

# ------------------ CUSTOM CSS ------------------ #
st.markdown("""
<style>
h2, h3, h4 { font-family: 'Segoe UI', sans-serif; color: #007bff; }
p, div, label { font-family: 'Segoe UI', sans-serif; }
.bill-card {
    background: #f8f9fa; padding: 20px; border-radius: 12px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px;
}
.metric { font-size: 18px; font-weight: bold; color: #333; }
.value { font-size: 20px; color: #007bff; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
th { background-color: #007bff; color: white; }
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

# ------------------ BILL CALCULATION ------------------ #
def calculate_electricity_bill(units, bill_days, load_kw, bill_date, due_date):
    monthly_units = units / bill_days * 30
    category = None

    # ---------- CATEGORY 1 ----------
    if load_kw <= 2 and monthly_units <= 100:
        category = "Category 1 (Upto 2 KW & 100 Units)"
        slab1_units = min(units, (50 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (50 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [2.20, 2.70, 0]
        slab_ranges = ["0-50 units", "51-100 units", "101+ units"]
        fixed = 0.0
        fsa = units*0.47 if monthly_units>200 else 0.0

    # ---------- CATEGORY 2 ----------
    elif load_kw <= 5:
        category = "Category 2 (Upto 5 KW)"
        slab1_units = min(units, (150 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (150 / 30) * bill_days)
        slab3_units = min(max(units - slab1_units - slab2_units, 0), (200 / 30) * bill_days)
        slab4_units = max(units - slab1_units - slab2_units - slab3_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units, slab4_units]
        slab_rates = [2.95, 5.25, 6.45, 7.10]
        slab_ranges = ["0-150 units", "151-300 units", "301-500 units", "501+ units"]
        if slab3_units>0:
            fixed = (load_kw*50/30)*bill_days
        else:
            fixed = 0.0
        fsa = units*0.47 if monthly_units>200 else 0.0

    # ---------- CATEGORY 3 ----------
    else:
        category = "Category 3 (Above 5 KW)"
        slab1_units = min(units, (500 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units,0), (500 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units,0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [6.50,7.15,7.50]
        slab_ranges = ["0-500 units", "501-1000 units", "1001+ units"]
        fixed = (load_kw*75/30)*bill_days
        fsa = units*0.47 if monthly_units>200 else 0.0

    slab_amounts = [round(s*u,2) for s,u in zip(slab_units, slab_rates)]
    energy = sum(slab_amounts)

    # ---------- Other charges ----------
    ed = round(units*0.10,2)
    mtax = round((energy+fixed+fsa)*0.02,2)

    last_grace_date = add_working_days(due_date,10)
    today = date.today()
    if today <= due_date:
        surcharge_rate = 0.0
        surcharge_note = "✅ No Surcharge (Paid Before Due Date)"
    elif due_date < today <= last_grace_date:
        surcharge_rate = 0.015
        surcharge_note = "🕒 Grace Period Active (1.5% Surcharge)"
    else:
        surcharge_rate = 0.03
        surcharge_note = "⚠️ Late Payment (3% Surcharge Applied)"

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
        "Slab Units": slab_units,
        "Slab Rates": slab_rates,
        "Slab Amounts": slab_amounts,
        "Slab Ranges": slab_ranges,
        "Due Date": due_date
    }

# ------------------ STREAMLIT UI ------------------ #
units = st.number_input("Units Consumed", min_value=0.0, step=1.0, format="%.2f")
load = st.number_input("Load (KW)", min_value=1.0, step=0.1, format="%.2f")
days = st.number_input("Bill Days", min_value=1, step=1)
bill_date = st.date_input("Bill Date", value=date.today())
due_date = st.date_input("Due Date", value=date.today())

if st.button("⚡ Calculate Bill"):
    result = calculate_electricity_bill(units, days, load, bill_date, due_date)

    # ---------- Bill Summary ----------
    st.markdown("<h3>📋 Bill Summary</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='bill-card'><h4>{result['Category']}</h4>", unsafe_allow_html=True)

    for key in ["Units Consumed","Bill Days","Load (KW)","Energy Charges","Fixed Charges","FSA","M-Tax","ED","Surcharge","Total Bill"]:
        st.markdown(f"<p class='metric'>{key}: <span class='value'>₹{result[key]:.2f}</span></p>", unsafe_allow_html=True) if "Charges" in key or key=="Total Bill" else st.markdown(f"<p class='metric'>{key}: <span class='value'>{result[key]}</span></p>", unsafe_allow_html=True)

    st.markdown(f"<p class='metric'>Surcharge Note: <span class='value'>{result['Surcharge Note']}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='metric'>Due Date: <span class='value'>{result['Due Date'].strftime('%d-%m-%Y')}</span></p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Bill Breakout Table ----------
    st.markdown("<h3>🔍 Bill Breakout</h3>", unsafe_allow_html=True)
    slab_table = "<table><tr><th>Slab</th><th>Unit Range</th><th>Units Consumed</th><th>Rate (₹/unit)</th><th>Amount (₹)</th></tr>"
    for i, (r, u, rate, amt) in enumerate(zip(result['Slab_Ranges'], result['Slab_Units'], result['Slab_Rates'], result['Slab_Amounts'])):
        slab_table += f"<tr><td>Slab {i+1}</td><td>{r}</td><td>{u:.2f}</td><td>{rate:.2f}</td><td>{amt:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>Fixed Charges</b></td><td>{result['Fixed Charges']:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>FSA</b></td><td>{result['FSA']:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>M-Tax</b></td><td>{result['M-Tax']:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>ED</b></td><td>{result['ED']:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>Surcharge</b></td><td>{result['Surcharge']:.2f}</td></tr>"
    slab_table += f"<tr><td colspan='4'><b>Total Bill</b></td><td>{result['Total Bill']:.2f}</td></tr>"
    slab_table += "</table>"
    st.markdown(slab_table, unsafe_allow_html=True)

    # ---------- Footer ----------
    st.markdown("<hr><div style='text-align:center; font-size:14px; color:gray;'>Created by <b>ANKIT GAUR</b></div>", unsafe_allow_html=True)























