import psycopg2

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host='dpg-d84d9st8nd3s73cvll00-a.virginia-postgres.render.com',
    port='5432',
    database='db_tjz5',
    user='pgres',
    password='t5nzKAPql0vKUi5si7DAbEybCSaYuYfl'
)
pg_cursor = pg_conn.cursor()

# Add phonetic data for common words
phonetic_data = {
    'Ubiquitous': 'yoo-BIK-wi-tuhs',
    'Pragmatic': 'prag-MAT-ik',
    'Eloquent': 'EL-uh-kwuhnt',
    'Benevolent': 'buh-NEV-uh-luhnt',
    'Ambiguous': 'am-BIG-yoo-uhs',
    'Meticulous': 'muh-TIK-yoo-luhs',
    'Resilient': 'ri-ZIL-yuhnt',
    'Innovative': 'IN-uh-vay-tiv',
    'Substantial': 'suhb-STAN-shuhl',
    'Ephemeral': 'i-FEM-er-uhl',
    'Diligent': 'DIL-uh-juhnt',
    'Ubiquitous': 'yoo-BIK-wi-tuhs',
    'Friendly': 'FREND-lee',
    'Abundant': 'uh-BUHN-duhnt',
    'Allocate': 'AL-uh-wayt',
    'Catalyst': 'KAT-uh-list',
    'Deprecated': 'DEP-ruh-kay-tid',
    'Elusive': 'i-LOO-siv',
    'Formulate': 'FOR-myoo-layt',
    'Generate': 'JEN-uh-rayt',
    'Hypothesis': 'hy-POTH-uh-sis',
    'Inherent': 'in-HER-uhnt',
    'Justify': 'JUS-tuh-fy',
    'Migrate': 'MY-grayt',
    'Notorious': 'noh-TOR-ee-uhs',
    'Optimistic': 'op-tuh-MIS-tik',
    'Perspective': 'per-SPEK-tiv',
    'Quantitative': 'KWAHN-tuh-tay-tiv',
    'Robust': 'roh-BUHST',
    'Scrutinize': 'SKROO-tuh-nyz',
    'Sustainable': 'suh-STAY-nuh-buhl',
    'Transient': 'TRAN-zee-uhnt',
    'Vulnerable': 'VUL-ner-uh-buhl',
}

# Update phonetic values
updated = 0
for word, phonetic in phonetic_data.items():
    pg_cursor.execute(
        "UPDATE vocabulary SET phonetic = %s WHERE LOWER(word) = LOWER(%s) AND (phonetic IS NULL OR phonetic = '')",
        (phonetic, word)
    )
    if pg_cursor.rowcount > 0:
        updated += 1

pg_conn.commit()
print(f'Updated {updated} words with phonetic data')

# Verify
pg_cursor.execute("SELECT word, phonetic FROM vocabulary WHERE phonetic IS NOT NULL AND phonetic != '' LIMIT 5")
for r in pg_cursor.fetchall():
    print(f'  {r[0]} -> {r[1]}')

pg_conn.close()