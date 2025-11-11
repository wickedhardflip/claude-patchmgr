# ManageEngine Patch Manager Plus Database Reporting

Python scripts for querying and reporting on ManageEngine Patch Manager Plus database.

## Overview

This project provides direct database access to ManageEngine Patch Manager Plus for generating custom reports and extracting patch management data. Since API access is not licensed, these scripts connect directly to the PostgreSQL database for read-only reporting.

## Features

### Data Sync to Private Database ⭐ NEW!
- **Sync to PostgreSQL**: Extract all patch compliance data to your private `claude_bwagner` database
- **Comprehensive Audit Data**: System info, patch counts, severity levels, compliance percentages
- **Automated Queries**: Pre-built views and query examples
- **See**: [SYNC_GUIDE.md](SYNC_GUIDE.md) for complete documentation

### Direct PMP Reporting
- **System Inventory**: List all managed computers with status and last contact
- **Patch Compliance**: Missing/installed patch counts per system
- **Patch Status**: Overall patch status breakdown across environment
- **Recent Patches**: Track newly available patches
- **Custom Queries**: Framework for building custom reports

## Prerequisites

- Python 3.x
- Network access to Patch Manager Plus server (10.100.1.49:8028)
- Database credentials (stored in `credentials.env`)

## Installation

1. Clone this repository
2. Install required Python packages:
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

## Configuration

Database credentials are stored in `C:\Users\admbwagner\Documents\claude\.claude\credentials.env`:

```env
PATCHMGR_HOST=10.100.1.49
PATCHMGR_PORT=8028
PATCHMGR_USER=medc
PATCHMGR_PASSWORD=********
PATCHMGR_DATABASE=desktopcentral
```

**Security Note**: The `.gitignore` file prevents credentials from being committed to version control.

## Database Information

- **Type**: PostgreSQL
- **Server**: 10.100.1.49:8028
- **Database**: desktopcentral
- **Tables**: 4,433 tables total
- **Access**: Read-only (user: medc)

### Key Tables

| Table | Rows | Description |
|-------|------|-------------|
| `resource` | 2,351 | System/computer names and details |
| `managedcomputer` | 83 | Managed computer information |
| `patchdetails` | 676,074 | Available patches from all vendors |
| `affectedpatchstatus` | 8,287 | Patch status per system |
| `pmresourcepatchcount` | 106 | Patch count summaries |
| `customerpatchstatus` | 186 | Custom patch approval statuses |
| `collectiontopatch` | 2,741 | Collection-patch mappings |

## Usage

### Sync Patch Compliance Data ⭐ RECOMMENDED

Extract all patch compliance data to your private database:

```bash
python scripts/sync_patch_compliance.py
```

This creates a `patch_compliance` table in your `claude_bwagner` database with:
- All 83 managed systems
- Patch counts by type (MS, third-party, drivers, BIOS)
- Severity breakdown (Critical, Important, Moderate, Low, Unrated)
- Compliance percentages
- Last contact and patch dates
- Auto-calculated totals and indexes

**Query the synced data:**

```bash
python scripts/query_compliance.py
```

**Or use PostgreSQL directly:**

```sql
-- Connect
psql -h 10.100.4.22 -U bwagner -d claude_bwagner

-- View summary
SELECT * FROM patch_compliance_summary;

-- Systems with critical patches
SELECT system_name, missing_critical, missing_patches_total
FROM patch_compliance
WHERE missing_critical > 0
ORDER BY missing_critical DESC;
```

**See [SYNC_GUIDE.md](SYNC_GUIDE.md) for complete documentation.**

---

### Quick Connection Test

```bash
python scripts/quick_test.py
```

Verifies database connection and lists available tables.

### Generate Standard Report

```bash
python scripts/patch_report.py
```

Produces comprehensive report with:
- Systems being patched (all 83 managed computers)
- Patch counts per system (missing/installed breakdown)
- Patch status summary (Available, Ignore, Missing counts)
- Recently available patches (last 30 days)

### Explore Database Schema

```bash
python scripts/explore_schema.py
```

Searches for tables related to systems, patches, and policies with row counts.

### Examine Table Structures

```bash
python scripts/examine_key_tables.py
```

Shows column definitions and sample data from key tables.

## Scripts

### `scripts/quick_test.py`
Basic connection test that verifies database access and lists tables.

### `scripts/patch_report.py`
Main reporting script generating comprehensive patch management reports.

### `scripts/explore_schema.py`
Schema exploration tool for finding relevant tables by keyword search.

### `scripts/examine_key_tables.py`
Detailed table structure examination showing columns and sample data.

### `scripts/test_connection.py`
Advanced connection tester with database discovery features.

### `scripts/find_db_port.py`
Port scanner for locating database services on the server.

## Report Examples

