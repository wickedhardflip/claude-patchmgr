"""
Scan for open database ports on Patch Manager Plus server
Tests common PostgreSQL and MS SQL ports
"""

import socket
import sys
from dotenv import load_dotenv
import os

# Load credentials
load_dotenv('C:/Users/admbwagner/Documents/claude/.claude/credentials.env')

host = os.getenv('PATCHMGR_HOST')
user = os.getenv('PATCHMGR_USER')
password = os.getenv('PATCHMGR_PASSWORD')

print(f"Scanning {host} for database ports...")
print("-" * 60)

# Common ports for Patch Manager Plus
ports_to_test = [
    (5432, "PostgreSQL default"),
    (15432, "PMP PostgreSQL alternate"),
    (33061, "PMP PostgreSQL common"),
    (65432, "PMP PostgreSQL alternate"),
    (1433, "MS SQL Server default"),
    (3306, "MySQL/MariaDB"),
    (8383, "PMP Web Interface"),
]

open_ports = []

for port, description in ports_to_test:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"[OPEN]   Port {port:5d} - {description}")
            open_ports.append((port, description))
        else:
            print(f"[CLOSED] Port {port:5d} - {description}")
    except Exception as e:
        print(f"[ERROR]  Port {port:5d} - {description}: {e}")

print("\n" + "=" * 60)
if open_ports:
    print(f"Found {len(open_ports)} open port(s):")
    for port, desc in open_ports:
        print(f"  - Port {port}: {desc}")

    # Try connecting to open database ports
    print("\n" + "=" * 60)
    print("Testing database connections on open ports...")

    for port, desc in open_ports:
        if port == 8383:
            continue  # Skip web interface

        if "SQL" in desc or "PostgreSQL" in desc or "MySQL" in desc:
            print(f"\nTrying port {port}...")

            # Try PostgreSQL
            if "PostgreSQL" in desc or "PMP" in desc:
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        database='postgres',
                        connect_timeout=5
                    )
                    print(f"  SUCCESS! PostgreSQL connection on port {port}")
                    conn.close()
                    break
                except Exception as e:
                    print(f"  PostgreSQL failed: {str(e)[:80]}")

            # Try MS SQL
            if "SQL Server" in desc:
                try:
                    import pymssql
                    conn = pymssql.connect(
                        server=host,
                        port=port,
                        user=user,
                        password=password,
                        database='master',
                        timeout=5
                    )
                    print(f"  SUCCESS! MS SQL connection on port {port}")
                    conn.close()
                    break
                except ImportError:
                    print(f"  pymssql not installed, skipping MS SQL test")
                except Exception as e:
                    print(f"  MS SQL failed: {str(e)[:80]}")
else:
    print("No open database ports found.")
    print("\nThe database may be:")
    print("  1. Configured to only listen on localhost")
    print("  2. Behind a firewall")
    print("  3. Using a non-standard port")
    print("\nRecommendations:")
    print("  - Check if you can RDP/console to the server")
    print("  - Look for database port in PMP config files")
    print("  - Enable remote database access in PMP settings")
