/* =======================================================================
   קובץ: Constraints.sql
   תיאור: הוספת 3 אילוצים להגנה על שלמות הנתונים + בדיקות הכשלה
======================================================================= */

-- ==========================================
-- אילוץ 1: מחיר בסיס של סוג חדר חייב להיות חיובי
-- ==========================================
ALTER TABLE ROOMTYPE
ADD CONSTRAINT chk_positive_base_price 
CHECK (BasePrice > 0);

-- 💥 פקודת הכשלה (לצלם שגיאה): מנסים לעדכן מחיר למינוס 50!
 --UPDATE ROOMTYPE SET BasePrice = -50 WHERE RoomTypeID = (SELECT MIN(RoomTypeID) FROM ROOMTYPE);


-- ==========================================
-- אילוץ 2: אחוז הנחה במבצע חייב להיות בין 0 ל-100
-- ==========================================
ALTER TABLE SPECIALOFFER
ADD CONSTRAINT chk_valid_discount 
CHECK (DiscountPercentage >= 0 AND DiscountPercentage <= 100);

-- 💥 פקודת הכשלה (לצלם שגיאה): מנסים לתת 150% הנחה!
 --UPDATE SPECIALOFFER SET DiscountPercentage = 150 WHERE OfferID = (SELECT MIN(OfferID) FROM SPECIALOFFER);


-- ==========================================
-- אילוץ 3: תפוסת חדר לא יכולה להיות 0 או שלילית
-- ==========================================
ALTER TABLE ROOM
ADD CONSTRAINT chk_valid_occupancy 
CHECK (MaxOccupancy > 0);

-- 💥 פקודת הכשלה (לצלם שגיאה): מנסים לשנות תפוסת חדר ל-0!
-- UPDATE ROOM SET MaxOccupancy = 0WHERE RoomID = (SELECT MIN(RoomID) FROM ROOM);