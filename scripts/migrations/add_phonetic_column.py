import os
import psycopg2

try:
    conn = psycopg2.connect(
        host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
        port='5432',
        database='db_tjz5',
        user='pgres',
        password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
    )
    print('PostgreSQL connected!')
    
    cursor = conn.cursor()
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'vocabulary'")
    cols = cursor.fetchall()
    print('Columns:', [c[0] for c in cols])
    
    col_names = [c[0] for c in cols]
    if 'phonetic' not in col_names:
        cursor.execute('ALTER TABLE vocabulary ADD COLUMN phonetic VARCHAR(100)')
        conn.commit()
        print('Added phonetic column')
    else:
        print('phonetic column already exists')
        
    conn.close()
except Exception as e:
    print('Error:', e)