import pymysql
from pymysql.cursors import DictCursor
import dotenv
import os
from pathlib import Path

def get_connection():
    dotenv.load_dotenv(Path('.env'))
    config = {'host': os.environ.get('HOST'),
              'user': os.environ.get('USER'),
              'password': os.environ.get('PASSWORD'),
              'cursorclass': DictCursor,
              'charset': 'utf8mb4',
              'database': 'sakila'}
    return pymysql.connect(**config)


def search_keyword(keyword, offset=0, limit=10):
    connection = get_connection()
    cursor = connection.cursor()
    request = """
        SELECT title, release_year, description
        FROM film
        WHERE title LIKE %s
        ORDER BY title
        LIMIT %s OFFSET %s
    """
    cursor.execute(request, (f"%{keyword}%", limit, offset))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results


def get_genres_and_years():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM category ORDER BY name")
    genres = [row['name'] for row in cursor.fetchall()]

    cursor.execute("SELECT MIN(release_year), MAX(release_year) FROM film")
    result = cursor.fetchone()
    min_year = result['MIN(release_year)']
    max_year = result['MAX(release_year)']
    cursor.close()
    connection.close()
    return genres, min_year, max_year


def search_genre_and_years(genre, year_from, year_to, offset=0, limit=10):
    connection = get_connection()
    cursor = connection.cursor()
    request = """
        SELECT f.title, f.release_year, f.description
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE c.name = %s AND f.release_year BETWEEN %s AND %s
        ORDER BY f.release_year, f.title
        LIMIT %s OFFSET %s
    """
    cursor.execute(request, (genre, year_from, year_to, limit, offset))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results