""" Click CLI app to trigger ETL API and validate subsequent ETL data """

import os
import click
import subprocess
import psycopg2
from prettytable import from_db_cursor

# PostgreSQL Connection creds
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


@click.command()
@click.option('--api', is_flag=True, help="Run API call with data in data/ directory")
@click.option('--validate', is_flag=True, help="Query the database to validate results")
def run_command(api, validate):

    if api:
        api_curl_cmd = "curl -X POST -H 'Content-Type: application/json' -d '{\"path_to_data\":\"data/\"}' http://web:5000/experiments"
        subprocess.run(api_curl_cmd, shell=True)

    if validate:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM derived_exp_data;")
        validation_table = from_db_cursor(cur)
        print(validation_table)


if __name__ == '__main__':
    run_command()
