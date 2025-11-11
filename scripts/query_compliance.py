"""
Query patch compliance data from private database
"""

import os
from dotenv import load_dotenv
import psycopg2

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB_PRIVATE')
)
cursor = conn.cursor()

print("PATCH COMPLIANCE QUERY EXAMPLES")
print("=" * 80)

# Query 1: Summary view
print("\n1. COMPLIANCE SUMMARY (via view)")
print("-" * 80)
cursor.execute("""
    SELECT
        system_name,
        missing_patches_total,
        missing_critical,
        patch_compliance_pct,
        contact_status,
        risk_level
    FROM patch_compliance_summary
    ORDER BY missing_critical DESC, missing_patches_total DESC
    LIMIT 15;
""")

print(f"{'System':30s} | {'Missing':>7s} | {'Critical':>8s} | {'Compliance':>10s} | {'Contact':>10s} | {'Risk':>12s}")
print("-" * 90)
for row in cursor.fetchall():
    sys, missing, crit, compliance, contact, risk = row
    print(f"{sys:30s} | {missing:7d} | {crit:8d} | {compliance:9.2f}% | {contact:10s} | {risk:12s}")

# Query 2: Systems needing critical patches
print("\n\n2. SYSTEMS WITH CRITICAL PATCHES MISSING")
print("-" * 80)
cursor.execute("""
    SELECT
        system_name,
        system_domain,
        last_contact,
        missing_critical,
        missing_important,
        missing_patches_total
    FROM patch_compliance
    WHERE missing_critical > 0
    ORDER BY missing_critical DESC, missing_patches_total DESC;
""")

print(f"{'System':30s} | {'Domain':15s} | {'Last Contact':16s} | {'Crit':>4s} | {'Imp':>4s} | {'Total':>5s}")
print("-" * 90)
for row in cursor.fetchall():
    sys, domain, contact, crit, imp, total = row
    domain_str = domain[:14] if domain else "N/A"
    contact_str = contact.strftime("%Y-%m-%d %H:%M") if contact else "Never"
    print(f"{sys:30s} | {domain_str:15s} | {contact_str:16s} | {crit:4d} | {imp:4d} | {total:5d}")

# Query 3: Compliance by severity
print("\n\n3. MISSING PATCHES BY SEVERITY (Environment Totals)")
print("-" * 80)
cursor.execute("""
    SELECT
        SUM(missing_critical) as total_critical,
        SUM(missing_important) as total_important,
        SUM(missing_moderate) as total_moderate,
        SUM(missing_low) as total_low,
        SUM(missing_unrated) as total_unrated,
        SUM(missing_patches_total) as grand_total
    FROM patch_compliance;
""")

row = cursor.fetchone()
crit, imp, mod, low, unrated, total = row
print(f"Critical:  {crit:5d}")
print(f"Important: {imp:5d}")
print(f"Moderate:  {mod:5d}")
print(f"Low:       {low:5d}")
print(f"Unrated:   {unrated:5d}")
print(f"{'':10s}-------")
print(f"Total:     {total:5d}")

# Query 4: Systems by compliance percentage
print("\n\n4. SYSTEMS BY COMPLIANCE LEVEL")
print("-" * 80)
cursor.execute("""
    SELECT
        CASE
            WHEN patch_compliance_pct >= 95 THEN '95-100%'
            WHEN patch_compliance_pct >= 90 THEN '90-94%'
            WHEN patch_compliance_pct >= 80 THEN '80-89%'
            WHEN patch_compliance_pct >= 70 THEN '70-79%'
            ELSE 'Below 70%'
        END as compliance_bracket,
        COUNT(*) as system_count
    FROM patch_compliance
    GROUP BY compliance_bracket
    ORDER BY compliance_bracket DESC;
""")

print(f"{'Compliance Range':20s} | {'System Count':>12s}")
print("-" * 40)
for bracket, count in cursor.fetchall():
    print(f"{bracket:20s} | {count:12d}")

# Query 5: Recently contacted vs stale systems
print("\n\n5. SYSTEM CONTACT STATUS")
print("-" * 80)
cursor.execute("""
    SELECT
        CASE
            WHEN last_contact > NOW() - INTERVAL '7 days' THEN 'Active (< 7 days)'
            WHEN last_contact > NOW() - INTERVAL '30 days' THEN 'Stale (7-30 days)'
            WHEN last_contact > NOW() - INTERVAL '90 days' THEN 'Inactive (30-90 days)'
            ELSE 'Very Stale (> 90 days)'
        END as status,
        COUNT(*) as count
    FROM patch_compliance
    GROUP BY status
    ORDER BY status;
""")

print(f"{'Status':25s} | {'System Count':>12s}")
print("-" * 45)
for status, count in cursor.fetchall():
    print(f"{status:25s} | {count:12d}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Query complete!")
