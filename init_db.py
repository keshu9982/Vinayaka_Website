import sqlite3

conn = sqlite3.connect('database.db')  # Make sure this matches your app
cursor = conn.cursor()

# Create company_info table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS company_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        email TEXT,
        phone TEXT,
        logo TEXT
    )
''')

# Optional: Insert default company info
cursor.execute('''
    INSERT INTO company_info (name, address, email, phone, logo)
    VALUES (?, ?, ?, ?, ?)
''', (
    'My Company', '123 Business St', 'info@mycompany.com', '1234567890', 'logo.png'
))

conn.commit()
conn.close()

print("company_info table created and initialized.")
