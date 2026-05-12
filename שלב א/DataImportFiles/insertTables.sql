INSERT INTO ROOMTYPE (RoomTypeID, TypeName, BasePrice, Description, BedType) VALUES
(1, 'Single', 300, 'Single room', 'Single Bed'),
(2, 'Double', 450, 'Double room', 'Double Bed');

INSERT INTO ROOMSTATUS (StatusID, StatusName) VALUES
(1, 'Available'),
(2, 'Occupied');

INSERT INTO AMENITY (AmenityID, AmenityName, AmenityCategory) VALUES
(1, 'WiFi', 'Tech'),
(2, 'TV', 'Entertainment');

INSERT INTO SEASON (SeasonID, SeasonName, StartDate, EndDate) VALUES
(1, 'Winter', '2026-12-01', '2027-02-28'),
(2, 'Summer', '2026-06-01', '2026-08-31');

INSERT INTO SPECIALOFFER (OfferID, OfferName, DiscountPercentage) VALUES
(1, 'No Discount', 0),
(2, 'Weekend Deal', 10);

INSERT INTO ROOM (RoomID, RoomNumber, Floor, MaxOccupancy, PhoneNumber, RoomTypeID, StatusID) VALUES
(1, 101, 1, 1, '1001', 1, 1),
(2, 102, 1, 2, '1002', 2, 2);

INSERT INTO ROOMAMENITY (RoomID, AmenityID) VALUES
(1, 1), 
(1, 2), 
(2, 1);

INSERT INTO ROOMMAINTENANCE (MaintenanceID, StartDate, EndDate, Description, RepairCost, MaintenanceStatus, RoomID) VALUES
(1, '2026-04-01', '2026-04-03', 'Air conditioner repair', 250, 'Fixed', 1),
(2, '2026-04-05', NULL, 'Bathroom leak inspection', 0, 'Reported', 2);

INSERT INTO PRICERATE (RateID, RoomTypeID, SeasonID, OfferID, FinalPrice)
SELECT 
    -- יצירת מזהה רץ (למשל 1, 2, 3...)
    row_number() OVER () AS RateID, 
    RT.RoomTypeID, 
    S.SeasonID, 
    SO.OfferID,
    -- הנוסחה לחישוב המחיר הסופי:
    CASE 
        WHEN S.SeasonName = 'Winter' THEN (RT.BasePrice + 100) * (1 - SO.DiscountPercentage/100.0)
        WHEN S.SeasonName = 'Summer' THEN (RT.BasePrice + 200) * (1 - SO.DiscountPercentage/100.0)
        ELSE RT.BasePrice * (1 - SO.DiscountPercentage/100.0)
    END AS CalculatedFinalPrice
FROM ROOMTYPE RT
CROSS JOIN SEASON S -- מחבר כל סוג חדר עם כל עונה
CROSS JOIN SPECIALOFFER SO -- מוסיף את אפשרויות המבצע
WHERE SO.OfferName IN ('No Discount', 'Weekend Deal'); -- פילטר כדי שלא ייווצרו יותר מדי שילובים