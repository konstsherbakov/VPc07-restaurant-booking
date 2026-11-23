
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


class PostgresDriver:

    def get_connection(self):
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

    def create_tables(self):
        conn = self.get_connection()

        try:
            with conn:
                with conn.cursor() as cur:

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            phone TEXT NOT NULL
                        );
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS restaurant_tables (
                            id SERIAL PRIMARY KEY,
                            table_number INTEGER UNIQUE NOT NULL
                                CHECK (table_number > 0),
                            seats INTEGER NOT NULL
                                CHECK (seats > 0)
                        );
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS bookings (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL
                                REFERENCES users(id)
                                ON DELETE CASCADE,
                            table_id INTEGER NOT NULL
                                REFERENCES restaurant_tables(id)
                                ON DELETE CASCADE,
                            start_time TIMESTAMP NOT NULL,
                            end_time TIMESTAMP NOT NULL,
                            CHECK (end_time > start_time)
                        );
                    """)

            print("Таблицы успешно созданы!")

        finally:
            conn.close()
            print("Соединение закрыто.")


if __name__ == "__main__":
    driver = PostgresDriver()
    driver.create_tables()
