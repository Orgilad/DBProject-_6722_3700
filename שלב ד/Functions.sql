/* =======================================================================
   קובץ: Functions.sql
   תיאור: יצירת פונקציות מורכבות הכוללות סמנים (Cursors), לולאות וטיפול בשגיאות.
======================================================================= */

-- =======================================================================
-- פונקציה 1: Get_Room_Total_Maintenance_Cost
-- תיאור: הפונקציה מקבלת מזהה חדר (RoomID) ומחשבת את סך כל הוצאות 
-- התחזוקה שהיו עליו אי פעם.
-- דרישות מרצה שיושמו: סמן מפורש (Explicit Cursor), לולאה (LOOP), רשומה (RECORD).
-- =======================================================================

CREATE OR REPLACE FUNCTION Get_Room_Total_Maintenance_Cost(p_room_id INT)
RETURNS NUMERIC AS $$
DECLARE
    total_cost NUMERIC := 0;      -- משתנה לשמירת הסכום הכולל
    maint_record RECORD;          -- משתנה מסוג רשומה שיחזיק כל שורה מהסמן
    
    -- הגדרת סמן מפורש (Explicit Cursor) ששולף את עלויות התיקון לחדר הספציפי
    cur_maintenance CURSOR FOR 
        SELECT RepairCost 
        FROM ROOMMAINTENANCE 
        WHERE RoomID = p_room_id AND RepairCost IS NOT NULL;
BEGIN
    -- פתיחת הסמן
    OPEN cur_maintenance;
    
    -- לולאה שעוברת על כל הרשומות שהסמן מצא
    LOOP
        FETCH cur_maintenance INTO maint_record;
        
        -- תנאי יציאה מהלולאה: כאשר אין יותר רשומות לקרוא
        EXIT WHEN NOT FOUND;
        
        -- הוספת עלות התיקון הנוכחית לסכום הכולל
        total_cost := total_cost + maint_record.RepairCost;
    END LOOP;
    
    -- סגירת הסמן בסיום השימוש
    CLOSE cur_maintenance;
    
    -- החזרת הסכום הכולל
    RETURN total_cost;
END;
$$ LANGUAGE plpgsql;


-- =======================================================================
-- פונקציה 2: Get_Active_Rates_For_RoomType
-- תיאור: הפונקציה מקבלת מזהה סוג חדר (RoomTypeID) ומחזירה מצביע (Cursor) 
-- לטבלה עם כל התעריפים שלו. אם סוג החדר לא קיים במערכת - נזרקת שגיאה!
-- דרישות מרצה שיושמו: חריגה (Exception), סמן מוחזר (Ref Cursor), הסתעפות (IF).
-- =======================================================================

CREATE OR REPLACE FUNCTION Get_Active_Rates_For_RoomType(p_room_type_id INT)
RETURNS refcursor AS $$
DECLARE
    type_exists INT;           -- משתנה לבדיקה אם סוג החדר קיים
    rate_cursor refcursor;     -- הגדרת מצביע (Ref Cursor) שיוחזר למשתמש
BEGIN
    -- בדיקה האם סוג החדר המבוקש קיים בטבלת סוגי החדרים
    SELECT COUNT(*) INTO type_exists 
    FROM ROOMTYPE 
    WHERE RoomTypeID = p_room_type_id;
    
    -- הסתעפות: אם סוג החדר לא קיים, זורקים שגיאה (Exception)
    IF type_exists = 0 THEN
        RAISE EXCEPTION 'שגיאה: סוג חדר עם מזהה % לא קיים במערכת LuxStay!', p_room_type_id;
    END IF;
    
    -- אם סוג החדר קיים, פותחים את הסמן ומכניסים אליו את השאילתה המורכבת
    OPEN rate_cursor FOR
        SELECT pr.RateID, pr.FinalPrice, s.SeasonName, so.OfferName
        FROM PRICERATE pr
        JOIN SEASON s ON pr.SeasonID = s.SeasonID
        JOIN SPECIALOFFER so ON pr.OfferID = so.OfferID
        WHERE pr.RoomTypeID = p_room_type_id;
        
    -- מחזירים את הסמן עם התוצאות
    RETURN rate_cursor;
END;
$$ LANGUAGE plpgsql;