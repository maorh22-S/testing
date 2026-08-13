#================ חלק 1 =======================

import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# ⚙️ מפסק פיילוט: True הופך את (לילה, פתיחת בוקר כל השבוע וכל שישי-שבת) לאפורות. False פותח כרגיל.
DISABLE_pilot = True
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def check_shift_blocking(day_en, shift_en, current_role, disable_pilot_flag):
    """
    פונקציה מאוחדת לבדיקת חסימות ואילוצים לכל סוגי המסכים.
    מחזירה: (האם חסום [True/False], סיבת החסימה)
    """
    is_blocked = False
    block_reason = "לא יכול ❌"

    # 1️⃣ שלב א': חסימות קבועות של הארגון (תמיד קורות)
    if day_en == "Saturday" and shift_en == "open_T":
        is_blocked = True; block_reason = "אין משמרת"
    elif day_en in ["Friday", "Saturday"] and shift_en == "Support":
        is_blocked = True; block_reason = "אין משמרת תמך בסוף השבוע"
    elif "בדק" in current_role and day_en == "Friday" and shift_en in ["Afternoon", "Night"]:
        is_blocked = True; block_reason = "אין משמרת"
    elif "בדק" in current_role and day_en == "Saturday":
        is_blocked = True; block_reason = "אין משמרת"

    # 2️⃣ שלב ב': חסימות הפיילוט (רצות רק על משמרות שלא נחסמו קודם, וכשהדגל חיובי)
    if disable_pilot_flag and not is_blocked:
        if shift_en == "Night": 
            is_blocked = True; block_reason = " (לילה)"
        elif shift_en in ["open_T"]: 
            is_blocked = True; block_reason = " (פתיחת בוקר)"
        elif day_en in ["Friday", "Saturday"]: 
            is_blocked = True; block_reason = " (סוף שבוע)"

    return is_blocked, block_reason
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# הגדרת הודעות טקסט בעברית 
MSG_TITLE = "📋 מערכת סידור משמרות שבועי"
MSG_SUBHEADER = "🔒 התחברות למערכת"
MSG_SELECT_NAME = "בחר את שמך:"
MSG_PASSWORD = "הכנס סיסמה:"
MSG_LOGIN_BTN = "התחבר"
MSG_LOGIN_ERR = "שם משתמש או סיסמה שגויים"
MSG_CONN_ERR = "⚠️ שגיאת תקשורת בטעינת המשתמשים מגוגל."
MSG_RELOAD_BTN = "נסה לטעון מחדש"
MSG_LOGOUT_BTN = "התנתק מהמערכת"
MSG_INFO_SUBMIT = "### ✍️ הגשת אילוצים וזמינות לשבוע הקרוב"
MSG_INFO_NOTE = "💡 משמרת שתישאר לא מסומנת תיחשב אוטומטית כ-יכול."
MSG_INFO_NOTE2 = "💡 משמרת שתישאר לא מסומנת תיחשב כ-יכול. 🔒 משמרות (פתיחת בוקר, לילות, וסופי שבוע) סגורות להגשה."
MSG_SUBMIT_BTN = "🚀 שליחת סידור משמרות"
MSG_SUBMIT_ERR = "⚠️ לא ניתן לשלוח את הטופס! סימנת גם 'יכול' וגם 'מ.ש' במשמרות הבאות:\n\n"
MSG_SPINNER_SAVE = "שומר את הנתונים ..."
MSG_SAVE_SUCCESS = "✅ הסידור נשמר בהצלחה !"
MSG_SAVE_ERR = "⚠️ חלה שגיאה בשמירת הנתונים, נא לנסות שוב."
MSG_NO_PASSWORD = "⚠️ זהו שם משתמש ללא סיסמה במערכת! אנא לחץ על כפתור הגדרת סיסמה ראשונית למטה."

st.set_page_config(layout="wide", menu_items=None)

