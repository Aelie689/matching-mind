import streamlit as st
import pyrebase
from firebase_config import firebase_config
import datetime

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# ----------------------------
# ✅ โหลดรหัสลับจาก Firebase
# ----------------------------
@st.cache_data(ttl=300)
def load_hotel_secrets():
    try:
        data = db.child("hotel_secrets").get()
        return data.val() if data.val() else {}
    except Exception as e:
        st.error(f"❌ โหลดรหัสลับไม่สำเร็จ: {e}")
        return {}

HOTEL_SECRETS = load_hotel_secrets()

# ----------------------------
# ✅ ตรวจสอบ session login
# ----------------------------
if "user" not in st.session_state:
    st.sidebar.title("🔐 เข้าสู่ระบบหรือสมัครสมาชิก")

    menu = st.sidebar.selectbox("เลือกเมนู", ["เข้าสู่ระบบ", "สมัครสมาชิก"])
    email = st.sidebar.text_input("อีเมล")
    password = st.sidebar.text_input("รหัสผ่าน", type="password")
    hotel_name = st.sidebar.selectbox("เลือกโรงแรม", list(HOTEL_SECRETS.keys()))
    hotel_secret = st.sidebar.text_input("รหัสลับประจำโรงแรม", type="password")

    if menu == "สมัครสมาชิก":
        if st.sidebar.button("สมัครสมาชิก"):
            if "@" not in email or "." not in email:
                st.sidebar.warning("⚠️ กรุณาใช้อีเมลที่ถูกต้อง")
            elif len(password) < 6:
                st.sidebar.warning("⚠️ รหัสผ่านต้องมีอย่างน้อย 6 ตัว")
            elif hotel_secret != HOTEL_SECRETS.get(hotel_name, ""):
                st.sidebar.warning("❌ รหัสลับไม่ถูกต้อง")
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
                if hotel_secret != HOTEL_SECRETS.get(hotel_name, ""):
                    st.sidebar.warning("❌ รหัสลับไม่ถูกต้อง")
                else:
                    st.session_state["user"] = user
                    st.session_state["hotel"] = hotel_name
                    st.rerun()
            except Exception as e:
                st.sidebar.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")

# ----------------------------
# ✅ ผู้ใช้เข้าสู่ระบบแล้ว
# ----------------------------
else:
    st.sidebar.success(f"🎉 เข้าสู่ระบบแล้ว: {st.session_state['hotel']}")
    if st.sidebar.button("ออกจากระบบ"):
        st.session_state.clear()
        st.rerun()

    hotel = st.session_state["hotel"]
    tab1, tab2 = st.tabs(["👩‍🍳 สูตรอาหารในครัว", "🧼 สูตรแม่บ้าน"])

    # ----------------------------
    # 🍳 สูตรอาหาร
    # ----------------------------
    with tab1:
        st.title("📒 สูตรอาหารภายในโรงแรม")
        name = st.text_input("ชื่อสูตรอาหาร")
        content = st.text_area("รายละเอียด/ส่วนผสม/วิธีทำ")

        if st.button("💾 บันทึกสูตร"):
            if name and content:
                recipe = {
                    "name": name,
                    "content": content,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                db.child("recipes").child(hotel).push(recipe)
                st.success(f"✅ บันทึก '{name}' เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.warning("⚠️ กรุณาใส่ชื่อและรายละเอียดให้ครบ")

        st.divider()
        st.subheader("🔍 ค้นหาสูตรอาหาร")
        search = st.text_input("พิมพ์คำค้น เช่น 'ผัดไทย' หรือ 'ซุป'")

        recipes = db.child("recipes").child(hotel).get().val() or {}
        for key, recipe in reversed(list(recipes.items())):
            if search.lower() in recipe["name"].lower() or search.lower() in recipe["content"].lower():
                st.markdown(f"### 🍽️ {recipe['name']}")
                st.caption(f"🕒 บันทึกเมื่อ {recipe['timestamp']}")
                st.write(recipe["content"])
                if st.button(f"🗑 ลบสูตร '{recipe['name']}'", key=f"delete_recipe_{key}"):
                    db.child("recipes").child(hotel).child(key).remove()
                    st.success(f"✅ ลบสูตร '{recipe['name']}' แล้ว")
                    st.rerun()
                st.divider()

    # ----------------------------
    # 🧼 สูตรแม่บ้าน
    # ----------------------------
    with tab2:
        st.header("🧼 สูตรแม่บ้าน (น้ำยาทำความสะอาด ฯลฯ)")
        name2 = st.text_input("ชื่อสูตรแม่บ้าน", key="house_name")
        content2 = st.text_area("รายละเอียดวิธีใช้/ปริมาณ/อัตราส่วน", key="house_content")

        if st.button("💾 บันทึกสูตรแม่บ้าน"):
            if name2 and content2:
                house_recipe = {
                    "name": name2,
                    "content": content2,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                db.child("house_recipes").child(hotel).push(house_recipe)
                st.success(f"✅ บันทึกสูตรแม่บ้าน '{name2}' แล้วค่ะ")
                st.rerun()
            else:
                st.warning("⚠️ กรุณาใส่ชื่อและรายละเอียดให้ครบ")

        st.divider()
        search2 = st.text_input("🔍 ค้นหาสูตรแม่บ้าน", key="search_house")
        house_data = db.child("house_recipes").child(hotel).get().val() or {}
        for key, recipe in reversed(list(house_data.items())):
            if search2.lower() in recipe["name"].lower() or search2.lower() in recipe["content"].lower():
                st.markdown(f"### 🧽 {recipe['name']}")
                st.caption(f"🕒 บันทึกเมื่อ {recipe['timestamp']}")
                st.write(recipe["content"])
                if st.button(f"🗑 ลบสูตรแม่บ้าน '{recipe['name']}'", key=f"delete_house_{key}"):
                    db.child("house_recipes").child(hotel).child(key).remove()
                    st.success(f"✅ ลบสูตรแม่บ้าน '{recipe['name']}' แล้วค่ะ")
                    st.rerun()
                st.divider()
