import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="CleanFoam Unified App", page_icon="✅", layout="wide")
st.title("CleanFoam System")

# تسجيل الدخول
credentials = {
    "M": "12345",
    "Admin": "CF3010"
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in credentials and credentials[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Logged in successfully.")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

is_admin = st.session_state.username == "Admin"

# تهيئة المتغيرات
if 'workers' not in st.session_state:
    st.session_state.workers = []
if 'name_input' not in st.session_state:
    st.session_state.name_input = ""
if 'value_input' not in st.session_state:
    st.session_state.value_input = ""
if 'withdrawn_input' not in st.session_state:
    st.session_state.withdrawn_input = ""
if 'due_input' not in st.session_state:
    st.session_state.due_input = ""
if 'manual_date_input' not in st.session_state:
    st.session_state.manual_date_input = ""

def clean_number(n):
    return int(n) if n == int(n) else n

def user_interface():
    st.subheader("Today's Date")
    manual_date = st.text_input("Date", st.session_state.manual_date_input)
    st.session_state.manual_date_input = manual_date

    st.subheader("Add Worker")
    name = st.text_input("Name", st.session_state.name_input)
    value = st.text_input("Enter the total :", st.session_state.value_input)
    withdrawn = st.text_input("Enter the withdrawn:", st.session_state.withdrawn_input)
    due_optional = st.text_input("Enter custom Due (optional):", st.session_state.due_input)
    is_cf = st.checkbox("CF")

    if st.button("OK"):
        if manual_date and name and value:
            try:
                value_f = float(value)
                withdrawn_f = float(withdrawn) if withdrawn else 0
                due_custom = float(due_optional) if due_optional else None

                if is_cf:
                    st.session_state.workers.append({
                        "Worker": name,
                        "Total": clean_number(value_f),
                        "Due": "",
                        "Withdrawn": "",
                        "Remaining": "",
                        "Received": False
                    })
                else:
                    half_value = value_f / 2
                    after_withdraw = half_value - withdrawn_f

                    if due_custom is not None:
                        fee = due_custom
                    elif half_value == 40:
                        fee = 20
                    elif half_value == 45:
                        fee = 20
                    elif half_value == 50:
                        fee = 25
                    elif half_value == 52.5:
                        fee = 27.5
                    elif half_value == 55:
                        fee = 25
                    elif value_f == 95:
                        fee = 22.5
                    elif int(value_f) % 10 == 5:
                        fee = 32.5
                    else:
                        fee = 30

                    final_amount = after_withdraw - fee

                    st.session_state.workers.append({
                        "Worker": name,
                        "Total": clean_number(value_f),
                        "Due": clean_number(fee),
                        "Withdrawn": clean_number(withdrawn_f),
                        "Remaining": clean_number(final_amount),
                        "Received": False
                    })

                st.session_state.name_input = ""
                st.session_state.value_input = ""
                st.session_state.withdrawn_input = ""
                st.session_state.due_input = ""

                st.rerun()

            except ValueError:
                st.error("Please enter valid numbers.")
        else:
            st.warning("Please fill in at least date, name, and total.")

    if st.session_state.workers:
        df = pd.DataFrame(st.session_state.workers)
        df = df[["Worker", "Total", "Due", "Withdrawn", "Remaining", "Received"]]

        # صف التاريخ في الزاوية اليمنى
        date_row = pd.DataFrame([{
            "Worker": "",
            "Total": "",
            "Due": "",
            "Withdrawn": "",
            "Remaining": "",
            "Received": f"Date: {manual_date}"
        }])
        df_with_date = pd.concat([date_row, df], ignore_index=True)

        st.markdown("### Workers Table")
        def highlight_negative(val):
            return 'background-color: #ffcccc;' if isinstance(val, (int, float)) and val < 0 else ''
        styled_df = df_with_date.style.applymap(highlight_negative, subset=["Remaining"])
        st.dataframe(styled_df, use_container_width=True)

        total_sum = sum([w['Total'] for w in st.session_state.workers if isinstance(w['Total'], (int, float))])
        for_workera = sum([
            (w['Withdrawn'] if isinstance(w['Withdrawn'], (int, float)) else 0) +
            (w['Remaining'] if isinstance(w['Remaining'], (int, float)) else 0)
            for w in st.session_state.workers
        ])
        for_cleanfoam = total_sum - for_workera

        st.markdown(f"### Total: **{clean_number(total_sum)}**")
        st.markdown(f"**For workera:** {clean_number(for_workera)}")
        st.markdown(f"**For CleanFoam:** {clean_number(for_cleanfoam)}")

        # حذف عامل
        st.markdown("### Delete")
        worker_names = [w['Worker'] for w in st.session_state.workers]
        selected_worker = st.selectbox("Select worker to delete", worker_names)
        if st.button("Delete"):
            st.session_state.workers = [w for w in st.session_state.workers if w['Worker'] != selected_worker]
            st.success(f"Worker '{selected_worker}' has been deleted.")
            st.rerun()

        # إرسال البيانات
        if st.button("Send"):
            save_dir = "submissions"
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, f"{manual_date}.csv")
            pd.DataFrame(st.session_state.workers).to_csv(filepath, index=False)
            st.success(f"Data saved as '{filepath}'")
    else:
        st.info("No workers added yet.")

def admin_interface():
    st.subheader("Admin Panel")
    folder = "submissions"
    files = os.listdir(folder) if os.path.exists(folder) else []
    if files:
        selected_file = st.selectbox("Select submission date", files)
        df = pd.read_csv(os.path.join(folder, selected_file))
        edited_df = st.data_editor(df, num_rows="dynamic")
        if st.button("Save Changes"):
            edited_df.to_csv(os.path.join(folder, selected_file), index=False)
            st.success("Changes saved.")
    else:
        st.info("No submissions found.")

# واجهة حسب المستخدم
if is_admin:
    admin_interface()
else:
    user_interface()
