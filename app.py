import streamlit as st
import pyrebase
from firebase_config import firebase_config
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# 🧠 โปรไฟล์จำลอง
profiles = {
    "มุก": [0.9, 0.8, 0.3],
    "แทน": [0.7, 0.6, 0.4],
    "ใบเฟิร์น": [0.2, 0.3, 0.9],
    "ซันนี่": [0.8, 0.7, 0.2],
    "พลอย": [0.4, 0.5, 0.8],
}

# 📌 ตรวจสอบ session login
if "user" not in st.session_state:
    st.sidebar.title("🔐 เข้าสู่ระบบหรือสมัครสมาชิก")

    menu = st.sidebar.selectbox("เลือกเมนู", ["เข้าสู่ระบบ", "สมัครสมาชิก"])
    email = st.sidebar.text_input("อีเมล")
    password = st.sidebar.text_input("รหัสผ่าน", type="password")

    if menu == "สมัครสมาชิก":
        if st.sidebar.button("สมัครสมาชิก"):
            if "@" not in email or "." not in email:
                st.sidebar.warning("⚠️ กรุณาใช้อีเมลที่ถูกต้อง")
            elif len(password) < 6:
                st.sidebar.warning("⚠️ รหัสผ่านต้องมีอย่างน้อย 6 ตัว")
            else:
                try:
                    auth.create_user_with_email_and_password(email, password)
                    st.sidebar.success("✅ สมัครสำเร็จ! กรุณาเข้าสู่ระบบ")
                except Exception as e:
                    st.sidebar.error(f"เกิดข้อผิดพลาด: {e}")

    elif menu == "เข้าสู่ระบบ":
        if st.sidebar.button("เข้าสู่ระบบ"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state["user"] = user
                st.experimental_rerun()
            except Exception as e:
                st.sidebar.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")

else:
    # ✅ ผู้ใช้เข้าสู่ระบบแล้ว
    st.sidebar.success("🎉 คุณได้เข้าสู่ระบบแล้ว")
    if st.sidebar.button("ออกจากระบบ"):
        st.session_state.clear()
        st.experimental_rerun()

    # ----------------------------
    # 🌟 หน้าแอพหลัก (จับคู่ Mind Profile)
    # ----------------------------

    st.title("🧠 Matching Mind")
    st.subheader("🤝 จับคู่คนที่มี Mind Profile คล้ายกัน")

    st.write("💬 ใส่โปรไฟล์ของคุณ")
    self_reflection = st.slider("Self Reflection", 0.0, 1.0, 0.5)
    emotional_openness = st.slider("Emotional Openness", 0.0, 1.0, 0.5)
    fear_of_judgment = st.slider("Fear of Judgment", 0.0, 1.0, 0.5)

    user_profile = [self_reflection, emotional_openness, fear_of_judgment]

    if st.button("🔍 ค้นหาเพื่อนที่ใกล้คุณที่สุด"):
        df = pd.DataFrame.from_dict(profiles, orient='index', columns=[
            "SelfReflection", "EmotionalOpenness", "FearOfJudgment"
        ])
        df["Distance"] = euclidean_distances([user_profile], df.values)[0]
        best_match = df["Distance"].idxmin()

        st.success(f"✅ เพื่อนที่ใกล้เคียงกับคุณที่สุดคือ **{best_match}**")
        st.write("🎯 ความใกล้:", round(df["Distance"].min(), 4))
        st.subheader("👥 โปรไฟล์ของเขา:")
        st.dataframe(df.loc[[best_match]].drop(columns="Distance"))
