"""
Check severity level structure in Patch Manager Plus database - Part 2
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

print("Examining Severity Tables in Detail")
print("=" * 80)

# Check pmseverity table
print("\n1. PMSEVERITY TABLE (Severity Definitions)")
print("-" * 80)
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'pmseverity'
        ORDER BY ordinal_position;
    """)
    cols = cursor.fetchall()
    print("Columns:")
    for col, dtype in cols:
        print(f"  - {col}: {dtype}")

    cursor.execute('SELECT * FROM pmseverity ORDER BY severityid;')
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    print(f"\nData ({len(rows)} rows):")
    print(f"  {col_names}")
    for row in rows:
        print(f"  {row}")
except Exception as e:
    print(f"Error: {e}")

# Check pmrespatchseveritycount table
print("\n2. PMRESPATCHSEVERITYCOUNT TABLE (Resource Patch Severity Counts)")
print("-" * 80)
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'pmrespatchseveritycount'
        ORDER BY ordinal_position;
    """)
    cols = cursor.fetchall()
    print("Columns:")
    for col, dtype in cols:
        print(f"  - {col}: {dtype}")

    cursor.execute('SELECT * FROM pmrespatchseveritycount LIMIT 10;')
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    print(f"\nSample data ({len(rows)} rows shown):")
    for row in rows[:3]:
        print(f"  {row}")
except Exception as e:
    print(f"Error: {e}")

# Check resourcepatchseveritycount table
print("\n3. RESOURCEPATCHSEVERITYCOUNT TABLE")
print("-" * 80)
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'resourcepatchseveritycount'
        ORDER BY ordinal_position;
    """)
    cols = cursor.fetchall()
    print("Columns:")
    for col, dtype in cols:
        print(f"  - {col}: {dtype}")

    cursor.execute('SELECT COUNT(*) FROM resourcepatchseveritycount;')
    count = cursor.fetchone()[0]
    print(f"\nTotal rows: {count}")

    if count > 0:
        cursor.execute('SELECT * FROM resourcepatchseveritycount LIMIT 5;')
        rows = cursor.fetchall()
        print(f"\nSample data:")
        for row in rows[:3]:
            print(f"  {row}")
except Exception as e:
    print(f"Error: {e}")

# Check affectedpatchstatus columns
print("\n4. AFFECTEDPATCHSTATUS COLUMNS")
print("-" * 80)
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'affectedpatchstatus'
        ORDER BY ordinal_position;
    """)
    cols = cursor.fetchall()
    print("Columns:")
    for col, dtype in cols:
        print(f"  - {col}: {dtype}")
except Exception as e:
    print(f"Error: {e}")

# Try to find how to get severity per patch per resource
print("\n5. FINDING SEVERITY DATA PER RESOURCE")
print("-" * 80)
try:
    # Try joining tables to get severity info
    cursor.execute("""
        SELECT
            r.resource_id,
            r.name,
            psc.severityid,
            psc.missing_count,
            psc.installed_count
        FROM pmrespatchseveritycount psc
        LEFT JOIN resource r ON psc.resource_id = r.resource_id
        WHERE psc.missing_count > 0
        LIMIT 10;
    """)
    rows = cursor.fetchall()
    print("Sample: Resource patch counts by severity")
    print(f"  {'Res ID':>6} | {'Resource Name':30s} | {'Sev':>3} | {'Missing':>7} | {'Installed':>9}")
    print("  " + "-" * 65)
    for res_id, name, sev_id, missing, installed in rows:
        name_str = name[:28] if name else "Unknown"
        print(f"  {res_id:6d} | {name_str:30s} | {sev_id:3d} | {missing:7d} | {installed:9d}")
except Exception as e:
    print(f"Error: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Severity analysis complete!")
