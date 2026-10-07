from mcpSuunto.duckdb.database import get_connection


def main():
    connection = get_connection()

    print("Database connected!")

    connection.close()


if __name__ == "__main__":
    main()