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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👩‍🍳 สูตรอาหารในครัว", 
        "🧼 สูตรแม่บ้าน", 
        "📋 บันทึกงานประจำวัน", 
        "📑 รายงานห้องพัก",
        "📦 บันทึกวัตถุดิบ",
        "🍳 เมนูที่ทำในแต่ละวัน"
    ])

    # ----------------------------
    # 🍳 สูตรอาหาร
    # ----------------------------
    with tab1:
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

    # ----------------------------
    # 📋 บันทึกงานประจำวัน
    # ----------------------------
    with tab3:
        st.header("📋 งานที่คุณทำวันนี้")

        # ใช้ timestamp เป็นชื่อ key
        user_id = st.session_state["user"]["localId"]
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        task = st.text_area("คุณทำอะไรไปบ้างในวันนี้")

        if st.button("📝 บันทึกงานวันนี้"):
            if task:
                log = {
                    "task": task,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                db.child("work_logs").child(hotel).child(today).child(user_id).set(log)
                st.success("✅ บันทึกงานวันนี้เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกรายละเอียดงาน")

        st.divider()
        st.subheader("📆 งานที่บันทึกไว้แล้ว")
        logs = db.child("work_logs").child(hotel).child(today).get().val() or {}

        for uid, entry in logs.items():
            st.markdown(f"👤 **พนักงาน ID:** `{uid}`")
            st.caption(f"🕒 {entry['timestamp']}")
            st.write(entry["task"])
            st.divider()

    # ----------------------------
    # 📋 รายงานห้องพักประจำวัน
    # ----------------------------
    with tab4:
        st.header("📑 รายงานห้องพักประจำวัน")

        selected_date = st.date_input("เลือกวันที่สำหรับรายงาน", value=datetime.date.today())
        selected_date_str = selected_date.strftime('%Y-%m-%d')

        st.caption(f"📅 วันที่รายงาน: {selected_date.strftime('%d/%m/%Y')}")

        # 🔧 เตรียมตารางข้อมูล
        default_rows = []
        for i in range(1, 21):
            default_rows.append({
                "ห้อง": f"Room {i}",
                "ชื่อลูกค้า": "",
                "จำนวนผู้เข้าพัก": 1,
                "จำนวนผู้ใหญ่": 1,
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
                "จำนวนผู้เข้าพัก": st.column_config.NumberColumn(min_value=1, max_value=10),
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
        col2.metric("🧍‍♂️ ผู้ใหญ่ที่รับ ABF", total_adult)
        col3.metric("🧒 เด็กที่รับ ABF", total_child)

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
    with tab5:
        st.header("📦 บันทึกการซื้อวัตถุดิบ")
        purchase_date = st.date_input("🗓 วันที่ซื้อวัตถุดิบ", value=datetime.date.today(), key="purchase_date")

        if "ingredients" not in st.session_state:
            st.session_state["ingredients"] = []

        st.subheader("➕ เพิ่มรายการวัตถุดิบ")

        with st.form("add_ingredient_form", clear_on_submit=True):
            cols = st.columns([3, 2, 2])
            name = cols[0].text_input("ชื่อวัตถุดิบ", key="ing_name")
            qty = cols[1].number_input("จำนวน", min_value=0.0, step=0.1, key="ing_qty")
            unit = cols[2].selectbox("หน่วย", ["กรัม", "กิโลกรัม"], key="ing_unit")
            submitted = st.form_submit_button("➕ เพิ่ม")

            if submitted and name:
                st.session_state["ingredients"].append({
                    "name": name,
                    "qty": qty,
                    "unit": unit
                })

        if st.session_state["ingredients"]:
            st.subheader("📋 รายการที่เพิ่ม")
            for idx, ing in enumerate(st.session_state["ingredients"]):
                st.write(f"🟩 {ing['name']} - {ing['qty']} {ing['unit']}")
                if st.button(f"❌ ลบ", key=f"delete_ing_{idx}"):
                    st.session_state["ingredients"].pop(idx)
                    st.rerun()

            if st.button("💾 บันทึกทั้งหมด"):
                for ing in st.session_state["ingredients"]:
                    db.child("ingredient_stock").child(hotel).child(str(purchase_date)).push({
                        "name": ing["name"],
                        "qty": ing["qty"],
                        "unit": ing["unit"],
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                st.success("✅ บันทึกวัตถุดิบทั้งหมดเรียบร้อยแล้ว")
                st.session_state["ingredients"] = []
                st.rerun()

        # ----------------------------
        # 📊 แสดงวัตถุดิบคงเหลือ
        # ----------------------------
        st.markdown("---")
        st.subheader("📉 คำนวณวัตถุดิบคงเหลือวันนี้")
        selected_report_date = st.date_input("เลือกวันที่ต้องการดูยอดคงเหลือ", value=datetime.date.today(), key="stock_balance_date")
        selected_report_str = selected_report_date.strftime('%Y-%m-%d')

        # รวมวัตถุดิบที่ซื้อทั้งหมดจนถึงวันที่เลือก
        purchases = db.child("ingredient_stock").child(hotel).get().val() or {}
        total_stock = {}
        for date_str, entries in purchases.items():
            if date_str <= selected_report_str:
                for _, entry in entries.items():
                    name = entry.get("name")
                    qty = entry.get("qty", 0)
                    unit = entry.get("unit", "กรัม")
                    qty_in_grams = qty * 1000 if unit == "กิโลกรัม" else qty
                    total_stock[name] = total_stock.get(name, 0) + qty_in_grams

        # รวมวัตถุดิบที่ใช้จากเมนูที่ทำ
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
                                ing_name = ing.get("name")
                                ing_qty = ing.get("qty", 0)
                                ing_unit = ing.get("unit", "กรัม")
                                qty_in_grams = ing_qty * 1000 if ing_unit == "กิโลกรัม" else ing_qty
                                used_ingredients[ing_name] = used_ingredients.get(ing_name, 0) + qty_in_grams

        # คำนวณคงเหลือ
        st.subheader("📦 คงเหลือวัตถุดิบ ณ วันที่เลือก")
        if total_stock:
            for name in sorted(total_stock):
                bought = total_stock.get(name, 0)
                used = used_ingredients.get(name, 0)
                remaining = bought - used
                st.write(f"{name}: {remaining:.2f} กรัม (มีทั้งหมด {bought:.2f}, ใช้ไป {used:.2f})")
        else:
            st.info("ไม่มีข้อมูลวัตถุดิบในระบบ")

    # ----------------------------
    # 🍳 เมนูที่ทำในแต่ละวัน
    # ----------------------------
        with tab6:
            st.header("🍳 บันทึกเมนูที่ทำในแต่ละวัน")
            cooking_date = st.date_input("📅 วันที่ทำอาหาร", value=datetime.date.today(), key="cooking_date")

            all_recipes = db.child("recipes").child(hotel).get().val() or {}
            recipe_options = [r["name"] for r in all_recipes.values()] if all_recipes else []

            if "daily_menu" not in st.session_state:
                st.session_state["daily_menu"] = []

            st.subheader("➕ เพิ่มเมนูที่ทำ")

            with st.form("add_menu_form", clear_on_submit=True):
                menu = st.selectbox("🍽 เลือกเมนู", recipe_options, key="menu_select")
                submitted = st.form_submit_button("➕ เพิ่ม")

                if submitted and menu:
                    st.session_state["daily_menu"].append(menu)

            if st.session_state["daily_menu"]:
                st.subheader("📋 เมนูที่เพิ่ม")
                for idx, m in enumerate(st.session_state["daily_menu"]):
                    st.write(f"✅ {m}")
                    if st.button(f"❌ ลบเมนู", key=f"delete_menu_{idx}"):
                        st.session_state["daily_menu"].pop(idx)
                        st.rerun()

                if st.button("📝 บันทึกเมนูทั้งหมด"):
                    db.child("daily_cooked_menu").child(hotel).child(str(cooking_date)).set({
                        "menus": st.session_state["daily_menu"],
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.success("✅ บันทึกเมนูทั้งหมดเรียบร้อยแล้ว")
                    st.session_state["daily_menu"] = []
                    st.rerun()


