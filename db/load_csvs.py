import sqlite3
import pandas as pd


def load_csv_to_sqlite(db_name, csv_file, table_name):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Load CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Dynamically generate SQL for creating a table
    columns = df.columns
    col_types = df.dtypes
    col_defs = []

    for col, col_type in zip(columns, col_types):
        col_quoted = f'"{col}"'  # Quote the column names
        if col_type == 'int64':
            col_defs.append(f"{col_quoted} INTEGER")
        elif col_type == 'float64':
            col_defs.append(f"{col_quoted} REAL")
        else:
            col_defs.append(f"{col_quoted} TEXT")

    col_defs_str = ", ".join(col_defs)
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs_str})'

    # Create table
    cursor.execute(create_table_sql)

    # Insert data into the table
    df.to_sql(table_name, conn, if_exists='append', index=False)

    # Commit and close connection
    conn.commit()
    conn.close()


# Example usage
db_name = 'workouts.db'
csv_file = './data/TRM.csv'
table_name = 'TRM'
load_csv_to_sqlite(db_name, csv_file, table_name)
