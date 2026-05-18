import sqlite3
import psycopg2

# Get SQLite data
sqlite_conn = sqlite3.connect('vocabpro.db')
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute('SELECT word, phonetic, meaning_bn, example, category FROM vocabulary')
words = sqlite_cursor.fetchall()
print(f'SQLite: {len(words)} words')
sqlite_conn.close()

# Insert into PostgreSQL
pg_conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
pg_cursor = pg_conn.cursor()

# Check existing words
pg_cursor.execute('SELECT word FROM vocabulary')
existing = set(r[0].lower() for r in pg_cursor.fetchall())
print(f'PostgreSQL: {len(existing)} existing words')

# Insert new words
inserted = 0
for word, phonetic, meaning_bn, example, category in words:
    if word.lower() not in existing:
        pg_cursor.execute(
            'INSERT INTO vocabulary (word, phonetic, meaning_bn, example, category) VALUES (%s, %s, %s, %s, %s)',
            (word, phonetic, meaning_bn, example, category)
        )
        inserted += 1

pg_conn.commit()
print(f'Inserted {inserted} new words')

# Verify
pg_cursor.execute('SELECT COUNT(*) FROM vocabulary')
print(f'Total in PostgreSQL: {pg_cursor.fetchone()[0]}')

pg_conn.close()