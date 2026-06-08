import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Update the database to point to your local files
cursor.execute("UPDATE products SET image_url = '/static/images/1.jpg' WHERE id = 1")
cursor.execute("UPDATE products SET image_url = '/static/images/2.jpg' WHERE id = 2")
cursor.execute("UPDATE products SET image_url = '/static/images/3.jpg' WHERE id = 3")
cursor.execute("UPDATE products SET image_url = '/static/images/4.jpg' WHERE id = 4")

conn.commit()
conn.close()

print("Database updated! Products now point to your local images.")