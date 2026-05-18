import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()
cursor.execute('SELECT word, phonetic FROM vocabulary WHERE phonetic IS NOT NULL AND phonetic != \'\' ORDER BY id DESC LIMIT 10')
print('Words with phonetic:')
for r in cursor.fetchall():
    print(f'{r[0]} -> {r[1]}')
conn.close()