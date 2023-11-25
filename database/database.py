import psycopg2



def init_db():
    conn = psycopg2.connect(user="postgres",
                                password="WnKa1g_-kJI",
                                host="127.0.0.1",
                                port="57325",
                                database="book_bot")

    cursor = conn.cursor()
    cursor.execute("SELECT user_id, page_number FROM pages")

    conn.commit()
    return conn, cursor

def add_user(cursor, conn, user_id):
    cursor.execute('INSERT INTO pages (user_id, page_number) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING', (user_id, 0))
    conn.commit()
