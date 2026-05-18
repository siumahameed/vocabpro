import psycopg2
conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()
cursor.execute("SELECT word, phonetic FROM vocabulary LIMIT 10")
results = cursor.fetchall()
print('First 10 words:')
for r in results:
    print(f'  {r[0]} -> {r[1]}')
conn.close()