# 📱 עיצובי CSS רספונסיביים משודרגים למירכוז ויישור כותרות ורכיבי בחירה
st.markdown("""
<style>
.stApp { direction: rtl; } /* כל הדף מימין לשמאל */
h1, h2, h3, .stMarkdown, [data-testid="stHeading"] { text-align: center !important; justify-content: center !important; display: flex; width: 100%; }

/* יישור יציב לימין של כפתורי הבחירה (Radio) ומניעת זריקה הצידה */
div[data-testid="stRadio"] { direction: rtl !important; text-align: right !important; width: 100% !important; display: block !important; }
div[data-testid="stRadio"] > label { text-align: right !important; justify-content: flex-start !important; width: 100% !important; }
div[data-testid="stRadio"] [data-testid="stWidgetLabel"] { text-align: right !important; width: 100% !important; display: block !important; }

div[data-testid="stForm"] { max-width: 800px; margin: 0 auto; padding: 20px; box-shadow: 0px 0px 10px rgba(0,0,0,0.05); border-radius: 10px; background-color: #ffffff; }

/* סידור תיבות הסימון בצורה קריאה וישרה לצד הכיתוב */ 
div[data-testid="stCheckbox"] label { display: flex; align-items: center; justify-content: flex-start; gap: 10px; direction: rtl; text-align: right; }

hr { margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #edf2f7; }
.day-header { text-align: center; font-size: 16px; font-weight: bold; margin-bottom: 2px; color: #2c3e50; }
.day-date { text-align: center; font-size: 13px; color: #7f8c8d; margin-bottom: 5px; font-weight: bold; }
.shift-header { text-align: right; font-weight: bold; margin-top: 12px; margin-bottom: 4px; font-size: 14px; color: #34495e; }

/* עיצוב כרטיסיות הסיכום התחתונות */
.summary-box { border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); text-align: center; margin-top: 12px; max-width: 800px; margin-left: auto; margin-right: auto; }
.summary-day-title { font-size: 15px; font-weight: bold; color: #1e293b; text-align: center; }
.summary-day-date { font-size: 12px; color: #64748b; text-align: center; font-weight: bold; margin-bottom: 8px; }

/* ביטול מוחלט של כפתור ה-Sidebar הצידי במובייל כדי שלא יקפוץ ויפריע */
[data-testid="collapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

SCRIPT_URL = st.secrets.get("script_url", "")

#------------------------------
# ייעול קריטי: שמירת המשתמשים במטמון ל-10 דקות למניעת דיליי מול גוגל בכל לחיצה
@st.cache_data(ttl=600)
def get_allowed_users():
    if not SCRIPT_URL:
        return {}
    try:
        res = requests.get(f"{SCRIPT_URL}?sheet=users", timeout=15)
        if res.status_code == 200:
            raw_data = res.json()
            if isinstance(raw_data, list) and len(raw_data) > 0:
                users_dict = {}
                for row in raw_data:
                    if isinstance(row, dict) and "username" in row:
                        u = str(row["username"]).strip()
                        p = str(row.get("password", "")).strip()
                        r = str(row.get("role", "כללי")).strip()
                        if u:
                            users_dict[u] = {"password": p, "role": r}
                return users_dict
        
        # אם הסטטוס אינו תקין, נציג אזהרה ורענן את הדף אוטומטית אחרי כמה שניות
        st.warning("החיבור לגוגל התעכב, מבצע ניסיון חוזר...")
        st.rerun()
        
    except Exception as e:
        st.error(f"שגיאת תקשורת מול גוגל: {e}. מרענן את העמוד...")
        st.rerun()
        
    return {}
    
#---------------------------------------
USER_CREDENTIALS = get_allowed_users()

# בדיקה אם משתמש מחובר
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_name = ""
    st.session_state.user_role = ""

#*************************************************************************************************************************
#================ חלק 2 =======================

#================ חלק 2 מוגמר ומיועל =======================

# ייעול קריטי: שליפת תאריך דינמית ואנכית מתוך לשונית Settings (מותאם במדויק למבנה שלכם)
# 600 אומר שזה שומר את התאריך ל 10 דקות ולא צריך כל פעם לבדוק מה מוגדר בגוגל
@st.cache_data(ttl=600)
def get_week_settings():
    s_date_display = ""
    e_date_display = ""
    d_list = []
    if not SCRIPT_URL:
        return s_date_display, e_date_display, d_list
    
    try:
        settings_res = requests.get(f"{SCRIPT_URL}?sheet=Settings", timeout=60)
        if settings_res.status_code == 200:
            raw_json = settings_res.json()
            if isinstance(raw_json, list) and len(raw_json) >= 3:
                day_val = str(raw_json[0].get("Active_Week", "")).strip()
                month_val = str(raw_json[1].get("Active_Week", "")).strip()
                year_val = str(raw_json[2].get("Active_Week", "")).strip()
                
                if day_val and month_val and year_val:
                    if len(day_val) == 1: day_val = "0" + day_val
                    if len(month_val) == 1: month_val = "0" + month_val
                    
                    start_date_str = f"{day_val}/{month_val}/{year_val}"
                    base_date = datetime.strptime(start_date_str, "%d/%m/%Y")
                    
                    s_date_display = base_date.strftime("%d/%m/%Y")
                    # יצירת רשימה של 7 התאריכים לשבוע הבא
                    d_list = [(base_date + timedelta(days=i)).strftime('%d/%m/%Y') for i in range(7)]
                    e_date_display = (base_date + timedelta(days=6)).strftime("%d/%m/%Y")
    except Exception as e:
        st.error(f"שגיאה בשליפת הגדרות שבוע: {e}")
        
    return s_date_display, e_date_display, d_list

# טעינת הנתונים מהפונקציה המתוקנת
start_date_display, end_date_display, dates_list = get_week_settings()

if "reg_mode" not in st.session_state:
    st.session_state.reg_mode = False

# מסך התחברות והרשמה ראשונית למערכת
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns(3)
    with col2:
        if not st.session_state.reg_mode:
            st.subheader(MSG_SUBHEADER)
            if USER_CREDENTIALS:
                username = st.selectbox(MSG_SELECT_NAME, [""] + list(USER_CREDENTIALS.keys()))
                password = st.text_input(MSG_PASSWORD, type="password")
                
                login_button = st.button(MSG_LOGIN_BTN, use_container_width=True)
                if login_button:
                    if username:
                        user_info = USER_CREDENTIALS.get(username, {})
                        current_password_in_sheet = str(user_info.get("password", "")).strip()
                        current_role_in_sheet = str(user_info.get("role", "כללי")).strip()
                        
                        if current_password_in_sheet in ["", "none", "null"] or current_password_in_sheet.lower() == "none":
                            st.error(MSG_NO_PASSWORD)
                        elif current_password_in_sheet == str(password).strip():
                            st.session_state.authenticated = True
                            st.session_state.user_name = username
                            st.session_state.user_role = current_role_in_sheet
                            st.rerun()
                        else:
                            st.error(MSG_LOGIN_ERR)
                
                st.write("---")
                if st.button("✨ הגדרת סיסמה ראשונית (לעובדים חדשים)", use_container_width=True):
                    st.session_state.reg_mode = True
                    st.rerun()
            else:
                st.error(MSG_CONN_ERR)
                if st.button(MSG_RELOAD_BTN):
                    st.rerun()


#*****************************************************************************************************
#================ חלק 3 =======================

# מסך הגדרת סיסמה ראשונית נפרד (עם הגנת דריסה - משולב ומיועל)
        else:
            st.subheader("🔑 הגדרת סיסמה ראשונית")
            if USER_CREDENTIALS:
                reg_username = st.selectbox("בחר את שמך להגדרת הסיסמה:", [""] + list(USER_CREDENTIALS.keys()))
                if reg_username:
                    user_info = USER_CREDENTIALS.get(reg_username, {})
                    check_pwd = str(user_info.get("password", "")).strip()
                    current_role_in_sheet = str(user_info.get("role", "כללי")).strip()
                    
                    # אבטחה: שימוש בבדיקה המקוצרת והבטוחה של גרסה ב'
                    if check_pwd != "" and check_pwd.lower() not in ["none", "null"]:
                        st.error("⚠️ למשתמש זה כבר מוגדרת סיסמה קבועה במערכת! חזור למסך הקודם והתחבר כרגיל.")
                    else:
                        new_password = st.text_input("הכנס סיסמה חדשה:", type="password", key="reg_p1")
                        confirm_password = st.text_input("אמת סיסמה חדשה:", type="password", key="reg_p2")
                        register_button = st.button("💾 שמור סיסמה קבועה והתחבר", use_container_width=True)
                        
                        if register_button:
                            if not new_password:
                                st.error("⚠️ לא ניתן להגדיר סיסמה ריקה!")
                            elif new_password != confirm_password:
                                st.error("⚠️ הסיסמאות שהזנת אינן תואמות!")
                            else:
                                with st.spinner("שומר את הסיסמה ..."):
                                    register_payload = {
                                        "action": "update_password",
                                        "username": reg_username,
                                        "password": new_password
                                    }
                                    reg_res = requests.post(SCRIPT_URL, json=register_payload, timeout=10)
                                    if reg_res.status_code == 200:
                                        st.success("✅ הסיסמה נשמרה בהצלחה!")
                                        st.session_state.authenticated = True
                                        st.session_state.user_name = reg_username
                                        st.session_state.user_role = current_role_in_sheet
                                        st.session_state.reg_mode = False
                                        st.rerun()
                                    else:
                                        st.error("⚠️ שגיאת תקשורת, נא לנסות שוב.")
                
                st.write("") # רווח קל לעיניים
                back_button = st.button("⬅️ חזור למסך התחברות", use_container_width=True)
                if back_button:
                    st.session_state.reg_mode = False
                    st.rerun()

#=======================================================================================================
# מצב מחובר - אתחול מערכים ותצוגה
#=======================================================================================================
else:
    # הגדרת מערכים קבועה אחידה
    ימים = [
        {"he": "ראשון", "en": "Sunday"}, {"he": "שני", "en": "Monday"},
        {"he": "שלישי", "en": "Tuesday"}, {"he": "רביעי", "en": "Wednesday"},
        {"he": "חמישי", "en": "Thursday"}, {"he": "שישי", "en": "Friday"},
        {"he": "שבת", "en": "Saturday"}
    ]
    
    משמרות = [
        {"he": "פתיחת בוקר", "en": "open_T"},
        {"he": "בוקר", "en": "Morning"}, 
        {"he": "צהריים", "en": "Afternoon"},
        {"he": "לילה", "en": "Night"}, 
        {"he": "תמך (12 ש')", "en": "Support"}
    ]
    
    # אימוץ סידור השעות הכרונולוגי והתקין של גרסה ב'
    שעות_משמרת = {
        "open_T": "05:30 - 15:00", 
        "Morning": "06:30 - 15:00",
        "Afternoon": "14:40 - 23:00",
        "Night": "22:40 - 07:00", 
        "Support": "07:30 - 19:30"
    }
    
    # שימוש בחלוקת העמודות הרחבה [2, 1, 1] של גרסה א' לאיזון ויזואלי מושלם
    top_c1, top_c2, top_c3 = st.columns([2, 1, 1])
    with top_c1:
        st.markdown(f"<div style='text-align: right; font-size: 16px; font-weight: bold; padding-top: 10px;'>👋 שלום, {st.session_state.user_name} ({st.session_state.get('user_role', 'כללי')})</div>", unsafe_allow_html=True)
        
    with top_c2:
        if st.button(MSG_LOGOUT_BTN, use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_name = ""
            st.session_state.user_role = ""
            st.rerun()
    
    with top_c3:
        pass
    
    st.write("---")
    
    if not start_date_display:
        st.error("⚠️ לא נמצא תאריך שבוע בתוקף !")
    else:
        st.title(MSG_TITLE)
        st.write("### ✍️ הגשת אילוצים וזמינות לשבוע הקרוב")
        st.write(f"{MSG_INFO_NOTE}")
        st.write(f"📅 השבוע של: **{start_date_display}** עד **{end_date_display}**")


#*************************************************************************************************************************
#================ חלק 4 =======================

        #================ חלק 4 מוגמר ומיועל =======================
        st.markdown("""
        <style>
        div[data-testid="stForm"] * { color: #1e293b !important; }
        div[data-testid="stExpander"] details summary span { color: #1e293b !important; font-weight: bold; }
        .shift-block-title { font-weight: bold; font-size: 14px; margin-top: 12px; margin-bottom: 2px; color: #2c3e50; text-align: right; }
        .hours-badge-pc { font-size: 11px; color: #64748b; font-weight: normal; margin-top: -3px; display: block; }
        
        /* 💻 חוקי עיצוב בלעדיים למחשב  */
        @media (min-width: 768px) {
        div[data-testid="stForm"] { max-width: 80% !important; width: 80% !important; margin: 0 auto !important; padding: 1.5rem !important; }
        div[data-testid="stAppViewBlockContainer"] { max-width: 85% !important; }
        
        div[data-testid="stHorizontalBlock"] { gap: 8px !important; row-gap: 0px !important; align-items: start !important; }
        .pc-row-container { height: 95px !important; display: flex; flex-direction: column; justify-content: flex-start !important; margin-bottom: 0px !important; padding: 0px !important; }
        div[data-testid="stCheckbox"] { margin-top: 0px !important; margin-bottom: -12px !important; padding: 0px !important; height: 24px !important; }
        div[data-testid="stCheckbox"] label { padding-top: 0px !important; padding-bottom: 0px !important; min-height: 20px !important; }
        }
        
          /* 📱 חוקי עיצוב בלעדיים לנייד */ 
        @media (max-width: 767) { 
        div[data-testid="stHorizontalBlock"] { 
            display: flex !important; 
            flex-direction: row !important; 
            flex-wrap: nowrap !important; 
            overflow-x: auto !important; 
            min-width: 200% !important; /* 🔥   200%   גורם לחצי טבלה בדיוק להיכנס לעין */
            align-items: flex-start !important; 
            -webkit-overflow-scrolling: touch !important; 
        }
        
        /* 👈 כיווץ ואיזון הטורים הבודדים כדי שיתפרסו בצורה שווה  */
        div[data-testid="stHorizontalBlock"] > div { 
            min-width: calc(200% / 8) !important; /* 🔥 מחלק את ה-200% באופן שווה בין 8 הטורים  (טור שעות + 7 ימים) */
            flex-shrink: 0 !important; 
        }
        
        
        
        /* 👈  כיווץ רוחב הלוח בנייד ל-800 פיקסלים כדי שהתיבות לא ייפרסו בענק */
        div[data-testid="stHorizontalBlock"] { 
            display: flex !important; 
            flex-direction: row !important; 
            flex-wrap: nowrap !important; 
            overflow-x: auto !important; 
            min-width: 800px !important; 
            align-items: flex-start !important; 
            -webkit-overflow-scrolling: touch !important; 
        }
        
        /* 👈 רוחב הטורים:  למראה קומפקטי ונקי */
        div[data-testid="stHorizontalBlock"] > div { 
            min-width: 100px !important; 
            flex-shrink: 0 !important; 
        }
        
        .pc-row-container { height: auto !important; display: block !important; padding: 0px !important; }
        div[data-testid="stCheckbox"] { height: auto !important; margin-bottom: 2px !important; }
        div[data-testid="stCheckbox"] label p { font-size: 11px !important; }
        div[data-testid="stRadio"] label p { font-size: 13px !important; }
        }
    </style>
    """, unsafe_allow_html=True)
#**************************************************************************************************************************
            
        #================ חלק 5 מוגמר ומיועל =======================
        # 2. הוספת רכיבי הניווט, סגנון התצוגה וכפתור האיפוס המהיר מגרסה ב'
        st.write("---")
        nav_cols = st.columns([4, 1])  # יחס מורחב לטובת כפתור הבחירה
        with nav_cols[0]:
            view_option = st.radio("בחר סגנון תצוגה לעריכה:", ["טבלה", "רשימה נפתחת"], horizontal=True, key="view_style_opt")
        with nav_cols[1]:
            reset_all = st.button("🗑️ נקה הכל", use_container_width=True, help="מנקה ומאפס את כל סימוני המשמרות בטופס")
            if reset_all:
                for key in list(st.session_state.keys()):
                    if any(prefix in key for prefix in ["can_check_", "not_check_", "pref_check_", "day_mode_", "mobile_day_mode_"]):
                        if DISABLE_pilot and ("Friday" in key or "Saturday" in key) and ("Night" in key or "open_T" in key):
                            continue
                        st.session_state[key] = False
                st.toast("✅ כל תיבות הבחירה בטופס אופסו בהצלחה!")
                st.rerun()
        st.markdown("""
        <style>
        div[data-testid="stForm"] * { color: #1e293b !important; }
        div[data-testid="stExpander"] details summary span { color: #1e293b !important; font-weight: bold; }
        .shift-block-title { font-weight: bold; font-size: 14px; margin-top: 12px; margin-bottom: 2px; color: #2c3e50; text-align: right; }
        .hours-badge-pc { font-size: 11px; color: #64748b; font-weight: normal; margin-top: -3px; display: block; }
        
        @media (min-width: 768px) {
            div[data-testid="stForm"] { max-width: 80% !important; width: 80% !important; margin: 0 auto !important; padding: 1.5rem !important; }
            div[data-testid="stAppViewBlockContainer"] { max-width: 85% !important; }
            div[data-testid="stHorizontalBlock"] { gap: 8px !important; row-gap: 0px !important; align-items: start !important; }
            .pc-row-container { height: 95px !important; display: flex; flex-direction: column; justify-content: flex-start !important; margin-bottom: 0px !important; padding: 0px !important; }
            div[data-testid="stCheckbox"] { margin-top: 0px !important; margin-bottom: -12px !important; padding: 0px !important; height: 24px !important; }
            div[data-testid="stCheckbox"] label { padding-top: 0px !important; padding-bottom: 0px !important; min-height: 20px !important; }
        }
        @media (max-width: 767px) {
            /* 🔒 כופה על תיבת הטופס הראשית להכיל את הכול ומונעת בריחת אלמנטים מהמסך */
            div[data-testid="stForm"] { 
                width: 100% !important; 
                max-width: 100% !important; 
                padding: 10px !important; 
                box-sizing: border-box !important;
            }
            /* ⚡ מאפשר לרצועת הימים לגדול באופן דינמי ללא הגבלת רוחב, אך נועל את הגלילה בתוך התיבה */
            div[data-testid="stHorizontalBlock"] { 
                display: flex !important; 
                flex-direction: row !important; 
                flex-wrap: nowrap !important; 
                overflow-x: auto !important; 
                width: 100% !important;        /* נועל את מסילת הגלילה לרוחב המסך */
                max-width: 100% !important;    /* מונע פריצה החוצה מהמסגרת */
                align-items: flex-start !important; 
                -webkit-overflow-scrolling: touch !important; 
                padding-bottom: 12px !important;
            }
            /* 📐 רוחב העמודה   /
            div[data-testid="stHorizontalBlock"] > div { 
                width: 135px !important;       /* הגדרת רוחב קבועה וקשיחה */
                min-width: 135px !important; 
                flex-shrink: 0 !important;     /* מונע מסטרימליט למחוץ את הטורים */
            }
            .pc-row-container { height: auto !important; display: block !important; padding: 0px !important; }
            div[data-testid="stCheckbox"] { height: auto !important; margin-bottom: 2px !important; }
            div[data-testid="stCheckbox"] label p { font-size: 11px !important; }
            div[data-testid="stRadio"] label p { font-size: 13px !important; }
        }
    
        </style>
        """, unsafe_allow_html=True)
    
        
        # 3. מנגנון זמן וחסימת הגשות מיועל (שעון ירושלים)
        israel_tz = timezone(timedelta(hours=3))
        now_il = datetime.now(israel_tz)
        current_time_str = now_il.strftime("%H:%M:%S")
        current_date_str = now_il.strftime("%d/%m/%Y")
        
        st.markdown(f"<div style='text-align: left; font-size: 14px; color: #475569; direction: rtl; margin-bottom: 15px;'><b>שעון מערכת (ירושלים):</b> {current_time_str} | {current_date_str}</div>", unsafe_allow_html=True)
    
        
        # לוגיקת חסימה מדויקת: חוסם מרביעי (2) ב-11:00 ועד מוצאי שבת (5). יום ראשון (6) נשאר פתוח לחלוטין!
        is_submission_blocked = (
            (now_il.weekday() == 2 and now_il.hour >= 11) or 
            (2 < now_il.weekday() < 2)
        )
    

        
#**************************************************************************************************************************
#================ חלק 6  =======================

#================ חלק 6.1 מוגמר ומיועל =======================
        # פתיחת ה-form החוקי, ההרמטי והמלא שעוצר את ריענוני התיבות
        with st.form(key="shifts_form"):
            user_choices = {}
            current_role = str(st.session_state.get("user_role", "")).strip()
            
            # סנכרון משתנה התצוגה מול הבחירה שלך בחלק 5 (view_style_opt)
            is_wide_view = (st.session_state.get("view_style_opt", "טבלה") == "טבלה")
           
    
            # .1 מסלול מחשב (טבלה רחבה)
            if is_wide_view:
               
                days_cols = st.columns(len(ימים))
                for day_idx, d_info in enumerate(ימים):
                    tarih = f"({dates_list[day_idx][:5]})" if day_idx < len(dates_list) else ""
                
                    with days_cols[day_idx].container(border=True):
                        st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 15px; color: #1e293b;'>📅 יום {d_info['he']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align: right; font-size: 12px; color: #64748b; margin-bottom: 8px;'>{tarih}</div>", unsafe_allow_html=True)
    
                    
                        # 1. הגדרת מצבי החסימה של סוף השבוע
                        is_pilot_weekend = DISABLE_pilot and (d_info['en'] in ["Friday", "Saturday"])
                        is_bodekt_saturday = (current_role == "בודקת ביטחונית" and d_info['en'] == "Saturday")
                        should_disable_day = is_pilot_weekend or is_bodekt_saturday
                
                        # הגדרת המפתח של הרכיב מראש
                        radio_key = f"day_mode_{d_info['en']}"
                
                        # 2. קביעת סימון אוטומטי וכפיית הערך בזיכרון של Streamlit כדי למנוע את הבאג
                        if is_bodekt_saturday:
                            default_index = 3
                            st.session_state[radio_key] =  "🌴 חופשה מאושרת" # כופה על הזיכרון
                            st.caption("🔒 חסום (אין משמרות לבודקות בשבת)")
                        elif is_pilot_weekend:
                            default_index = 3
                            st.session_state[radio_key] = "🌴 חופשה מאושרת" # כופה על הזיכרון
                            st.caption("🔒 חסום ")
                        else:
                            default_index = 0
                
                        # 3. יצירת רכיב הרדיו במחשב
                        day_choice = st.radio(
                            f"בחר סטטוס ליום {d_info['he']}:",
                            ["בחר במשמרות", "🟢 יכול הכל היום", "🔴 לא יכול היום", "🌴 חופשה מאושרת"],
                            key=radio_key,
                            index=default_index,
                            horizontal=False,
                            label_visibility="collapsed",
                            disabled=should_disable_day
                        )
        
        
        
        
                        
                        all_can = (day_choice == "🟢 יכול הכל היום")
                        all_not = (day_choice == "🔴 לא יכול היום")
                        all_vacation = (day_choice == "🌴 חופשה מאושרת")  
        
                        st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                        
                        for s_info in משמרות:
                            column_name = f"{d_info['en']}_{s_info['en']}"
                            hours_txt = שעות_משמרת.get(s_info['en'], "")
                            hours_display = f" ({hours_txt})" if hours_txt else ""
        
                            #  קריאה לפונקציה החסימות 
                            is_blocked, block_reason = check_shift_blocking(
                                d_info['en'], s_info['en'], current_role, DISABLE_pilot
                            )
        
                            
        
                            st.write(f"**🔹 משמרת {s_info['he']}** {hours_display}")
                            
                            default_can = False if is_blocked else all_can
                            default_not = True if is_blocked else (all_not or all_vacation)
                            
                            if is_blocked or all_vacation:
                                final_reason = "🌴 חופשה" if all_vacation and not is_blocked else block_reason
                                st.checkbox(final_reason, key=f"not_check_{column_name}", value=True, disabled=True)
                                user_choices[column_name] = {"can": False, "cannot": True, "pref": False, "day_hebrew": d_info['he'], "shift_hebrew": s_info['he'], "all_can_selected": all_can, "all_not_selected": True, "all_vacation_selected": all_vacation}
                            else:
                                can_work = st.checkbox("יכול 👍", key=f"can_check_{column_name}", value=default_can)
                                cannot_work = st.checkbox("לא יכול ❌", key=f"not_check_{column_name}", value=default_not)
                                prefer_not = st.checkbox("מ.ש 🤷‍♂️", key=f"pref_check_{column_name}", value=False)
                                user_choices[column_name] = {"can": can_work, "cannot": cannot_work, "pref": prefer_not, "day_hebrew": d_info['he'], "shift_hebrew": s_info['he'], "all_can_selected": all_can, "all_not_selected": all_not, "all_vacation_selected": False}
        

#================ חלק 6.2 מוגמר ומיועל =======================
            # .2 מסלול נייד 
            else:
                for day_idx, d_info in enumerate(ימים):
                    tarih = f"({dates_list[day_idx][:5]})" if day_idx < len(dates_list) else ""
                    
                    with st.expander(f"📅 יום {d_info['he']} {tarih}", expanded=False):
                        # הגדרת המפתח של הרכיב מראש למובייל
                        mobile_radio_key = f"mobile_day_mode_{d_info['en']}"
    
                        # קביעת סימון אוטומטי וכפיית הערך בזיכרון של Streamlit במובייל
                        is_bodekt_saturday = st.session_state.get("is_bodekt_saturday", False)
                        is_pilot_weekend = st.session_state.get("is_pilot_weekend", False)
                        if is_bodekt_saturday:
                            default_index = 2
                            st.session_state[mobile_radio_key] = "🔴 לא יכול היום"
                            st.caption("🔒 חסום (אין משמרות לבודקות בשבת)")
                        elif is_pilot_weekend:
                            default_index = 3
                            st.session_state[mobile_radio_key] = "🌴 חופשה מאושרת"
                            st.caption("🔒 חסום (סוף שבוע פיילוט)")
                        else:
                            default_index = 0
                            
                        should_disable_day = False
                        day_choice = st.radio(
                            f"בחר סטטוס ליום {d_info['he']}",
                            ["בחר במשמרות", "🟢 יכול הכל היום", "🔴 לא יכול היום", "🌴 חופשה מאושרת"],
                            key=mobile_radio_key,
                            index=default_index,
                            horizontal=False,
                            label_visibility="collapsed",
                            disabled=should_disable_day
                        )
    
    
                        
                        all_can = (day_choice == "🟢 יכול הכל היום")
                        all_not = (day_choice == "🔴 לא יכול היום")
                        all_vacation = (day_choice == "🌴 חופשה מאושרת")  
                        
                        st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                        
                        for s_info in משמרות:
                            column_name = f"{d_info['en']}_{s_info['en']}"
                            hours_txt = שעות_משמרת.get(s_info['en'], "")
                            hours_display = f" ({hours_txt})" if hours_txt else ""
                           
                            
                            #  קריאה לפונקציה המאוחדת במקום כל הבלוק של החסימות הישנות שנמחקו
                            is_blocked, block_reason = check_shift_blocking(
                                d_info['en'], s_info['en'], current_role, DISABLE_pilot
                            )
    
                            # הצגת כותרת המשמרת (שורה 557 המקורית שלך)
                            st.write(f"**🔹 משמרת {s_info['he']}** {hours_display}")
                            
                            default_can = False if is_blocked else all_can
                            default_not = True if is_blocked else (all_not or all_vacation)
                            
                            if is_blocked or all_vacation:
                                final_reason = "🌴 חופשה" if all_vacation and not is_blocked else block_reason
                                # 🛠️ וידוא שימוש במפתח ייחודי m_ לחסימות מובייל
                                st.checkbox(final_reason, key=f"m_not_check_{column_name}", value=True, disabled=True)
                                user_choices[column_name] = {"can": False, "cannot": True, "pref": False, "day_hebrew": d_info['he'], "shift_hebrew": s_info['he'], "all_can_selected": all_can, "all_not_selected": True, "all_vacation_selected": all_vacation}
                            else:
                                # 🛠️ וידוא שימוש במפתח ייחודי m_ לתיבות הסימון הפתוחות במובייל למניעת Duplicate Key
                                can_work = st.checkbox("יכול 👍", key=f"m_can_check_{column_name}", value=default_can)
                                cannot_work = st.checkbox("לא יכול ❌", key=f"m_not_check_{column_name}", value=default_not)
                                prefer_not = st.checkbox("מ.ש 🤷‍♂️", key=f"m_pref_check_{column_name}", value=False)
                                user_choices[column_name] = {"can": can_work, "cannot": cannot_work, "pref": prefer_not, "day_hebrew": d_info['he'], "shift_hebrew": s_info['he'], "all_can_selected": all_can, "all_not_selected": all_not, "all_vacation_selected": False}
    


#***********************************************************************************************************************
#================ חלק 7 =======================

        # ===============================================================
        # .3 מחשבון מכסות וספירות משמרות שבועיות (לוגיקה מדויקת מגרסה א') [index]
        # ===============================================================
            count_morning = 0
            count_afternoon = 0
            count_night = 0
            cannot_count = 0
            count_support= 0
            
            for d_info in ימים:
                day_key = d_info['en']
                
                # שליפת סטטוס היום הנוכחי (תומך גם בטבלה וגם בנייד בצורה מושלמת)
                if is_wide_view:
                    day_status = st.session_state.get(f"day_mode_{day_key}", "בחר במשמרות")
                else:
                    day_status = st.session_state.get(f"mobile_day_mode_{day_key}", "בחר במשמרות")
        
                is_all_can = "🟢 יכול הכל היום" in day_status or "יכול הכל היום" in day_status
                is_vacation = "🌴 חופשה מאושרת" in day_status or "חופשה מאושרת" in day_status
                is_all_not = "🔴 לא יכול היום" in day_status or "לא יכול היום" in day_status
            
                # אם סומן "יכול הכל" או "חופשה מאושרת" ברמת היום, הוסף מיד 1 לכל סוגי המשמרות של אותו יום [index]
                is_pilot_weekend = DISABLE_pilot and (day_key in ["Friday", "Saturday"])
        
    
                # לולאה רגילה לספירת משמרות בודדות [index]
                for s_info in משמרות:
                    if DISABLE_pilot and (day_key in ["Friday", "Saturday"] or s_info.get('en', '') in ["open_T", "Night"]):
                        continue
            
                    col_name = f"{day_key}_{s_info['en']}"
                    shift_data2 = user_choices.get(col_name, {})
                    shift_key = s_info['en']
            
                    # בדיקה האם המשמרת נבחרה כיכולה (פרטנית או גלובלית) [index]
                    is_can_selected = shift_data2.get("can") or shift_data2.get("pref") or is_all_can or is_vacation
                    is_cannot_selected = shift_data2.get("cannot") or is_all_not or (day_status in ["🔴 לא יכול היום", "לא יכול היום"])
            
                    if is_can_selected:
                        if shift_key in ["open_T", "Morning"]:
                            count_morning += 1
                        elif shift_key == "Afternoon":
                            count_afternoon += 1
                        elif shift_key == "Night":
                            count_night += 1
                        elif shift_key == "Support":
                            count_support += 1
                    elif is_cannot_selected:
                        cannot_count += 1
            #                
            role_requirements = {
            "מאבטח": {"morning": 4, "afternoon": 3, "night": 0, "total": 10, "max_cannot": 5},
            "בודקת ביטחונית": {"morning": 3, "afternoon": 3, "night": 0, "total": 10, "max_cannot": 5},
            "בודק ביטחוני": {"morning": 3, "afternoon": 3, "night": 0, "total": 10, "max_cannot": 5},
            "אחמ''ש": {"morning": 1, "afternoon": 1, "night": 0, "total": 3, "max_cannot": 10},
            "מוקדנית": {"morning": 0, "afternoon": 0, "night": 0, "total": 6, "max_cannot": 3},
            "כללי": {"morning": 0, "afternoon": 0, "night": 0, "total": 0, "max_cannot": 5}
            }
    
                
            # שליפת הדרישות וטיפול מונע קריסות (הגנה מפני תפקיד חסר) [index]
            user_role_clean = current_role.strip()
            if user_role_clean == "בודק ביטחונית":
                user_role_clean = "בודקת ביטחונית"
                
            current_reqs = role_requirements.get(user_role_clean, role_requirements["כללי"])
            total_submitted = count_morning + count_afternoon + count_night + count_support
            
            # הצגת שורת הסיכום בצורה מובנית, מהירה וברורה [index]
            st.info(f"📊 **מדד מכסת הגשות שבועית לתפקידך:** בוקר: {count_morning}/{current_reqs['morning']} | צהריים: {count_afternoon}/{current_reqs['afternoon']} | לילה: {count_night}/{current_reqs['night']} | **סך הכל סומן:** {total_submitted}/{current_reqs['total']}")

#=======================================================================
# חלק 7: מנגנון בדיקת סתירות ושליחת הנתונים לגיליון (Timeout=20) [index]
#=======================================================================

            # תצוגת כפתור השליחה בהתאם למצב החסימה
            # --- תצוגת כפתור השליחה בהתאם למצב החסימה (שורות 624-631) ---
            # --- תצוגת כפתור השליחה בהתאם למצב החסימה ---
            if is_submission_blocked:
                st.error("הגשת האילוצים לשבוע זה נסגרה, לא ניתן לשלוח טפסים חדשים.")
                submit_button = st.form_submit_button("שלח אילוצים למערכת (חסום)", use_container_width=True, disabled=True)
            else:
                user_comments = st.text_input("💬 הערות ובקשות נוספות למנהל (אופציונלי):", value="", max_chars=250, key="user_free_comments")
                submit_button = st.form_submit_button(MSG_SUBMIT_BTN, use_container_width=True)
        
            # --- תחילת לוגיקת העיבוד לאחר לחיצה ---
            if submit_button and not is_submission_blocked:
                errors = []
        
                
                # בדיקת עמידה במכסות המינימום הארגוניות
                if count_morning < current_reqs.get("morning", 0):
                    errors.append(f"בוקר סומנו {count_morning}/{current_reqs.get('morning', 0)}")
                if count_afternoon < current_reqs.get("afternoon", 0):
                    errors.append(f"צהריים סומנו {count_afternoon}/{current_reqs.get('afternoon', 0)}")
                if count_night < current_reqs.get("night", 0):
                    errors.append(f"לילה סומנו {count_night}/{current_reqs.get('night', 0)}")
                if total_submitted < current_reqs.get("total", 0):
                    errors.append(f"סך הכל משמרות לשבוע סומנו {total_submitted}/{current_reqs.get('total', 0)}")
                    
                if errors:
                    st.error("🚨 לא ניתן לשלוח! חסר לך מכסת מינימום במשמרות הבאות:")
                    for err in errors:
                        st.markdown(f"<div style='text-align: right; font-size: 13px; color: #b91c1c; padding-right: 15px;'>• {err}</div>", unsafe_allow_html=True)
                    st.stop()
        
                # --- # 2. מעבר לבדיקת סתירות לוגיות והגבלת משמרות "לא יכול" (שורות 654 ואילך) ---
                has_error = False
                errors_list = []
                cannot_count = 0  # מונה שבועי למשמרות "לא יכול"
                
                # שליפת המגבלה המקסימלית של "לא יכול" לפי התפקיד מתוך ה- (ברירת המחדל היא 5) [index]
                max_cannot_allowed = current_reqs.get("max_cannot", 5)
                
                for d_info in ימים:
                    day_key = d_info['en']
                    day_he = d_info['he']
                    
                    status_key = f"day_mode_{day_key}" if is_wide_view else f"mobile_day_mode_{day_key}"
                    day_status = st.session_state.get(status_key, "בחר במשמרות")
                    
                    day_has_can = False
                    day_has_cannot = False
                    
                    for s_info in משמרות:
                        if is_vacation:
                            continue
                        if DISABLE_pilot and (day_key in ['Friday', 'Saturday'] or s_info.get('en', '') in ['open_T', 'Night']):
                            continue
                            
                        col_name = f"{day_key}_{s_info['en']}"
                        shift_data = user_choices.get(col_name, {})
                        
                        is_shift_cannot = False
                        is_shift_can = False
                        
                        is_weekend = day_key in ['Friday', 'Saturday']
                        
                        # א. בדיקת סטטוס "לא יכול" במשמרת הנוכחית
                        # אם הפיילוט פעיל ובסופ"ש - זה אוטומטית נחשב "לא יכול" אך מוחרג מהמונה השבועי [index]
                        if DISABLE_pilot and (is_weekend or s_info.get('en', '') in ['open_T', 'Night']):
                            is_shift_cannot = True
                            # חסימת פיילוט אוטומטית - לא מעלה את cannot_count!
                        elif shift_data.get("cannot") or "🔴" in day_status or "לא יכול" in day_status:
                            is_shift_cannot = True
                            day_has_cannot = True
                            cannot_count += 1
                                
                        # ב. בדיקת סטטוס "יכול" או "העדפה" במשמרת הנוכחית
                        if shift_data.get("can") or shift_data.get("pref"):
                            is_shift_can = True
                            day_has_can = True
                
                        # 🔒 [חסימת כפילות] - בדיקה אם סומן גם יכול וגם לא יכול באותה משמרת ספציפית [index]
                        if is_shift_can and is_shift_cannot:
                            has_error = True
                            errors_list.append(f"משמרת כפולה ביום {day_he} במשמרת {s_info.get('he', '')}: לא ניתן לסמן גם 'יכול' וגם 'לא יכול' יחד!")
        
                    # --- חסימה 1: בחר "יכול הכל היום" אך יש סימון "לא יכול" במשמרות ---
                    if ("🟢" in day_status or "יכול הכל" in day_status) and day_has_cannot:
                        has_error = True
                        errors_list.append(f"ביום {day_he}: בחרת 'יכול הכל היום' אך סימנת משמרת כ-'לא יכול'")
                
                    # --- חסימה 2: בחר "לא יכול היום" אך יש סימון "יכול" במשמרות ---
                    if ("🔴" in day_status or "לא יכול" in day_status) and day_has_can:
                        has_error = True
                        errors_list.append(f"ביום {day_he}: בחרת 'לא יכול היום' אך סימנת משמרת כ-'יכול'")
                
                    # --- חסימה 3: בחירת חופשה אך יש סימונים ידניים במשמרות ---
                   # בדיקת סתירות: רק אם נבחרה חופשה ויש סימונים ידניים (יכול, לא יכול, מ.ש) ולא בגלל חסימת פיילוט אוטומטית
                    if ("🌴" in day_status or "חופשה מאושרת" in day_status):
                        # בודקים אם יש סימונים אמיתיים שהם לא החסימה האוטומטית של הפיילוט
                        has_real_manual_marks = day_has_can or (day_has_cannot and not DISABLE_pilot)
                        
                        if has_real_manual_marks:
                            has_error = True
                            errors_list.append(f"ביום {day_he}: בחרת 'חופשה מאושרת' אך ישנם סימוני משמרות באותו יום")
                
                # --- חסימה שבועית דינמית: חריגת מקסימום משמרות "לא יכול" לפי הגדרות תפקיד [index]
                if cannot_count > max_cannot_allowed:
                    has_error = True
                    errors_list.append(f"חריגה בכמות משמרות 'לא יכול': מותר לסמן לכל היותר {max_cannot_allowed} משמרות בשבוע (סומנו {cannot_count}/{max_cannot_allowed})")
                    
                # --- הצגת שגיאות סתירה ועצירת ההגשה (שורות 709-713) ---
                if has_error:
                    st.error("🛑 לא ניתן לשלוח את הטופס! נמצאו סתירות או חריגות בסימונים הבאים:")
                    for err in errors_list:
                        st.markdown(f"<div style='text-align: right; font-size: 13px; color: #b91c1c; padding-right: 15px;'>• {err}</div>", unsafe_allow_html=True)
                    st.stop()
                    
                # --- שליחה לגוגל סקריפט במידה והכל תקין לחלוטין ---
                else:
                    with st.spinner(MSG_SPINNER_SAVE):
                        save_success = False  # מששתנה דגל שבודק אם השמירה הצליחה באמת
                        # שימוש ב-zoneinfo המובנה של פייתון ללא צורך ב-pytz
                        from zoneinfo import ZoneInfo
                        local_tz = ZoneInfo('Asia/Jerusalem')
                        timestamp = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
                        
                        payload = {
                            "Timestamp": timestamp,
                            "Employee Name": st.session_state.user_name,
                            "Week Date": start_date_display,
                            "role": current_role,
                            "Comments": user_comments
                        }
        
                        
                        # בניית ה-payload עבור התיבות השונות של המשמרות
                        for col_name, info in user_choices.items():
                            day_key_part = col_name.split('_')[0]
                            status_key = f"day_mode_{day_key_part}" if is_wide_view else f"mobile_day_mode_{day_key_part}"
                            day_status = st.session_state.get(status_key, "בחר במשמרות")
        
                            is_col_weekend = day_key_part in ['Friday', 'Saturday']
        
                            # 🛠️ החרגה לפיילוט: אם הדגל פעיל ובסופ"ש - נאלץ אוטומטית "לא יכול" (X) בגיליון [index]
                            if DISABLE_pilot and is_col_weekend:
                                payload[col_name] = "ח"
                            elif "🟢" in day_status or "יכול הכל" in day_status: # בדיקה כפולה של טקטס או צבע נקודה  
                                payload[col_name] = "V"
                            elif "🔴" in day_status or "לא יכול" in day_status:
                                payload[col_name] = "X"
                            elif "🌴" in day_status or "חופשה" in day_status:
                                payload[col_name] = "ח"
                            else:
                                is_cannot = info.get("cannot") or info.get("all_not_selected")
                                is_pref = info.get("pref")
                                is_can = info.get("can")
        
                                if not (is_cannot or is_pref or is_can):
                                    payload[col_name] = "V"
                                else:
                                    if is_cannot:
                                        payload[col_name] = "X"
                                    elif is_pref:
                                        payload[col_name] = "מ.ש"
                                    else:
                                        payload[col_name] = "V"
        
                        try:
                            res_submit = requests.post(SCRIPT_URL, json=payload, timeout=20)
                            if res_submit.status_code == 200:
                                save_success = True
                                # יצירת הודעה בולטת במרכז המסך
                                with st.container():
                                    st.markdown("""
                                        <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; border: 2px solid #28a745; text-align: center;">
                                            <h2 style="color: #155724; margin: 0;">✅ הבקשות נשלחו בהצלחה!</h2>
                                            <p style="color: #155724; font-size: 18px;">הסידור נקלט במערכת.</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # כפתור אישור שמופיע רק אחרי השליחה
                                    if st.button("אישור ", key="confirm_submission_done"):
                                        st.rerun()
                                    
                                    # עצירה כדי שהמשתמש לא ימשיך לעבוד על המסך מאחורה
                                    st.stop()
                            else:
                                st.error(MSG_SAVE_ERR)
                                if st.button("🔄 נסה לשלוח שוב", key="retry_submit_failed_btn"):
                                    st.rerun()
                        except Exception:
                            # אם תפסה שגיאה, נבדוק האם בפועל השמירה נכשלה לגמרי
                            if not save_success:
                                st.error("⚠️ שגיאת קטיעת זמן בשמירה מול גוגל, אך ייתכן שהנתונים נקלטו. נא לבדוק בגיליון הסיכום.")





#*********************************************************************************************************************
#================ חלק 8  (תצוגת כרטיסיות הבקשות) =======================
    st.write("---")
 # 🗓️ חלק תצוגת הבקשות שהוגשו 
    st.write("###  📋 הבקשות המעודכנות במערכת")


try:
    current_user = str(st.session_state.get("user_name", "")).strip()
    if current_user:
        import time
        # 1. מניעת מטמון (Cache Buster) לקבלת נתונים עדכניים
        cache_buster = int(time.time())
        active_res = requests.get(f"{SCRIPT_URL}?sheet=Sheet1&cb={cache_buster}", timeout=40)
        
        if active_res.status_code == 200:
            raw_data = active_res.json()
            raw_rows = [r for r in raw_data if isinstance(r, dict)] if isinstance(raw_data, list) else []
            
            # תאריך היעד מה-Settings בפורמט DD/MM/YYYY
            target_date_clean = start_date_display.strip() 
            
            raw_sheet_val = ""
            clean_date_after_4_hours = "לא ידוע"
            filtered_user_rows = []
            
            # 2. מעבר על הגיליון וביצוע סינון מדויק
            for row in raw_rows:
                row_user = str(row.get("Employee Name", "")).strip()
                row_week = ""
                for k, v in row.items():
                    if "week" in str(k).lower() and "date" in str(k).lower():
                        row_week = str(v).strip()
                        break
                
                if row_user.lower() == current_user.lower() and row_week:
                    row_week_clean = ""
                    try:
                        w_str = row_week.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(w_str)
                        dt_adjusted = dt + timedelta(hours=4)
                        row_week_clean = dt_adjusted.strftime('%d/%m/%Y')
                    except Exception:
                        if '-' in row_week:
                            p = row_week[:10].split('-')
                            if len(p) == 3: 
                                row_week_clean = f"{p}/{p}/{p}"
                        else:
                            row_week_clean = row_week[:10]
                   # st.write(f"Comparing -> Target: [{target_date_clean}] vs Row: [{row_week_clean}]")
                    if target_date_clean == row_week_clean.strip():
                        filtered_user_rows.append(row)
            
            # חילוץ נתונים לצורך חילוץ התאריך הנקי האחרון מההיסטוריה
            user_rows = [r for r in raw_rows if str(r.get("Employee Name", "")).strip().lower() == current_user.lower()]
            if user_rows:
                user_rows.sort(key=lambda x: str(x.get("Timestamp", "")))
                latest_backup_row = user_rows[-1]
                for k, v in latest_backup_row.items():
                    if "week" in str(k).lower() and "date" in str(k).lower():
                        raw_sheet_val = str(v).strip()
                        break
                try:
                    w_str = raw_sheet_val.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(w_str)
                    dt_adjusted = dt + timedelta(hours=4)
                    clean_date_after_4_hours = dt_adjusted.strftime('%d/%m/%Y')
                except Exception:
                    clean_date_after_4_hours = raw_sheet_val[:10]
            
            # 3. בדיקת התאמה והצגת הודעות מצב
            user_row = None
            
            if filtered_user_rows:
                # נמצאה בקשה מדויקת לתאריך המבוקש - ניקח את המעודכנת ביותר מביניהן
                user_row = filtered_user_rows[-1]
                raw_ts = user_row.get("Timestamp", "")
                try:
                    w_str = raw_ts.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(w_str)
                    dt_adjusted = dt + timedelta(hours=3) # או מספר השעות שתרצה להוסיף
                    formatted_time = dt_adjusted.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    formatted_time = raw_ts
                
                st.success(f"הבקשות הוגשו ב- {formatted_time}")
            else:
                # אין בקשה לתאריך המוגדר
                st.warning("אין בקשות לשבוע הבא - נא להגיש")
                user_row = None
            
            # 4. רינדור כרטיסיות המשמרות (יוצג רק אם נמצאה שורה תואמת)
            if user_row:
                clean_user_row = {str(k).strip(): str(v).strip() for k, v in user_row.items()}
                current_view = locals().get("view_option", st.session_state.get("view_option", ""))
                is_mobile_device = st.session_state.get("is_mobile", False)

               
            
                is_wide_view_summary = ("טבלה" in str(current_view) and not is_mobile_device)
                days_order_en = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                days_order_he = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
        
                
                # --- מצב א': תצוגה רחבה (מחשב) - שימוש ב-st.columns רשמי מימין לשמאל ---
               
                if is_wide_view_summary:
                    summary_cols = st.columns(7)
                    
                    # התיקון: הסרנו את reversed כדי שהתאריכים יתחילו מ-02/08 בימין ויתקדמו ימינה בצורה טבעית
                    for col_idx, (day_idx, d_info) in enumerate(list(enumerate(dates_list))):
                        en_day = days_order_en[day_idx] if day_idx < len(days_order_en) else "Sunday"
                        he_day_name = days_order_he[day_idx] if day_idx < len(days_order_he) else "שבוע"
                        
                        date_str = d_info.get('date', d_info) if isinstance(d_info, dict) else str(d_info)
                        main_title = date_str[:10]
                        
                        day_lines = []
                        for c_info in משמרות:
                            s_en = c_info.get('en', c_info) if isinstance(c_info, dict) else str(c_info)
                            s_he = c_info.get('he', c_info) if isinstance(c_info, dict) else str(c_info)
                            exact_col = f"{en_day}_{s_en}"
                            val = clean_user_row.get(exact_col, "")
                            
                            if val in ["V", "v", "TRUE", "True", "1", "יכול"]: day_lines.append(f"<b>{s_he}</b>: יכול 👍")
                            elif val in ["מ.ש", "ש.מ"]: day_lines.append(f"<b>{s_he}</b>: מ.ש 🙋‍♂️")
                            elif val in ["ח", "חופשה", "🌴", "ח "]: day_lines.append(f"<b>{s_he}</b>: חופשה 🌴")
                            elif val in ["X", "x", "FALSE", "False", "0", "לא יכול", "n", "N"]: day_lines.append(f"<b>{s_he}</b>: לא יכול ❌")
                            elif val: day_lines.append(f"<b>{s_he}</b>: {val}")
                            else: day_lines.append(f"<b>{s_he}</b>: (אין ערך)")
                        
                        lines_html = "".join([f"<div style='font-size: 13px; margin-bottom: 3px; color: #1e293b; text-align: right;'>• {line}</div>" for line in day_lines])
                        
                        summary_html = f"""
                            <div dir='rtl' style='text-align: right; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; background-color: #ffffff; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>
                                <div style='font-size: 16px; font-weight: bold; color: #1e293b; text-align: center;'>{date_str} 📅</div>
                                <div style='font-size: 13px; color: #64748b; text-align: center; margin-bottom: 8px;'>{he_day_name}</div>
                                <hr style='margin: 5px 0 10px 0; border: none; border-top: 1px solid #edf2f7;'>
                                {''.join([f"<div style='text-align: right; font-size: 13px; margin-bottom: 3px; color: #1e293b;'>• {line}</div>" for line in day_lines])}
                            </div>
                        """
                        with summary_cols[col_idx]:
                            st.markdown(summary_html, unsafe_allow_html=True)
                            
                # --- מצב ב': תצוגת מובייל / רשימה אנכית (אחד מתחת לשני) ---
                else:
                    for day_idx, d_info in enumerate(dates_list):
                        en_day = days_order_en[day_idx] if day_idx < len(days_order_en) else "Sunday"
                        he_day_name = days_order_he[day_idx] if day_idx < len(days_order_he) else "שבוע"
                        
                        date_str = d_info.get('date', d_info) if isinstance(d_info, dict) else str(d_info)
                        main_title = date_str[:10]
                        
                        day_lines = []
                        for c_info in משמרות:
                            s_en = c_info.get('en', c_info) if isinstance(c_info, dict) else str(c_info)
                            s_he = c_info.get('he', c_info) if isinstance(c_info, dict) else str(c_info)
                            exact_col = f"{en_day}_{s_en}"
                            val = clean_user_row.get(exact_col, "")
                            
                            if val in ["V", "v", "TRUE", "True", "1", "יכול"]: day_lines.append(f"<b>{s_he}</b>: יכול 👍")
                            elif val in ["מ.ש", "ש.מ"]: day_lines.append(f"<b>{s_he}</b>: מ.ש 🙋‍♂️")
                            elif val in ["ח", "חופשה", "🌴", "ח "]: day_lines.append(f"<b>{s_he}</b>: חופשה 🌴")
                            elif val in ["X", "x", "FALSE", "False", "0", "לא יכול", "n", "N"]: day_lines.append(f"<b>{s_he}</b>: לא יכול ❌")
                            elif val: day_lines.append(f"<b>{s_he}</b>: {val}")
                            else: day_lines.append(f"<b>{s_he}</b>: (אין ערך)")
                        
                        lines_html = "".join([f"<div style='font-size: 13px; margin-bottom: 3px; color: #1e293b; text-align: right;'>• {line}</div>" for line in day_lines])
                        
                        summary_html = f"""
                            <div dir='rtl' style='text-align: right; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; background-color: #ffffff; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>
                                <div style='font-size: 16px; font-weight: bold; color: #1e293b; text-align: center;'>{date_str} 📅</div>
                                <div style='font-size: 13px; color: #64748b; text-align: center; margin-bottom: 8px;'>{he_day_name}</div>
                                <hr style='margin: 5px 0 10px 0; border: none; border-top: 1px solid #edf2f7;'>
                                {''.join([f"<div style='text-align: right; font-size: 13px; margin-bottom: 3px; color: #1e293b;'>• {line}</div>" for line in day_lines])}
                            </div>
                        """
                        st.markdown(summary_html, unsafe_allow_html=True)
        #----                
        else:
            st.error("⚠️ לא ניתן לקרוא נתונים משרת גוגל.")
            if st.button("🔄 נסה לטעון נתונים מחדש", key="refresh_requests_failed"):
                st.rerun()
                
except Exception as e:
    st.warning(f"⚠️ שגיאה בטעינת נתוני סיכום: {e}")
