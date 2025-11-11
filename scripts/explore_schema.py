"""
Explore Patch Manager Plus database schema
Find tables related to systems, patches, policies, and deployment
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

print("Patch Manager Plus Database Schema Explorer")
print("=" * 70)

# Search for system/computer related tables
keywords_systems = ['computer', 'system', 'machine', 'resource', 'device', 'endpoint', 'agent']
keywords_patches = ['patch', 'update', 'vulnerability', 'missing', 'deployed', 'installed']
keywords_policies = ['policy', 'group', 'config', 'deployment', 'schedule']

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
all_tables = [row[0] for row in cursor.fetchall()]

def find_tables_by_keywords(tables, keywords, category):
    matches = []
    for table in tables:
        table_lower = table.lower()
        for keyword in keywords:
            if keyword in table_lower:
                matches.append(table)
                break
    return matches

# Find system tables
print("\n1. SYSTEM/COMPUTER TABLES:")
print("-" * 70)
system_tables = find_tables_by_keywords(all_tables, keywords_systems, "System")
for table in system_tables[:30]:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
    count = cursor.fetchone()[0]
    print(f"  {table:50s} ({count:,} rows)")
if len(system_tables) > 30:
    print(f"  ... and {len(system_tables) - 30} more system tables")

# Find patch tables
print("\n2. PATCH/UPDATE TABLES:")
print("-" * 70)
patch_tables = find_tables_by_keywords(all_tables, keywords_patches, "Patch")
for table in patch_tables[:30]:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
    count = cursor.fetchone()[0]
    print(f"  {table:50s} ({count:,} rows)")
if len(patch_tables) > 30:
    print(f"  ... and {len(patch_tables) - 30} more patch tables")

# Find policy tables
print("\n3. POLICY/GROUP TABLES:")
print("-" * 70)
policy_tables = find_tables_by_keywords(all_tables, keywords_policies, "Policy")
for table in policy_tables[:30]:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
    count = cursor.fetchone()[0]
    print(f"  {table:50s} ({count:,} rows)")
if len(policy_tables) > 30:
    print(f"  ... and {len(policy_tables) - 30} more policy tables")

# Look for key tables (common ME table names)
print("\n4. KEY TABLES (likely most important):")
print("-" * 70)
key_table_hints = [
    'ManagedComputer', 'Resource', 'PatchDetails', 'PatchInstalled',
    'PatchMissing', 'PatchStatus', 'ResourcePatch', 'PatchApproval',
    'DeploymentPolicy', 'ConfigData', 'SystemPatch', 'PatchHistory'
]
for hint in key_table_hints:
    matching = [t for t in all_tables if hint.lower() in t.lower()]
    if matching:
        print(f"\n  Tables matching '{hint}':")
        for table in matching[:10]:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cursor.fetchone()[0]
            print(f"    {table:48s} ({count:,} rows)")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("Schema exploration complete!")
