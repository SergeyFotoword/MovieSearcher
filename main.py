from mysql_connector import search_keyword, search_genre_and_years, get_genres_and_years
from log_writer import save_log
from log_stats import get_top_queries, get_recent_queries
from handler_error import log_error
from formatter import print_table
from tabulate import tabulate
from pymongo.errors import PyMongoError
import pymysql



def safe_input_int(prompt, default=None):
    try:
        return int(input(prompt).strip())
    except ValueError as e:
        print("Error: enter a number!")
        log_error("user_input", e)
        return default


def format_params(params: dict) -> str:
    if not params:
        return "-"
    return ", ".join(f"{k}={v}" for k, v in params.items())


def film_finder():
    while True:
        print("\n************ FilmFinder ************\n"
              "*** Best Movie Search Application ***")
        print("1. Search by keyword")
        print("2. Search by genre and year range")
        print("3. Show top 5 popular queries")
        print("4. Show last 5 queries")
        print("0. Exit")
        choice = input("Enter the menu item number: ").strip()

        try:
            if choice == "1":
                keyword = input("Enter keyword for movie title: ").strip()
                offset = 0
                attempt = 1
                while True:

                    try:
                        results = search_keyword(keyword, offset)
                    except pymysql.MySQLError as e:
                        print(f"MySQL error: {e}")
                        log_error("search_keyword", e)
                        continue

                    if not results:
                        print("No more results.")
                        break
                    print_table(results)

                    if attempt == 1:
                        save_log("keyword", {"keyword": keyword}, len(results))

                    continue_ = input("Show next 10 results? (y/n): ").lower()
                    if continue_ != "y":
                        break
                    offset += 10
                    attempt += 1

            elif choice == "2":

                try:
                    genres, min_year, max_year = get_genres_and_years()
                except pymysql.MySQLError as e:
                    print(f"MySQL error: {e}")
                    log_error("get_genres_and_years", e)
                    continue

                print("\nAvailable genres:")
                for genre in genres:
                    print(f"- {genre}")
                print()
                print(f"\nMovies available from {min_year} to {max_year}")

                genre = input("Enter genre: ").strip()
                year_from = int(input("Enter start year: ").strip())
                year_to = int(input("Enter end year: ").strip())
                if year_from is None or year_to is None:
                    continue

                offset = 0
                attempt = 1
                while True:

                    try:
                        results = search_genre_and_years(genre, year_from, year_to, offset)
                    except pymysql.MySQLError as e:
                        print(f"MySQL error: {e}")
                        log_error("search_genre_and_years", e)
                        break

                    if not results:
                        print("No more results.")
                        break

                    print_table(results)

                    if attempt == 1:
                        save_log("genre_year", {"genre": genre, "from": year_from, "to": year_to}, len(results))

                    continue_ = input("Show next 10 results? (y/n): ").lower()
                    if continue_ != "y":
                        break
                    offset += 10
                    attempt += 1

            elif choice == "3":
                print("\nTop 5 popular queries:")
                try:
                    results = get_top_queries()
                    table = []
                    for res in results:
                        search_type = res["_id"].get("type", "-")
                        params = format_params(res["_id"].get("params", {}))
                        table.append({
                            "Type": search_type,
                            "Params": params,
                            "Count": res.get("count", 0)
                        })
                    print(tabulate(table, headers="keys", tablefmt="grid"))
                except PyMongoError as e:
                    print(f"MongoDB error: {e}")
                    log_error("get_top_queries", e)

            elif choice == "4":
                print("\nLast 5 queries:")
                try:
                    results = get_recent_queries()
                    table = []
                    for res in results:
                        search_type = res.get("search_type", "-")
                        params = format_params(res.get("params", {}))
                        ts = res.get("timestamp")
                        # ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "-"
                        table.append({
                            "Type": search_type,
                            "Params": params,
                            "Date": ts
                        })
                    print(tabulate(table, headers="keys", tablefmt="grid"))
                except PyMongoError as e:
                    print(f"MongoDB error: {e}")
                    log_error("get_recent_queries", e)

            elif choice == "0":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Try again.")

        except Exception as e:
            print(f"Unexpected error: {e}")
            log_error("film_finder", e)


if __name__ == "__main__":
    film_finder()
