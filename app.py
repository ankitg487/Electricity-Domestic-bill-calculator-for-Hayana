import streamlit as st
from datetime import date, timedelta

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Electricity Bill Calculator", layout="centered")

# ------------------ CUSTOM CSS ------------------ #
st.markdown("""
<style>
h2, h3, h4 { font-family: 'Segoe UI', sans-serif; color: #007bff; }
p, div, label, td { font-family: 'Segoe UI', sans-serif; }
.bill-card { background: #f8f9fa; padding: 20px; border-radius: 12px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px;}
.metric { font-size: 18px; font-weight: bold; color: #333; }
.value { font-size: 20px; color: #007bff; }
table { border-collapse: collapse; width: 100%; margin-top: 15px;}
th, td { border: 1px solid #ccc; padding: 8px; text-align: center;}
th { background-color: #007bff; color: white;}
.total-row { font-weight: bold; background-color: #f0f8ff;}
.footer { text-align:center; font-size:14px; color:gray; margin-top:15px;}
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

    # Category 1
    if load_kw <= 2 and monthly_units <= 100:
        category = "Category 1 (Upto 2 KW & 100 Units)"
        slab1_units = min(units, (50/30)*bill_days)
        slab2_units = min(max(units - slab1_units,0), (50/30)*bill_days)
        slab3_units = max(units - slab1_units - slab2_units,0)
        slab_amounts = [slab1_units*2.20, slab2_units*2.70, 0]
        energy = sum(slab_amounts)
        fixed = 0.0
        fsa = units*0.47 if monthly_units>200 else 0.0

    # Category 2
    elif load_kw <=5:
        category = "Category 2 (Upto 5 KW)"
        slab1_units = min(units,(150/30)*bill_days)
        slab2_units = min(max(units-slab1_units,0),(150/30)*bill_days)
        slab3_units = min(max(units-slab1_units-slab2_units,0),(200/30)*bill_days)
        slab4_units = max(units-slab1_units-slab2_units-slab3_units,0)
        rates = [2.95,5.25,6.45,7.10]
        slab_amounts = [slab1_units*rates[0], slab2_units*rates[1], slab3_units*rates[2], slab4_units*rates[3]]
        energy = sum(slab_amounts)
        # Fixed charge logic only if slab3_units > 0
        if slab3_units>0:
            fixed = (load_kw*50/30)*bill_days
        else:
            fixed = 0.0
        fsa = units*0.47 if monthly_units>200 else 0.0

    # Category 3
    else:
        category = "Category 3 (Above 5 KW)"
        slab1_units = min(units,(500/30)*bill_days)
        slab2_units = min(max(units-slab1_units,0),(500/30)*bill_days)
        slab3_units = max(units-slab1_units-slab2_units,0)
        rates = [6.50,7.15,7.50]
        slab_amounts = [slab1_units*rates[0], slab2_units*rates[1], slab3_units*rates[2]]
        energy = sum(slab_amounts)
        fixed = (load_kw*75/30)*bill_days
        fsa = units*0.47 if monthly_units>200 else 0.0

    ed = round(units*0.10,2)
    mtax = round((energy+fixed+fsa)*0.02,2)

    # Surcharge
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

    total = energy+fixed+mtax+fsa+surcharge+ed

    return {
        "Category": category,
        "Units Consumed": round(units,2),
        "Bill Days": bill_days,
        "Load (KW)": load_kw,
        "Slabs": [
            ("Slab 1", slab1_units, rates[0] if category!="Category 1 (Upto 2 KW & 100 Units)" else [2.20,2.70,0][0], slab1_units* (rates[0] if category!="Category 1" else [2.20,2.70,0][0]), "Units × Rate"),
            ("Slab 2", slab2_units, rates[1] if category!="Category 1" else [2.20,2.70,0][1], slab2_units* (rates[1] if category!="Category 1" else [2.20,2.70,0][1]), "Units × Rate"),
            ("Slab 3", slab3_units, rates[2] if category=="Category 2" else ([0,0,0][2] if category=="Category 1" else rates[2]), slab3_units* (rates[2] if category=="Category 2" or category=="Category 3" else 0), "Units × Rate"),
        ],
        "Energy Charges": round(energy,2),
        "Fixed Charges": round(fixed,2),
        "FSA": round(fsa,2),
        "Municipal Tax (M-Tax)": mtax,
        "Electricity Duty (ED)": ed,
        "Surcharge": surcharge,
        "Surcharge Note": surcharge_note,
        "Total Bill": round(total,2),
        "Grace Period Ends": last_grace_date
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

    # Summary Metrics
    for key in ["Units Consumed","Bill Days","Load (KW)","Energy Charges","Fixed Charges","FSA","Municipal Tax (M-Tax)","Electricity Duty (ED)","Surcharge","Total Bill"]:
        st.markdown(f"<p class='metric'>{key}: <span class='value'>₹{result[key]:.2f}</span></p>" if "Charges" in key or key in ["FSA","M-Tax","ED","Surcharge","Total Bill"] else f"<p class='metric'>{key}: <span class='value'>{result[key]}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='metric'>Surcharge Note: <span class='value'>{result['Surcharge Note']}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='metric'>Grace Period Ends On: <span class='value'>{result['Grace Period Ends'].strftime('%d-%m-%Y')}</span></p>", unsafe_allow_html=True)

    # ------------------ Bill Breakout Table ------------------ #
    st.markdown("<h3>🔍 Bill Breakout</h3>", unsafe_allow_html=True)

    table_html = "<table><tr><th>Component</th><th>Units</th><th>Rate</th><th>Amount</th><th>Calculation Base</th></tr>"
    # Slabs
    for slab in result["Slabs"]:
        table_html += f"<tr><td>{slab[0]}</td><td>{slab[1]:.2f}</td><td>{slab[2]:.2f}</td><td>{slab[3]:.2f}</td><td>{slab[4]}</td></tr>"
    # Fixed
    table_html += f"<tr><td>Fixed Charges</td><td>-</td><td>-</td><td>{result['Fixed Charges']:.2f}</td><td>Load × Rate × Days</td></tr>"
    # FSA
    table_html += f"<tr><td>FSA</td><td>-</td><td>0.47</td><td>{result['FSA']:.2f}</td><td>Units × 0.47 if units>200 else 0</td></tr>"
    # M-Tax
    table_html += f"<tr><td>M-Tax</td><td>-</td><td>2%</td><td>{result['Municipal Tax (M-Tax)']:.2f}</td><td>(Energy+Fixed+FSA) × 2%</td></tr>"
    # ED
    table_html += f"<tr><td>Electricity Duty (ED)</td><td>-</td><td>0.10</td><td>{result['Electricity Duty (ED)']:.2f}</td><td>Units × 0.10</td></tr>"
    # Surcharge
    table_html += f"<tr><td>Surcharge</td><td>-</td><td>-</td><td>{result['Surcharge']:.2f}</td><td>(Energy+FSA+Fixed) × Rate</td></tr>"
    # Total
    table_html += f"<tr class='total-row'><td colspan='3'>Total Bill</td><td>{result['Total Bill']:.2f}</td><td>-</td></tr>"
    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)

    # ------------------ Footer ------------------ #
    st.markdown("<div class='footer'>Created by <b>ANKIT GAUR</b></div>", unsafe_allow_html=True)




















