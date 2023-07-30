""" Small ETL flask app to derive data from user experiments. Justin Guiel 2023 """

import os
from flask import Flask, request, jsonify
import pandas as pd
import psycopg2
from contextlib import contextmanager
from app_helpers import (
    load_dataframes,
    transform_data,
)


# Creds
# Obviously, these normally would be in a .env file or AWS secrets manager for security
DB_HOST = 'pgdb'
DB_NAME = 'eikondb'
DB_USER = 'justin_eikonemployee'
DB_PASSWORD = 'supersecurepass123'
app = Flask(__name__)


# PostgreSQL Connection, yield as context manager
@contextmanager
def pg_conn(host, database, user, password):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=host, 
            database=database, 
            user=user, 
            password=password
        )
        cursor = conn.cursor()
        yield cursor
    finally:
        if cursor:
            conn.commit()
            cursor.close()
            conn.close()
        else:
            return jsonify({'Bad connection': f"User {user} on db {database}"}), 401


@app.route('/experiments', methods=['POST'])
def run_experiment_etl():

    try:
        # Import and transform
        path_to_data = request.json['path_to_data']
        transformed_data = experiment_etl(path_to_data)
        # Load data to postgres
        load_data_pg(transformed_data)
        # Return 200
        return jsonify({'Success': True,}), 200
    
    # Error handling
    except FileNotFoundError as err:
        return jsonify({'Bad path to data': str(err)}), 404
    except Exception as err:
        print(err)
        return jsonify({'uh-oh': str(err)}), 500
    

def experiment_etl(path_to_data: str) -> pd.DataFrame:
    
    # Load CSVs to dataframe
    users_df, experiments_df, compounds_df = load_dataframes(path_to_data)
    # Extract derived data
    return transform_data(users_df, experiments_df, compounds_df)


def load_data_pg(derived_results: pd.DataFrame) -> None:
    
    # Connection as context mgr
    with pg_conn(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) as cursor:
        # Create table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS derived_exp_data (
            user_id INT,
            total_exp_per_user INT,
            avg_experiment_count FLOAT8,
            avg_exp_time_per_user FLOAT8,
            most_consumed_compound INT,
            most_consumed_compound_name TEXT
        )
        """
        cursor.execute(create_table_query)

        # Iterate through df and insert to new pg table
        for _, user_data in derived_results.iterrows():
            insert_query = """
            INSERT INTO derived_exp_data (
                user_id,
                total_exp_per_user,
                avg_experiment_count,
                avg_exp_time_per_user,
                most_consumed_compound,
                most_consumed_compound_name
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = tuple(user_data)
            cursor.execute(insert_query, values)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
