"""
Sync Patch Compliance Data from Patch Manager Plus to Private Database

This script:
1. Connects to Patch Manager Plus database
2. Extracts comprehensive patch compliance data for all systems
3. Loads data into claude_bwagner database (replaces existing data)
4. Creates indexes for performance

Severity Levels:
- 0 = Unrated
- 1 = Low
- 2 = Moderate
- 3 = Important
- 4 = Critical
- 5 = Info
"""

import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

print("=" * 80)
print("PATCH COMPLIANCE DATA SYNC")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# STEP 1: Connect to Patch Manager Plus Database
# ============================================================================
print("STEP 1: Connecting to Patch Manager Plus database...")
try:
    pmp_conn = psycopg2.connect(
        host=os.getenv('PATCHMGR_HOST'),
        port=os.getenv('PATCHMGR_PORT'),
        user=os.getenv('PATCHMGR_USER'),
        password=os.getenv('PATCHMGR_PASSWORD'),
        database=os.getenv('PATCHMGR_DATABASE')
    )
    pmp_cursor = pmp_conn.cursor()
    print("  Connected to Patch Manager Plus!")
except Exception as e:
    print(f"  ERROR: Failed to connect to PMP database: {e}")
    exit(1)

# ============================================================================
# STEP 2: Extract Data from Patch Manager Plus
# ============================================================================
print("\nSTEP 2: Extracting patch compliance data from PMP...")

query = """
    SELECT
        mc.resource_id,
        r.name as system_name,
        r.domain_netbios_name as system_domain,
        r.resource_type,

        -- Last patch and contact dates
        to_timestamp(mc.agent_executed_on/1000) as last_contact,
        to_timestamp(pc.db_updated_time/1000) as last_patch_date,

        -- Status fields
        mc.managed_status,
        mc.agent_status,
        mc.installation_status,

        -- Overall patch counts
        pc.total_ms_patches,
        pc.missing_ms_patches,
        pc.installed_ms_patches,
        pc.total_tp_patches,
        pc.missing_tp_patches,
        pc.installed_tp_patches,
        pc.total_driver_patches,
        pc.missing_driver_patches,
        pc.installed_driver_patches,
        pc.total_bios_patches,
        pc.missing_bios_patches,
        pc.installed_bios_patches,

        -- Severity counts (missing patches by severity)
        COALESCE(psc.critical_count, 0) as missing_critical,
        COALESCE(psc.important_count, 0) as missing_important,
        COALESCE(psc.moderate_count, 0) as missing_moderate,
        COALESCE(psc.low_count, 0) as missing_low,
        COALESCE(psc.unrated_count, 0) as missing_unrated,

        -- System details
        mc.fqdn_name,
        mc.friendly_name,
        mc.agent_version,
        to_timestamp(mc.added_time/1000) as system_added_date

    FROM managedcomputer mc
    LEFT JOIN resource r ON mc.resource_id = r.resource_id
    LEFT JOIN pmresourcepatchcount pc ON mc.resource_id = pc.resource_id
    LEFT JOIN pmrespatchseveritycount psc ON mc.resource_id = psc.resource_id
    WHERE mc.managed_status = 61  -- Only managed systems
    ORDER BY r.name;
"""

try:
    pmp_cursor.execute(query)
    systems = pmp_cursor.fetchall()
    print(f"  Extracted data for {len(systems)} managed systems")
except Exception as e:
    print(f"  ERROR: Failed to extract data: {e}")
    pmp_conn.close()
    exit(1)

# ============================================================================
# STEP 3: Connect to Private Database
# ============================================================================
print("\nSTEP 3: Connecting to private database (claude_bwagner)...")
try:
    priv_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB_PRIVATE')
    )
    priv_conn.autocommit = False
    priv_cursor = priv_conn.cursor()
    print("  Connected to private database!")
except Exception as e:
    print(f"  ERROR: Failed to connect to private database: {e}")
    pmp_conn.close()
    exit(1)

# ============================================================================
# STEP 4: Create/Recreate Table
# ============================================================================
print("\nSTEP 4: Creating patch_compliance table...")

