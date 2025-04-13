import streamlit as st
import pandas as pd
import base64
import os
import json

# تسجيل الدخول
def login():
    st.title("تسجيل الدخول")
    user_type = st.selectbox("اختر نوع المستخدم", ["مستخدم", "مشرف"])
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("تسجيل الدخول"):
        if user_type == "مستخدم" and username == "M" and password == "12345":
            st.session_state.logged_in = True
            st.session_state.user_type = "مستخدم"
            st.success("تم تسجيل الدخول كمستخدم!")
            st.experimental_rerun()
        elif user_type == "مشرف" and username == "Admin" and password == "CF3010":
            st.session_state.logged_in = True
            st.session_state.user_type = "مشرف"
            st.success("تم تسجيل الدخول كمشرف!")
            st.experimental_rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")

# التحقق من حالة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    # تهيئة البيانات إذا لم تكن موجودة في الحالة
    if 'workers' not in st.session_state:
        st.session_state.workers = []
    
    # إذا كان المستخدم قد سجل الدخول
    if st.session_state.user_type == "مستخدم":
        # واجهة المستخدم
        st.title("واجهة المستخدم")
        
        # إضافة البيانات
        st.subheader("إضافة عامل")
        if 'manual_date_input' not in st.session_state:
            st.session_state.manual_date_input = ""

        manual_date = st.text_input("تاريخ", st.session_state.manual_date_input)
        st.session_state.manual_date_input = manual_date

        name = st.text_input("اسم العامل")
        value = st.text_input("إجمالي المبلغ:")
        withdrawn = st.text_input("المبلغ المسحوب:")
        due_optional = st.text_input("المبلغ المستحق (اختياري):")
        is_cf = st.checkbox("CF")

        # تهيئة received_status
        if 'received_status' not in st.session_state:
            st.session_state.received_status = {}

        if st.button("OK"):
            if manual_date and name and value:
                try:
                    value_f = float(value)
                    withdrawn_f = float(withdrawn) if withdrawn else 0
                    due_custom = float(due_optional) if due_optional else None

                    if is_cf:
                        data = {
                            "Worker": name,
                            "Total": int(value_f),
                            "Due": "",
                            "Withdrawn": "",
                            "Remaining": "",
                            "Received": False
                        }
                    else:
                        half_value = value_f / 2
                        after_withdraw = half_value - withdrawn_f
                        fee = due_custom if due_custom is not None else 30

                        final_amount = after_withdraw - fee
                        data = {
                            "Worker": name,
                            "Total": int(value_f),
                            "Due": int(fee),
                            "Withdrawn": int(withdrawn_f),
                            "Remaining": int(final_amount),
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
                    st.error("يرجى إدخال أرقام صحيحة.")
            else:
                st.warning("يرجى ملء الحقول المطلوبة.")

        if st.session_state.workers:
            display_df = pd.DataFrame(st.session_state.workers)
            st.dataframe(display_df)

            # حفظ البيانات كملف
            if st.button("حفظ البيانات"):
                folder = "submissions"
                if not os.path.exists(folder):
                    os.makedirs(folder)

                filepath = os.path.join(folder, f"{manual_date}.json")
                with open(filepath, "w") as f:
                    json.dump(st.session_state.workers, f, indent=2)

                st.success(f"تم حفظ البيانات تحت اسم {manual_date}.json")
    elif st.session_state.user_type == "مشرف":
        # واجهة المشرف
        st.title("واجهة المشرف")

        # تأكد من تهيئة البيانات في حالة عدم وجودها
        if 'workers' not in st.session_state:
            st.session_state.workers = []

        if st.session_state.workers:
            display_df = pd.DataFrame(st.session_state.workers)

            # عرض جميع البيانات مع إمكانية تعديل خيار "Received"
            for i, worker in enumerate(display_df["Worker"]):
                received_key = f"received_{i}"
                if received_key not in st.session_state:
                    st.session_state[received_key] = display_df.at[i, "Received"]

                st.session_state[received_key] = st.checkbox(
                    f"Received: {worker}", value=st.session_state[received_key]
                )
                display_df.at[i, "Received"] = st.session_state[received_key]

            # تلوين الصفوف التي تحتوي على "Remaining" سالب
            def highlight_negative(val):
                return 'background-color: #ffcccc' if val < 0 else ''

            styled_df = display_df.style.applymap(highlight_negative, subset=["Remaining"])

            st.dataframe(styled_df)

            # حفظ البيانات بعد التعديل
            if st.button("حفظ التعديلات"):
                folder = "admin_submissions"
                if not os.path.exists(folder):
                    os.makedirs(folder)

                filepath = os.path.join(folder, f"admin_{st.session_state.manual_date_input}.json")
                with open(filepath, "w") as f:
                    json.dump(st.session_state.workers, f, indent=2)

                st.success(f"تم حفظ التعديلات تحت اسم {st.session_state.manual_date_input}.json")
        else:
            st.info("لا توجد بيانات حالياً.")
