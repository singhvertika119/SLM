import sqlite3

def create_database():
    # Connect to (and create) the database file
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Create a simple table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            item_name TEXT,
            quantity INTEGER,
            price REAL
        )
    ''')

    # Clear old data if you run this multiple times
    cursor.execute('DELETE FROM inventory')

    # Insert some dummy hardware stock
    dummy_data = [
        ('NVIDIA RTX 4090', 12, 1599.99),
        ('AMD Ryzen 9 7950X', 45, 599.00),
        ('Corsair 32GB RAM', 120, 114.99),
        ('Samsung 2TB SSD', 85, 169.50)
    ]
    
    cursor.executemany('INSERT INTO inventory (item_name, quantity, price) VALUES (?, ?, ?)', dummy_data)
    conn.commit()
    conn.close()
    
    print("Successfully created inventory.db with dummy data!")

if __name__ == "__main__":
    create_database()