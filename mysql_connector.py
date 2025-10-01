import pymysql
from pymysql.cursors import DictCursor
import dotenv
import os
from pathlib import Path


class MySQLDatabase:
    def __init__(self):
        dotenv.load_dotenv(Path('.env'))
        self.config = {
            'host': os.environ.get('HOST'),
            'user': os.environ.get('USER'),
            'password': os.environ.get('PASSWORD'),
            'cursorclass': DictCursor,
            'charset': 'utf8mb4',
            'database': 'sakila'
        }

    def _get_connection(self):
        return pymysql.connect(**self.config)

    def request_all(self, sql: str, params: tuple = None):
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        finally:
            connection.close()

    def request_one(self, sql: str, params: tuple = None):
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchone()
        finally:
            connection.close()

    def search_keyword(self, keyword: str):
        sql = """
            SELECT title, release_year, description
            FROM film
            WHERE title LIKE %s
            ORDER BY title
        """
        return self.request_all(sql, (f"%{keyword}%",))

    def get_genres_and_years(self):
        sql_genres = "SELECT name FROM category ORDER BY name"
        genres = [row['name'] for row in self.request_all(sql_genres)]

        sql_ranges = """
            SELECT cat.name, MIN(f.release_year) AS min_year, MAX(f.release_year) AS max_year
            FROM category AS cat
            JOIN film_category AS fcat ON cat.category_id = fcat.category_id
            JOIN film AS f ON fcat.film_id = f.film_id
            GROUP BY cat.name
            ORDER BY cat.name
        """
        genre_ranges = self.request_all(sql_ranges)

        return genres, genre_ranges

    def search_genre_and_years(self, genre: str, year_from: int, year_to: int):
        sql = """
            SELECT f.title, f.release_year, f.description
            FROM film AS f
            JOIN film_category AS fcat ON f.film_id = fcat.film_id
            JOIN category AS cat ON fcat.category_id = cat.category_id
            WHERE cat.name = %s
              AND f.release_year BETWEEN %s AND %s
            ORDER BY f.release_year, f.title
        """
        return self.request_all(sql, (genre, year_from, year_to))
