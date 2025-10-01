from log_writer import save_log
from log_stats import get_top_queries, get_recent_queries
from handler_error import log_error
from formatter import print_table
from tabulate import tabulate
from pymongo.errors import PyMongoError
import pymysql
from mysql_connector import MySQLDatabase

class MenuBack(Exception):
    """Return to the main menu by entering 'q' during the parameter entry stage."""
    pass

def _read_str(prompt: str, allow_quit: bool = False) -> str:
    """
    Reading a string. If allow_quit=True and 'q' is entered, it brings up MenuBack.
    """
    s = input(prompt)
    if allow_quit and s.strip().lower() == "q":
        raise MenuBack
    return s


def safe_input_int(prompt, default=None, allow_quit: bool = False):
    """
    Reads an integer number. If allow_quit=True and 'q' is entered,
    it returns to the menu (MenuBack).
    If the integer is invalid, it reports an error and returns default.
    """
    try:
        raw = _read_str(prompt, allow_quit=allow_quit).strip()
        return int(raw)
    except MenuBack:
        # we push error handling up the calling stack
        raise

    except ValueError as e:
        print("Error: enter a number!")
        log_error("user_input", e)
        return default

def ask_yes_no(prompt: str) -> bool:
    """Returns True for 'y', False for 'n'. Prompts until the input is correct."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in ("y", "n"):
            return choice == "y"
        print("Please enter 'y' or 'n'.")


def safe_menu_choice(valid=("1", "2", "3", "4", "0")) -> str:
    """
    Indefinitely prompts the user for a menu item number
    until the user enters a valid number from valid.
    Returns a string ('1', '2', ...).
    """
    while True:
        val = safe_input_int("Enter the menu item number: ")
        if val is None:
            continue
        s = str(val)
        if s in valid:
            return s
        print(f"Please choose one of: {', '.join(valid)}.")


def paginate_results(results, page_size=10):
    for i in range(0, len(results), page_size):
        yield results[i:i + page_size]


def format_params(params: dict) -> str:
    if not params:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in params.items())


def _suggest_genres(raw: str, names: list[str]) -> list[str]:
    """
    Suggestion generator:
    - genres starting with the entered text first,
    - genres containing the entered text next.
    Returns a maximum of 3 results.
    """
    raw = raw.lower()
    if not raw:
        return []
    starts = [name for name in names if name.lower().startswith(raw)]
    contains = [name for name in names if raw in name.lower() and name not in starts]
    return (starts + contains)[:3]


def prompt_genre(genre_ranges: list[dict]) -> dict:
    """
    Queries the genre until it is valid (or 'q' to return).
    Returns a genre dictionary: {'name', 'min_year', 'max_year'}.
    """
    by_lower = {genre['name'].lower(): genre for genre in genre_ranges}
    names = [genre['name'] for genre in genre_ranges]

    while True:
        try:
            raw = _read_str("Enter genre (or 'q' to go back): ", allow_quit=True).strip().lower()
        except MenuBack:
            raise

        if raw in by_lower:
            return by_lower[raw]

        suggestions = _suggest_genres(raw, names)
        if suggestions:
            proposal = ", ".join(suggestions)
            print(f"Unknown genre. Did you mean: {proposal}? Try again or press 'q' to go back.")
        else:
            print("Unknown genre. Please try again or press 'q' to go back.")


def prompt_year(prompt: str, min_year: int, max_year: int) -> int:
    """
    Requests a year up to the valid value in [min_year, max_year].
    Supports 'q' to return to the menu.
    """
    while True:
        try:
            year = safe_input_int(f"{prompt} ({min_year}-{max_year}, or 'q' to go back): ", allow_quit=True)
        except MenuBack:
            raise
        if year is None:
            continue
        if year < min_year or year > max_year:
            print(f"Year must be between {min_year} and {max_year}. Try again.")
            continue
        return year


# Menu actions

def action_search_keyword(db: MySQLDatabase):
    try:
        keyword = _read_str("Enter keyword for movie title (or 'q' to go back): ", allow_quit=True).strip()
    except MenuBack:
        print("\nReturning to main menu...")
        return

    if not keyword:
        print("Please enter a non-empty keyword.")
        return

    try:
        results = db.search_keyword(keyword)
    except pymysql.MySQLError as e:
        print("Database error while searching by keyword.")
        log_error("search_keyword", e)
        return

    if not results:
        print("No results found.")
        return

    try:
        save_log("keyword", {"keyword": keyword}, len(results))
    except PyMongoError as e:
        print("Warning: failed to write stats to Mongo.")
        log_error("save_log_keyword", e)

    pages = list(paginate_results(results))
    for idx, page in enumerate(pages, start=1):
        print_table(page)
        if idx < len(pages):
            if not ask_yes_no("Show next 10 results? (y/n): "):
                break


def action_search_genre_year(db: MySQLDatabase):
    try:
        _, genre_ranges = db.get_genres_and_years()
    except pymysql.MySQLError as e:
        print("Database error while fetching genres/year ranges.")
        log_error("get_genres_and_years", e)
        return

    print("\nAvailable genres and year ranges:")
    for genre in genre_ranges:
        print(f"- {genre['name']} ({genre['min_year']} - {genre['max_year']})")


    try:
        gr = prompt_genre(genre_ranges)
        genre = gr['name']
        gmin, gmax = int(gr['min_year']), int(gr['max_year'])
        print(f"Selected: {genre}. Available years: {gmin}-{gmax}")

        year_from = prompt_year("Enter start year", gmin, gmax)

        while True:
            year_to = prompt_year("Enter end year", gmin, gmax)
            if year_to < year_from:
                print(f"End year must be >= start year ({year_from}). Try again.")
                continue
            break

    except MenuBack:
        print("\nReturning to main menu...")
        return

    try:
        results = db.search_genre_and_years(genre, year_from, year_to)
    except pymysql.MySQLError as e:
        print("Database error while searching by genre and years.")
        log_error("search_genre_and_years", e)
        return

    if not results:
        print("No results found.")
        return

    try:
        save_log("genre_year", {"genre": genre, "from": year_from, "to": year_to}, len(results))
    except PyMongoError as e:
        print("Warning: failed to write stats to Mongo.")
        log_error("save_log_genre_year", e)

    pages = list(paginate_results(results))
    for idx, page in enumerate(pages, start=1):
        print_table(page)
        if idx < len(pages):
            if not ask_yes_no("Show next 10 results? (y/n): "):
                break



def action_show_top_queries():
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


def action_show_recent_queries():
    print("\nLast 5 queries:")
    try:
        results = get_recent_queries()
        table = []
        for res in results:
            search_type = res.get("search_type", "-")
            params = format_params(res.get("params", {}))
            ts = res.get("timestamp")
            table.append({
                "Type": search_type,
                "Params": params,
                "Date": ts
            })
        print(tabulate(table, headers="keys", tablefmt="grid"))
    except PyMongoError as e:
        print(f"MongoDB error: {e}")
        log_error("get_recent_queries", e)