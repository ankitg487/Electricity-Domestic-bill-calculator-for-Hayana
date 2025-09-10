import streamlit as st
from datetime import date, timedelta
import pandas as pd

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

    # default
    category, slab_units, slab_rates = None, [], []

    if load_kw <= 2 and monthly_units <= 100:
        category = "Category 1 (Upto 2 KW & 100 Units)"
        slab1_units = min(units, (50 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (50 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [2.20, 2.70, 0]
        energy = slab1_units*2.20 + slab2_units*2.70
        fixed = 0.0
        fsa = units * 0.47 if monthly_units > 200 else 0.0

    elif load_kw <= 5:
        category = "Category 2 (Upto 5 KW)"
        slab1_units = min(units, (150 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (150 / 30) * bill_days)
        slab3_units = min(max(units - slab1_units - slab2_units, 0), (200 / 30) * bill_days)
        slab4_units = max(units - slab1_units - slab2_units - slab3_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units, slab4_units]
        slab_rates = [2.95, 5.25, 6.45, 7.10]
        energy = sum([u*r for u, r in zip(slab_units, slab_rates)])
        fixed = (load_kw * 50 / 30) * bill_days
        fsa = units * 0.47 if monthly_units > 200 else 0.0

    else:
        category = "Category 3 (Above 5 KW)"
        slab1_units = min(units, (500 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (500 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [6.50, 7.15, 7.50]
        energy = sum([u*r for u, r in zip(slab_units, slab_rates)])
        fixed = (load_kw * 75 / 30) * bill_days
        fsa = units * 0.47 if monthly_units > 200 else 0.0

    # taxes
    ed = round(units * 0.10, 2)
    mtax = round((energy + fixed + fsa) * 0.02, 2)

    # surcharge logic
    last_grace_date = add_working_days(due_date, 10)
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
    surcharge = round((energy + fsa + fixed) * surcharge_rate, 2)

    total = energy + fixed + mtax + fsa + surcharge + ed

    return {
        "Category": category,
        "Units Consumed": round(units,2),
        "Bill Days": bill_days,
        "Load (KW)": load_kw,
        "Energy Charges": round(energy,2),
        "Fixed Charges": round(fixed,2),
        "Municipal Tax (M-Tax)": mtax,
        "FSA": round(fsa,2),
        "Electricity Duty (ED)": ed,
        "Surcharge": surcharge,
        "Surcharge Note": surcharge_note,
        "Total Bill": round(total,2),
        "Due Date": due_date,
        "Grace Period Ends": last_grace_date,
        "Slab Units": slab_units,
        "Slab Rates": slab_rates,
        "Surcharge Rate": surcharge_rate
    }

# ------------------ STREAMLIT UI ------------------ #
units = st.number_input("Units Consumed", min_value=0.0, step=1.0, format="%.2f")
load = st.number_input("Load (KW)", min_value=1.0, step=0.1, format="%.2f")
days = st.number_input("Bill Days", min_value=1, step=1)
bill_date = st.date_input("Bill Date", value=date.today())
due_date = st.date_input("Due Date", value=date.today())

if st.button("⚡ Calculate Bill"):
    result = calculate_electricity_bill(units, days, load, bill_date, due_date)

    st.markdown("<h3>📋 Bill Summary</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='bill-card'><h4>{result['Category']}</h4>", unsafe_allow_html=True)

    for key, value in result.items():
        if key not in ["Category", "Slab Units", "Slab Rates", "Surcharge Rate"]:
            if key in ["Energy Charges", "Fixed Charges", "Municipal Tax (M-Tax)", "FSA", "Electricity Duty (ED)", "Surcharge", "Total Bill"]:
                st.markdown(f"<p class='metric'>{key}: <span class='value'>₹{value:.2f}</span></p>", unsafe_allow_html=True)
            elif key in ["Due Date", "Grace Period Ends"]:
                st.markdown(f"<p class='metric'>{key}: <span class='value'>{value.strftime('%d-%m-%Y')}</span></p>", unsafe_allow_html=True)
            elif key == "Surcharge Note":
                color = "#28a745" if "No Surcharge" in value else "#ffc107" if "Grace Period" in value else "#dc3545"
                st.markdown(f"<p class='metric'>{key}: <span class='value' style='color:{color}'>{value}</span></p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='metric'>{key}: <span class='value'>{value}</span></p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ BILL BREAKOUT SECTION ------------------ #
    st.markdown("### 🔍 Detailed Bill Breakout")

    components = []

    # slabs
    for i, (u, r) in enumerate(zip(result["Slab Units"], result["Slab Rates"]), 1):
        if u > 0 and r > 0:
            components.append({
                "Component": f"Energy (Slab {i})",
                "Base": f"{u:.2f} × ₹{r:.2f}",
                "Rate": f"₹{r:.2f}",
                "Amount (₹)": round(u*r,2)
            })

    # other charges
    components += [
        {"Component": "Fixed Charges", "Base": f"{result['Load (KW)']} KW × ₹50/KW (Pro-rata)", "Rate": "-", "Amount (₹)": result["Fixed Charges"]},
        {"Component": "FSA", "Base": f"{result['Units Consumed']} × ₹0.47 (if >200 units)", "Rate": "-", "Amount (₹)": result["FSA"]},
        {"Component": "Electricity Duty", "Base": f"{result['Units Consumed']} × 10%", "Rate": "-", "Amount (₹)": result["Electricity Duty (ED)"]},
        {"Component": "Municipal Tax (M-Tax)", "Base": "(Energy+Fixed+FSA) × 2%", "Rate": "-", "Amount (₹)": result["Municipal Tax (M-Tax)"]},
        {"Component": "Surcharge", "Base": f"(Energy+Fixed+FSA) × {result['Surcharge Rate']*100:.1f}%", "Rate": "-", "Amount (₹)": result["Surcharge"]},
        {"Component": "Total Bill", "Base": "", "Rate": "", "Amount (₹)": result["Total Bill"]}
    ]

    df = pd.DataFrame(components)
    st.dataframe(df, use_container_width=True)

    # ------------------ FOOTER ------------------ #
    st.markdown("""
    <hr>
    <div style='text-align:center; font-size:14px; color:gray;'>
        Created by <b>ANKIT GAUR</b>
    </div>
    """, unsafe_allow_html=True)












