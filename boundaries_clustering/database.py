import pg8000
import numpy as np

def get_dataset():
    # database connection and data retrieval logic
    # Connect to your PostgreSQL database
    conn = pg8000.connect(
        database="agdb",
        user="postgres",
        password="F3fubxVDBehJhkjWSbLO",
        host="alphaground-1.c1fuujrhmqpn.eu-central-1.rds.amazonaws.com",
        port=5432  # default port, change if necessary
    )

    # Create a cursor object
    cur = conn.cursor()

    # Execute a query to get the coordinates from your table where clean_status_type is 'accepted'
    cur.execute("SELECT ST_X(coordinates), ST_Y(coordinates) FROM geometry_points WHERE clean_status_type != 'distance_rejected' AND roadworks = 'on' AND logbook_id IN (40, 41, 42) ORDER BY time_of_measure ASC;")

    # Fetch all the rows
    rows = cur.fetchall()
    dataset = np.array(rows)

    # Close the connection
    conn.close()

    return dataset