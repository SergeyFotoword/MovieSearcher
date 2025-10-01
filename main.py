from mysql_connector import MySQLDatabase
from logics import (
    safe_menu_choice,
    action_search_keyword,
    action_search_genre_year,
    action_show_top_queries,
    action_show_recent_queries,
)

def movie_searcher():
    db = MySQLDatabase()
    while True:
        print("\n************* MovieSearcher *************\n"
              "***** Best Movie Search Application *****")
        print("1. Search by keyword")
        print("2. Search by genre and year range")
        print("3. Show top 5 popular queries")
        print("4. Show last 5 queries")
        print("0. Exit")
        choice = safe_menu_choice()

        if choice == "1":
            action_search_keyword(db)
        elif choice == "2":
            action_search_genre_year(db)
        elif choice == "3":
            action_show_top_queries()
        elif choice == "4":
            action_show_recent_queries()
        elif choice == "0":
            print("Goodbye!")
            break


if __name__ == "__main__":
    movie_searcher()