### Systems Report
```
    ID | Computer Name                            | Type       | Last Contact
  1807 | ADAUDIT                                  | 1          | 2025-11-10 16:10
  2730 | CTXBASEIMG19                             | 1          | 2025-11-09 00:01
  ...
Total systems: 83
```

### Patch Counts Report
```
Computer Name                            |  Missing MS | Installed MS |  Missing TP |  Total Missing
VeeamDS                                  |          53 |         1052 |          14 |             67
CTXITJUMP22-01                           |           5 |            8 |           6 |             11
...
```

### Patch Status Summary
```
Status               |  Status ID |      Count
Available            |        201 |      7,342
Ignore               |        201 |        693
Missing              |        202 |         61
```

## Creating Custom Reports

To create a new custom report:

1. Copy `patch_report.py` as a template
2. Load credentials using the same pattern:
   ```python
   from dotenv import load_dotenv
   import os

   load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

   conn = psycopg2.connect(
       host=os.getenv('PATCHMGR_HOST'),
       port=os.getenv('PATCHMGR_PORT'),
       user=os.getenv('PATCHMGR_USER'),
       password=os.getenv('PATCHMGR_PASSWORD'),
       database=os.getenv('PATCHMGR_DATABASE')
   )
   ```
3. Write your custom SQL queries
4. Format and display results

## Common Queries

### List All Managed Computers
```sql
SELECT r.resource_id, r.name, mc.managed_status
FROM managedcomputer mc
JOIN resource r ON mc.resource_id = r.resource_id
WHERE mc.managed_status = 61;
```

### Missing Patches Per System
```sql
SELECT r.name, pc.missing_ms_patches, pc.missing_tp_patches
FROM pmresourcepatchcount pc
JOIN resource r ON pc.resource_id = r.resource_id
WHERE (pc.missing_ms_patches + pc.missing_tp_patches) > 0
ORDER BY (pc.missing_ms_patches + pc.missing_tp_patches) DESC;
```

### Patch Details
```sql
SELECT patchid, description, to_timestamp(releasedtime/1000) as release_date
FROM patchdetails
WHERE releasedtime > EXTRACT(EPOCH FROM NOW() - INTERVAL '30 days') * 1000
ORDER BY releasedtime DESC;
```

## Patch Status Codes

| Status | Status ID | Description |
|--------|-----------|-------------|
| Available | 201 | Patch is available but not installed |
| Ignore | 201/202 | Patch has been marked to ignore |
| Missing | 202 | Patch is missing and needs attention |

## Security

- **Read-only access**: Database user `medc` has read-only permissions
- **Credential management**: Passwords stored securely in `credentials.env`
- **Network security**: Database accessible only from authorized network
- **No password display**: Scripts never echo or display credentials

## Troubleshooting

### Connection Timeout
If connection times out:
1. Verify network connectivity: `ping 10.100.1.49`
2. Test port accessibility: `Test-NetConnection -ComputerName 10.100.1.49 -Port 8028`
3. Confirm database service is running

### Authentication Failed
If authentication fails:
1. Verify credentials in `credentials.env`
2. Check database user account status
3. Confirm password hasn't changed

### No Data Returned
If queries return no data:
1. Verify table names (case-sensitive)
2. Check table has data: `SELECT COUNT(*) FROM tablename;`
3. Review WHERE clause conditions

## Slash Command

Use `/patchmgr` in Claude Code to get context-specific help for patch reporting tasks.

## Project Structure

```
claude-patchmgr/
├── .claude/
│   └── commands/
│       └── patchmgr.md          # Slash command definition
├── scripts/
│   ├── quick_test.py            # Connection test
│   ├── patch_report.py          # Main reporting script
│   ├── explore_schema.py        # Schema exploration
│   ├── examine_key_tables.py    # Table structure examination
│   ├── test_connection.py       # Advanced connection test
│   └── find_db_port.py          # Port scanner
├── .env.example                 # Example credentials file
├── .gitignore                   # Git exclusions
└── README.md                    # This file
```

## Environment

- **Server**: Patch Manager Plus at 10.100.1.49
- **Database**: PostgreSQL on port 8028
- **Python**: 3.x
- **Platform**: Windows (Citrix environment)

## Future Enhancements

Potential future additions:
- CSV export functionality
- Excel report generation
- Email report distribution
- Automated scheduling
- Dashboard visualization
- Integration with ticketing systems
- Compliance reporting
- Historical trend analysis

## License

Internal tool for IT operations. Not for redistribution.

## Support

For issues or questions:
- Check troubleshooting section above
- Review ManageEngine Patch Manager Plus documentation
- Verify database connectivity and credentials

## Contributors

- Built with Claude Code AI assistant
- Maintained by IT Operations team

---

**Last Updated**: 2025-11-11
**Version**: 1.0
