"""
Patch Manager Plus Reporting Script
Generates reports on systems, patches, and compliance
"""

import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import csv

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

print("Patch Manager Plus Reports")
print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 80)

# First, find the resource table with names
print("\n1. FINDING RESOURCE NAMES TABLE...")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE '%resource%'
    AND table_name NOT LIKE '%extn'
    ORDER BY table_name
    LIMIT 20;
""")
resource_tables = [row[0] for row in cursor.fetchall()]
print(f"Found resource tables: {', '.join(resource_tables[:10])}")

# Try to find resource name column
for table in ['resource', 'adresource', 'managedcomputer']:
    try:
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}'
            AND (column_name LIKE '%name%' OR column_name LIKE '%computer%')
            ORDER BY column_name;
        """)
        cols = [row[0] for row in cursor.fetchall()]
        if cols:
            print(f"  {table}: {', '.join(cols)}")
    except:
        pass

# REPORT 1: Systems Summary
print("\n\n" + "=" * 80)
print("REPORT 1: SYSTEMS BEING PATCHED")
print("=" * 80)

try:
    # Try to get system names from resource table if it exists
    cursor.execute("""
        SELECT
            mc.resource_id,
            r.name as resource_name,
            r.resource_type,
            mc.managed_status,
            mc.agent_status,
            to_timestamp(mc.agent_executed_on/1000) as last_contact
        FROM managedcomputer mc
        LEFT JOIN resource r ON mc.resource_id = r.resource_id
        WHERE mc.managed_status = 61
        ORDER BY r.name
        LIMIT 100;
    """)

    print(f"\n{'ID':>6} | {'Computer Name':40s} | {'Type':10s} | {'Last Contact':20s}")
    print("-" * 90)

    systems = cursor.fetchall()
    for row in systems:
        res_id, name, res_type, status, agent_status, last_contact = row
        name_str = name if name else f"Unknown (ID: {res_id})"
        type_str = str(res_type) if res_type else "Unknown"
        contact_str = last_contact.strftime("%Y-%m-%d %H:%M") if last_contact else "Never"
        print(f"{res_id:6d} | {name_str:40s} | {type_str:10s} | {contact_str:20s}")

    print(f"\nTotal systems: {len(systems)}")

except Exception as e:
    print(f"Error getting system details: {e}")
    # Fallback to just managed computer
    cursor.execute("SELECT COUNT(*) FROM managedcomputer WHERE managed_status = 61;")
    count = cursor.fetchone()[0]
    print(f"Total managed computers: {count}")

# REPORT 2: Patch Counts Per System
print("\n\n" + "=" * 80)
print("REPORT 2: PATCH COUNTS PER SYSTEM")
print("=" * 80)

try:
    cursor.execute("""
        SELECT
            pc.resource_id,
            r.name as resource_name,
            pc.missing_ms_patches,
            pc.installed_ms_patches,
            pc.missing_tp_patches,
            pc.installed_tp_patches,
            (pc.missing_ms_patches + pc.missing_tp_patches) as total_missing
        FROM pmresourcepatchcount pc
        LEFT JOIN resource r ON pc.resource_id = r.resource_id
        WHERE (pc.missing_ms_patches + pc.missing_tp_patches) > 0
        ORDER BY total_missing DESC
        LIMIT 20;
    """)

    print(f"\n{'Computer Name':40s} | {'Missing MS':>11s} | {'Installed MS':>12s} | {'Missing TP':>11s} | {'Total Missing':>14s}")
    print("-" * 100)

    for row in cursor.fetchall():
        res_id, name, miss_ms, inst_ms, miss_tp, inst_tp, total_miss = row
        name_str = name if name else f"Unknown (ID: {res_id})"
        print(f"{name_str:40s} | {miss_ms:11d} | {inst_ms:12d} | {miss_tp:11d} | {total_miss:14d}")

except Exception as e:
    print(f"Error: {e}")

# REPORT 3: Patch Status Summary
print("\n\n" + "=" * 80)
print("REPORT 3: PATCH STATUS SUMMARY")
print("=" * 80)

try:
    cursor.execute("""
        SELECT
            status,
            status_id,
            COUNT(*) as count
        FROM affectedpatchstatus
        GROUP BY status, status_id
        ORDER BY count DESC;
    """)

    print(f"\n{'Status':20s} | {'Status ID':>10s} | {'Count':>10s}")
    print("-" * 45)

    for status, status_id, count in cursor.fetchall():
        print(f"{status:20s} | {status_id:10d} | {count:10,d}")

except Exception as e:
    print(f"Error: {e}")

# REPORT 4: Recently Added Patches
print("\n\n" + "=" * 80)
print("REPORT 4: RECENTLY AVAILABLE PATCHES (Last 30 days)")
print("=" * 80)

try:
    cursor.execute("""
        SELECT
            patchid,
            description,
            to_timestamp(releasedtime/1000) as release_date
        FROM patchdetails
        WHERE releasedtime > EXTRACT(EPOCH FROM NOW() - INTERVAL '30 days') * 1000
        ORDER BY releasedtime DESC
        LIMIT 20;
    """)

    print(f"\n{'Patch ID':>10s} | {'Release Date':15s} | {'Description':50s}")
    print("-" * 80)

    for patch_id, desc, release_date in cursor.fetchall():
        desc_short = desc[:47] + "..." if len(desc) > 50 else desc
        date_str = release_date.strftime("%Y-%m-%d") if release_date else "Unknown"
        print(f"{patch_id:10d} | {date_str:15s} | {desc_short:50s}")

except Exception as e:
    print(f"Error: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Report generation complete!")
