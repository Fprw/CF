import os
import json
import streamlit as st
import pandas as pd

def clean_number(n):
    return int(n) if n == int(n) else n

st.set_page_config(page_title="CleanFoam Admin", page_icon="✅")
st.title("CleanFoam - Admin Panel")

# --- تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.error("يرجى تسجيل الدخول من الواجهة الرئيسية.")
    st.stop()

if st.session_state.role != "admin":
    st.warning("هذه الواجهة مخصصة للمشرف فقط.")
    st.stop()

# --- واجهة المشرف ---
folder = os.path.join(".", "submissions")
os.makedirs(folder, exist_ok=True)

files = [f for f in os.listdir(folder) if f.endswith(".json")]
if not files:
    st.warning("لا توجد ملفات بعد.")
    st.stop()

selected_file = st.selectbox("اختر تاريخ الملف", files)
filepath = os.path.join(folder, selected_file)

with open(filepath, "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# تعديل Received
st.subheader("تحديث Received")
for i, row in df.iterrows():
    current = row.get("Received", False)
    updated = st.checkbox(f"{row['Worker']}", value=current, key=f"chk_{i}")
    df.at[i, "Received"] = updated

# تلوين الصفوف
def highlight_negative_rows_admin(row):
    color = '#ffcccc' if isinstance(row["Remaining"], (int, float)) and row["Remaining"] < 0 else ''
    return ['background-color: {}'.format(color)] * len(row)

styled_df = df.style.apply(highlight_negative_rows_admin, axis=1)
st.markdown("### البيانات")
st.dataframe(styled_df, use_container_width=True)

if st.button("حفظ التعديلات"):
    with open(filepath, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)
    st.success("تم حفظ التعديلات بنجاح.")
