import psycopg2

conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE users ADD COLUMN achievements JSONB DEFAULT \'[]\'')
    print('Added achievements column')
except:
    print('achievements column already exists')

try:
    cursor.execute('ALTER TABLE users ADD COLUMN quiz_high_score INTEGER DEFAULT 0')
    print('Added quiz_high_score column')
except:
    print('quiz_high_score already exists')

conn.commit()
conn.close()
print('Done!')