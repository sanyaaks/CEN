import sqlite3

conn = sqlite3.connect("mospi_airfare.db")
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)

# Check if clean_fares exists and try to add column
for t in tables:
    if t[0] == "clean_fares":
        # Check existing columns
        cur.execute("PRAGMA table_info(clean_fares)")
        columns = cur.fetchall()
        col_names = [c[1] for c in columns]
        print("Existing columns:", col_names)
        
        if "tax_estimated" not in col_names:
            cur.execute("ALTER TABLE clean_fares ADD COLUMN tax_estimated BOOLEAN NOT NULL DEFAULT 1")
            conn.commit()
            print("Added tax_estimated column (defaulting existing rows to True)")
        else:
            print("tax_estimated column already exists")
        break

conn.close()
