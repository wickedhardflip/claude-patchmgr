"""
Test connection to ManageEngine Patch Manager Plus database
Discovers database name, port, and lists available tables
"""

import sys
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

# Get connection parameters
host = os.getenv('PATCHMGR_HOST')
port = os.getenv('PATCHMGR_PORT', '5432')
user = os.getenv('PATCHMGR_USER')
password = os.getenv('PATCHMGR_PASSWORD')
database = os.getenv('PATCHMGR_DATABASE', 'postgres')  # Try default first

print(f"Testing connection to Patch Manager Plus database...")
print(f"Host: {host}")
print(f"Port: {port}")
print(f"User: {user}")
print(f"Database: {database}")
print("-" * 60)

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Installing...")
    os.system('pip install psycopg2-binary')
    import psycopg2

# Try to connect
try:
    print("\n1. Attempting connection to default 'postgres' database...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database='postgres',
        connect_timeout=10
    )
    cursor = conn.cursor()

    # List all databases
    print("✓ Connection successful!")
    print("\nAvailable databases:")
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
    databases = cursor.fetchall()
    for db in databases:
        print(f"  - {db[0]}")

    cursor.close()
    conn.close()

    # Now try to find the Patch Manager database
    print("\n2. Looking for Patch Manager database...")
    possible_names = ['pmpdb', 'desktopcentral', 'patchmanager', 'patch_manager', 'dcdb']

    found_db = None
    for db_name in possible_names:
        if any(db_name.lower() in db[0].lower() for db in databases):
            found_db = [db[0] for db in databases if db_name.lower() in db[0].lower()][0]
            print(f"✓ Found potential Patch Manager database: {found_db}")
            break

    if not found_db:
        print("⚠ Could not identify Patch Manager database automatically.")
        print("Please check the database list above and update PATCHMGR_DATABASE in credentials.env")
        sys.exit(0)

    # Connect to the Patch Manager database
    print(f"\n3. Connecting to {found_db}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=found_db,
        connect_timeout=10
    )
    cursor = conn.cursor()
    print("✓ Connected successfully!")

    # List all tables
    print(f"\n4. Tables in {found_db}:")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    if tables:
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("⚠ No tables found in public schema")

    # Try to find system/computer related tables
    print("\n5. Looking for system/computer tables...")
    system_keywords = ['computer', 'system', 'machine', 'host', 'device', 'resource']
    system_tables = [t[0] for t in tables if any(kw in t[0].lower() for kw in system_keywords)]

    if system_tables:
        print("Found potential system tables:")
        for table in system_tables:
            print(f"  - {table}")
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cursor.fetchone()[0]
            print(f"    (contains {count} rows)")

    # Try to find patch related tables
    print("\n6. Looking for patch tables...")
    patch_keywords = ['patch', 'update', 'vulnerability', 'missing']
    patch_tables = [t[0] for t in tables if any(kw in t[0].lower() for kw in patch_keywords)]

    if patch_tables:
        print("Found potential patch tables:")
        for table in patch_tables:
            print(f"  - {table}")
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cursor.fetchone()[0]
            print(f"    (contains {count} rows)")

    # Try to find policy/group tables
    print("\n7. Looking for policy/group tables...")
    policy_keywords = ['policy', 'group', 'config', 'deployment']
    policy_tables = [t[0] for t in tables if any(kw in t[0].lower() for kw in policy_keywords)]

    if policy_tables:
        print("Found potential policy/group tables:")
        for table in policy_tables:
            print(f"  - {table}")
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cursor.fetchone()[0]
            print(f"    (contains {count} rows)")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("CONNECTION TEST COMPLETE!")
    print(f"Update credentials.env with: PATCHMGR_DATABASE={found_db}")
    print("=" * 60)

except psycopg2.OperationalError as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Verify the server is reachable: ping {host}")
    print("2. Check if PostgreSQL is running on port {port}")
    print("3. Verify username and password are correct")
    print("4. Check firewall settings")

except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
