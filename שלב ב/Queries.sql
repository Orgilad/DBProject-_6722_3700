/* =======================================================================
   קובץ: Queries.sql
   מערכת: PostgreSQL
   תיאור: 8 שאילתות SELECT למערכת ניהול חדרים (מתוכן 4 כפולות ליעילות),
          3 שאילתות UPDATE, ו-3 שאילתות DELETE.
          כולל פונקציות תאריך, קיבוץ, מיון, ותתי-שאילתות.
======================================================================= */

-- =======================================================================
-- חלק א': שאילתות SELECT (למסכי המערכת)
-- =======================================================================

/* -----------------------------------------------------------------------
   שאילתה 1 (כפולה) - למסך Dashboard: דוח הכנסות לפי חודשים לשנת 2026.
   מציגה את מספר החודש, סך ההכנסה הצפויה ומספר התעריפים שהוגדרו.
   שימוש בפונקציית EXTRACT לחילוץ חודש ושנה.
----------------------------------------------------------------------- */

-- דרך א' (היעילה: שימוש ב-JOIN ו-GROUP BY)
SELECT 
    EXTRACT(MONTH FROM S.StartDate) AS Month_Number,
    SUM(P.FinalPrice) AS Total_Projected_Revenue,
    COUNT(P.RateID) AS Rates_Count
FROM PRICERATE P
JOIN SEASON S ON P.SeasonID = S.SeasonID
WHERE EXTRACT(YEAR FROM S.StartDate) = 2026
GROUP BY EXTRACT(MONTH FROM S.StartDate)
ORDER BY Month_Number;

-- דרך ב' (הפחות יעילה: שימוש בתת-שאילתה ב-FROM - Inline View)
SELECT 
    MonthData.Month_Number,
    SUM(P.FinalPrice) AS Total_Projected_Revenue,
    COUNT(P.RateID) AS Rates_Count
FROM PRICERATE P, 
     (SELECT SeasonID, EXTRACT(MONTH FROM StartDate) AS Month_Number 
      FROM SEASON 
      WHERE EXTRACT(YEAR FROM StartDate) = 2026) MonthData
WHERE P.SeasonID = MonthData.SeasonID
GROUP BY MonthData.Month_Number
ORDER BY MonthData.Month_Number;

/* הסבר לדוח: דרך א' יעילה יותר כי האופטימייזר של PostgreSQL מבצע Hash Join על הטבלאות ישירות. בדרך ב', יצירת טבלה וירטואלית (Subquery ב-FROM) עשויה לדרוש שלב ביניים נוסף בזיכרון של שרת מסד הנתונים. */


/* -----------------------------------------------------------------------
   שאילתה 2 (רגילה) - למסך Dashboard: סיכום מצב חדרים הכולל תפוסה פוטנציאלית.
   שימוש ב-LEFT JOIN כדי להציג סטטוסים גם אם אין בהם כרגע חדרים.
----------------------------------------------------------------------- */
SELECT 
    RS.StatusName, 
    COUNT(R.RoomID) AS Total_Rooms,
    SUM(COALESCE(R.MaxOccupancy, 0)) AS Potential_Guests
FROM ROOMSTATUS RS
LEFT JOIN ROOM R ON RS.StatusID = R.StatusID
GROUP BY RS.StatusName
ORDER BY Total_Rooms DESC;


/* -----------------------------------------------------------------------
   שאילתה 3 (כפולה) - למסך Inventory: מציאת חדרים שיש בהם 3 מתקנים או יותר.
----------------------------------------------------------------------- */

-- דרך א' (היעילה: שימוש ב-JOIN, GROUP BY ו-HAVING)
SELECT 
    R.RoomNumber, 
    R.Floor, 
    COUNT(RA.AmenityID) AS Total_Amenities
FROM ROOM R
JOIN ROOMAMENITY RA ON R.RoomID = RA.RoomID
GROUP BY R.RoomNumber, R.Floor
HAVING COUNT(RA.AmenityID) >= 3
ORDER BY Total_Amenities DESC, R.RoomNumber;

-- דרך ב' (הפחות יעילה: שימוש בתת-שאילתה תלויה - Correlated Subquery)
SELECT 
    R.RoomNumber, 
    R.Floor,
    (SELECT COUNT(*) FROM ROOMAMENITY RA WHERE RA.RoomID = R.RoomID) AS Total_Amenities
FROM ROOM R
WHERE (SELECT COUNT(*) FROM ROOMAMENITY RA WHERE RA.RoomID = R.RoomID) >= 3
ORDER BY Total_Amenities DESC, R.RoomNumber;

/* הסבר לדוח: דרך ב' מריצה פקודת מנייה (COUNT) מחדש עבור *כל* שורה בטבלת החדרים בנפרד (Nested Loop). דרך א' מבצעת את הקישור והקיבוץ במעבר אחד של המנוע על הנתונים, ולכן מהירה משמעותית. */


