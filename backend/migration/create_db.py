import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database connection details from user
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "safe70!!"
DB_NAME = "skyboot.mail"

def create_database():
    """
    Creates the specified database if it does not already exist.
    """
    # Connect to the default 'postgres' database to create the new database
    default_db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    try:
        engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            # Check if the database already exists
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
            if result.scalar() == 1:
                print(f"Database '{DB_NAME}' already exists.")
                return

            # Create the database
            print(f"Creating database '{DB_NAME}'...")
            connection.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
            print(f"Database '{DB_NAME}' created successfully.")

    except OperationalError as e:
        print(f"Error connecting to the default 'postgres' database: {e}")
        return
    except Exception as e:
        print(f"An error occurred during database creation: {e}")
        return

    # Verify the connection to the new database
    new_db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    try:
        new_engine = create_engine(new_db_url)
        with new_engine.connect() as connection:
            print(f"Successfully connected to the new database '{DB_NAME}'.")
    except OperationalError as e:
        print(f"Error connecting to the new database '{DB_NAME}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while connecting to the new database: {e}")


if __name__ == "__main__":
    create_database()