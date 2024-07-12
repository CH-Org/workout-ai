-- Create a new table with the added column
CREATE TABLE IF NOT EXISTS exercises_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    pattern TEXT NOT NULL,
    new_column TEXT -- Add your new column definition here
);

-- Copy data from the old table to the new table
INSERT INTO exercises_new (id, name, description, pattern)
SELECT id, name, description, pattern
FROM exercises;

-- Drop the old table
DROP TABLE IF EXISTS exercises;

-- Rename the new table to the original table name
ALTER TABLE exercises_new RENAME TO exercises;
