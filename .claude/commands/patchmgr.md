# Patch Manager Plus Reporting Command

You are assisting with ManageEngine Patch Manager Plus database reporting.

## Database Connection

The Patch Manager Plus database is accessible at:
- **Host**: 10.100.1.49
- **Port**: 8028
- **Database**: desktopcentral
- **User**: medc (read-only access)
- **Credentials**: Stored in `C:\Users\admbwagner\Documents\claude\.claude\credentials.env`

## Available Scripts

All scripts are located in `C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\`:

1. **quick_test.py** - Test database connection
2. **explore_schema.py** - Explore database schema and find tables
3. **examine_key_tables.py** - Examine key table structures
4. **patch_report.py** - Generate comprehensive patch reports

## Key Database Tables

- **resource** - System/computer names and details
- **managedcomputer** - Managed computer information (83 systems)
- **patchdetails** - Available patches (676,074 patches)
- **affectedpatchstatus** - Patch status per system
- **pmresourcepatchcount** - Patch count summaries per resource
- **customerpatchstatus** - Custom patch statuses
- **collectiontopatch** - Collection-patch mappings

## Common Tasks

### Run Standard Patch Report
```bash
python "C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\patch_report.py"
```

### Test Database Connection
```bash
python "C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\quick_test.py"
```

### Explore Schema
```bash
python "C:\Users\admbwagner\Documents\claude\claude-patchmgr\scripts\explore_schema.py"
```

## Report Sections

The standard patch report includes:
1. **Systems Being Patched** - List of all managed computers with last contact time
2. **Patch Counts Per System** - Missing/installed patches by system
3. **Patch Status Summary** - Overall patch status breakdown
4. **Recently Available Patches** - Patches added in last 30 days

## Security Notes

- **Never display passwords** in output or commands
- Credentials are loaded from environment file
- Database user has read-only access
- All credentials are stored securely in `credentials.env`

## When User Requests Patch Information

1. Ask what specific information they need
2. Run appropriate report script
3. Offer to create custom queries if needed
4. Suggest exporting to CSV if they want to analyze data further

## Creating Custom Reports

If the user needs custom data, create a new Python script in the `scripts/` directory that:
1. Loads credentials from the shared credentials.env
2. Connects to the database
3. Runs custom SQL queries
4. Formats output appropriately
5. Follows the pattern from existing scripts

Remember: This is a **read-only** database connection for reporting purposes only.
