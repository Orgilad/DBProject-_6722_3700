import psycopg2
import sys

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mydatabase",
    "user": "or",
    "password": "1234"
}

def run_tests():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
    except Exception as e:
        print("Failed to connect to database:", e)
        sys.exit(1)

    print("Connection successful!")

    # 1. Test fetching rooms with joins
    print("\n--- Testing Room Fetch Join ---")
    try:
        cur.execute("""
            SELECT r.roomid, r.roomnumber, r.floor, r.maxoccupancy, r.phonenumber, rt.typename, rs.statusname
            FROM room r
            LEFT JOIN roomtype rt ON r.roomtypeid = rt.roomtypeid
            LEFT JOIN roomstatus rs ON r.statusid = rs.statusid
            LIMIT 5;
        """)
        rows = cur.fetchall()
        print(f"Fetched {len(rows)} rooms successfully:")
        for r in rows:
            print(f"Room Number: {r[1]}, Type: {r[5]}, Status: {r[6]}")
    except Exception as e:
        print("Error fetching rooms:", e)
        conn.rollback()

    # 2. Test CRUD on Room table
    print("\n--- Testing Room CRUD Operations ---")
    test_room_id = 9999
    test_room_number = 999
    
    try:
        # Check if exists and clean up
        cur.execute("DELETE FROM room WHERE roomid = %s OR roomnumber = %s;", (test_room_id, test_room_number))
        conn.commit()
        
        # Get dynamic status and roomtype
        cur.execute("SELECT roomtypeid FROM roomtype LIMIT 1;")
        type_id = cur.fetchone()[0]
        cur.execute("SELECT statusid FROM roomstatus LIMIT 1;")
        status_id = cur.fetchone()[0]
        
        # Insert
        print("Inserting room...")
        cur.execute("""
            INSERT INTO room (roomid, roomnumber, floor, maxoccupancy, phonenumber, roomtypeid, statusid)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (test_room_id, test_room_number, 3, 2, "123-456", type_id, status_id))
        conn.commit()
        print("Room inserted successfully!")
        
        # Read
        cur.execute("SELECT roomnumber, floor, phonenumber FROM room WHERE roomid = %s;", (test_room_id,))
        room = cur.fetchone()
        print(f"Read room: Number={room[0]}, Floor={room[1]}, Phone={room[2]}")
        
        # Update
        print("Updating room...")
        cur.execute("""
            UPDATE room 
            SET floor = %s, phonenumber = %s
            WHERE roomid = %s;
        """, (4, "999-999", test_room_id))
        conn.commit()
        
        cur.execute("SELECT floor, phonenumber FROM room WHERE roomid = %s;", (test_room_id,))
        room = cur.fetchone()
        print(f"Updated room: Floor={room[0]} (expected 4), Phone={room[1]} (expected 999-999)")
        
        # Delete
        print("Deleting room...")
        cur.execute("DELETE FROM room WHERE roomid = %s;", (test_room_id,))
        conn.commit()
        print("Room deleted successfully!")
        
    except Exception as e:
        print("CRUD Test failed:", e)
        conn.rollback()

    # 3. Test SQL queries from Stage B
    print("\n--- Testing Stage B Query 1 (Status Summary) ---")
    try:
        cur.execute("""
            SELECT 
                RS.StatusName, 
                COUNT(R.RoomID) AS Total_Rooms,
                SUM(COALESCE(R.MaxOccupancy, 0)) AS Potential_Guests
            FROM ROOMSTATUS RS
            LEFT JOIN ROOM R ON RS.StatusID = R.StatusID
            GROUP BY RS.StatusName
            ORDER BY Total_Rooms DESC;
        """)
        rows = cur.fetchall()
        print(f"Query 1 succeeded. Rows returned: {len(rows)}")
        for r in rows[:3]:
            print(r)
    except Exception as e:
        print("Query 1 failed:", e)
        conn.rollback()

    print("\n--- Testing Stage B Query 2 (Rooms with >= 3 Amenities) ---")
    try:
        cur.execute("""
            SELECT 
                R.RoomNumber, 
                R.Floor, 
                COUNT(RA.AmenityID) AS Total_Amenities
            FROM ROOM R
            JOIN ROOMAMENITY RA ON R.RoomID = RA.RoomID
            GROUP BY R.RoomNumber, R.Floor
            HAVING COUNT(RA.AmenityID) >= 3
            ORDER BY Total_Amenities DESC, R.RoomNumber
            LIMIT 100;
        """)
        rows = cur.fetchall()
        print(f"Query 2 succeeded. Rows returned: {len(rows)}")
        for r in rows[:3]:
            print(r)
    except Exception as e:
        print("Query 2 failed:", e)
        conn.rollback()

    # 4. Test calling stored function Get_Room_Total_Maintenance_Cost
    print("\n--- Testing Stored Function Get_Room_Total_Maintenance_Cost ---")
    try:
        cur.execute("SELECT roomid FROM room LIMIT 1;")
        res_room = cur.fetchone()
        if res_room:
            room_id = res_room[0]
            cur.execute("SELECT Get_Room_Total_Maintenance_Cost(%s);", (room_id,))
            cost = cur.fetchone()[0]
            print(f"Function called successfully for Room ID {room_id}. Total Maintenance Cost: {cost}")
        else:
            print("No rooms in DB to test function.")
    except Exception as e:
        print("Function call failed:", e)
        conn.rollback()

    # 5. Test calling stored procedure Update_Room_Status
    print("\n--- Testing Stored Procedure Update_Room_Status ---")
    try:
        cur.execute("SELECT roomnumber, statusid FROM room LIMIT 1;")
        res_room = cur.fetchone()
        if res_room:
            room_number = res_room[0]
            orig_status_id = res_room[1]
            
            cur.execute("SELECT statusname FROM roomstatus WHERE statusid = %s;", (orig_status_id,))
            orig_status_name = cur.fetchone()[0]
            
            # Find another status to update to
            cur.execute("SELECT statusname FROM roomstatus WHERE statusid != %s LIMIT 1;", (orig_status_id,))
            another_status = cur.fetchone()
            if another_status:
                new_status_name = another_status[0]
                print(f"Calling Update_Room_Status({room_number}, '{new_status_name}')...")
                cur.execute("CALL Update_Room_Status(%s, %s);", (room_number, new_status_name))
                conn.commit()
                print("Procedure called successfully!")
                
                # Check status updated
                cur.execute("""
                    SELECT rs.statusname FROM room r 
                    JOIN roomstatus rs ON r.statusid = rs.statusid 
                    WHERE r.roomnumber = %s;
                """, (room_number,))
                updated_status = cur.fetchone()[0]
                print(f"Status in DB now: {updated_status} (expected {new_status_name})")
                
                # Restore original status
                cur.execute("CALL Update_Room_Status(%s, %s);", (room_number, orig_status_name))
                conn.commit()
                print("Restored original room status.")
            else:
                print("Only one status exists, cannot test status update procedure.")
        else:
            print("No rooms in DB to test procedure.")
    except Exception as e:
        print("Procedure call failed:", e)
        conn.rollback()

    cur.close()
    conn.close()
    print("\nAll database SQL syntax tests completed.")

if __name__ == "__main__":
    run_tests()
