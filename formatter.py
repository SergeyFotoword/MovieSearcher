from tabulate import tabulate


def print_table(results):
    if not results:
        print("No results found.")
        return
    headers = results[0].keys()
    rows = [row.values() for row in results]
    print(tabulate(rows, headers, tablefmt="grid"))

# Первый вариант
# import pandas as pd
#
# # cursor.execute("SELECT * FROM customers")
# data = cursor.fetchall()
# columns = [desc[0] for desc in cursor.description]
#
# df = pd.DataFrame(data, columns=columns)
# display(df)  # или print(df.to_string())