/* -----------------------------------------------------------------------
   שאילתה 4 (רגילה) - למסך Inventory: הצגת חדרים בקומת הקרקע/מרתף וסוג המיטה.
----------------------------------------------------------------------- */
SELECT 
    R.RoomNumber, 
    R.Floor, 
    RT.TypeName,
    RT.BedType
FROM ROOM R
JOIN ROOMTYPE RT ON R.RoomTypeID = RT.RoomTypeID
WHERE R.Floor <= 4
ORDER BY R.RoomNumber;


/* -----------------------------------------------------------------------
   שאילתה 5 (כפולה) - למסך Maintenance: חדרים שתוקנו אך טרם קיבלו אישור.
   כולל חישוב משך זמן התיקון בימים.
----------------------------------------------------------------------- */

-- דרך א' (מחזירה את כל המידע הנדרש לתצוגה, כולל תיאור ועלות)
SELECT 
    R.RoomNumber, 
    RM.Description, 
    RM.RepairCost,
    (RM.EndDate - RM.StartDate) AS Days_In_Repair
FROM ROOM R
JOIN ROOMMAINTENANCE RM ON R.RoomID = RM.RoomID
WHERE RM.MaintenanceStatus = 'Fixed' 
  AND RM.EndDate IS NOT NULL;

-- דרך ב' (יעילה יותר לבדיקת "קיום" בלבד באמצעות EXISTS)
SELECT 
    R.RoomNumber, 
    R.Floor,
    R.PhoneNumber
FROM ROOM R
WHERE EXISTS (
    SELECT 1 
    FROM ROOMMAINTENANCE RM 
    WHERE RM.RoomID = R.RoomID 
      AND RM.MaintenanceStatus = 'Fixed'
      AND RM.EndDate IS NOT NULL
);

/* הסבר לדוח: שאילתת ה-EXISTS לרוב תהיה מהירה יותר כי היא עוצרת את הסריקה ברגע שנמצאת התאמה אחת לחדר (Short-circuit). עם זאת, לטובת מסך המערכת שמציג את עלות התיקון עצמו, דרך א' הכרחית כדי לשלוף נתונים מטבלת התחזוקה. */


/* -----------------------------------------------------------------------
   שאילתה 6 (רגילה) - למסך Maintenance: הצגת פרטי התיקון היקר ביותר במלון.
----------------------------------------------------------------------- */
SELECT 
    R.RoomNumber, 
    RM.Description, 
    RM.RepairCost, 
    RM.StartDate
FROM ROOMMAINTENANCE RM
JOIN ROOM R ON RM.RoomID = R.RoomID
WHERE RM.RepairCost = (SELECT MAX(RepairCost) FROM ROOMMAINTENANCE);


/* -----------------------------------------------------------------------
   שאילתה 7 (כפולה) - מחירים לעונה הראשונה במערכת שיש להם מבצע.
----------------------------------------------------------------------- */

-- דרך א' (היעילה: שימוש מרובה ב-JOIN)
SELECT 
    RT.TypeName, 
    S.SeasonName, 
    SO.OfferName, 
    P.FinalPrice
FROM PRICERATE P
JOIN ROOMTYPE RT ON P.RoomTypeID = RT.RoomTypeID
JOIN SEASON S ON P.SeasonID = S.SeasonID
JOIN SPECIALOFFER SO ON P.OfferID = SO.OfferID
WHERE S.SeasonID = (SELECT MIN(SeasonID) FROM SEASON);

-- דרך ב' (הפחות יעילה: שימוש בתתי-שאילתות מסורבלות ב-SELECT וב-WHERE)
SELECT 
    RT.TypeName, 
    (SELECT SeasonName FROM SEASON WHERE SeasonID = (SELECT MIN(SeasonID) FROM SEASON)) AS SeasonName,
    (SELECT MAX(OfferName) FROM SPECIALOFFER WHERE OfferID IN (SELECT OfferID FROM PRICERATE WHERE RoomTypeID = RT.RoomTypeID AND SeasonID = (SELECT MIN(SeasonID) FROM SEASON))) AS OfferName,
    (SELECT MAX(FinalPrice) FROM PRICERATE WHERE RoomTypeID = RT.RoomTypeID AND SeasonID = (SELECT MIN(SeasonID) FROM SEASON) AND OfferID IN (SELECT OfferID FROM SPECIALOFFER WHERE DiscountPercentage > 0)) AS FinalPrice
FROM ROOMTYPE RT
WHERE RT.RoomTypeID IN (
    SELECT RoomTypeID 
    FROM PRICERATE 
    WHERE SeasonID = (SELECT MIN(SeasonID) FROM SEASON)
      AND OfferID IN (SELECT OfferID FROM SPECIALOFFER WHERE DiscountPercentage > 0)
);
/* הסבר לדוח: ה-JOIN (דרך א') מאפשר לאופטימייזר של PostgreSQL לבחור את סדר קריאת הטבלאות המיטבי (Execution Plan). שימוש בתתי-שאילתות מקוננות עמוקות (דרך ב') מכריח את המנוע לבצע בדיקות כבדות ומסורבלות. */


