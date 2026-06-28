/* =======================================================================
   קובץ: Triggers.sql
   תיאור: יצירת טריגרים לאכיפת לוגיקה עסקית ואוטומציה.
======================================================================= */

-- =======================================================================
-- טריגר 1: trg_Auto_Available_Room (מופעל אחרי UPDATE)
-- תיאור: כאשר קריאת תחזוקה מסתיימת (MaintenanceStatus משתנה ל-'Fixed'),
-- הטריגר מעדכן אוטומטית את החדר בחזרה לסטטוס 1 ('Available').
-- =======================================================================

-- שלב א': יצירת הפונקציה של הטריגר
CREATE OR REPLACE FUNCTION set_room_available()
RETURNS TRIGGER AS $$
BEGIN
    -- נבדוק אם הסטטוס החדש הוא 'Fixed' והסטטוס הישן לא היה כזה
    IF NEW.MaintenanceStatus = 'Fixed' AND OLD.MaintenanceStatus <> 'Fixed' THEN
        -- עדכון סטטוס החדר בחזרה ל-1 (פנוי)
        UPDATE ROOM
        SET StatusID = 1
        WHERE RoomID = NEW.RoomID;
        
        RAISE NOTICE 'טריגר אוטומטי פעל: חדר % חזר לסטטוס פנוי לאחר שהתיקון הסתיים.', NEW.RoomID;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- שלב ב': חיבור הטריגר לטבלה
CREATE TRIGGER trg_Auto_Available_Room
AFTER UPDATE ON ROOMMAINTENANCE
FOR EACH ROW
EXECUTE FUNCTION set_room_available();


-- =======================================================================
-- טריגר 2: trg_Check_Valid_Discount (מופעל לפני INSERT או UPDATE)
-- תיאור: מונע הכנסת אחוזי הנחה לא הגיוניים לטבלת המבצעים (קטן מ-0 או גדול מ-100).
-- =======================================================================

-- שלב א': יצירת הפונקציה של הטריגר
CREATE OR REPLACE FUNCTION check_discount_validity()
RETURNS TRIGGER AS $$
BEGIN
    -- בדיקה האם ההנחה מחוץ לטווח הגיוני
    IF NEW.DiscountPercentage < 0 OR NEW.DiscountPercentage > 100 THEN
        RAISE EXCEPTION 'שגיאת טריגר: אחוז הנחה חייב להיות בין 0 ל-100. הערך שהוזן: %', NEW.DiscountPercentage;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- שלב ב': חיבור הטריגר לטבלה
CREATE TRIGGER trg_Check_Valid_Discount
BEFORE INSERT OR UPDATE ON SPECIALOFFER
FOR EACH ROW
EXECUTE FUNCTION check_discount_validity();