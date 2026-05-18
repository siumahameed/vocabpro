import psycopg2

conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
cursor = conn.cursor()

# Add progress tracking columns
try:
    cursor.execute('ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0')
    print('Added streak_days')
except:
    print('streak_days already exists')

try:
    cursor.execute('ALTER TABLE users ADD COLUMN last_active_date DATE')
    print('Added last_active_date')
except:
    print('last_active_date already exists')

try:
    cursor.execute('ALTER TABLE users ADD COLUMN total_words_sent INTEGER DEFAULT 0')
    print('Added total_words_sent')
except:
    print('total_words_sent already exists')

conn.commit()
conn.close()
print('Done!')