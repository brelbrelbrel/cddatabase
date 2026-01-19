
import sqlite3

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Add new columns if they don't exist
    columns = [
        ('discogs_listing_id', 'INTEGER'),
        ('listing_status', 'TEXT') # 'Draft', 'Listed', 'Sold', etc.
    ]
    
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE releases ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column already exists: {col_name}")
            else:
                print(f"Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
