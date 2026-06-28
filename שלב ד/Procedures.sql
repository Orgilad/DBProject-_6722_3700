/* =======================================================================
   קובץ: Procedures.sql
   תיאור: יצירת פרוצדורות המבצעות פעולות DML (עדכונים), הסתעפויות ולולאות.
======================================================================= */

-- =======================================================================
-- פרוצדורה 1: Update_Room_Status
-- תיאור: מקבלת מספר חדר (RoomNumber) ושם של סטטוס (StatusName).
-- מוודאת שהסטטוס והחדר קיימים, ומעדכנת את החדר לסטטוס החדש (פעולת DML).
-- דרישות שיושמו: DML (UPDATE), הסתעפויות (IF/ELSE), חריגות (Exception).
-- =======================================================================

CREATE OR REPLACE PROCEDURE Update_Room_Status(p_room_number INT, p_status_name VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_status_id INT;
    v_room_id INT;
BEGIN
    -- 1. מחפשים את מזהה הסטטוס לפי השם שלו
    SELECT StatusID INTO v_status_id 
    FROM ROOMSTATUS 
    WHERE StatusName = p_status_name;

    -- אם הסטטוס לא נמצא במערכת - נזרוק שגיאה
    IF v_status_id IS NULL THEN
        RAISE EXCEPTION 'שגיאה: הסטטוס "%" לא קיים בטבלת ROOMSTATUS.', p_status_name;
    END IF;

    -- 2. מחפשים את המזהה הפנימי של החדר לפי מספר החדר (RoomNumber)
    SELECT RoomID INTO v_room_id 
    FROM ROOM 
    WHERE RoomNumber = p_room_number;

    -- אם החדר לא קיים - נזרוק שגיאה
    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'שגיאה: חדר מספר % לא נמצא במערכת.', p_room_number;
    END IF;

    -- 3. פעולת DML: עדכון סטטוס החדר
    UPDATE ROOM
    SET StatusID = v_status_id
    WHERE RoomID = v_room_id;

    -- הדפסת הודעת הצלחה ללוג
    RAISE NOTICE 'הצלחה: חדר % עודכן לסטטוס %.', p_room_number, p_status_name;
END;
$$;


-- =======================================================================
-- פרוצדורה 2: Apply_Discount_To_Season
-- תיאור: מקבלת מזהה עונה (SeasonID) ואחוז הנחה, ורצה בלולאה על כל 
-- התעריפים של אותה עונה כדי לעדכן ולהוזיל אותם.
-- דרישות שיושמו: סמן מרומז (Implicit Cursor) בתוך לולאת FOR, פעולת DML.
-- =======================================================================

CREATE OR REPLACE PROCEDURE Apply_Discount_To_Season(p_season_id INT, p_discount_percent NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
    v_rate_record RECORD;      -- רשומה עבור הלולאה
    v_season_exists INT;
    v_updated_count INT := 0;  -- מונה לכמות התעריפים שעודכנו
BEGIN
    -- בדיקה האם העונה קיימת בכלל
    SELECT COUNT(*) INTO v_season_exists 
    FROM SEASON 
    WHERE SeasonID = p_season_id;
    
    IF v_season_exists = 0 THEN
        RAISE EXCEPTION 'שגיאה: עונה מספר % לא קיימת במערכת.', p_season_id;
    END IF;

    -- שימוש בסמן מרומז (Implicit Cursor) בתוך לולאת FOR
    FOR v_rate_record IN 
        SELECT RateID, FinalPrice 
        FROM PRICERATE 
        WHERE SeasonID = p_season_id
    LOOP
        -- פעולת DML: עדכון המחיר עבור כל תעריף שנמצא בלולאה
        UPDATE PRICERATE
        SET FinalPrice = FinalPrice - (FinalPrice * (p_discount_percent / 100.0))
        WHERE RateID = v_rate_record.RateID;
        
        -- קידום המונה
        v_updated_count := v_updated_count + 1;
    END LOOP;

    -- הדפסת סיכום הפעולה
    RAISE NOTICE 'הצלחה: הנחה של % אחוזים הוחלה על % תעריפים בעונה %.', p_discount_percent, v_updated_count, p_season_id;
END;
$$;