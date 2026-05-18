import psycopg2

conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()

# Delete words without phonetic
cursor.execute("DELETE FROM vocabulary WHERE phonetic IS NULL OR phonetic = ''")
deleted = cursor.rowcount
conn.commit()

# Count remaining
cursor.execute('SELECT COUNT(*) FROM vocabulary')
remaining = cursor.fetchone()[0]

print(f'Deleted: {deleted} words without phonetic')
print(f'Remaining: {remaining} words')

conn.close()