create_table_sql = """
DROP TABLE IF EXISTS patch_compliance CASCADE;

CREATE TABLE patch_compliance (
    id SERIAL PRIMARY KEY,

    -- Snapshot metadata
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- System identification
    resource_id BIGINT NOT NULL,
    system_name VARCHAR(255),
    system_domain VARCHAR(100),
    resource_type INTEGER,
    fqdn_name VARCHAR(500),
    friendly_name VARCHAR(255),

    -- Dates
    last_contact TIMESTAMP,
    last_patch_date TIMESTAMP,
    system_added_date TIMESTAMP,

    -- Status fields
    managed_status INTEGER,
    agent_status INTEGER,
    installation_status INTEGER,
    agent_version VARCHAR(50),

    -- Microsoft patches
    total_ms_patches INTEGER DEFAULT 0,
    missing_ms_patches INTEGER DEFAULT 0,
    installed_ms_patches INTEGER DEFAULT 0,

    -- Third-party patches
    total_tp_patches INTEGER DEFAULT 0,
    missing_tp_patches INTEGER DEFAULT 0,
    installed_tp_patches INTEGER DEFAULT 0,

    -- Driver patches
    total_driver_patches INTEGER DEFAULT 0,
    missing_driver_patches INTEGER DEFAULT 0,
    installed_driver_patches INTEGER DEFAULT 0,

    -- BIOS/Firmware patches
    total_bios_patches INTEGER DEFAULT 0,
    missing_bios_patches INTEGER DEFAULT 0,
    installed_bios_patches INTEGER DEFAULT 0,

    -- Missing patches by severity
    missing_critical INTEGER DEFAULT 0,
    missing_important INTEGER DEFAULT 0,
    missing_moderate INTEGER DEFAULT 0,
    missing_low INTEGER DEFAULT 0,
    missing_unrated INTEGER DEFAULT 0,

    -- Calculated totals
    missing_patches_total INTEGER GENERATED ALWAYS AS (
        missing_ms_patches + missing_tp_patches + missing_driver_patches + missing_bios_patches
    ) STORED,

    installed_patches_total INTEGER GENERATED ALWAYS AS (
        installed_ms_patches + installed_tp_patches + installed_driver_patches + installed_bios_patches
    ) STORED,

    missing_by_severity_total INTEGER GENERATED ALWAYS AS (
        missing_critical + missing_important + missing_moderate + missing_low + missing_unrated
    ) STORED,

    -- Compliance percentage (installed / total * 100)
    patch_compliance_pct DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN (total_ms_patches + total_tp_patches + total_driver_patches + total_bios_patches) > 0
            THEN (
                (installed_ms_patches + installed_tp_patches + installed_driver_patches + installed_bios_patches)::DECIMAL
                / (total_ms_patches + total_tp_patches + total_driver_patches + total_bios_patches)::DECIMAL
                * 100
            )
            ELSE 100.00
        END
    ) STORED,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_patch_compliance_system_name ON patch_compliance(system_name);
CREATE INDEX idx_patch_compliance_snapshot_date ON patch_compliance(snapshot_date);
CREATE INDEX idx_patch_compliance_last_contact ON patch_compliance(last_contact);
CREATE INDEX idx_patch_compliance_missing_total ON patch_compliance(missing_patches_total);
CREATE INDEX idx_patch_compliance_missing_critical ON patch_compliance(missing_critical);
CREATE INDEX idx_patch_compliance_compliance_pct ON patch_compliance(patch_compliance_pct);

-- Create view for easy querying
CREATE OR REPLACE VIEW patch_compliance_summary AS
SELECT
    system_name,
    system_domain,
    last_contact,
    last_patch_date,
    missing_patches_total,
    missing_ms_patches,
    missing_tp_patches,
    missing_critical,
    missing_important,
    missing_moderate,
    installed_patches_total,
    patch_compliance_pct,
    CASE
        WHEN last_contact > NOW() - INTERVAL '7 days' THEN 'Active'
        WHEN last_contact > NOW() - INTERVAL '30 days' THEN 'Stale'
        ELSE 'Inactive'
    END as contact_status,
    CASE
        WHEN missing_critical > 0 THEN 'Critical'
        WHEN missing_important > 0 THEN 'Important'
        WHEN missing_moderate > 0 THEN 'Moderate'
        WHEN missing_patches_total > 0 THEN 'Low'
        ELSE 'Compliant'
    END as risk_level
FROM patch_compliance
ORDER BY missing_critical DESC, missing_important DESC, missing_patches_total DESC;

COMMENT ON TABLE patch_compliance IS 'Patch compliance data synced from ManageEngine Patch Manager Plus';
COMMENT ON COLUMN patch_compliance.snapshot_date IS 'When this data was captured';
COMMENT ON COLUMN patch_compliance.last_contact IS 'When the system last contacted the patch server';
COMMENT ON COLUMN patch_compliance.last_patch_date IS 'When patch data was last updated for this system';
COMMENT ON COLUMN patch_compliance.missing_critical IS 'Count of missing critical severity patches';
COMMENT ON COLUMN patch_compliance.patch_compliance_pct IS 'Percentage of patches installed (installed/total * 100)';
"""

