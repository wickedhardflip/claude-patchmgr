"""
Examine structure of key Patch Manager tables
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

print("Examining Key Patch Manager Tables")
print("=" * 80)

# Key tables to examine
tables_to_examine = [
    ('managedcomputer', 'Systems/Computers being managed'),
    ('patchdetails', 'Available patches'),
    ('affectedpatchstatus', 'Patch status per system'),
    ('customerpatchstatus', 'Custom patch statuses'),
    ('pmresourcepatchcount', 'Patch counts per resource'),
    ('collectiontopatch', 'Collection-patch mappings'),
]

for table_name, description in tables_to_examine:
    print(f"\n{table_name.upper()} - {description}")
    print("-" * 80)

    # Get column information
    cursor.execute(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()

    print(f"  Columns ({len(columns)} total):")
    for col_name, data_type, max_length in columns:
        type_str = f"{data_type}"
        if max_length:
            type_str += f"({max_length})"
        print(f"    - {col_name:40s} {type_str}")

    # Get sample data
    print(f"\n  Sample data (first 3 rows):")
    try:
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 3;')
        rows = cursor.fetchall()
        if rows:
            # Show column headers
            col_names = [desc[0] for desc in cursor.description]
            print(f"    Columns: {', '.join(col_names[:10])}")  # Show first 10 columns
            if len(col_names) > 10:
                print(f"             ... and {len(col_names) - 10} more columns")

            for i, row in enumerate(rows, 1):
                print(f"    Row {i}: {str(row[:5])[:120]}...")  # Show first 5 values, truncated
        else:
            print("    (no data)")
    except Exception as e:
        print(f"    Error reading sample data: {e}")

# Now examine managedcomputer in detail
print("\n\n" + "=" * 80)
print("DETAILED ANALYSIS: MANAGEDCOMPUTER TABLE")
print("=" * 80)

cursor.execute("""
    SELECT
        resource_id,
        resource_name,
        domain_netbios_name,
        branch_office_id,
        customer_id
    FROM managedcomputer
    LIMIT 10;
""")

print("\nSample managed computers:")
for row in cursor.fetchall():
    print(f"  ID: {row[0]:5d} | Name: {row[1]:30s} | Domain: {str(row[2]):20s}")

# Check affectedpatchstatus
print("\n\n" + "=" * 80)
print("DETAILED ANALYSIS: AFFECTEDPATCHSTATUS TABLE")
print("=" * 80)

cursor.execute("""
    SELECT
        patch_id,
        resource_id,
        status_id,
        severity_id
    FROM affectedpatchstatus
    LIMIT 10;
""")

print("\nSample patch status records:")
for row in cursor.fetchall():
    print(f"  Patch: {row[0]:8d} | Resource: {row[1]:5d} | Status: {row[2]:3d} | Severity: {row[3]}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Examination complete!")
