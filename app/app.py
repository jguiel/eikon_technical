""" Small ETL flask app to derive data from user experiments. Justin Guiel 2023 """

import os
from flask import Flask, request, jsonify
import pandas as pd
import psycopg2
from contextlib import contextmanager


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
    
    # Load to pandas dataframes, under assumption of static file name defined in strings here
    users_df = pd.read_csv(os.path.join(path_to_data, "users.csv"))
    experiments_df = pd.read_csv(os.path.join(path_to_data, "user_experiments.csv"))
    compounds_df = pd.read_csv(os.path.join(path_to_data, "compounds.csv"))

    # Instantiate new dict object for derived results
    derived_results_py = dict()

    # Produce list of ALL user_ids in system
    user_ids = users_df['user_id'].tolist()
    derived_results_py['user_id'] = user_ids

    # Find total experiment count for every user_id that has commited experiment
    total_exp_per_users = experiments_df['user_id'].value_counts()
    # Add to dict, defaulting to 0 if no experiments found
    derived_results_py['total_exp_per_user'] = [total_exp_per_users[x] if x in total_exp_per_users.keys() else 0 for x in user_ids]

    # Average experiment count for all users
    avg_experiment_count = round(experiments_df.shape[0]/users_df.shape[0], 2)
    derived_results_py['avg_experiment_count'] = [avg_experiment_count for _ in user_ids]

    # Mean experiment run time
    total_exp_time_per_user = experiments_df.groupby('user_id')['experiment_run_time'].sum()
    derived_results_py['avg_exp_time_per_user'] = [round(total_exp_time_per_user[x]/total_exp_per_users[x], 2) if x in total_exp_per_users.keys() else 0 for x in user_ids]

    # Change experiment_compound_ids in-place to list of ints instead of semicolon-delimited str
    experiments_df['experiment_compound_ids'] = experiments_df['experiment_compound_ids'].str.split(';').apply(
        lambda x: list(map(int, x))
    )

    # Concatenate compounds consumed for all experiments, per user, into singular list
    all_compounds_consumed_per_user = experiments_df.groupby('user_id')['experiment_compound_ids'].sum()
    # Create `collections.Counter`-ish object for each user_id to count how many of each compound was consumed
    compound_id_counts_by_user = all_compounds_consumed_per_user.apply(lambda x: pd.Series(x).value_counts())

    # Select user's most used compound_id
    most_consumed_compound_id = compound_id_counts_by_user.idxmax(axis=1)
    # Must be declared as series of dtype=object, to handle both int and NaN
    derived_results_py["most_consumed_compound_id"] = pd.Series(
        [int(most_consumed_compound_id[x]) if x in most_consumed_compound_id.keys() else None for x in user_ids], 
        dtype=object
    )
    # Select user's most used compound_name
    most_consumed_compound = most_consumed_compound_id.map(compounds_df.set_index('compound_id')['compound_name'])
    derived_results_py["most_consumed_compound_name"] = [most_consumed_compound[x] if x in most_consumed_compound.keys() else None for x in user_ids]
    
    # DataFramed for ease of ingestion to pgsql
    derived_results = pd.DataFrame(derived_results_py)
    return derived_results


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
