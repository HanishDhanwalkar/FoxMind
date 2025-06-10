import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd

from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUXDB_URL = "http://172.16.2.43:8086"
INFLUXDB_TOKEN = "uRzKFjPBtQhoIBAJLp7wPALASjDRlejolbNe27lLRyE90yuBwkSyDo9zayEtEChU6jj_iboHApSI4SxMWrcHDQ=="
INFLUXDB_ORG = "unibo"
INFLUXDB_BUCKET = "smart-pantry" # This maps to your 'database' concept in the JS code

def main():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()

    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -90d)

    """
    print("Executing query:")
    print(query)

    tables = query_api.query(query, org=INFLUXDB_ORG)
    data = {
        "room": [],
        "day": [],
    }

    for table in tables:
        for record in table.records:
            data["room"].append(record["room"])
            data["day"].append(record["_time"].isoformat()) 

    df = pd.DataFrame(data)
    print("\n--- Query Results ---")
    print(df)

    client.close()

def write_data_to_influxdb():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=WriteOptions(batch_size=100, flush_interval=1000, jitter_interval=0, retry_interval=5000, max_retries=3))

    try:
        print(f"Attempting to write data to InfluxDB at {INFLUXDB_URL} (manual close)...")
# #####
        point1 = Point("home").tag("room", "kitchen_manual").field("temp", 42.5).time(datetime.utcnow())
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point1)
        print("Point (manual) written successfully.")

    except Exception as e:
        print(f"An error occurred during write operation: {e}")
    finally:
        write_api.flush()
        write_api.close()
        client.close()
        print("InfluxDB client and write API closed manually.")

if __name__ == "__main__":
#    main()
    write_data_to_influxdb()
    main()