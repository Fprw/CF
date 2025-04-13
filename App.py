import streamlit as st
import pandas as pd
import base64
import json
import os

# إعداد الصفحة
st.set_page_config(page_title="CleanFoam", page_icon="✅")
st.title("CleanFoam")

# تحديد بيانات تسجيل الدخول
user_credentials = {
    "user": "12345",  # كلمة مرور المستخدم
    "admin": "CF3010"  # كلمة مرور المشرف
}

# واجهة تسجيل الدخول في الشريط الجانبي
st.sidebar.subheader("Login")

role = st.sidebar.radio("Select Role", ["user", "admin"])

# إدخال كلمة المرور
password = st.sidebar.text_input("Enter Password", type="password")

# التحقق من كلمة المرور
if role == "user" and password == user_credentials["user"]:
    st.session_state.role = "user"
elif role == "admin" and password == user_credentials["admin"]:
    st.session_state.role = "admin"
else:
    st.session_state.role = None
    st.error("Invalid credentials")

# الآن سنعرض المحتوى بناءً على الدور الذي تم تحديده:
if st.session_state.role == "user":
    # واجهة المستخدم
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

        # إرسال البيانات
        st.markdown("### إرسال البيانات")
        if st.button("إرسال"):
            folder = "submissions"
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, f"{manual_date}.json")
            with open(filepath, "w") as f:
                json.dump(st.session_state.workers, f, indent=2)
            st.success(f"تم إرسال البيانات باسم {manual_date}")

else:
    # واجهة المشرف
    if st.session_state.role == "admin":
        st.subheader("Admin View")

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
