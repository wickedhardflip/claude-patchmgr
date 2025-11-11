"""Quick connection test for Patch Manager Plus database"""

import os
from dotenv import load_dotenv

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

host = os.getenv('PATCHMGR_HOST')
port = os.getenv('PATCHMGR_PORT')
user = os.getenv('PATCHMGR_USER')
password = os.getenv('PATCHMGR_PASSWORD')
database = os.getenv('PATCHMGR_DATABASE')

print(f"Connecting to {host}:{port}/{database} as {user}...")

try:
    import psycopg2
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=10
    )
    cursor = conn.cursor()

    print("SUCCESS! Connected to Patch Manager database!")

    # List tables
    print("\n" + "="*60)
    print("Available tables:")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    print(f"Found {len(tables)} tables:")
    for i, table in enumerate(tables[:20], 1):  # Show first 20
        print(f"  {i}. {table[0]}")

    if len(tables) > 20:
        print(f"  ... and {len(tables) - 20} more tables")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("Database connection verified!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
