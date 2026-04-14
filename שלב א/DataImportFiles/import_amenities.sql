COPY AMENITY (AmenityID, AmenityName, AmenityCategory)
FROM '/data/amenities.csv'
DELIMITER ','
CSV HEADER;''