try:
    priv_cursor.execute(create_table_sql)
    priv_conn.commit()
    print("  Table and indexes created successfully!")
except Exception as e:
    print(f"  ERROR: Failed to create table: {e}")
    priv_conn.rollback()
    priv_conn.close()
    pmp_conn.close()
    exit(1)

# ============================================================================
# STEP 5: Insert Data
# ============================================================================
print("\nSTEP 5: Loading data into private database...")

insert_sql = """
    INSERT INTO patch_compliance (
        resource_id, system_name, system_domain, resource_type,
        last_contact, last_patch_date,
        managed_status, agent_status, installation_status,
        total_ms_patches, missing_ms_patches, installed_ms_patches,
        total_tp_patches, missing_tp_patches, installed_tp_patches,
        total_driver_patches, missing_driver_patches, installed_driver_patches,
        total_bios_patches, missing_bios_patches, installed_bios_patches,
        missing_critical, missing_important, missing_moderate, missing_low, missing_unrated,
        fqdn_name, friendly_name, agent_version, system_added_date
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    );
"""

try:
    inserted = 0
    for row in systems:
        priv_cursor.execute(insert_sql, row)
        inserted += 1

    priv_conn.commit()
    print(f"  Loaded {inserted} systems into database!")
except Exception as e:
    print(f"  ERROR: Failed to insert data: {e}")
    priv_conn.rollback()
    priv_conn.close()
    pmp_conn.close()
    exit(1)

# ============================================================================
# STEP 6: Generate Summary Statistics
# ============================================================================
print("\nSTEP 6: Generating summary statistics...")

try:
    # Total systems
    priv_cursor.execute("SELECT COUNT(*) FROM patch_compliance;")
    total_systems = priv_cursor.fetchone()[0]

    # Systems with missing patches
    priv_cursor.execute("SELECT COUNT(*) FROM patch_compliance WHERE missing_patches_total > 0;")
    systems_with_missing = priv_cursor.fetchone()[0]

    # Systems with critical patches
    priv_cursor.execute("SELECT COUNT(*) FROM patch_compliance WHERE missing_critical > 0;")
    systems_critical = priv_cursor.fetchone()[0]

    # Total missing patches
    priv_cursor.execute("SELECT SUM(missing_patches_total) FROM patch_compliance;")
    total_missing = priv_cursor.fetchone()[0] or 0

    # Average compliance
    priv_cursor.execute("SELECT AVG(patch_compliance_pct) FROM patch_compliance;")
    avg_compliance = priv_cursor.fetchone()[0] or 0

    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Systems:                {total_systems:,}")
    print(f"Systems with Missing Patches: {systems_with_missing:,} ({systems_with_missing/total_systems*100:.1f}%)")
    print(f"Systems with Critical Patches: {systems_critical:,} ({systems_critical/total_systems*100:.1f}%)")
    print(f"Total Missing Patches:        {total_missing:,}")
    print(f"Average Compliance:           {avg_compliance:.2f}%")

    # Top 10 systems needing patches
    print("\n" + "-" * 80)
    print("TOP 10 SYSTEMS NEEDING PATCHES")
    print("-" * 80)
    priv_cursor.execute("""
        SELECT
            system_name,
            missing_patches_total,
            missing_critical,
            missing_important,
            patch_compliance_pct
        FROM patch_compliance
        WHERE missing_patches_total > 0
        ORDER BY missing_critical DESC, missing_important DESC, missing_patches_total DESC
        LIMIT 10;
    """)

    print(f"{'System Name':40s} | {'Missing':>7s} | {'Critical':>8s} | {'Important':>9s} | {'Compliance':>10s}")
    print("-" * 80)
    for row in priv_cursor.fetchall():
        sys_name, missing, crit, imp, compliance = row
        print(f"{sys_name:40s} | {missing:7d} | {crit:8d} | {imp:9d} | {compliance:9.2f}%")

except Exception as e:
    print(f"  ERROR: Failed to generate statistics: {e}")

# ============================================================================
# Cleanup
# ============================================================================
priv_cursor.close()
priv_conn.close()
pmp_cursor.close()
pmp_conn.close()

print("\n" + "=" * 80)
print(f"SYNC COMPLETE")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print("\nData is available in table: patch_compliance")
print("Summary view available: patch_compliance_summary")
print("\nExample queries:")
print("  SELECT * FROM patch_compliance_summary;")
print("  SELECT * FROM patch_compliance WHERE missing_critical > 0;")
print("  SELECT system_name, missing_patches_total FROM patch_compliance ORDER BY missing_patches_total DESC;")
