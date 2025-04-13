import streamlit as st
import pandas as pd
import base64
import json
import os

# إعداد الصفحة
st.set_page_config(page_title="CleanFoam", page_icon="✅")
st.title("CleanFoam")

# تحديد دور المستخدم
if 'role' not in st.session_state:
    st.session_state.role = "user"  # القيمة الافتراضية للمستخدم العادي

# اختيار دور المستخدم
st.sidebar.subheader("Choose your role")
role = st.sidebar.radio("Select Role", ["user", "admin"])

# تغيير الدور عند الاختيار
if role != st.session_state.role:
    st.session_state.role = role
    st.experimental_rerun()

# Session state init
if 'workers' not in st.session_state:
    st.session_state.workers = []
if 'received_status' not in st.session_state:
    st.session_state.received_status = {}
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

# دالة تنظيف الأرقام
def clean_number(n):
    return int(n) if n == int(n) else n

# إدخال التاريخ
st.subheader("Today's Date")
manual_date = st.text_input("Date", st.session_state.manual_date_input)
st.session_state.manual_date_input = manual_date

# إضافة عامل
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
                data = {
                    "Worker": name,
                    "Total": clean_number(value_f),
                    "Due": "",
                    "Withdrawn": "",
                    "Remaining": "",
                    "Received": False
                }
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

                data = {
                    "Worker": name,
                    "Total": clean_number(value_f),
                    "Due": clean_number(fee),
                    "Withdrawn": clean_number(withdrawn_f),
                    "Remaining": clean_number(final_amount),
                    "Received": False
                }

            st.session_state.workers.append(data)
            st.session_state.received_status[name] = False

            # Clear inputs
            st.session_state.name_input = ""
            st.session_state.value_input = ""
            st.session_state.withdrawn_input = ""
            st.session_state.due_input = ""

            st.rerun()

        except ValueError:
            st.error("Please enter valid numbers.")
    else:
        st.warning("Please fill in at least date, name, and total.")

# عرض الجدول
if st.session_state.workers:
    st.markdown(f"### Workers Table — Date: **{manual_date}**")

    display_df = pd.DataFrame(st.session_state.workers)

    # التحكم في Received لكل عامل (المشرف فقط)
    if st.session_state.role == "admin":
        for i, worker in enumerate(display_df["Worker"]):
            received_key = f"received_{i}"
            if received_key not in st.session_state:
                st.session_state[received_key] = display_df.at[i, "Received"]

            st.session_state[received_key] = st.checkbox(
                f"Received: {worker}", value=st.session_state[received_key]
            )
            display_df.at[i, "Received"] = st.session_state[received_key]

    # تلوين الصفوف التي تحتوي على Remaining سالب
    def highlight_negative(val):
        return 'background-color: #ffcccc' if val < 0 else ''

    styled_df = display_df.style.applymap(highlight_negative, subset=["Remaining"])

    st.dataframe(styled_df, use_container_width=True)

    # حساب المجموع
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
    if st.session_state.role == "admin":
        st.markdown("### Delete")
        worker_names = [w['Worker'] for w in st.session_state.workers]
        selected_worker = st.selectbox("Select worker to delete", worker_names)

        if st.button("Delete"):
            st.session_state.workers = [w for w in st.session_state.workers if w['Worker'] != selected_worker]
            st.success(f"Worker '{selected_worker}' has been deleted.")
            st.rerun()

    # إرسال البيانات
    if st.session_state.role == "user":
        st.markdown("### إرسال البيانات")
        if st.button("إرسال"):
            folder = "submissions"
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, f"{manual_date}.json")
            with open(filepath, "w") as f:
                json.dump(st.session_state.workers, f, indent=2)
            st.success(f"تم إرسال البيانات باسم {manual_date}")
    else:
        # عرض البيانات المرسلة من قبل المستخدمين
        st.markdown("### Sent Data")
        folder = "submissions"
        files = [f for f in os.listdir(folder) if f.endswith(".json")]

        if not files:
            st.info("لا توجد بيانات مرسلة بعد.")
        else:
            selected_file = st.selectbox("اختر التاريخ", files)
            filepath = os.path.join(folder, selected_file)

            with open(filepath, "r") as f:
                data = json.load(f)

            df = pd.DataFrame(data)
            st.markdown(f"### البيانات من: **{selected_file.replace('.json', '')}**")

            for i in range(len(df)):
                received_key = f"received_{i}"
                df.at[i, "Received"] = st.checkbox(
                    f"Received: {df.at[i, 'Worker']}", value=df.at[i]["Received"], key=received_key
                )

            if st.button("حفظ"):
                with open(filepath, "w") as f:
                    json.dump(df.to_dict(orient="records"), f, indent=2)
                st.success("تم الحفظ بنجاح.")

            st.dataframe(df, use_container_width=True)

else:
    st.info("No workers added yet.")
