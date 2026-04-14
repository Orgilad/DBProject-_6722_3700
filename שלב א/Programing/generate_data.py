from datetime import date, timedelta

output_file = "generated_insert_data.sql"

with open(output_file, "w", encoding="utf-8") as f:
    # ROOMTYPE - 500 rows
    for i in range(1, 501):
        f.write(
            f"INSERT INTO ROOMTYPE (RoomTypeID, TypeName, BasePrice, Description, BedType) "
            f"VALUES ({i}, 'Room Type {i}', {200 + i}, 'Description for room type {i}', 'Bed Type {i % 5 + 1}');\n"
        )

    # ROOMSTATUS - 500 rows
    for i in range(1, 501):
        f.write(
            f"INSERT INTO ROOMSTATUS (StatusID, StatusName) "
            f"VALUES ({i}, 'Status {i}');\n"
        )

    # AMENITY - 500 rows
    for i in range(1, 501):
        f.write(
            f"INSERT INTO AMENITY (AmenityID, AmenityName, AmenityCategory) "
            f"VALUES ({i}, 'Amenity {i}', 'Category {i % 10 + 1}');\n"
        )

    # SEASON - 500 rows
    start = date(2026, 1, 1)
    for i in range(1, 501):
        start_date = start + timedelta(days=i * 3)
        end_date = start_date + timedelta(days=2)
        f.write(
            f"INSERT INTO SEASON (SeasonID, SeasonName, StartDate, EndDate) "
            f"VALUES ({i}, 'Season {i}', '{start_date}', '{end_date}');\n"
        )

    # SPECIALOFFER - 500 rows
    for i in range(1, 501):
        discount = i % 51
        f.write(
            f"INSERT INTO SPECIALOFFER (OfferID, OfferName, DiscountPercentage) "
            f"VALUES ({i}, 'Offer {i}', {discount});\n"
        )

    # ROOM - 500 rows
    for i in range(1, 501):
        room_number = 1000 + i
        floor = (i % 20) + 1
        max_occupancy = (i % 4) + 1
        phone = f"05{i:08d}"[:10]
        room_type_id = (i % 500) + 1
        status_id = (i % 500) + 1

        f.write(
            f"INSERT INTO ROOM (RoomID, RoomNumber, Floor, MaxOccupancy, PhoneNumber, RoomTypeID, StatusID) "
            f"VALUES ({i}, {room_number}, {floor}, {max_occupancy}, '{phone}', {room_type_id}, {status_id});\n"
        )

    # ROOMMAINTENANCE - 20,000 rows
    for i in range(1, 20001):
        room_id = (i % 500) + 1
        start_date = date(2026, 1, 1) + timedelta(days=i % 365)
        end_date = start_date + timedelta(days=i % 5)
        cost = (i % 1000) + 50
        status = ["Reported", "In Progress", "Fixed", "Verified"][i % 4]

        f.write(
            f"INSERT INTO ROOMMAINTENANCE (MaintenanceID, StartDate, EndDate, Description, RepairCost, MaintenanceStatus, RoomID) "
            f"VALUES ({i}, '{start_date}', '{end_date}', 'Maintenance record {i}', {cost}, '{status}', {room_id});\n"
        )

    # PRICERATE - 500 rows
    for i in range(1, 501):
        season_id = i
        offer_id = i
        room_type_id = i
        final_price = 250 + (i % 300)

        f.write(
            f"INSERT INTO PRICERATE (RateID, SeasonID, OfferID, RoomTypeID, FinalPrice) "
            f"VALUES ({i}, {season_id}, {offer_id}, {room_type_id}, {final_price});\n"
        )

    # ROOMAMENITY - 20,000 rows
    counter = 1
    for room_id in range(1, 501):
        for amenity_id in range(1, 41):
            f.write(
                f"INSERT INTO ROOMAMENITY (RoomID, AmenityID) "
                f"VALUES ({room_id}, {amenity_id});\n"
            )
            counter += 1

print(f"Created {output_file}")