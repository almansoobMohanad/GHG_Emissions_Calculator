import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Connect WITHOUT specifying a database
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        ssl_disabled=False
    )
    
    cursor = connection.cursor()
    
    # Create your database
    database_name = "ghg_app_db"  # You can change this name
    cursor.execute(f"CREATE DATABASE {database_name}")
    print(f"✅ Database '{database_name}' created successfully!")
    
    # Verify it was created
    cursor.execute("SHOW DATABASES")
    print("\nAvailable databases:")
    for (db,) in cursor:
        print(f"  - {db}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ Error: {e}")