import sqlite3

conn = sqlite3.connect("mospi_airfare.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(index_values)")
columns = cur.fetchall()
col_names = [c[1] for c in columns]
print("IndexValue existing columns:", col_names)

if "base_period_is_real_data" not in col_names:
    cur.execute("ALTER TABLE index_values ADD COLUMN base_period_is_real_data BOOLEAN NOT NULL DEFAULT 1")
    conn.commit()
    print("Added base_period_is_real_data column to index_values.")
else:
    print("base_period_is_real_data column already exists.")

conn.close()
