/* =======================================================================
   קובץ: Index.sql
   תיאור: הוספת 3 אינדקסים לשיפור מהירות השאילתות
======================================================================= */

-- אינדקס 1: חיפוש מהיר של חדרים לפי קומה (שימושי למסך Inventory)
CREATE INDEX idx_room_floor ON ROOM(Floor);

-- אינדקס 2: חיפוש מהיר של תיקונים לפי סטטוס (שימושי למסך Maintenance)
CREATE INDEX idx_maintenance_status ON ROOMMAINTENANCE(MaintenanceStatus);

-- אינדקס 3: חיפוש מהיר של תעריפים לפי עונה (שימושי למסך Pricing)
CREATE INDEX idx_price_season ON PRICERATE(SeasonID);