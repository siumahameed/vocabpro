import psycopg2
conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM vocabulary')
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE phonetic IS NOT NULL AND phonetic != ''")
with_phonetic = cursor.fetchone()[0]
print(f'Total words: {total}')
print(f'With phonetic: {with_phonetic}')
print(f'Without phonetic: {total - with_phonetic}')
cursor.execute("SELECT word, phonetic FROM vocabulary WHERE phonetic IS NOT NULL AND phonetic != ''")
print('Words with phonetic:')
for r in cursor.fetchall():
    print(f'  {r[0]} -> {r[1]}')
conn.close()