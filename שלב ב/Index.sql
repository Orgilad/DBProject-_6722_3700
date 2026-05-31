/* =======================================================================
   קובץ: Index.sql
   תיאור: הוספת 3 אינדקסים ובדיקת זמני ריצה (לפני ואחרי)
======================================================================= */

-- ==========================================
-- אינדקס 1: חיפוש מהיר של חדרים לפי קומה
-- ==========================================

-- שלב א: בדיקת זמן ריצה *לפני* האינדקס (לצלם מסך של זמן הריצה execution time)
EXPLAIN ANALYZE 
SELECT * FROM ROOM WHERE Floor = 3;

-- שלב ב: יצירת האינדקס
CREATE INDEX idx_room_floor ON ROOM(Floor);

-- שלב ג: בדיקת זמן ריצה *אחרי* האינדקס (לצלם מסך ולהראות למרצה איך הזמן ירד)
EXPLAIN ANALYZE 
SELECT * FROM ROOM WHERE Floor = 3;


-- ==========================================
-- אינדקס 2: חיפוש מהיר של תיקונים לפי סטטוס
-- ==========================================

-- שלב א: בדיקת זמן ריצה *לפני* (בהנחה שיש סטטוס בשם 'Open' או 'Pending', אם זה מספר שפרי ל-1)
EXPLAIN ANALYZE 
SELECT * FROM ROOMMAINTENANCE WHERE MaintenanceStatus = 'Open';

-- שלב ב: יצירת האינדקס
CREATE INDEX idx_maintenance_status ON ROOMMAINTENANCE(MaintenanceStatus);

-- שלב ג: בדיקת זמן ריצה *אחרי*
EXPLAIN ANALYZE 
SELECT * FROM ROOMMAINTENANCE WHERE MaintenanceStatus = 'Open';


-- ==========================================
-- אינדקס 3: חיפוש מהיר של תעריפים לפי עונה
-- ==========================================

-- שלב א: בדיקת זמן ריצה *לפני*
EXPLAIN ANALYZE 
SELECT * FROM PRICERATE WHERE SeasonID = 1;

-- שלב ב: יצירת האינדקס
CREATE INDEX idx_price_season ON PRICERATE(SeasonID);

-- שלב ג: בדיקת זמן ריצה *אחרי*
EXPLAIN ANALYZE 
SELECT * FROM PRICERATE WHERE SeasonID = 1;