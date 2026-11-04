
import os
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Load database credentials
load_dotenv(BASE_DIR / ".env")

host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
user = os.getenv("MYSQL_USER", "root")
password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
database = os.getenv("MYSQL_DATABASE", "student_analytics")

# Create database connection
engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    pool_pre_ping=True
)

# Read cleaned CSV
csv_path = BASE_DIR / "data" / "cleaned_student.csv"
df = pd.read_csv(csv_path)

# Validate CSV columns
print("CSV columns:", df.columns.tolist())
print("Total students:", len(df))

# Load data into MySQL
with engine.begin() as connection:

    # Remove existing records
    connection.execute(text("DELETE FROM students"))

    # Insert new records
    df.to_sql(
        "students",
        connection,
        if_exists="append",
        index=False
    )

print(f"Successfully loaded {len(df)} students into MySQL!")
