# Patch Compliance Data Sync Guide

## Overview

The `sync_patch_compliance.py` script extracts comprehensive patch compliance data from ManageEngine Patch Manager Plus and loads it into your private PostgreSQL database (`claude_bwagner`) for analysis, reporting, and auditing.

## What Gets Synced

### System Information
- System name, domain, and FQDN
- Resource ID (PMP identifier)
- Agent status and contact information
- System added date

### Patch Counts
Broken down by type:
- **Microsoft patches** (total, missing, installed)
- **Third-party patches** (total, missing, installed)
- **Driver patches** (total, missing, installed)
- **BIOS/Firmware patches** (total, missing, installed)

### Severity Breakdown
Missing patches categorized by severity:
- **Critical** (Severity 4)
- **Important** (Severity 3)
- **Moderate** (Severity 2)
- **Low** (Severity 1)
- **Unrated** (Severity 0)

### Audit Fields
- **Snapshot date** - When the data was captured
- **Last contact** - When system last checked in
- **Last patch date** - When patch data was last updated
- **Compliance percentage** - Auto-calculated (installed/total × 100)

## Database Schema

### Main Table: `patch_compliance`

```sql
-- System identification
resource_id BIGINT
system_name VARCHAR(255)
system_domain VARCHAR(100)
fqdn_name VARCHAR(500)

-- Status and dates
last_contact TIMESTAMP
last_patch_date TIMESTAMP
managed_status INTEGER
agent_status INTEGER

-- Microsoft patches
total_ms_patches INTEGER
missing_ms_patches INTEGER
installed_ms_patches INTEGER

-- Third-party patches
total_tp_patches INTEGER
missing_tp_patches INTEGER
installed_tp_patches INTEGER

-- Driver patches
total_driver_patches INTEGER
missing_driver_patches INTEGER
installed_driver_patches INTEGER

-- BIOS patches
total_bios_patches INTEGER
missing_bios_patches INTEGER
installed_bios_patches INTEGER

-- Severity counts (missing)
missing_critical INTEGER
missing_important INTEGER
missing_moderate INTEGER
missing_low INTEGER
missing_unrated INTEGER

-- Calculated fields (auto-generated)
missing_patches_total INTEGER
installed_patches_total INTEGER
missing_by_severity_total INTEGER
patch_compliance_pct DECIMAL(5,2)
```

### Summary View: `patch_compliance_summary`

Simplified view with calculated risk levels:
- **Risk Level**: Critical, Important, Moderate, Low, or Compliant
- **Contact Status**: Active, Stale, or Inactive

## Usage

### Running the Sync

```bash
python "C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\sync_patch_compliance.py"
```

**What happens:**
1. Connects to Patch Manager Plus database
2. Extracts data for all 83 managed systems
3. Drops and recreates the `patch_compliance` table
4. Loads all current data
5. Creates indexes for performance
6. Displays summary statistics

**Runtime**: ~2-3 seconds

### Querying the Data

#### Use the built-in query script:
```bash
python "C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\query_compliance.py"
```

#### Or connect directly to PostgreSQL:
```bash
psql -h 10.100.4.22 -U bwagner -d claude_bwagner
```

## Example Queries

### 1. Systems with Critical Patches
```sql
SELECT
    system_name,
    missing_critical,
    missing_patches_total,
    patch_compliance_pct,
    last_contact
FROM patch_compliance
WHERE missing_critical > 0
ORDER BY missing_critical DESC, missing_patches_total DESC;
```

### 2. Compliance Summary
```sql
SELECT * FROM patch_compliance_summary
ORDER BY missing_critical DESC, missing_patches_total DESC;
```

### 3. Systems Below 90% Compliance
```sql
SELECT
    system_name,
    patch_compliance_pct,
    missing_patches_total,
    installed_patches_total
FROM patch_compliance
WHERE patch_compliance_pct < 90
ORDER BY patch_compliance_pct ASC;
```

### 4. Environment-Wide Severity Totals
```sql
SELECT
    SUM(missing_critical) as critical,
    SUM(missing_important) as important,
    SUM(missing_moderate) as moderate,
    SUM(missing_low) as low,
    SUM(missing_patches_total) as total_missing
FROM patch_compliance;
```

### 5. Stale Systems (No Contact in 7+ Days)
```sql
SELECT
    system_name,
    last_contact,
    AGE(NOW(), last_contact) as time_since_contact,
    missing_patches_total
FROM patch_compliance
WHERE last_contact < NOW() - INTERVAL '7 days'
ORDER BY last_contact ASC;
```

