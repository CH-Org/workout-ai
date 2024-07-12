import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('workouts.db')

# Create a cursor object
c = conn.cursor()

# Read the schema from the file
with open('exercises.schema.sql', 'r') as f:
    schema = f.read()

# Execute the schema
c.executescript(schema)

# Commit the changes
conn.commit()

# Close the connection
conn.close()
