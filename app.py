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

    slab_units, slab_rates = [], []

    if load_kw <= 2 and monthly_units <= 100:
        category = "Category 1 (Upto 2 KW & 100 Units)"
        slab1_units = min(units, (50 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (50 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [2.20, 2.70, 0.00]
        energy = slab1_units * 2.20 + slab2_units * 2.70
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
        energy = (slab1_units*2.95 + slab2_units*5.25 +
                  slab3_units*6.45 + slab4_units*7.10)
        fixed = (load_kw * 50 / 30) * bill_days
        fsa = units * 0.47 if monthly_units > 200 else 0.0

    else:
        category = "Category 3 (Above 5 KW)"
        slab1_units = min(units, (500 / 30) * bill_days)
        slab2_units = min(max(units - slab1_units, 0), (500 / 30) * bill_days)
        slab3_units = max(units - slab1_units - slab2_units, 0)
        slab_units = [slab1_units, slab2_units, slab3_units]
        slab_rates = [6.50, 7.15, 7.50]
        energy = (slab1_units*6.50 + slab2_units*7.15 +
                  slab3_units*7.50)
        fixed = (load_kw * 75 / 30) * bill_days
        fsa = units * 0.47 if monthly_units > 200 else 0.0

    ed = round(units * 0.10, 2)
    mtax = round((energy + fixed + fsa) * 0.02, 2)

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
        "Slabs": {"Units": slab_units, "Rates": slab_rates}
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
        if key not in ["Category", "Slabs", "Grace Period Ends", "Surcharge Note"]:
            if key in [
                "Energy Charges", "Fixed Charges", "Municipal Tax (M-Tax)",
                "FSA", "Electricity Duty (ED)", "Surcharge", "Total Bill"
            ]:
                st.markdown(
                    f"<p class='metric'>{key}: <span class='value'>₹{value:.2f}</span></p>",
                    unsafe_allow_html=True
                )
            elif key == "Due Date":
                st.markdown(
                    f"<p class='metric'>Due Date: <span class='value'>{value.strftime('%d-%m-%Y')} "
                    f"(Grace Period Ends: {result['Grace Period Ends'].strftime('%d-%m-%Y')})</span></p>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<p class='metric'>{key}: <span class='value'>{value}</span></p>",
                    unsafe_allow_html=True
                )
        elif key == "Surcharge Note":
            color = "#28a745" if "No Surcharge" in value else "#ffc107" if "Grace Period" in value else "#dc3545"
            st.markdown(
                f"<p class='metric'>{key}: <span class='value' style='color:{color}'>{value}</span></p>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ BILL BREAKOUT SECTION ------------------ #
    st.markdown("<h3>🔍 Detailed Bill Breakout</h3>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#f8f9fa; padding:20px; border-radius:12px; 
                box-shadow:2px 2px 8px rgba(0,0,0,0.1); margin-top:10px;">
    <table style="width:100%; border-collapse: collapse; margin-top:10px;">
        <tr style="background-color:#007bff; color:white; text-align:center;">
            <th style="padding:8px; border:1px solid #ddd;">Component</th>
            <th style="padding:8px; border:1px solid #ddd;">Units</th>
            <th style="padding:8px; border:1px solid #ddd;">Rate (₹)</th>
            <th style="padding:8px; border:1px solid #ddd;">Amount (₹)</th>
            <th style="padding:8px; border:1px solid #ddd;">Basis</th>
        </tr>
    """, unsafe_allow_html=True)

    # Slabs rows
    slab_units = result["Slabs"]["Units"]
    slab_rates = result["Slabs"]["Rates"]

    for i, (u, r) in enumerate(zip(slab_units, slab_rates), 1):
        if u > 0:
            st.markdown(f"""
            <tr style="text-align:center;">
                <td style="padding:8px; border:1px solid #ddd;">Slab {i}</td>
                <td style="padding:8px; border:1px solid #ddd;">{u:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd;">{r:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd;">{u*r:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd;">Units × Rate</td>
            </tr>
            """, unsafe_allow_html=True)

    # Other components with basis
    other_components = [
        ("Fixed Charges", result['Fixed Charges'], f"₹50 × {result['Load (KW)']} × {result['Bill Days']}/30"),
        ("FSA", result['FSA'], "Units × ₹0.47 (if >200 units)"),
        ("Municipal Tax (M-Tax)", result['Municipal Tax (M-Tax)'], "2% of (Energy + Fixed + FSA)"),
        ("Electricity Duty (ED)", result['Electricity Duty (ED)'], "₹0.10 × Units"),
        ("Surcharge", result['Surcharge'], result['Surcharge Note'])
    ]

    for name, val, basis in other_components:
        st.markdown(f"""
        <tr style="text-align:center;">
            <td style="padding:8px; border:1px solid #ddd;">{name}</td>
            <td style="padding:8px; border:1px solid #ddd;">-</td>
            <td style="padding:8px; border:1px solid #ddd;">-</td>
            <td style="padding:8px; border:1px solid #ddd;">{val:.2f}</td>
            <td style="padding:8px; border:1px solid #ddd;">{basis}</td>
        </tr>
        """, unsafe_allow_html=True)

    # Total row highlighted
    st.markdown(f"""
    <tr style="background-color:#f0f0f0; font-weight:bold; text-align:center;">
        <td style="padding:8px; border:1px solid #ddd;" colspan="4">➡️ Total Bill</td>
        <td style="padding:8px; border:1px solid #ddd; color:#007bff;">₹{result['Total Bill']:.2f}</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # ------------------ FOOTER ------------------ #
    st.markdown("""
    <hr>
    <div style='text-align:center; font-size:14px; color:gray;'>
        Created by <b>ANKIT GAUR</b>
    </div>
    """, unsafe_allow_html=True)









