# -*- coding: utf-8 -*-
"""
קובץ: app.py
תיאור: האפליקציה הגרפית הראשית (Tkinter) עבור מערכת LuxStay OS.
       מתחברת למסד הנתונים PostgreSQL ומציגה מסכי CRUD לכל הטבלאות,
       דוחות מורכבים והרצת פונקציות/פרוצדורות.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import db  # ייבוא קובץ החיבור שיצרנו

# =======================================================================
# הגדרות עיצוב כלליות למערכת (Design Tokens)
# =======================================================================
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_LABEL = (FONT_FAMILY, 10, "bold")
FONT_ENTRY = (FONT_FAMILY, 10)
FONT_BUTTON = (FONT_FAMILY, 10, "bold")

COLOR_PRIMARY = "#2C3E50"      # כחול כהה (עבור כותרות ורקעים ראשיים)
COLOR_SECONDARY = "#18BC9C"    # ירוק טורקיז (עבור כפתורי אישור/הוספה)
COLOR_DANGER = "#E74C3C"       # אדום (עבור כפתורי מחיקה/ביטול)
COLOR_BG = "#ECF0F1"           # אפור בהיר (רקע כללי)
COLOR_WHITE = "#FFFFFF"        # לבן (רקע טפסים/טבלאות)

# =======================================================================
# פונקציות עזר לשליפת מזהה הבא (Auto-Suggestion)
# =======================================================================
def suggest_next_id(table, col):
    """ מחזיר את ה-ID הפנוי הבא בטבלה. """
    try:
        res = db.fetch_query(f"SELECT COALESCE(MAX({col}), 0) + 1 FROM {table};")
        return res[0][0]
    except Exception:
        return 1

# =======================================================================
# מחלקת הבסיס לחלון ניהול - מכילה פונקציונליות משותפת
# =======================================================================
class BaseManagementWindow(tk.Toplevel):
    def __init__(self, parent, title, size="900x600"):
        super().__init__(parent)
        self.title(title)
        self.geometry(size)
        self.configure(bg=COLOR_BG)
        
        # מרכוז החלון על המסך
        self.center_window()
        
        # כותרת ראשית
        self.header_label = tk.Label(
            self, text=title, font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_WHITE
        )
        self.header_label.pack(fill="x", side="top")
        
        # שדות לשמירת נתונים
        self.selected_pk = None  # יישמר כאן ה-PK של הרשומה שנטענה לעדכון

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

# =======================================================================
# 1. מסך ניהול חדרים (Room CRUD)
# =======================================================================
class RoomWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול חדרים - Room Management", "1000x650")
        
        # מילוי מילונים של מפתחות זרים
        self.load_fk_mappings()
        
        # יצירת המבנה הכללי: עליון = טבלה, תחתון = טופס וכפתורים
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def load_fk_mappings(self):
        try:
            # שליפת סוגי חדרים
            types = db.fetch_query("SELECT roomtypeid, typename FROM roomtype;")
            self.type_name_to_id = {row[1]: row[0] for row in types}
            self.type_id_to_name = {row[0]: row[1] for row in types}

            # שליפת סטטוסים
            statuses = db.fetch_query("SELECT statusid, statusname FROM roomstatus;")
            self.status_name_to_id = {row[1]: row[0] for row in statuses}
            self.status_id_to_name = {row[0]: row[1] for row in statuses}
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת נתוני מפתחות זרים:\n{e}")

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # הגדרת עמודות - לא מציגים רק IDs אלא שמות ברורים!
        columns = ("roomid", "roomnumber", "floor", "maxoccupancy", "phonenumber", "typename", "statusname")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        self.tree.heading("roomid", text="מזהה פנימי (ID)")
        self.tree.heading("roomnumber", text="מספר חדר")
        self.tree.heading("floor", text="קומה")
        self.tree.heading("maxoccupancy", text="תפוסה מקסימלית")
        self.tree.heading("phonenumber", text="מספר טלפון")
        self.tree.heading("typename", text="סוג חדר")
        self.tree.heading("statusname", text="סטטוס חדר")
        
        # רוחב עמודות
        self.tree.column("roomid", width=80, anchor="center")
        self.tree.column("roomnumber", width=100, anchor="center")
        self.tree.column("floor", width=80, anchor="center")
        self.tree.column("maxoccupancy", width=120, anchor="center")
        self.tree.column("phonenumber", width=120, anchor="center")
        self.tree.column("typename", width=180, anchor="e")
        self.tree.column("statusname", width=150, anchor="e")
        
        # הוספת פס גלילה
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # אירוע בחירת שורה
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי החדר (עריכה / הוספה)", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        # שדות קלט
        tk.Label(form_frame, text="מזהה חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="מספר חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_number = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_number.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="קומה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.ent_floor = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_floor.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="תפוסה מקסימלית:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_occupancy = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_occupancy.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="טלפון בחדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_phone = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_phone.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="סוג חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=4, sticky="w", padx=5, pady=5)
        self.cmb_type = ttk.Combobox(form_frame, values=list(self.type_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_type.grid(row=1, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="סטטוס חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.cmb_status = ttk.Combobox(form_frame, values=list(self.status_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_status.grid(row=2, column=1, padx=5, pady=5)
        
        # כפתורים
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        # מחיקת שורות קיימות בטבלה
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # שליפה עם JOIN להצגת שמות במקום קודים
        query = """
            SELECT r.roomid, r.roomnumber, r.floor, r.maxoccupancy, r.phonenumber, rt.typename, rs.statusname
            FROM room r
            LEFT JOIN roomtype rt ON r.roomtypeid = rt.roomtypeid
            LEFT JOIN roomstatus rs ON r.statusid = rs.statusid
            ORDER BY r.roomnumber;
        """
        try:
            rows = db.fetch_query(query)
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליפת חדרים:\n{e}")

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        # מציע אוטומטית מזהה פנוי
        next_id = suggest_next_id("room", "roomid")
        self.ent_id.insert(0, str(next_id))
        
        self.ent_number.delete(0, tk.END)
        self.ent_floor.delete(0, tk.END)
        self.ent_occupancy.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.cmb_type.set("")
        self.cmb_status.set("")
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            # אם לא נבחר בטבלה, אולי הזין מפתח ידנית
            manual_id = self.ent_id.get().strip()
            if not manual_id:
                messagebox.showwarning("טעינת נתונים", "אנא בחר שורה בטבלה או הזן מזהה חדר בשדה.")
                return
            try:
                row = db.fetch_query("SELECT roomid, roomnumber, floor, maxoccupancy, phonenumber, roomtypeid, statusid FROM room WHERE roomid = %s;", (int(manual_id),))
                if not row:
                    messagebox.showwarning("לא נמצא", f"חדר עם מזהה {manual_id} לא נמצא.")
                    return
                # עדכון שדות טעינה מה-DB
                r = row[0]
                self.clear_fields()
                self.ent_id.delete(0, tk.END)
                self.ent_id.insert(0, str(r[0]))
                self.ent_number.insert(0, str(r[1]))
                self.ent_floor.insert(0, str(r[2]))
                self.ent_occupancy.insert(0, str(r[3]))
                self.ent_phone.insert(0, r[4] or "")
                self.cmb_type.set(self.type_id_to_name.get(r[5], ""))
                self.cmb_status.set(self.status_id_to_name.get(r[6], ""))
                self.selected_pk = r[0]
                return
            except ValueError:
                messagebox.showerror("שגיאה", "מזהה חדר חייב להיות מספר שלם.")
                return
            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה בטעינה לפי מפתח:\n{e}")
                return

        # טעינה מהטבלה הגרפית
        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_number.insert(0, item[1])
        self.ent_floor.insert(0, item[2])
        self.ent_occupancy.insert(0, item[3])
        self.ent_phone.insert(0, item[4] if item[4] != "None" else "")
        self.cmb_type.set(item[5])
        self.cmb_status.set(item[6])
        
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            rid = int(self.ent_id.get().strip())
            rnum = int(self.ent_number.get().strip())
            rfloor = int(self.ent_floor.get().strip())
            rocc = int(self.ent_occupancy.get().strip())
        except ValueError:
            messagebox.showerror("שגיאת קלט", "המזהה, מספר החדר, הקומה והתפוסה חייבים להיות מספרים שלמים!")
            return None
        
        phone = self.ent_phone.get().strip()
        typename = self.cmb_type.get()
        statusname = self.cmb_status.get()
        
        if not typename or not statusname:
            messagebox.showerror("שגיאת קלט", "חובה לבחור סוג חדר וסטטוס!")
            return None
            
        type_id = self.type_name_to_id[typename]
        status_id = self.status_name_to_id[statusname]
        
        return rid, rnum, rfloor, rocc, phone, type_id, status_id

    def add_record(self):
        data = self.validate_inputs()
        if not data:
            return
        
        rid, rnum, rfloor, rocc, phone, type_id, status_id = data
        
        # בדיקה שהמזהה לא קיים כבר
        exists = db.fetch_query("SELECT COUNT(*) FROM room WHERE roomid = %s OR roomnumber = %s;", (rid, rnum))
        if exists[0][0] > 0:
            messagebox.showerror("שגיאה", "מזהה חדר או מספר חדר זה כבר קיימים במערכת!")
            return

        try:
            db.execute_query(
                "INSERT INTO room (roomid, roomnumber, floor, maxoccupancy, phonenumber, roomtypeid, statusid) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (rid, rnum, rfloor, rocc, phone if phone else None, type_id, status_id)
            )
            messagebox.showinfo("הצלחה", "החדר נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בהוספה", f"לא ניתן להוסיף את הרשומה:\n{e}")

    def update_record(self):
        if self.selected_pk is None:
            messagebox.showwarning("עדכון", "יש לטעון רשומה תחילה (על ידי לחיצה כפולה בטבלה או טעינה לפי מפתח)!")
            return
        
        data = self.validate_inputs()
        if not data:
            return
            
        rid, rnum, rfloor, rocc, phone, type_id, status_id = data
        
        # אם שינו את ה-ID עצמו, נוודא שאין התנגשות עם ID אחר
        if rid != self.selected_pk:
            exists = db.fetch_query("SELECT COUNT(*) FROM room WHERE roomid = %s;", (rid,))
            if exists[0][0] > 0:
                messagebox.showerror("שגיאה", "המזהה החדש כבר קיים במערכת!")
                return

        try:
            db.execute_query(
                """UPDATE room 
                   SET roomid = %s, roomnumber = %s, floor = %s, maxoccupancy = %s, phonenumber = %s, roomtypeid = %s, statusid = %s
                   WHERE roomid = %s;""",
                (rid, rnum, rfloor, rocc, phone if phone else None, type_id, status_id, self.selected_pk)
            )
            messagebox.showinfo("הצלחה", "פרטי החדר עודכנו בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בעדכון", f"לא ניתן לעדכן את הרשומה:\n{e}")

    def delete_record(self):
        if self.selected_pk is None:
            # ננסה לקחת מהשדה אם המשתמש הקיש ידנית
            manual_id = self.ent_id.get().strip()
            if not manual_id:
                messagebox.showwarning("מחיקה", "אנא בחר חדר למחיקה מהטבלה או הזן מזהה חדר.")
                return
            try:
                self.selected_pk = int(manual_id)
            except ValueError:
                messagebox.showerror("שגיאה", "מזהה חדר חייב להיות מספר.")
                return

        confirm = messagebox.askyesno("אישור מחיקה", f"האם אתה בטוח שברצונך למחוק את חדר {self.selected_pk}?\nשימו לב: פעולה זו עלולה להיכשל אם ישנן רשומות מקושרות (תחזוקה/מתקנים).")
        if not confirm:
            return
            
        try:
            db.execute_query("DELETE FROM room WHERE roomid = %s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "החדר נמחק בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", f"לא ניתן למחוק את החדר (ייתכן שיש לו מתקנים מקושרים או רשומות תחזוקה):\n{e}")

# =======================================================================
# 2. מסך ניהול סוגי חדרים (RoomType CRUD)
# =======================================================================
class RoomTypeWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול סוגי חדרים - Room Types", "900x600")
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("roomtypeid", "typename", "baseprice", "description", "bedtype")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        self.tree.heading("roomtypeid", text="מזהה סוג (ID)")
        self.tree.heading("typename", text="שם הסוג")
        self.tree.heading("baseprice", text="מחיר בסיס")
        self.tree.heading("description", text="תיאור")
        self.tree.heading("bedtype", text="סוג מיטה")
        
        self.tree.column("roomtypeid", width=80, anchor="center")
        self.tree.column("typename", width=150, anchor="e")
        self.tree.column("baseprice", width=100, anchor="center")
        self.tree.column("description", width=300, anchor="e")
        self.tree.column("bedtype", width=120, anchor="e")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי סוג החדר", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה סוג:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="שם הסוג:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="מחיר בסיס:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.ent_price = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_price.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="סוג מיטה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_bed = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_bed.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="תיאור:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_desc = tk.Entry(form_frame, font=FONT_ENTRY, width=40)
        self.ent_desc.grid(row=1, column=3, columnspan=3, sticky="we", padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = db.fetch_query("SELECT roomtypeid, typename, baseprice, description, bedtype FROM roomtype ORDER BY roomtypeid;")
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליפת סוגי חדרים:\n{e}")

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        next_id = suggest_next_id("roomtype", "roomtypeid")
        self.ent_id.insert(0, str(next_id))
        self.ent_name.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_bed.delete(0, tk.END)
        self.ent_desc.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id:
                messagebox.showwarning("טעינה", "אנא בחר שורה או הזן מזהה.")
                return
            try:
                row = db.fetch_query("SELECT roomtypeid, typename, baseprice, description, bedtype FROM roomtype WHERE roomtypeid = %s;", (int(manual_id),))
                if not row:
                    messagebox.showwarning("לא נמצא", f"סוג חדר {manual_id} לא נמצא.")
                    return
                r = row[0]
                self.clear_fields()
                self.ent_id.delete(0, tk.END)
                self.ent_id.insert(0, str(r[0]))
                self.ent_name.insert(0, r[1])
                self.ent_price.insert(0, str(r[2]))
                self.ent_desc.insert(0, r[3] or "")
                self.ent_bed.insert(0, r[4] or "")
                self.selected_pk = r[0]
                return
            except ValueError:
                messagebox.showerror("שגיאה", "מזהה חייב להיות מספר.")
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_name.insert(0, item[1])
        self.ent_price.insert(0, item[2])
        self.ent_desc.insert(0, item[3] if item[3] != "None" else "")
        self.ent_bed.insert(0, item[4] if item[4] != "None" else "")
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            tid = int(self.ent_id.get().strip())
            price = float(self.ent_price.get().strip())
        except ValueError:
            messagebox.showerror("קלט לא תקין", "מזהה חייב להיות שלם, מחיר בסיס חייב להיות מספר.")
            return None
        
        name = self.ent_name.get().strip()
        bed = self.ent_bed.get().strip()
        desc = self.ent_desc.get().strip()
        
        if not name:
            messagebox.showerror("קלט חסר", "חובה להזין שם לסוג החדר!")
            return None
            
        return tid, name, price, desc, bed

    def add_record(self):
        data = self.validate_inputs()
        if not data:
            return
        tid, name, price, desc, bed = data
        
        exists = db.fetch_query("SELECT COUNT(*) FROM roomtype WHERE roomtypeid = %s;", (tid,))
        if exists[0][0] > 0:
            messagebox.showerror("שגיאה", "מזהה סוג זה כבר קיים במערכת!")
            return
            
        try:
            db.execute_query(
                "INSERT INTO roomtype (roomtypeid, typename, baseprice, description, bedtype) VALUES (%s, %s, %s, %s, %s);",
                (tid, name, price, desc if desc else None, bed if bed else None)
            )
            messagebox.showinfo("הצלחה", "סוג החדר נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None:
            messagebox.showwarning("עדכון", "אנא טען רשומה תחילה!")
            return
        data = self.validate_inputs()
        if not data:
            return
        tid, name, price, desc, bed = data
        
        if tid != self.selected_pk:
            exists = db.fetch_query("SELECT COUNT(*) FROM roomtype WHERE roomtypeid = %s;", (tid,))
            if exists[0][0] > 0:
                messagebox.showerror("שגיאה", "מזהה סוג החדש כבר תפוס!")
                return

        try:
            db.execute_query(
                "UPDATE roomtype SET roomtypeid=%s, typename=%s, baseprice=%s, description=%s, bedtype=%s WHERE roomtypeid=%s;",
                (tid, name, price, desc if desc else None, bed if bed else None, self.selected_pk)
            )
            messagebox.showinfo("הצלחה", "סוג החדר עודכן בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בעדכון", str(e))

    def delete_record(self):
        if self.selected_pk is None:
            manual_id = self.ent_id.get().strip()
            if not manual_id:
                messagebox.showwarning("מחיקה", "אנא בחר שורה למחיקה.")
                return
            try:
                self.selected_pk = int(manual_id)
            except ValueError:
                return

        confirm = messagebox.askyesno("אישור", "האם למחוק סוג חדר זה?")
        if not confirm:
            return
        try:
            db.execute_query("DELETE FROM roomtype WHERE roomtypeid = %s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "הרשומה נמחקה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", f"לא ניתן למחוק (ייתכן ויש חדרים המשויכים לסוג זה):\n{e}")

# =======================================================================
# 3. מסך ניהול סטטוסים (RoomStatus CRUD)
# =======================================================================
class RoomStatusWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול סטטוסים - Room Statuses", "800x500")
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("statusid", "statusname")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("statusid", text="מזהה סטטוס (ID)")
        self.tree.heading("statusname", text="שם הסטטוס")
        
        self.tree.column("statusid", width=150, anchor="center")
        self.tree.column("statusname", width=300, anchor="e")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי הסטטוס", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה סטטוס:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="שם הסטטוס:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = db.fetch_query("SELECT statusid, statusname FROM roomstatus ORDER BY statusid;")
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        next_id = suggest_next_id("roomstatus", "statusid")
        self.ent_id.insert(0, str(next_id))
        self.ent_name.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT statusid, statusname FROM roomstatus WHERE statusid=%s;", (int(manual_id),))
                if row:
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(row[0][0]))
                    self.ent_name.insert(0, row[0][1])
                    self.selected_pk = row[0][0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return
                
        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_name.insert(0, item[1])
        self.selected_pk = int(item[0])

    def add_record(self):
        try:
            sid = int(self.ent_id.get().strip())
            name = self.ent_name.get().strip()
            if not name:
                messagebox.showerror("שגיאה", "נא להזין שם סטטוס!")
                return
            db.execute_query("INSERT INTO roomstatus (statusid, statusname) VALUES (%s, %s);", (sid, name))
            messagebox.showinfo("הצלחה", "סטטוס נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        try:
            sid = int(self.ent_id.get().strip())
            name = self.ent_name.get().strip()
            if not name: return
            db.execute_query("UPDATE roomstatus SET statusid=%s, statusname=%s WHERE statusid=%s;", (sid, name, self.selected_pk))
            messagebox.showinfo("הצלחה", "סטטוס עודכן!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק סטטוס זה?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM roomstatus WHERE statusid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "נמחק!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", f"לא ניתן למחוק סטטוס בשימוש:\n{e}")

# =======================================================================
# 4. מסך ניהול מתקנים (Amenity CRUD)
# =======================================================================
class AmenityWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול מתקנים - Amenities", "850x550")
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("amenityid", "amenityname", "amenitycategory")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("amenityid", text="מזהה מתקן (ID)")
        self.tree.heading("amenityname", text="שם המתקן")
        self.tree.heading("amenitycategory", text="קטגוריה")
        
        self.tree.column("amenityid", width=100, anchor="center")
        self.tree.column("amenityname", width=250, anchor="e")
        self.tree.column("amenitycategory", width=200, anchor="e")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי המתקן", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה מתקן:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="שם המתקן:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="קטגוריה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.ent_cat = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_cat.grid(row=0, column=5, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = db.fetch_query("SELECT amenityid, amenityname, amenitycategory FROM amenity ORDER BY amenityid;")
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        next_id = suggest_next_id("amenity", "amenityid")
        self.ent_id.insert(0, str(next_id))
        self.ent_name.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT amenityid, amenityname, amenitycategory FROM amenity WHERE amenityid=%s;", (int(manual_id),))
                if row:
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(row[0][0]))
                    self.ent_name.insert(0, row[0][1])
                    self.ent_cat.insert(0, row[0][2] or "")
                    self.selected_pk = row[0][0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return
                
        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_name.insert(0, item[1])
        self.ent_cat.insert(0, item[2] if item[2] != "None" else "")
        self.selected_pk = int(item[0])

    def add_record(self):
        try:
            aid = int(self.ent_id.get().strip())
            name = self.ent_name.get().strip()
            cat = self.ent_cat.get().strip()
            if not name:
                messagebox.showerror("שגיאה", "נא להזין שם מתקן!")
                return
            db.execute_query("INSERT INTO amenity (amenityid, amenityname, amenitycategory) VALUES (%s, %s, %s);", (aid, name, cat if cat else None))
            messagebox.showinfo("הצלחה", "מתקן נוסף!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        try:
            aid = int(self.ent_id.get().strip())
            name = self.ent_name.get().strip()
            cat = self.ent_cat.get().strip()
            if not name: return
            db.execute_query("UPDATE amenity SET amenityid=%s, amenityname=%s, amenitycategory=%s WHERE amenityid=%s;", (aid, name, cat if cat else None, self.selected_pk))
            messagebox.showinfo("הצלחה", "מתקן עודכן!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק מתקן זה?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM amenity WHERE amenityid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "נמחק!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", f"לא ניתן למחוק (ייתכן ומשויך לחדרים):\n{e}")

# =======================================================================
# 5. מסך ניהול תחזוקה (RoomMaintenance CRUD)
# =======================================================================
class RoomMaintenanceWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול תחזוקה - Room Maintenance", "1050x650")
        self.load_fk_mappings()
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def load_fk_mappings(self):
        try:
            # חדרים: נמפה מספר חדר למזהה פנימי
            rooms = db.fetch_query("SELECT roomid, roomnumber FROM room ORDER BY roomnumber;")
            self.room_number_to_id = {str(row[1]): row[0] for row in rooms}
            self.room_id_to_number = {row[0]: str(row[1]) for row in rooms}
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת חדרים:\n{e}")

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("maintenanceid", "roomnumber", "startdate", "enddate", "repaircost", "maintenancestatus", "description")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        self.tree.heading("maintenanceid", text="מזהה תחזוקה (ID)")
        self.tree.heading("roomnumber", text="מספר חדר")
        self.tree.heading("startdate", text="תאריך התחלה")
        self.tree.heading("enddate", text="תאריך סיום")
        self.tree.heading("repaircost", text="עלות תיקון")
        self.tree.heading("maintenancestatus", text="סטטוס תחזוקה")
        self.tree.heading("description", text="תיאור תקלה")
        
        self.tree.column("maintenanceid", width=120, anchor="center")
        self.tree.column("roomnumber", width=100, anchor="center")
        self.tree.column("startdate", width=120, anchor="center")
        self.tree.column("enddate", width=120, anchor="center")
        self.tree.column("repaircost", width=100, anchor="center")
        self.tree.column("maintenancestatus", width=130, anchor="center")
        self.tree.column("description", width=250, anchor="e")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי קריאת התחזוקה", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה קריאה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="מספר חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.cmb_room = ttk.Combobox(form_frame, values=list(self.room_number_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_room.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="סטטוס תחזוקה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.cmb_status = ttk.Combobox(form_frame, values=['Reported', 'In Progress', 'Fixed', 'Verified'], state="readonly", font=FONT_ENTRY)
        self.cmb_status.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="תאריך התחלה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_start = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_start.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="(YYYY-MM-DD)", font=FONT_ENTRY, fg="gray", bg=COLOR_WHITE).grid(row=1, column=1, sticky="e", padx=5)

        tk.Label(form_frame, text="תאריך סיום:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_end = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_end.grid(row=1, column=3, padx=5, pady=5)
        tk.Label(form_frame, text="(YYYY-MM-DD)", font=FONT_ENTRY, fg="gray", bg=COLOR_WHITE).grid(row=1, column=3, sticky="e", padx=5)

        tk.Label(form_frame, text="עלות תיקון:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=4, sticky="w", padx=5, pady=5)
        self.ent_cost = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_cost.grid(row=1, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="תיאור התקלה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ent_desc = tk.Entry(form_frame, font=FONT_ENTRY, width=70)
        self.ent_desc.grid(row=2, column=1, columnspan=5, sticky="we", padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        query = """
            SELECT m.maintenanceid, r.roomnumber, m.startdate, m.enddate, m.repaircost, m.maintenancestatus, m.description
            FROM roommaintenance m
            LEFT JOIN room r ON m.roomid = r.roomid
            ORDER BY m.maintenanceid DESC;
        """
        try:
            rows = db.fetch_query(query)
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        next_id = suggest_next_id("roommaintenance", "maintenanceid")
        self.ent_id.insert(0, str(next_id))
        
        self.cmb_room.set("")
        self.cmb_status.set("Reported")
        self.ent_start.delete(0, tk.END)
        # הכנסת תאריך היום כברירת מחדל
        import datetime
        self.ent_start.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        self.ent_end.delete(0, tk.END)
        self.ent_cost.delete(0, tk.END)
        self.ent_cost.insert(0, "0.00")
        self.ent_desc.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT maintenanceid, roomid, startdate, enddate, repaircost, maintenancestatus, description FROM roommaintenance WHERE maintenanceid=%s;", (int(manual_id),))
                if row:
                    r = row[0]
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(r[0]))
                    self.cmb_room.set(self.room_id_to_number.get(r[1], ""))
                    self.ent_start.delete(0, tk.END)
                    self.ent_start.insert(0, str(r[2]))
                    self.ent_end.delete(0, tk.END)
                    self.ent_end.insert(0, str(r[3]) if r[3] else "")
                    self.ent_cost.delete(0, tk.END)
                    self.ent_cost.insert(0, str(r[4]))
                    self.cmb_status.set(r[5])
                    self.ent_desc.delete(0, tk.END)
                    self.ent_desc.insert(0, r[6])
                    self.selected_pk = r[0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.cmb_room.set(item[1])
        
        self.ent_start.delete(0, tk.END)
        self.ent_start.insert(0, item[2])
        
        self.ent_end.delete(0, tk.END)
        self.ent_end.insert(0, item[3] if item[3] != "None" else "")
        
        self.ent_cost.delete(0, tk.END)
        self.ent_cost.insert(0, item[4])
        
        self.cmb_status.set(item[5])
        
        self.ent_desc.delete(0, tk.END)
        self.ent_desc.insert(0, item[6])
        
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            mid = int(self.ent_id.get().strip())
            cost = float(self.ent_cost.get().strip())
        except ValueError:
            messagebox.showerror("שגיאה", "מזהה חייב להיות שלם, עלות חייבת להיות מספר.")
            return None
            
        rnum = self.cmb_room.get()
        status = self.cmb_status.get()
        start = self.ent_start.get().strip()
        end = self.ent_end.get().strip()
        desc = self.ent_desc.get().strip()
        
        if not rnum or not status or not start or not desc:
            messagebox.showerror("שגיאה", "שדות חדר, סטטוס, תאריך התחלה ותיאור הם חובה!")
            return None
            
        room_id = self.room_number_to_id[rnum]
        return mid, room_id, start, end if end else None, cost, status, desc

    def add_record(self):
        data = self.validate_inputs()
        if not data: return
        mid, room_id, start, end, cost, status, desc = data
        
        try:
            db.execute_query(
                "INSERT INTO roommaintenance (maintenanceid, roomid, startdate, enddate, repaircost, maintenancestatus, description) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (mid, room_id, start, end, cost, status, desc)
            )
            messagebox.showinfo("הצלחה", "קריאת התחזוקה נפתחה בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        data = self.validate_inputs()
        if not data: return
        mid, room_id, start, end, cost, status, desc = data
        
        try:
            db.execute_query(
                """UPDATE roommaintenance 
                   SET maintenanceid=%s, roomid=%s, startdate=%s, enddate=%s, repaircost=%s, maintenancestatus=%s, description=%s
                   WHERE maintenanceid=%s;""",
                (mid, room_id, start, end, cost, status, desc, self.selected_pk)
            )
            messagebox.showinfo("הצלחה", "קריאת התחזוקה עודכנה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בעדכון", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק קריאת תחזוקה זו?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM roommaintenance WHERE maintenanceid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "קריאת התחזוקה נמחקה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", str(e))

# =======================================================================
# 6. מסך ניהול עונות (Season CRUD)
# =======================================================================
class SeasonWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול עונות - Seasons", "900x550")
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("seasonid", "seasonname", "startdate", "enddate")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("seasonid", text="מזהה עונה (ID)")
        self.tree.heading("seasonname", text="שם העונה")
        self.tree.heading("startdate", text="תאריך התחלה")
        self.tree.heading("enddate", text="תאריך סיום")
        
        self.tree.column("seasonid", width=100, anchor="center")
        self.tree.column("seasonname", width=250, anchor="e")
        self.tree.column("startdate", width=150, anchor="center")
        self.tree.column("enddate", width=150, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי העונה", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה עונה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="שם העונה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="תאריך התחלה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_start = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_start.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="(YYYY-MM-DD)", font=FONT_ENTRY, fg="gray", bg=COLOR_WHITE).grid(row=1, column=1, sticky="e", padx=5)

        tk.Label(form_frame, text="תאריך סיום:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_end = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_end.grid(row=1, column=3, padx=5, pady=5)
        tk.Label(form_frame, text="(YYYY-MM-DD)", font=FONT_ENTRY, fg="gray", bg=COLOR_WHITE).grid(row=1, column=3, sticky="e", padx=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = db.fetch_query("SELECT seasonid, seasonname, startdate, enddate FROM season ORDER BY seasonid;")
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, str(suggest_next_id("season", "seasonid")))
        self.ent_name.delete(0, tk.END)
        self.ent_start.delete(0, tk.END)
        self.ent_end.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT seasonid, seasonname, startdate, enddate FROM season WHERE seasonid=%s;", (int(manual_id),))
                if row:
                    r = row[0]
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(r[0]))
                    self.ent_name.insert(0, r[1])
                    self.ent_start.insert(0, str(r[2]))
                    self.ent_end.insert(0, str(r[3]))
                    self.selected_pk = r[0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_name.insert(0, item[1])
        self.ent_start.insert(0, item[2])
        self.ent_end.insert(0, item[3])
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            sid = int(self.ent_id.get().strip())
        except ValueError:
            messagebox.showerror("שגיאה", "מזהה חייב להיות מספר שלם!")
            return None
        name = self.ent_name.get().strip()
        start = self.ent_start.get().strip()
        end = self.ent_end.get().strip()
        if not name or not start or not end:
            messagebox.showerror("שגיאה", "כל השדות הם חובה!")
            return None
        return sid, name, start, end

    def add_record(self):
        data = self.validate_inputs()
        if not data: return
        sid, name, start, end = data
        try:
            db.execute_query("INSERT INTO season (seasonid, seasonname, startdate, enddate) VALUES (%s, %s, %s, %s);", (sid, name, start, end))
            messagebox.showinfo("הצלחה", "העונה נוספה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        data = self.validate_inputs()
        if not data: return
        sid, name, start, end = data
        try:
            db.execute_query("UPDATE season SET seasonid=%s, seasonname=%s, startdate=%s, enddate=%s WHERE seasonid=%s;", (sid, name, start, end, self.selected_pk))
            messagebox.showinfo("הצלחה", "העונה עודכנה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק עונה זו?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM season WHERE seasonid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "העונה נמחקה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", f"לא ניתן למחוק עונה (ייתכן ויש תעריפים המשויכים אליה):\n{e}")

# =======================================================================
# 7. מסך ניהול מבצעים (SpecialOffer CRUD)
# =======================================================================
class SpecialOfferWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול מבצעים - Special Offers", "850x500")
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("offerid", "offername", "discountpercentage")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("offerid", text="מזהה מבצע (ID)")
        self.tree.heading("offername", text="שם המבצע")
        self.tree.heading("discountpercentage", text="אחוז הנחה")
        
        self.tree.column("offerid", width=100, anchor="center")
        self.tree.column("offername", width=250, anchor="e")
        self.tree.column("discountpercentage", width=150, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי המבצע", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה מבצע:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="שם המבצע:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.ent_name = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="אחוז הנחה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.ent_disc = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_disc.grid(row=0, column=5, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = db.fetch_query("SELECT offerid, offername, discountpercentage FROM specialoffer ORDER BY offerid;")
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, str(suggest_next_id("specialoffer", "offerid")))
        self.ent_name.delete(0, tk.END)
        self.ent_disc.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT offerid, offername, discountpercentage FROM specialoffer WHERE offerid=%s;", (int(manual_id),))
                if row:
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(row[0][0]))
                    self.ent_name.insert(0, row[0][1])
                    self.ent_disc.insert(0, str(row[0][2]))
                    self.selected_pk = row[0][0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.ent_name.insert(0, item[1])
        self.ent_disc.insert(0, item[2])
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            oid = int(self.ent_id.get().strip())
            disc = float(self.ent_disc.get().strip())
            if not (0 <= disc <= 100):
                messagebox.showerror("שגיאה", "אחוז הנחה חייב להיות בין 0 ל-100!")
                return None
        except ValueError:
            messagebox.showerror("שגיאה", "מזהה חייב להיות מספר שלם, הנחה חייבת להיות מספר.")
            return None
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showerror("שגיאה", "שם מבצע הוא שדה חובה!")
            return None
        return oid, name, disc

    def add_record(self):
        data = self.validate_inputs()
        if not data: return
        oid, name, disc = data
        try:
            db.execute_query("INSERT INTO specialoffer (offerid, offername, discountpercentage) VALUES (%s, %s, %s);", (oid, name, disc))
            messagebox.showinfo("הצלחה", "המבצע נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        data = self.validate_inputs()
        if not data: return
        oid, name, disc = data
        try:
            db.execute_query("UPDATE specialoffer SET offerid=%s, offername=%s, discountpercentage=%s WHERE offerid=%s;", (oid, name, disc, self.selected_pk))
            messagebox.showinfo("הצלחה", "המבצע עודכן!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק מבצע זה?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM specialoffer WHERE offerid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "המבצע נמחק!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", f"לא ניתן למחוק (ייתכן ומשויך לתעריפים):\n{e}")

# =======================================================================
# 8. מסך ניהול תעריפים (PriceRate CRUD)
# =======================================================================
class PriceRateWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "ניהול תעריפים - Price Rates", "1000x600")
        self.load_fk_mappings()
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def load_fk_mappings(self):
        try:
            # עונות
            seasons = db.fetch_query("SELECT seasonid, seasonname FROM season;")
            self.season_name_to_id = {row[1]: row[0] for row in seasons}
            self.season_id_to_name = {row[0]: row[1] for row in seasons}

            # מבצעים (יכול להיות NULL)
            offers = db.fetch_query("SELECT offerid, offername FROM specialoffer;")
            self.offer_name_to_id = {row[1]: row[0] for row in offers}
            self.offer_id_to_name = {row[0]: row[1] for row in offers}
            self.offer_name_to_id["ללא מבצע"] = None
            
            # סוגי חדרים
            types = db.fetch_query("SELECT roomtypeid, typename FROM roomtype;")
            self.type_name_to_id = {row[1]: row[0] for row in types}
            self.type_id_to_name = {row[0]: row[1] for row in types}
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת מפתחות זרים:\n{e}")

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("rateid", "seasonname", "offername", "typename", "finalprice")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        self.tree.heading("rateid", text="מזהה תעריף (ID)")
        self.tree.heading("seasonname", text="עונה")
        self.tree.heading("offername", text="מבצע")
        self.tree.heading("typename", text="סוג חדר")
        self.tree.heading("finalprice", text="מחיר סופי")
        
        self.tree.column("rateid", width=100, anchor="center")
        self.tree.column("seasonname", width=200, anchor="e")
        self.tree.column("offername", width=200, anchor="e")
        self.tree.column("typename", width=200, anchor="e")
        self.tree.column("finalprice", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי התעריף", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="מזהה תעריף:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_id = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_id.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="עונה:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.cmb_season = ttk.Combobox(form_frame, values=list(self.season_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_season.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="מבצע:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.cmb_offer = ttk.Combobox(form_frame, values=list(self.offer_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_offer.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="סוג חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.cmb_type = ttk.Combobox(form_frame, values=list(self.type_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_type.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="מחיר סופי:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_price = tk.Entry(form_frame, font=FONT_ENTRY)
        self.ent_price.grid(row=1, column=3, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        query = """
            SELECT p.rateid, s.seasonname, o.offername, t.typename, p.finalprice
            FROM pricerate p
            LEFT JOIN season s ON p.seasonid = s.seasonid
            LEFT JOIN specialoffer o ON p.offerid = o.offerid
            LEFT JOIN roomtype t ON p.roomtypeid = t.roomtypeid
            ORDER BY p.rateid;
        """
        try:
            rows = db.fetch_query(query)
            for row in rows:
                # טיפול במקרה של מבצע שהוא NULL
                r = list(row)
                if r[2] is None:
                    r[2] = "ללא מבצע"
                self.tree.insert("", "end", values=r)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה בשליפה", str(e))

    def clear_fields(self):
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, str(suggest_next_id("pricerate", "rateid")))
        self.cmb_season.set("")
        self.cmb_offer.set("ללא מבצע")
        self.cmb_type.set("")
        self.ent_price.delete(0, tk.END)
        self.selected_pk = None

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            manual_id = self.ent_id.get().strip()
            if not manual_id: return
            try:
                row = db.fetch_query("SELECT rateid, seasonid, offerid, roomtypeid, finalprice FROM pricerate WHERE rateid=%s;", (int(manual_id),))
                if row:
                    r = row[0]
                    self.clear_fields()
                    self.ent_id.delete(0, tk.END)
                    self.ent_id.insert(0, str(r[0]))
                    self.cmb_season.set(self.season_id_to_name.get(r[1], ""))
                    self.cmb_offer.set(self.offer_id_to_name.get(r[2], "ללא מבצע"))
                    self.cmb_type.set(self.type_id_to_name.get(r[3], ""))
                    self.ent_price.insert(0, str(r[4]))
                    self.selected_pk = r[0]
                return
            except Exception as e:
                messagebox.showerror("שגיאה", str(e))
                return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.ent_id.delete(0, tk.END)
        self.ent_id.insert(0, item[0])
        self.cmb_season.set(item[1])
        self.cmb_offer.set(item[2])
        self.cmb_type.set(item[3])
        self.ent_price.insert(0, item[4])
        self.selected_pk = int(item[0])

    def validate_inputs(self):
        try:
            rid = int(self.ent_id.get().strip())
            price = float(self.ent_price.get().strip())
        except ValueError:
            messagebox.showerror("שגיאה", "מזהה חייב להיות שלם, מחיר חייב להיות מספר.")
            return None
            
        sname = self.cmb_season.get()
        oname = self.cmb_offer.get()
        tname = self.cmb_type.get()
        
        if not sname or not tname:
            messagebox.showerror("שגיאה", "עונה וסוג חדר הם שדות חובה!")
            return None
            
        season_id = self.season_name_to_id[sname]
        offer_id = self.offer_name_to_id[oname]
        type_id = self.type_name_to_id[tname]
        
        return rid, season_id, offer_id, type_id, price

    def add_record(self):
        data = self.validate_inputs()
        if not data: return
        rid, season_id, offer_id, type_id, price = data
        try:
            db.execute_query(
                "INSERT INTO pricerate (rateid, seasonid, offerid, roomtypeid, finalprice) VALUES (%s, %s, %s, %s, %s);",
                (rid, season_id, offer_id, type_id, price)
            )
            messagebox.showinfo("הצלחה", "התעריף נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def update_record(self):
        if self.selected_pk is None: return
        data = self.validate_inputs()
        if not data: return
        rid, season_id, offer_id, type_id, price = data
        try:
            db.execute_query(
                """UPDATE pricerate 
                   SET rateid=%s, seasonid=%s, offerid=%s, roomtypeid=%s, finalprice=%s 
                   WHERE rateid=%s;""",
                (rid, season_id, offer_id, type_id, price, self.selected_pk)
            )
            messagebox.showinfo("הצלחה", "התעריף עודכן!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def delete_record(self):
        if self.selected_pk is None: return
        confirm = messagebox.askyesno("אישור", "האם למחוק תעריף זה?")
        if not confirm: return
        try:
            db.execute_query("DELETE FROM pricerate WHERE rateid=%s;", (self.selected_pk,))
            messagebox.showinfo("הצלחה", "התעריף נמחק!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", str(e))

# =======================================================================
# 9. מסך קישור חדרים למתקנים (RoomAmenity CRUD)
# =======================================================================
class RoomAmenityWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "קישור חדרים למתקנים - Room Amenities", "900x550")
        self.load_fk_mappings()
        self.create_treeview()
        self.create_form()
        self.refresh_table()

    def load_fk_mappings(self):
        try:
            # חדרים
            rooms = db.fetch_query("SELECT roomid, roomnumber FROM room ORDER BY roomnumber;")
            self.room_number_to_id = {str(row[1]): row[0] for row in rooms}
            self.room_id_to_number = {row[0]: str(row[1]) for row in rooms}
            
            # מתקנים
            amenities = db.fetch_query("SELECT amenityid, amenityname FROM amenity ORDER BY amenityname;")
            self.amenity_name_to_id = {row[1]: row[0] for row in amenities}
            self.amenity_id_to_name = {row[0]: row[1] for row in amenities}
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת חדרים ומתקנים:\n{e}")

    def create_treeview(self):
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("roomnumber", "amenityname")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("roomnumber", text="מספר חדר")
        self.tree.heading("amenityname", text="שם המתקן")
        
        self.tree.column("roomnumber", width=200, anchor="center")
        self.tree.column("amenityname", width=350, anchor="e")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.load_selected())

    def create_form(self):
        form_frame = tk.LabelFrame(self, text="פרטי הקישור", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=15, pady=10)
        form_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(form_frame, text="בחר חדר:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.cmb_room = ttk.Combobox(form_frame, values=list(self.room_number_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_room.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="בחר מתקן:", font=FONT_LABEL, bg=COLOR_WHITE).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.cmb_amenity = ttk.Combobox(form_frame, values=list(self.amenity_name_to_id.keys()), state="readonly", font=FONT_ENTRY)
        self.cmb_amenity.grid(row=0, column=3, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Button(btn_frame, text="הוספה (Create)", bg=COLOR_SECONDARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.add_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="טען רשומה נבחרת", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=18, command=self.load_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="עדכון (Update)", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.update_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="מחיקה (Delete)", bg=COLOR_DANGER, fg=COLOR_WHITE, font=FONT_BUTTON, width=15, command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btn_frame, text="נקה שדות", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=12, command=self.clear_fields).pack(side="left", padx=5)
        tk.Button(btn_frame, text="רענן", bg=COLOR_WHITE, fg=COLOR_PRIMARY, font=FONT_BUTTON, width=10, command=self.refresh_table).pack(side="right", padx=5)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        query = """
            SELECT r.roomnumber, a.amenityname
            FROM roomamenity ra
            LEFT JOIN room r ON ra.roomid = r.roomid
            LEFT JOIN amenity a ON ra.amenityid = a.amenityid
            ORDER BY r.roomnumber, a.amenityname;
        """
        try:
            rows = db.fetch_query(query)
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    def clear_fields(self):
        self.cmb_room.set("")
        self.cmb_amenity.set("")
        self.selected_pk = None  # במקרה של מפתח מורכב נשמור אותו כטאפל (room_id, amenity_id)

    def load_selected(self):
        selected = self.tree.selection()
        if not selected:
            # במפתח מורכב עדיף לבחור מהטבלה בלבד
            messagebox.showwarning("טעינה", "אנא בחר שורה בטבלה לטעינת הקישור.")
            return

        item = self.tree.item(selected[0], "values")
        self.clear_fields()
        self.cmb_room.set(item[0])
        self.cmb_amenity.set(item[1])
        
        rid = self.room_number_to_id.get(item[0])
        aid = self.amenity_name_to_id.get(item[1])
        self.selected_pk = (rid, aid)

    def validate_inputs(self):
        rnum = self.cmb_room.get()
        aname = self.cmb_amenity.get()
        if not rnum or not aname:
            messagebox.showerror("שגיאה", "אנא בחר חדר ומתקן!")
            return None
        rid = self.room_number_to_id[rnum]
        aid = self.amenity_name_to_id[aname]
        return rid, aid

    def add_record(self):
        data = self.validate_inputs()
        if not data: return
        rid, aid = data
        
        # בדיקת כפילות
        exists = db.fetch_query("SELECT COUNT(*) FROM roomamenity WHERE roomid=%s AND amenityid=%s;", (rid, aid))
        if exists[0][0] > 0:
            messagebox.showerror("שגיאה", "מתקן זה כבר מקושר לחדר זה!")
            return
            
        try:
            db.execute_query("INSERT INTO roomamenity (roomid, amenityid) VALUES (%s, %s);", (rid, aid))
            messagebox.showinfo("הצלחה", "הקישור נוסף בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בהוספה", str(e))

    def update_record(self):
        if self.selected_pk is None:
            messagebox.showwarning("עדכון", "יש לבצע לחיצה כפולה על שורה בטבלה כדי לטעון רשומה לעדכון!")
            return
        data = self.validate_inputs()
        if not data: return
        new_rid, new_aid = data
        orig_rid, orig_aid = self.selected_pk
        
        # אם יש שינוי, נוודא שהקומבינציה החדשה לא קיימת כבר
        if (new_rid, new_aid) != (orig_rid, orig_aid):
            exists = db.fetch_query("SELECT COUNT(*) FROM roomamenity WHERE roomid=%s AND amenityid=%s;", (new_rid, new_aid))
            if exists[0][0] > 0:
                messagebox.showerror("שגיאה", "הקומבינציה החדשה כבר קיימת במערכת!")
                return
                
        try:
            db.execute_query(
                "UPDATE roomamenity SET roomid=%s, amenityid=%s WHERE roomid=%s AND amenityid=%s;",
                (new_rid, new_aid, orig_rid, orig_aid)
            )
            messagebox.showinfo("הצלחה", "הקישור עודכן בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה בעדכון", str(e))

    def delete_record(self):
        if self.selected_pk is None:
            # אם לא טעון, נסה לקחת מהקומבו הנוכחי
            data = self.validate_inputs()
            if not data: return
            self.selected_pk = data

        confirm = messagebox.askyesno("אישור", "האם למחוק קישור זה?")
        if not confirm: return
        rid, aid = self.selected_pk
        try:
            db.execute_query("DELETE FROM roomamenity WHERE roomid=%s AND amenityid=%s;", (rid, aid))
            messagebox.showinfo("הצלחה", "הקישור נמחק בהצלחה!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("שגיאה במחיקה", str(e))

# =======================================================================
# 10. מסך דוחות, שאילתות ופונקציות (Reports, Queries, Functions)
# =======================================================================
class ReportsWindow(BaseManagementWindow):
    def __init__(self, parent):
        super().__init__(parent, "דוחות, שאילתות ופונקציות - Analytics", "1100x650")
        self.create_tabs()
        
    def create_tabs(self):
        # יצירת כרטיסיות
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # כרטיסיה 1: שאילתות ודוחות (Selects)
        self.tab_queries = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_queries, text="שאילתות ודוחות (שלב ב׳)")
        self.setup_queries_tab()
        
        # כרטיסיה 2: פונקציות ופרוצדורות (Stored Programs)
        self.tab_stored = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_stored, text="פונקציות ופרוצדורות (שלב ד׳)")
        self.setup_stored_tab()

    # --- כרטיסיית שאילתות ---
    def setup_queries_tab(self):
        # כפתורי הפעלה
        ctrl_frame = tk.Frame(self.tab_queries, bg=COLOR_BG)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(ctrl_frame, text="בחר שאילתה להרצה:", font=FONT_SUBTITLE, bg=COLOR_BG).pack(side="left", padx=5)
        
        tk.Button(ctrl_frame, text="1. סיכום מצב חדרים ( occupancy )", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.run_query_1).pack(side="left", padx=5)
        tk.Button(ctrl_frame, text="2. חדרים עם 3+ מתקנים", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.run_query_2).pack(side="left", padx=5)
        tk.Button(ctrl_frame, text="3. חדרים שתוקנו וממתינים לאישור", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.run_query_3).pack(side="left", padx=5)
        
        # תצוגת תוצאות (Treeview דינמי)
        self.result_frame = tk.Frame(self.tab_queries, bg=COLOR_BG)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree_res = None
        self.lbl_no_data = tk.Label(self.result_frame, text="אין נתונים להצגה. לחצי על אחד הלחצנים למעלה.", font=FONT_SUBTITLE, bg=COLOR_BG)
        self.lbl_no_data.pack(expand=True)

    def display_query_results(self, cols, rows, hebrew_headings=None):
        # ניקוי המנהל הקודם
        if self.tree_res:
            self.tree_res.destroy()
        self.lbl_no_data.pack_forget()
        
        # יצירת Treeview חדש לפי השאילתה
        self.tree_res = ttk.Treeview(self.result_frame, columns=cols, show="headings")
        
        # כותרות
        for i, col in enumerate(cols):
            heading_text = hebrew_headings[i] if (hebrew_headings and i < len(hebrew_headings)) else col
            self.tree_res.heading(col, text=heading_text)
            self.tree_res.column(col, width=150, anchor="center")
            
        scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.tree_res.yview)
        self.tree_res.configure(yscrollcommand=scrollbar.set)
        
        self.tree_res.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # הוספת הנתונים
        for row in rows:
            self.tree_res.insert("", "end", values=row)

    def run_query_1(self):
        # שאילתה 1: סיכום מצב חדרים
        q = """
            SELECT 
                RS.StatusName, 
                COUNT(R.RoomID) AS Total_Rooms,
                SUM(COALESCE(R.MaxOccupancy, 0)) AS Potential_Guests
            FROM ROOMSTATUS RS
            LEFT JOIN ROOM R ON RS.StatusID = R.StatusID
            GROUP BY RS.StatusName
            ORDER BY Total_Rooms DESC;
        """
        try:
            cols, rows = db.fetch_columns(q)
            heb = ["שם הסטטוס", "סה\"כ חדרים במערכת", "תפוסת אורחים פוטנציאלית"]
            self.display_query_results(cols, rows, heb)
        except Exception as e:
            messagebox.showerror("שגיאה בהרצת השאילתה", str(e))

    def run_query_2(self):
        # שאילתה 2: חדרים שיש בהם 3 מתקנים או יותר
        q = """
            SELECT 
                R.RoomNumber, 
                R.Floor, 
                COUNT(RA.AmenityID) AS Total_Amenities
            FROM ROOM R
            JOIN ROOMAMENITY RA ON R.RoomID = RA.RoomID
            GROUP BY R.RoomNumber, R.Floor
            HAVING COUNT(RA.AmenityID) >= 3
            ORDER BY Total_Amenities DESC, R.RoomNumber
            LIMIT 100;
        """
        try:
            cols, rows = db.fetch_columns(q)
            heb = ["מספר חדר", "קומה", "סה\"כ מתקנים בחדר"]
            self.display_query_results(cols, rows, heb)
        except Exception as e:
            messagebox.showerror("שגיאה בהרצת השאילתה", str(e))

    def run_query_3(self):
        # שאילתה 3: חדרים שתוקנו וממתינים לאישור (מצב Fixed)
        q = """
            SELECT 
                R.RoomNumber, 
                RM.StartDate, 
                RM.EndDate, 
                RM.RepairCost, 
                RM.Description
            FROM ROOMMAINTENANCE RM
            JOIN ROOM R ON RM.RoomID = R.RoomID
            WHERE RM.MaintenanceStatus = 'Fixed'
            ORDER BY RM.EndDate DESC;
        """
        try:
            cols, rows = db.fetch_columns(q)
            heb = ["מספר חדר", "תאריך התחלה", "תאריך סיום התיקון", "עלות התיקון", "תיאור תקלה"]
            self.display_query_results(cols, rows, heb)
        except Exception as e:
            messagebox.showerror("שגיאה בהרצת השאילתה", str(e))

    # --- כרטיסיית פונקציות ופרוצדורות ---
    def setup_stored_tab(self):
        # חלוקה ל-3 חלקים עיקריים במסך
        self.tab_stored.grid_columnconfigure(0, weight=1)
        self.tab_stored.grid_columnconfigure(1, weight=1)
        self.tab_stored.grid_columnconfigure(2, weight=1)
        
        # פנל 1: פונקציית עלות תחזוקה
        f_frame = tk.LabelFrame(self.tab_stored, text="פונקציה: עלות תחזוקה כוללת לחדר", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=10, pady=10)
        f_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=15)
        
        tk.Label(f_frame, text="בחר חדר (או הקלד מזהה חדר):", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor="w", pady=5)
        
        # טעינת חדרים
        try:
            rooms = db.fetch_query("SELECT roomid, roomnumber FROM room ORDER BY roomnumber;")
            room_list = [f"{r[1]} (ID: {r[0]})" for r in rooms]
        except:
            room_list = []
            
        self.cmb_f_room = ttk.Combobox(f_frame, values=room_list, font=FONT_ENTRY)
        self.cmb_f_room.pack(fill="x", pady=5)
        
        tk.Button(f_frame, text="חשב עלות תחזוקה", font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, command=self.run_function_maint).pack(fill="x", pady=15)
        
        self.lbl_f_res = tk.Label(f_frame, text="עלות כוללת: - ", font=FONT_SUBTITLE, bg=COLOR_WHITE, fg=COLOR_PRIMARY)
        self.lbl_f_res.pack(anchor="w", pady=10)

        # פנל 2: פרוצדורה לעדכון סטטוס חדר
        p1_frame = tk.LabelFrame(self.tab_stored, text="פרוצדורה: Update_Room_Status", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=10, pady=10)
        p1_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=15)
        
        tk.Label(p1_frame, text="בחר מספר חדר:", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor="w", pady=5)
        
        try:
            room_nums = [str(r[1]) for r in rooms]
        except:
            room_nums = []
            
        self.cmb_p1_room = ttk.Combobox(p1_frame, values=room_nums, state="readonly", font=FONT_ENTRY)
        self.cmb_p1_room.pack(fill="x", pady=5)
        
        tk.Label(p1_frame, text="בחר סטטוס חדש:", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor="w", pady=5)
        
        try:
            statuses = [s[0] for s in db.fetch_query("SELECT statusname FROM roomstatus ORDER BY statusid;")]
        except:
            statuses = []
            
        self.cmb_p1_status = ttk.Combobox(p1_frame, values=statuses, state="readonly", font=FONT_ENTRY)
        self.cmb_p1_status.pack(fill="x", pady=5)
        
        tk.Button(p1_frame, text="הפעל פרוצדורת עדכון סטטוס", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.run_proc_status).pack(fill="x", pady=15)

        # פנל 3: פרוצדורה להחלת הנחה עונתית
        p2_frame = tk.LabelFrame(self.tab_stored, text="פרוצדורה: Apply_Discount_To_Season", font=FONT_SUBTITLE, bg=COLOR_WHITE, padx=10, pady=10)
        p2_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=15)
        
        tk.Label(p2_frame, text="בחר עונה:", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor="w", pady=5)
        
        try:
            seasons = db.fetch_query("SELECT seasonid, seasonname FROM season;")
            season_list = [f"{s[1]} (ID: {s[0]})" for s in seasons]
        except:
            season_list = []
            
        self.cmb_p2_season = ttk.Combobox(p2_frame, values=season_list, state="readonly", font=FONT_ENTRY)
        self.cmb_p2_season.pack(fill="x", pady=5)
        
        tk.Label(p2_frame, text="הזן אחוז הנחה (0-100):", font=FONT_LABEL, bg=COLOR_WHITE).pack(anchor="w", pady=5)
        self.ent_p2_discount = tk.Entry(p2_frame, font=FONT_ENTRY)
        self.ent_p2_discount.pack(fill="x", pady=5)
        self.ent_p2_discount.insert(0, "10.0")
        
        tk.Button(p2_frame, text="החל הנחה על העונה", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg=COLOR_WHITE, command=self.run_proc_discount).pack(fill="x", pady=15)

    def run_function_maint(self):
        val = self.cmb_f_room.get()
        if not val:
            messagebox.showerror("שגיאה", "אנא בחר או הקלד מזהה חדר!")
            return
            
        # חילוץ מזהה החדר
        try:
            if "ID:" in val:
                room_id = int(val.split("ID:")[1].replace(")", "").strip())
            else:
                room_id = int(val.strip())
        except ValueError:
            messagebox.showerror("שגיאה", "מזהה חדר לא תקין. עליו להיות מספר שלם.")
            return

        try:
            res = db.fetch_query("SELECT Get_Room_Total_Maintenance_Cost(%s);", (room_id,))
            cost = res[0][0]
            if cost is None:
                cost = 0.00
            self.lbl_f_res.configure(text=f"עלות כוללת: {cost:,.2f} ש\"ח")
            messagebox.showinfo("הרצת פונקציה", f"הפונקציה רצה בהצלחה עבור חדר {room_id}.\nעלות התחזוקה שהוחזרה: {cost} ש\"ח")
        except Exception as e:
            messagebox.showerror("שגיאה בהפעלת פונקציה", f"שגיאה בהפעלת Get_Room_Total_Maintenance_Cost:\n{e}")

    def run_proc_status(self):
        rnum_str = self.cmb_p1_room.get()
        status_name = self.cmb_p1_status.get()
        if not rnum_str or not status_name:
            messagebox.showerror("שגיאה", "חובה לבחור מספר חדר וסטטוס חדש!")
            return
            
        try:
            room_number = int(rnum_str)
            # הרצת פרוצדורה בעזרת CALL
            db.execute_query("CALL Update_Room_Status(%s, %s);", (room_number, status_name))
            messagebox.showinfo("הפעלת פרוצדורה", f"הפרוצדורה Update_Room_Status הופעלה בהצלחה!\nחדר {room_number} עודכן לסטטוס {status_name}.")
        except Exception as e:
            messagebox.showerror("שגיאה בהפעלת פרוצדורה", f"שגיאה בהפעלת Update_Room_Status:\n{e}")

    def run_proc_discount(self):
        season_str = self.cmb_p2_season.get()
        disc_str = self.ent_p2_discount.get().strip()
        if not season_str or not disc_str:
            messagebox.showerror("שגיאה", "אנא בחר עונה והזן אחוז הנחה!")
            return
            
        try:
            season_id = int(season_str.split("ID:")[1].replace(")", "").strip())
            discount = float(disc_str)
            if not (0 <= discount <= 100):
                raise ValueError()
        except:
            messagebox.showerror("שגיאה", "אחוז הנחה חייב להיות מספר בין 0 ל-100!")
            return

        try:
            # הרצת פרוצדורה Apply_Discount_To_Season
            db.execute_query("CALL Apply_Discount_To_Season(%s, %s);", (season_id, discount))
            messagebox.showinfo("הפעלת פרוצדורה", f"הפרוצדורה Apply_Discount_To_Season הופעלה בהצלחה!\nהוחלה הנחה בגובה {discount}% על כל התעריפים בעונה ID {season_id}.")
        except Exception as e:
            messagebox.showerror("שגיאה בהפעלת פרוצדורה", f"שגיאה בהפעלת Apply_Discount_To_Season:\n{e}")

# =======================================================================
# מסך הכניסה הראשי - LuxStay OS
# =======================================================================
class MainDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LuxStay OS - Hotel Management System")
        self.geometry("800x600")
        self.configure(bg=COLOR_BG)
        self.center_window()
        
        # יצירת כותרות
        title_frame = tk.Frame(self, bg=COLOR_PRIMARY)
        title_frame.pack(fill="x", side="top")
        
        lbl_title = tk.Label(title_frame, text="LuxStay OS", font=("Segoe UI", 28, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY)
        lbl_title.pack()
        
        lbl_subtitle = tk.Label(title_frame, text="מערכת ניהול בתי מלון - ממשק גרפי (שלב ה׳)", font=FONT_SUBTITLE, fg=COLOR_SECONDARY, bg=COLOR_PRIMARY, pady=5)
        lbl_subtitle.pack()
        
        # יצירת כפתורים לניהול (חלוקה לגריד מסודר)
        btn_container = tk.Frame(self, bg=COLOR_BG)
        btn_container.pack(fill="both", expand=True, padx=40)
        
        btn_container.grid_columnconfigure(0, weight=1)
        btn_container.grid_columnconfigure(1, weight=1)
        
        # רשימת הכפתורים, השמות שלהם והפונקציות לפתיחת חלונות
        modules = [
            ("ניהול חדרים", self.open_rooms),
            ("ניהול סוגי חדרים", self.open_room_types),
            ("ניהול סטטוסים", self.open_statuses),
            ("ניהול מתקנים", self.open_amenities),
            ("ניהול תחזוקה", self.open_maintenance),
            ("ניהול עונות", self.open_seasons),
            ("ניהול מבצעים", self.open_offers),
            ("ניהול תעריפים", self.open_rates),
            ("קישור חדרים למתקנים", self.open_room_amenities),
        ]
        
        # מיקום הכפתורים
        for idx, (label, command) in enumerate(modules):
            row = idx // 2
            col = idx % 2
            btn = tk.Button(
                btn_container, text=label, font=FONT_SUBTITLE, bg=COLOR_WHITE, fg=COLOR_PRIMARY,
                activebackground=COLOR_PRIMARY, activeforeground=COLOR_WHITE, bd=2, relief="groove",
                pady=10, cursor="hand2", command=command
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=15, pady=10)
            
        # שורה מיוחדת לדוחות ושאילתות
        row_reports = (len(modules) + 1) // 2
        btn_reports = tk.Button(
            btn_container, text="📊 דוחות, שאילתות ופונקציות", font=FONT_TITLE, bg=COLOR_SECONDARY, fg=COLOR_WHITE,
            activebackground=COLOR_PRIMARY, activeforeground=COLOR_WHITE, bd=2, relief="groove",
            pady=12, cursor="hand2", command=self.open_reports
        )
        btn_reports.grid(row=row_reports, column=0, columnspan=2, sticky="nsew", padx=15, pady=15)
        
        # כפתור יציאה בתחתית
        bottom_frame = tk.Frame(self, bg=COLOR_BG)
        bottom_frame.pack(fill="x", side="bottom")
        
        tk.Button(
            bottom_frame, text="יציאה מהמערכת", font=FONT_BUTTON, bg=COLOR_DANGER, fg=COLOR_WHITE,
            padx=20, pady=5, command=self.quit_app
        )
        
        # הדפסת הודעת חיבור מוצלחת ראשונית בלוג
        self.verify_db_connection()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def verify_db_connection(self):
        try:
            conn = db.get_connection()
            conn.close()
            print("התחברות ראשונית למסד הנתונים עברה בהצלחה!")
        except Exception as e:
            messagebox.showerror("שגיאת חיבור", f"לא ניתן להתחבר ל-PostgreSQL בכתובת localhost.\nאנא ודאו שהקונטיינר docker רץ.\nשגיאה: {e}")

    # פונקציות לפתיחת החלונות השונים
    def open_rooms(self):
        RoomWindow(self)

    def open_room_types(self):
        RoomTypeWindow(self)

    def open_statuses(self):
        RoomStatusWindow(self)

    def open_amenities(self):
        AmenityWindow(self)

    def open_maintenance(self):
        RoomMaintenanceWindow(self)

    def open_seasons(self):
        SeasonWindow(self)

    def open_offers(self):
        SpecialOfferWindow(self)

    def open_rates(self):
        PriceRateWindow(self)

    def open_room_amenities(self):
        RoomAmenityWindow(self)

    def open_reports(self):
        ReportsWindow(self)

    def quit_app(self):
        if messagebox.askyesno("אישור יציאה", "האם את/ה בטוח/ה שברצונך לצאת מהמערכת?"):
            self.destroy()

# =======================================================================
# הרצה ראשית
# =======================================================================
if __name__ == "__main__":
    app = MainDashboard()
    app.mainloop()