/* -----------------------------------------------------------------------
   שאילתה 8 (רגילה) - למסך Pricing: הפער בין מחיר הבסיס למחיר הסופי הממוצע.
----------------------------------------------------------------------- */
SELECT 
    RT.TypeName, 
    RT.BasePrice, 
    ROUND(AVG(P.FinalPrice), 2) AS Avg_Final_Price,
    ROUND(AVG(P.FinalPrice) - RT.BasePrice, 2) AS Price_Difference
FROM ROOMTYPE RT
JOIN PRICERATE P ON RT.RoomTypeID = P.RoomTypeID
GROUP BY RT.TypeName, RT.BasePrice
ORDER BY Price_Difference DESC;



-- =======================================================================
-- חלק ב': שאילתות מניפולציית נתונים (UPDATE & DELETE)
-- חובה לצלם את הנתונים בטבלאות *לפני* ההרצה ואז *אחרי* ההרצה לדוח!
-- =======================================================================

/* -----------------------------------------------------------------------
   UPDATE 1: העלאת מחירים עונתית
   מעדכן את המחיר הסופי ב-10% עבור העונה הראשונה במערכת.
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני" ו"אחרי":
-- SELECT RateID, FinalPrice, SeasonID FROM PRICERATE WHERE SeasonID = (SELECT MIN(SeasonID) FROM SEASON);

UPDATE PRICERATE
SET FinalPrice = FinalPrice * 1.10
WHERE SeasonID = (SELECT MIN(SeasonID) FROM SEASON);


/* -----------------------------------------------------------------------
   UPDATE 2: קידום סטטוס אוטומטי לתיקון היקר ביותר
   משנה את הסטטוס ל-'In Progress' עבור התיקון שעלה הכי הרבה כסף.
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני" ו"אחרי":
 --SELECT RoomID, MaintenanceStatus, RepairCost FROM ROOMMAINTENANCE WHERE RepairCost = (SELECT MAX(RepairCost) FROM ROOMMAINTENANCE);

UPDATE ROOMMAINTENANCE
SET MaintenanceStatus = 'In Progress'
WHERE RepairCost = (SELECT MAX(RepairCost) FROM ROOMMAINTENANCE);


/* -----------------------------------------------------------------------
   UPDATE 3: שדרוג תפוסה לסוג החדר היוקרתי ביותר
   מוסיף מקום לאדם נוסף לחדרים המשויכים לסוג החדר היקר ביותר (BasePrice).
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני" ו"אחרי":
 --SELECT RoomID, MaxOccupancy, RoomTypeID FROM ROOM WHERE RoomTypeID = (SELECT RoomTypeID FROM ROOMTYPE ORDER BY BasePrice DESC LIMIT 1);

UPDATE ROOM
SET MaxOccupancy = MaxOccupancy + 1
WHERE RoomTypeID = (SELECT RoomTypeID FROM ROOMTYPE ORDER BY BasePrice DESC LIMIT 1);


/* -----------------------------------------------------------------------
   DELETE 1: ניקוי מתקנים מחדר ספציפי
   מוחק את כל המתקנים (Amenities) המשויכים לחדר בעל המזהה (RoomID) הגבוה ביותר במערכת.
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני":
 --SELECT * FROM ROOMAMENITY WHERE RoomID = (SELECT MAX(RoomID) FROM ROOMAMENITY);

DELETE FROM ROOMAMENITY
WHERE RoomID = (SELECT MAX(RoomID) FROM ROOMAMENITY);

/* -----------------------------------------------------------------------
   DELETE 2: ארכוב היסטוריית תחזוקה ישנה
   מוחק את רשומת התחזוקה הישנה ביותר (לפי תאריך סיום).
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני":
 --SELECT * FROM ROOMMAINTENANCE WHERE EndDate = (SELECT MIN(EndDate) FROM ROOMMAINTENANCE);

DELETE FROM ROOMMAINTENANCE
WHERE EndDate = (SELECT MIN(EndDate) FROM ROOMMAINTENANCE);

/* -----------------------------------------------------------------------
   DELETE 3: מחיקת התעריף הזול ביותר
   מוחק את התעריף שהמחיר הסופי שלו הוא הנמוך ביותר במערכת.
----------------------------------------------------------------------- */
-- 📸 להרצה וצילום "לפני":
SELECT * FROM PRICERATE WHERE FinalPrice = (SELECT MIN(FinalPrice) FROM PRICERATE);

DELETE FROM PRICERATE
WHERE FinalPrice = (SELECT MIN(FinalPrice) FROM PRICERATE);