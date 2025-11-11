"""
Check severity level structure in Patch Manager Plus database
"""

import os
from dotenv import load_dotenv
import psycopg2

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

conn = psycopg2.connect(
    host=os.getenv('PATCHMGR_HOST'),
    port=os.getenv('PATCHMGR_PORT'),
    user=os.getenv('PATCHMGR_USER'),
    password=os.getenv('PATCHMGR_PASSWORD'),
    database=os.getenv('PATCHMGR_DATABASE')
)
cursor = conn.cursor()

print("Checking Severity Level Structure")
print("=" * 80)

# Find severity-related tables
print("\n1. Finding severity-related tables...")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE '%severity%'
    ORDER BY table_name;
""")
severity_tables = [row[0] for row in cursor.fetchall()]
print(f"Found tables: {', '.join(severity_tables)}")

# Check affectedpatchstatus for severity_id
print("\n2. Checking severity_id values in affectedpatchstatus...")
cursor.execute("""
    SELECT DISTINCT severity_id, COUNT(*) as count
    FROM affectedpatchstatus
    WHERE severity_id IS NOT NULL
    GROUP BY severity_id
    ORDER BY severity_id;
""")
severity_counts = cursor.fetchall()
print("\nSeverity ID distribution:")
for sev_id, count in severity_counts:
    print(f"  Severity {sev_id}: {count:,} patches")

# Look for severity definition table
print("\n3. Looking for severity definitions...")
for table in severity_tables:
    try:
        cursor.execute(f'SELECT * FROM "{table}" LIMIT 10;')
        rows = cursor.fetchall()
        if rows:
            cols = [desc[0] for desc in cursor.description]
            print(f"\n  Table: {table}")
            print(f"  Columns: {', '.join(cols)}")
            print("  Sample data:")
            for row in rows[:5]:
                print(f"    {row}")
    except Exception as e:
        print(f"  Error reading {table}: {e}")

# Check pmresourcepatchcount columns for severity
print("\n4. Checking pmresourcepatchcount structure...")
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'pmresourcepatchcount'
    ORDER BY ordinal_position;
""")
cols = [row[0] for row in cursor.fetchall()]
print(f"Columns: {', '.join(cols)}")

# Get sample data
cursor.execute("""
    SELECT *
    FROM pmresourcepatchcount
    LIMIT 5;
""")
print("\nSample data from pmresourcepatchcount:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check if there's a severity count table
print("\n5. Looking for severity count tables...")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND (table_name LIKE '%patch%count%' OR table_name LIKE '%severity%count%')
    ORDER BY table_name;
""")
count_tables = [row[0] for row in cursor.fetchall()]
print(f"Found tables: {', '.join(count_tables[:20])}")

# Check for patch severity in patchdetails
print("\n6. Checking patchdetails for severity info...")
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'patchdetails'
    ORDER BY ordinal_position;
""")
cols = [row[0] for row in cursor.fetchall()]
print(f"Columns: {', '.join(cols)}")

# Look for severity reference tables
print("\n7. Looking for severity level definitions...")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND (table_name LIKE '%severity%' OR table_name LIKE '%level%')
    ORDER BY table_name;
""")
ref_tables = [row[0] for row in cursor.fetchall()]
print(f"Reference tables: {', '.join(ref_tables[:20])}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Severity check complete!")