### 6. Top 10 Systems Needing Attention
```sql
SELECT
    system_name,
    missing_patches_total,
    missing_critical,
    missing_important,
    patch_compliance_pct
FROM patch_compliance
WHERE missing_patches_total > 0
ORDER BY
    missing_critical DESC,
    missing_important DESC,
    missing_patches_total DESC
LIMIT 10;
```

## Indexes

The following indexes are automatically created for performance:

- `idx_patch_compliance_system_name` - Fast lookup by system name
- `idx_patch_compliance_snapshot_date` - Historical tracking
- `idx_patch_compliance_last_contact` - Find stale systems
- `idx_patch_compliance_missing_total` - Sort by missing patches
- `idx_patch_compliance_missing_critical` - Prioritize critical patches
- `idx_patch_compliance_compliance_pct` - Compliance reports

## Current Statistics

**As of last sync:**
- **Total Systems**: 83
- **Systems with Missing Patches**: 78 (94.0%)
- **Systems with Critical Patches**: 10 (12.0%)
- **Total Missing Patches**: 252
- **Average Compliance**: 93.03%

**Missing Patches by Severity:**
- Critical: 19
- Important: 111
- Moderate: 104
- Low: 3
- Unrated: 15

## Sync Strategy

### Current: Replace on Each Run
The script currently **drops and recreates** the table on each run, replacing all data with the current snapshot. This ensures data is always fresh and eliminates stale records.

**Advantages:**
- Always current data
- No duplicate records
- Simple to maintain
- Fast (2-3 seconds)

**Disadvantages:**
- No historical tracking
- Can't see trends over time

### Future: Historical Tracking (Optional)

If you want to track changes over time, modify the script to:
1. Keep the table
2. Add new records with `snapshot_date`
3. Query by date to see trends

Example historical query:
```sql
SELECT
    snapshot_date::DATE as date,
    COUNT(*) as total_systems,
    AVG(patch_compliance_pct) as avg_compliance,
    SUM(missing_critical) as critical_patches
FROM patch_compliance
GROUP BY snapshot_date::DATE
ORDER BY date DESC;
```

## Scheduling Automated Syncs

### Option 1: Windows Task Scheduler
Create a scheduled task to run daily:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `"C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\sync_patch_compliance.py"`
5. Save task

### Option 2: Manual Sync
Run whenever you need current data:
```bash
python scripts/sync_patch_compliance.py
```

## Troubleshooting

### Connection Timeouts
**Problem**: Script times out connecting to PMP database
**Solution**: Verify network connectivity and database service:
```bash
ping 10.100.1.49
Test-NetConnection -ComputerName 10.100.1.49 -Port 8028
```

### Missing Data
**Problem**: Some systems show NULL values
**Cause**: Systems may not have patch count data yet
**Solution**: Wait for systems to complete their next patch scan

### Slow Queries
**Problem**: Queries take too long
**Solution**: Indexes should make queries fast. If slow:
```sql
-- Rebuild indexes
REINDEX TABLE patch_compliance;

-- Analyze table
ANALYZE patch_compliance;
```

## Security

- **Read-only PMP access**: User `medc` can only read, not modify
- **Credentials secured**: Stored in `credentials.env`, not in code
- **Private database**: Data synced to your private `claude_bwagner` database
- **No passwords in output**: Script never displays credentials

## Integration Examples

### Power BI / Tableau
Connect to PostgreSQL and query `patch_compliance_summary`:
- Host: 10.100.4.22
- Database: claude_bwagner
- Table: patch_compliance_summary

### Python Reports
```python
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host='10.100.4.22',
    database='claude_bwagner',
    user='bwagner',
    password='***'
)

df = pd.read_sql(
    "SELECT * FROM patch_compliance_summary",
    conn
)

# Generate Excel report
df.to_excel('patch_compliance_report.xlsx', index=False)
```

### Email Alerts
Create a script to email when critical patches are detected:
```python
import smtplib
from email.message import EmailMessage

# Query for critical patches
cursor.execute("""
    SELECT system_name, missing_critical
    FROM patch_compliance
    WHERE missing_critical > 0
""")

systems = cursor.fetchall()

if systems:
    # Send email alert
    msg = EmailMessage()
    msg['Subject'] = f'ALERT: {len(systems)} systems with critical patches'
    msg['From'] = 'patchmanager@company.com'
    msg['To'] = 'it-team@company.com'
    # ... send email
```

## Support

For questions or issues:
1. Check this guide
2. Review `sync_patch_compliance.py` script comments
3. Check main README.md

---

**Last Updated**: 2025-11-11
**Database**: claude_bwagner
**Table**: patch_compliance
**View**: patch_compliance_summary
