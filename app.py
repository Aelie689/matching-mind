import streamlit as st
import pyrebase
from firebase_config import firebase_config
import datetime
import math

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# ----------------------------
# ✅ โหลดรหัสลับจาก Firebase
# ----------------------------
@st.cache_data(ttl=300)
def load_hotel_secrets(id_token=None):
    try:
        if id_token:
            data = db.child("hotel_secrets").get(id_token)
        else:
            data = db.child("hotel_secrets").get()
        return data.val() if data.val() else {}
    except Exception as e:
        st.error(f"❌ โหลดรหัสลับไม่สำเร็จ: {e}")
        return {}



# ----------------------------
# ✅ ตรวจสอบ session login
# ----------------------------
if "user" not in st.session_state:
    st.sidebar.title("🔐 เข้าสู่ระบบหรือสมัครสมาชิก")

    menu = st.sidebar.selectbox("เลือกเมนู", ["เข้าสู่ระบบ", "สมัครสมาชิก"])
    email = st.sidebar.text_input("อีเมล")
    password = st.sidebar.text_input("รหัสผ่าน", type="password")

    hotel_secrets = {}

    # โหลด secrets ด้วย service account (ถ้า login แล้วจะโหลดด้วย idToken)
    try:
        user_temp = auth.sign_in_with_email_and_password(email, password)
        hotel_secrets = load_hotel_secrets(user_temp['idToken'])
    except:
        hotel_secrets = {}  # ยังไม่ login ก็โหลดไม่ได้

    hotel_secrets = load_hotel_secrets()  # ไม่ต้องใช้ id_token
    hotel_name = st.sidebar.selectbox("เลือกโรงแรม", list(hotel_secrets.keys()) if hotel_secrets else ["-"])
    hotel_secret = st.sidebar.text_input("รหัสลับประจำโรงแรม", type="password")

    if menu == "สมัครสมาชิก":
        if st.sidebar.button("สมัครสมาชิก"):
            if "@" not in email or "." not in email:
                st.sidebar.warning("⚠️ กรุณาใช้อีเมลที่ถูกต้อง")
            elif len(password) < 6:
                st.sidebar.warning("⚠️ รหัสผ่านต้องมีอย่างน้อย 6 ตัว")
            elif hotel_secret != hotel_secrets.get(hotel_name, ""):
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
                hotel_secrets = load_hotel_secrets(user['idToken'])

                if hotel_secret != hotel_secrets.get(hotel_name, ""):
                    st.sidebar.warning("❌ รหัสลับไม่ถูกต้อง")
                else:
                    st.session_state["user"] = user
                    st.session_state["hotel"] = hotel_name
                    st.session_state["hotel_secrets"] = hotel_secrets
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
    selected_tab = st.selectbox("📁 เลือกเมนูหลัก", [
    "👩‍🍳 สูตรอาหารในครัว",
    "📋 บันทึกงานประจำวัน",
    "🕒 ลงเวลางาน",
    "📑 รายงานห้องพัก",
    "📦 บันทึกวัตถุดิบ",
    "🍳 เมนูที่ทำในแต่ละวัน",
    "💰 รายรับรายวัน"
])

    # ----------------------------
    # 🍳 สูตรอาหาร
    # ----------------------------
    if selected_tab == "👩‍🍳 สูตรอาหารในครัว":
        st.title("📒 สูตรอาหารภายในโรงแรม")

        name = st.text_input("ชื่อสูตรอาหาร")
        content = st.text_area("รายละเอียด/ส่วนผสม/วิธีทำ")

        st.subheader("📦 วัตถุดิบในสูตร")
        if "recipe_ingredients" not in st.session_state:
            st.session_state["recipe_ingredients"] = []

        with st.form("add_recipe_ingredient_form", clear_on_submit=True):
            cols = st.columns([3, 2, 2])
            ing_name = cols[0].text_input("ชื่อวัตถุดิบ", key="rec_ing_name")
            ing_qty = cols[1].number_input("ปริมาณที่ใช้", min_value=0.0, step=0.1, key="rec_ing_qty")
            ing_unit = cols[2].selectbox("หน่วย", ["กรัม", "กิโลกรัม"], key="rec_ing_unit")
            submitted = st.form_submit_button("➕ เพิ่มวัตถุดิบในสูตร")

            if submitted and ing_name:
                st.session_state["recipe_ingredients"].append({
                    "name": ing_name,
                    "qty": ing_qty,
                    "unit": ing_unit
                })

        if st.session_state["recipe_ingredients"]:
            st.subheader("📋 รายการวัตถุดิบในสูตร")
            for idx, ing in enumerate(st.session_state["recipe_ingredients"]):
                st.write(f"🟩 {ing['name']} - {ing['qty']} {ing['unit']}")
                if st.button(f"❌ ลบวัตถุดิบ", key=f"del_recipe_ing_{idx}"):
                    st.session_state["recipe_ingredients"].pop(idx)
                    st.rerun()

        if st.button("💾 บันทึกสูตร"):
            if name and content:
                recipe = {
                    "name": name,
                    "content": content,
                    "ingredients": st.session_state["recipe_ingredients"],
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                db.child("recipes").child(hotel).push(recipe)
                st.success(f"✅ บันทึก '{name}' เรียบร้อยแล้ว")
                st.session_state["recipe_ingredients"] = []
                st.rerun()
            else:
                st.warning("⚠️ กรุณาใส่ชื่อและรายละเอียดให้ครบ")

        # 🔍 ค้นหาสูตรอาหาร
        st.divider()
        st.subheader("🔍 ค้นหาสูตรอาหาร")
        search = st.text_input("พิมพ์คำค้น เช่น 'ผัดไทย' หรือ 'ไข่เจียว'")

        recipes = db.child("recipes").child(hotel).get().val() or {}
        for key, recipe in reversed(list(recipes.items())):
            if search.lower() in recipe["name"].lower() or search.lower() in recipe["content"].lower():
                st.markdown(f"### 🍽️ {recipe['name']}")
                st.caption(f"🕒 บันทึกเมื่อ {recipe['timestamp']}")
                st.write(recipe["content"])

                # ✅ แสดงวัตถุดิบในสูตร
                if "ingredients" in recipe and recipe["ingredients"]:
                    st.markdown("**📦 วัตถุดิบในสูตร:**")
                    for ing in recipe["ingredients"]:
                        st.write(f"- {ing['name']} {ing['qty']} {ing['unit']}")

                if st.button(f"🗑 ลบสูตร '{recipe['name']}'", key=f"delete_recipe_{key}"):
                    db.child("recipes").child(hotel).child(key).remove()
                    st.success(f"✅ ลบสูตร '{recipe['name']}' แล้ว")
                    st.rerun()
                st.divider()


    # ----------------------------
    # 📋 บันทึกงานประจำวัน
    # ----------------------------
    elif selected_tab == "📋 บันทึกงานประจำวัน":
        st.header("📋 งานที่คุณทำวันนี้")

        today = datetime.date.today()
        today_str = today.strftime('%Y-%m-%d')

        emp_name = st.text_input("👤 ชื่อพนักงาน")
        task = st.text_area("📝 คุณทำอะไรไปบ้างในวันนี้")

        if st.button("✅ บันทึกงานวันนี้"):
            if emp_name and task:
                log = {
                    "name": emp_name,
                    "task": task,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                db.child("work_logs").child(hotel).child(today_str).child(emp_name).set(log)
                st.success(f"✅ บันทึกงานของ {emp_name} เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกชื่อและรายละเอียดงานให้ครบ")

        st.divider()
        st.subheader("📆 งานที่บันทึกไว้แล้ว")

        # 📅 เลือกวันที่เพื่อดูงานย้อนหลัง
        selected_date = st.date_input("เลือกวันที่", value=today, key="worklog_date")
        selected_date_str = selected_date.strftime('%Y-%m-%d')

        logs = db.child("work_logs").child(hotel).child(selected_date_str).get().val() or {}

        if logs:
            for emp_name, entry in logs.items():
                st.markdown(f"👤 **{emp_name}**")
                st.caption(f"🕒 {entry.get('timestamp', '-')}")
                st.write(entry.get("task", "-"))

                if st.button(f"🗑 ลบงานของ {emp_name}", key=f"delete_task_{selected_date_str}_{emp_name}"):
                    db.child("work_logs").child(hotel).child(selected_date_str).child(emp_name).remove()
                    st.success(f"🗑 ลบงานของ {emp_name} แล้วเรียบร้อย")
                    st.rerun()

                st.divider()
        else:
            st.info("🔎 ยังไม่มีงานที่บันทึกไว้สำหรับวันนี้")


    # ----------------------------
    # ⏱ ลงเวลางานเข้า-ออก
    # ----------------------------
    elif selected_tab == "🕒 ลงเวลางาน":
        st.header("🕒 ลงเวลางาน")

        # 🔽 รายชื่อพนักงาน
        EMPLOYEES = ["ดา", "นิว", "ออย", "เอิง", "สาว", "ลุงคม", "โอม", "ไข่"]

        selected_date = st.date_input("📅 เลือกวันที่ต้องการลงเวลา", value=datetime.date.today())
        selected_date_str = selected_date.strftime('%Y-%m-%d')

        name = st.selectbox("👤 เลือกชื่อพนักงาน", EMPLOYEES)
        col1, col2 = st.columns(2)

        if col1.button("✅ ลงเวลาเข้า"):
            db.child("attendance").child(hotel).child(selected_date_str).child(name).update({
                "in_time": datetime.datetime.now().strftime("%H:%M:%S")
            })
            st.success(f"✅ ลงเวลาเข้าเรียบร้อยแล้วสำหรับ {name}")
            st.rerun()

        if col2.button("📄 ลงเวลาออก"):
            db.child("attendance").child(hotel).child(selected_date_str).child(name).update({
                "out_time": datetime.datetime.now().strftime("%H:%M:%S")
            })
            st.success(f"📄 ลงเวลาออกเรียบร้อยแล้วสำหรับ {name}")
            st.rerun()

        st.divider()
        st.subheader("📅 ตารางลงเวลา")

        records = db.child("attendance").child(hotel).child(selected_date_str).get().val() or {}
        if records:
            for emp_name, times in records.items():
                in_time = times.get("in_time", "-")
                out_time = times.get("out_time", "-")
                st.write(f"👤 {emp_name} | ⏱ เข้า: {in_time} | 📄 ออก: {out_time}")
        else:
            st.info("ยังไม่มีพนักงานลงเวลาในวันนี้")

        st.divider()
        st.subheader("📆 สรุปเวลาทำงานรายเดือน")

        selected_emp = st.selectbox("🔍 เลือกชื่อพนักงาน", EMPLOYEES, key="summary_emp")
        selected_month = st.date_input("🗓️ เลือกเดือน", value=datetime.date.today(), key="month_select")

        if selected_emp:
            import math
            month_prefix = selected_month.strftime("%Y-%m")  # eg: 2025-06
            all_data = db.child("attendance").child(hotel).get().val() or {}

            total_hours = datetime.timedelta()

            for date_str, day_records in all_data.items():
                if date_str.startswith(month_prefix):
                    times = day_records.get(selected_emp, {})
                    in_time_str = times.get("in_time")
                    out_time_str = times.get("out_time")

                    if in_time_str and out_time_str:
                        try:
                            in_time = datetime.datetime.strptime(f"{date_str} {in_time_str}", "%Y-%m-%d %H:%M:%S")
                            out_time = datetime.datetime.strptime(f"{date_str} {out_time_str}", "%Y-%m-%d %H:%M:%S")
                            total_hours += (out_time - in_time)
                        except:
                            continue

            total_hours_float = total_hours.total_seconds() / 3600
            display_hours = math.floor(total_hours_float * 100) / 100  # ตัดทศนิยมไม่ปัดเศษ
            st.success(f"💼 รวมเวลาทำงานของ {selected_emp} ในเดือนนี้: {display_hours:.2f} ชั่วโมง")


    # ----------------------------
    # 📋 รายงานห้องพักประจำวัน
    # ----------------------------
    elif selected_tab == "📑 รายงานห้องพัก":
        st.header("📑 รายงานห้องพักประจำวัน")

        selected_date = st.date_input("เลือกวันที่สำหรับรายงาน", value=datetime.date.today())
        selected_date_str = selected_date.strftime('%Y-%m-%d')

        st.caption(f"📅 วันที่รายงาน: {selected_date.strftime('%d/%m/%Y')}")

        # 🔧 โหลดข้อมูลเก่าจาก Firebase ถ้ามี
        stored_data = db.child("room_reports").child(hotel).child(selected_date_str).get().val()
        default_rows = []
        for i in range(1, 21):
            room_name = f"Room {i}"
            if stored_data and room_name in stored_data:
                row = stored_data[room_name]
                default_rows.append({
                    "ห้อง": row.get("room", room_name),
                    "ชื่อลูกค้า": row.get("name", ""),
                    "จำนวนผู้เข้าพัก": row.get("guest", 1),
                    "จำนวนผู้ใหญ่": row.get("adult_abf", 1),
                    "จำนวนเด็ก": row.get("child_abf", 0),
                    "ABF": row.get("abf", "รับ"),
                    "วันที่เข้า": datetime.date.fromisoformat(row.get("in_date", selected_date_str)),
                    "วันที่ออก": datetime.date.fromisoformat(row.get("out_date", selected_date_str)),
                    "รู้จักเราจากช่องทางไหน": row.get("source", "เจอตอนค้นหาโรงแรมบน OTA ระบุ"),
                    "ช่องทางการจอง": row.get("booking_channel", "Walk-in"),
                    "หมายเหตุ": row.get("remark", "")
                })
            else:
                default_rows.append({
                    "ห้อง": room_name,
                    "ชื่อลูกค้า": "",
                    "จำนวนผู้เข้าพัก": 0,
                    "จำนวนผู้ใหญ่": 0,
                    "จำนวนเด็ก": 0,
                    "ABF": "รับ",
                    "วันที่เข้า": selected_date,
                    "วันที่ออก": selected_date,
                    "รู้จักเราจากช่องทางไหน": "เจอตอนค้นหาโรงแรมบน OTA ระบุ",
                    "ช่องทางการจอง": "Walk-in",
                    "หมายเหตุ": ""
                })

        edited_df = st.data_editor(
            default_rows,
            column_config={
                "ห้อง": st.column_config.TextColumn(disabled=True),
                "ชื่อลูกค้า": st.column_config.TextColumn(),
                "จำนวนผู้เข้าพัก": st.column_config.NumberColumn(min_value=0, max_value=10),
                "จำนวนผู้ใหญ่": st.column_config.NumberColumn(min_value=0, max_value=10),
                "จำนวนเด็ก": st.column_config.NumberColumn(min_value=0, max_value=10),
                "ABF": st.column_config.SelectboxColumn(options=["รับ", "ไม่รับ"]),
                "วันที่เข้า": st.column_config.DateColumn(),
                "วันที่ออก": st.column_config.DateColumn(),
                "รู้จักเราจากช่องทางไหน": st.column_config.SelectboxColumn(
                    options=[
                        "เจอตอนค้นหาโรงแรมบน OTA ระบุ",
                        "เจอตอนค้นหาโรงแรมผ่านเว็บรีวิวโรงแรมบน Google",
                        "ขับรถผ่าน",
                        "รู้จากคนรู้จัก",
                        "รู้จักผ่าน Facebook",
                        "รู้จักผ่าน IG",
                        "รู้จักผ่าน TikTok"
                    ]
                ),
                "ช่องทางการจอง": st.column_config.TextColumn(),
                "หมายเหตุ": st.column_config.TextColumn()
            },
            use_container_width=True,
            num_rows="fixed"
        )

        # ✅ แสดงผลรวมด้านล่าง
        total_guest = sum(row["จำนวนผู้เข้าพัก"] for row in edited_df)
        total_adult = sum(row["จำนวนผู้ใหญ่"] for row in edited_df)
        total_child = sum(row["จำนวนเด็ก"] for row in edited_df)

        st.markdown("---")
        st.subheader("📊 สรุปจำนวน")

        col1, col2, col3 = st.columns(3)
        col1.metric("👥 ผู้เข้าพักทั้งหมด", total_guest)
        col2.metric("🧍‍♂️ ผู้ใหญ่", total_adult)
        col3.metric("🧒 เด็ก", total_child)

        if st.button("💾 บันทึกรายงานห้องพัก"):
            for row in edited_df:
                room_id = row["ห้อง"]
                db.child("room_reports").child(hotel).child(selected_date_str).child(room_id).set({
                    "room": room_id,
                    "name": row["ชื่อลูกค้า"],
                    "guest": row["จำนวนผู้เข้าพัก"],
                    "adult_abf": row["จำนวนผู้ใหญ่"],
                    "child_abf": row["จำนวนเด็ก"],
                    "abf": row["ABF"],
                    "in_date": str(row["วันที่เข้า"]),
                    "out_date": str(row["วันที่ออก"]),
                    "source": row["รู้จักเราจากช่องทางไหน"],
                    "booking_channel": row["ช่องทางการจอง"],
                    "remark": row["หมายเหตุ"],
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            st.success(f"✅ บันทึกรายงานวันที่ {selected_date.strftime('%d/%m/%Y')} เรียบร้อยแล้ว")
            st.rerun()

    # ----------------------------
    # 📦 บันทึกวัตถุดิบ
    # ----------------------------
    elif selected_tab == "📦 บันทึกวัตถุดิบ":
        st.header("📦 บันทึกการซื้อวัตถุดิบ")
        purchase_date = st.date_input("🎓 วันที่ซื้อวัตถุดิบ", value=datetime.date.today(), key="purchase_date")
        purchase_date_str = str(purchase_date)

        previous_data = db.child("ingredient_stock").child(hotel).child(purchase_date_str).get().val() or {}
        if isinstance(previous_data, dict):
            previously_saved = list(previous_data.values())
        elif isinstance(previous_data, list):
            previously_saved = previous_data
        else:
            previously_saved = []

        if f"ingredients_{purchase_date_str}" not in st.session_state:
            st.session_state[f"ingredients_{purchase_date_str}"] = previously_saved

        st.subheader("➕ เพิ่มรายการวัตถุดิบ")
        with st.form("add_ingredient_form", clear_on_submit=True):
            cols = st.columns([3, 2, 2])
            name = cols[0].text_input("ชื่อวัตถุดิบ", key=f"ing_name_{purchase_date_str}")
            qty = cols[1].number_input("จำนวน", min_value=0.0, step=0.1, key=f"ing_qty_{purchase_date_str}")
            unit = cols[2].selectbox("หน่วย", ["กรัม", "กิโลกรัม"], key=f"ing_unit_{purchase_date_str}")
            submitted = st.form_submit_button("➕ เพิ่ม")

            if submitted and name:
                st.session_state[f"ingredients_{purchase_date_str}"].append({
                    "name": name,
                    "qty": qty,
                    "unit": unit
                })

                db.child("ingredient_stock").child(hotel).child(purchase_date_str).set({
                    str(i): {
                        "name": ing["name"],
                        "qty": ing["qty"],
                        "unit": ing["unit"],
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    } for i, ing in enumerate(st.session_state[f"ingredients_{purchase_date_str}"])
                    if isinstance(ing, dict) and all(k in ing for k in ["name", "qty", "unit"])
                })

                st.success("✅ เพิ่มและบันทึกเรียบร้อยแล้ว")
                st.rerun()

        if st.session_state[f"ingredients_{purchase_date_str}"]:
            st.subheader("👍 รายการวัตถุดิบที่เพิ่มแล้ว")
            for idx, ing in enumerate(st.session_state[f"ingredients_{purchase_date_str}"]):
                if not isinstance(ing, dict):
                    continue
                if not all(k in ing for k in ["name", "qty", "unit"]):
                    continue
                st.write(f"🟩 {ing['name']} - {ing['qty']} {ing['unit']}")
                if st.button(f"❌ ลบ {ing['name']}", key=f"delete_ing_{purchase_date_str}_{idx}"):
                    st.session_state[f"ingredients_{purchase_date_str}"].pop(idx)

                    db.child("ingredient_stock").child(hotel).child(purchase_date_str).set({
                        str(i): {
                            "name": ing["name"],
                            "qty": ing["qty"],
                            "unit": ing["unit"],
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        } for i, ing in enumerate(st.session_state[f"ingredients_{purchase_date_str}"])
                        if isinstance(ing, dict) and all(k in ing for k in ["name", "qty", "unit"])
                    })

                    st.success(f"✅ ลบ {ing['name']} เรียบร้อยแล้ว")
                    st.rerun()

        # ----------------------------
        # 📊 แสดงวัตถุดิบคงเหลือ
        # ----------------------------
        st.markdown("---")
        st.subheader("📉 คำนวณวัตถุดิบคงเหลือวันนี้")
        selected_report_date = st.date_input("เลือกวันที่ต้องการดูยอดคงเหลือ", value=datetime.date.today(), key="stock_balance_date")
        selected_report_str = selected_report_date.strftime('%Y-%m-%d')

        search_term = st.text_input("🔍 ค้นหาวัตถุดิบในคงเหลือ")

        purchases = db.child("ingredient_stock").child(hotel).get().val() or {}
        total_stock = {}
        item_keys = {}

        for date_str, entries in purchases.items():
            if date_str <= selected_report_str:
                if isinstance(entries, dict):
                    for key, entry in entries.items():
                        if not isinstance(entry, dict):
                            continue
                        name = entry.get("name")
                        qty = entry.get("qty", 0)
                        unit = entry.get("unit", "กรัม")
                        qty_in_grams = qty * 1000 if unit == "กิโลกรัม" else qty
                        total_stock[name] = total_stock.get(name, 0) + qty_in_grams
                        item_keys.setdefault(name, []).append((date_str, key))
                elif isinstance(entries, list):
                    for idx, entry in enumerate(entries):
                        if not isinstance(entry, dict):
                            continue
                        name = entry.get("name")
                        qty = entry.get("qty", 0)
                        unit = entry.get("unit", "กรัม")
                        qty_in_grams = qty * 1000 if unit == "กิโลกรัม" else qty
                        total_stock[name] = total_stock.get(name, 0) + qty_in_grams
                        item_keys.setdefault(name, []).append((date_str, str(idx)))

        daily_menus = db.child("daily_cooked_menu").child(hotel).get().val() or {}
        recipes = db.child("recipes").child(hotel).get().val() or {}

        used_ingredients = {}
        for date_str, menu_data in daily_menus.items():
            if date_str <= selected_report_str:
                menus = menu_data.get("menus", [])
                for menu in menus:
                    for _, recipe in recipes.items():
                        if recipe.get("name") == menu:
                            for ing in recipe.get("ingredients", []):
                                if not isinstance(ing, dict):
                                    continue
                                ing_name = ing.get("name")
                                ing_qty = ing.get("qty", 0)
                                ing_unit = ing.get("unit", "กรัม")
                                qty_in_grams = ing_qty * 1000 if ing_unit == "กิโลกรัม" else ing_qty
                                used_ingredients[ing_name] = used_ingredients.get(ing_name, 0) + qty_in_grams

        st.subheader("📦 คงเหลือวัตถุดิบ ณ วันที่เลือก")
        if total_stock:
            for name in sorted(total_stock):
                if search_term and search_term.lower() not in name.lower():
                    continue
                bought = total_stock.get(name, 0)
                used = used_ingredients.get(name, 0)
                remaining = bought - used
                st.write(f"{name}: {remaining:.2f} กรัม ( มีทั้งหมด {bought:.2f}, ใช้ไป {used:.2f} )")

                if st.button(f"🗑 ลบวัตถุดิบ '{name}'", key=f"delete_stock_{name}_{selected_report_str}"):
                    for date_str, key_list in item_keys.get(name, []):
                        db.child("ingredient_stock").child(hotel).child(date_str).child(key_list).remove()
                    st.success(f"✅ ลบ '{name}' จากรายการวัตถุดิบแล้ว")
                    st.rerun()
        else:
            st.info("ไม่มีข้อมูลวัตถุดิบในระบบ")


    # ----------------------------
    # 🍳 เมนูที่ทำในแต่ละวัน
    # ----------------------------
    elif selected_tab == "🍳 เมนูที่ทำในแต่ละวัน":
        st.header("🍳 บันทึกเมนูที่ทำในแต่ละวัน")
        cooking_date = st.date_input("📅 วันที่ทำอาหาร", value=datetime.date.today(), key="cooking_date")
        cooking_date_str = str(cooking_date)

        all_recipes = db.child("recipes").child(hotel).get().val() or {}
        recipe_options = [r["name"] for r in all_recipes.values()] if all_recipes else []

        # 👉 โหลดเมนูที่เคยบันทึกไว้ในวันนั้น
        previous_menus_data = db.child("daily_cooked_menu").child(hotel).child(cooking_date_str).get().val()
        previously_saved_menus = previous_menus_data.get("menus", []) if previous_menus_data else []

        if f"daily_menu_{cooking_date_str}" not in st.session_state:
            st.session_state[f"daily_menu_{cooking_date_str}"] = previously_saved_menus

        st.subheader("➕ เพิ่มเมนูที่ทำ")

        with st.form("add_menu_form", clear_on_submit=True):
            menu = st.selectbox("🍽 เลือกเมนู", recipe_options, key=f"menu_select_{cooking_date_str}")
            submitted = st.form_submit_button("➕ เพิ่ม")

            if submitted and menu and menu not in st.session_state[f"daily_menu_{cooking_date_str}"]:
                st.session_state[f"daily_menu_{cooking_date_str}"].append(menu)
                # ✅ บันทึกทันที
                db.child("daily_cooked_menu").child(hotel).child(cooking_date_str).set({
                    "menus": st.session_state[f"daily_menu_{cooking_date_str}"],
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("✅ เพิ่มเมนูและบันทึกเรียบร้อยแล้ว")
                st.rerun()

        if st.session_state[f"daily_menu_{cooking_date_str}"]:
            st.subheader("📋 เมนูที่เพิ่ม")
            for idx, m in enumerate(st.session_state[f"daily_menu_{cooking_date_str}"]):
                st.write(f"✅ {m}")
                if st.button(f"❌ ลบเมนู {m}", key=f"delete_menu_{cooking_date_str}_{idx}"):
                    st.session_state[f"daily_menu_{cooking_date_str}"].pop(idx)

                    if st.session_state[f"daily_menu_{cooking_date_str}"]:
                        # ยังมีเมนูเหลือ -> อัปเดตใน Firebase
                        db.child("daily_cooked_menu").child(hotel).child(cooking_date_str).set({
                            "menus": st.session_state[f"daily_menu_{cooking_date_str}"],
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        # ไม่มีเมนูเหลือ -> ลบทั้งวันที่ออกจาก Firebase
                        db.child("daily_cooked_menu").child(hotel).child(cooking_date_str).remove()

                    st.success(f"🗑 ลบเมนู '{m}' และอัปเดตข้อมูลแล้ว")
                    st.rerun()

    # ----------------------------
    # 💰 รายรับรายวัน
    # ----------------------------
    elif selected_tab == "💰 รายรับรายวัน":
        st.header("💰 รายรับรายวัน")
        income_date = st.date_input("📅 วันที่รายรับ", value=datetime.date.today(), key="income_date")
        income_date_str = str(income_date)

        for section in ["front", "bar"]:
            st.subheader(f"📍 {'ฟรอนต์' if section == 'front' else 'บาร'}")
            key_income = f"income_{section}_{income_date_str}"
            key_expense = f"expense_{section}_{income_date_str}"

            # โหลดข้อมูลเดิม
            for key, db_path in [(key_income, "daily_income"), (key_expense, "daily_expense")]:
                if key not in st.session_state:
                    data = db.child(db_path).child(hotel).child(income_date_str).child(section).get().val()
                    st.session_state[key] = data if isinstance(data, list) else []

            # ฟอร์มเพิ่มรายรับ / รายจ่าย
            with st.form(f"form_{section}", clear_on_submit=True):
                cols = st.columns([3, 2, 2, 1])
                entry_type = cols[0].text_input("ประเภท", key=f"type_{section}_{income_date_str}")
                amount = cols[1].number_input("จำนวนเงิน (บาท)", min_value=0.0, step=1.0, key=f"amount_{section}_{income_date_str}")
                method = cols[2].selectbox("วิธีการ", ["เงินสด", "โอน", "บัตร", "อื่น ๆ"], key=f"method_{section}_{income_date_str}")
                entry_mode = cols[3].selectbox("ประเภท", ["รายรับ", "รายจ่าย"], key=f"mode_{section}_{income_date_str}")
                submitted = st.form_submit_button("➕ เพิ่ม")

                if submitted and entry_type and amount > 0:
                    new_entry = {
                        "type": entry_type,
                        "amount": amount,
                        "method": method,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    if entry_mode == "รายรับ":
                        st.session_state[key_income].append(new_entry)
                        db.child("daily_income").child(hotel).child(income_date_str).child(section).set(st.session_state[key_income])
                    else:
                        st.session_state[key_expense].append(new_entry)
                        db.child("daily_expense").child(hotel).child(income_date_str).child(section).set(st.session_state[key_expense])

                    st.success("✅ บันทึกเรียบร้อยแล้ว")
                    st.rerun()

            # รายการที่บันทึกไว้แล้ว
            st.markdown("### 📅 รายรับ")
            income_by_method = {}
            for idx, item in enumerate(st.session_state[key_income]):
                st.write(f"+ {item['type']} / {item['amount']} บาท ({item['method']})")
                income_by_method[item['method']] = income_by_method.get(item['method'], 0) + item['amount']
                if st.button("❌ ลบ", key=f"del_inc_{section}_{idx}"):
                    st.session_state[key_income].pop(idx)
                    db.child("daily_income").child(hotel).child(income_date_str).child(section).set(st.session_state[key_income])
                    st.rerun()

            st.markdown("### 📅 รายจ่าย")
            expense_by_method = {}
            for idx, item in enumerate(st.session_state[key_expense]):
                st.write(f"- {item['type']} / {item['amount']} บาท ({item['method']})")
                expense_by_method[item['method']] = expense_by_method.get(item['method'], 0) + item['amount']
                if st.button("❌ ลบ", key=f"del_exp_{section}_{idx}"):
                    st.session_state[key_expense].pop(idx)
                    db.child("daily_expense").child(hotel).child(income_date_str).child(section).set(st.session_state[key_expense])
                    st.rerun()

            st.markdown("---")
            st.subheader("📈 สรุปรายรับ - รายจ่าย")
            all_methods = set(income_by_method.keys()).union(set(expense_by_method.keys()))
            for method in sorted(all_methods):
                inc = income_by_method.get(method, 0)
                exp = expense_by_method.get(method, 0)
                st.write(f"{method}: {inc:.2f} - {exp:.2f} = {inc - exp:.2f} บาท")

            # ✅ สรุปรวมแต่ละประเภท
            total_all = 0
            for method in all_methods:
                total_all += income_by_method.get(method, 0) - expense_by_method.get(method, 0)

            st.success(f"💰 รวมสุทธิทั้งหมดของแผนก{'ฟรอนต์' if section == 'front' else 'บาร์'}: {total_all:.2f} บาท")
