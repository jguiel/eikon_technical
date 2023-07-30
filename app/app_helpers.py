""" Helper functions for ETL api. Core extract/transform functions """

import os
import pandas as pd
from typing import Tuple, List


def load_dataframes(path_to_data: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Load to `data/`` CSVs to dataframes, under assumption of static file name defined in strings here
    users_df = pd.read_csv(os.path.join(path_to_data, "users.csv"))
    experiments_df = pd.read_csv(os.path.join(path_to_data, "user_experiments.csv"))
    compounds_df = pd.read_csv(os.path.join(path_to_data, "compounds.csv"))
    
    return users_df, experiments_df, compounds_df


def transform_data(
    users_df: pd.DataFrame, 
    experiments_df: pd.DataFrame, 
    compounds_df: pd.DataFrame
) -> pd.DataFrame:
    # Instantiate new dict object for derived results
    derived_results_py = dict()

    # Produce list of ALL user_ids in system
    user_ids = users_df['user_id'].tolist()
    derived_results_py['user_id'] = user_ids

    # Find total experiment count for every user_id that has committed experiment
    total_exp_per_users = experiments_df['user_id'].value_counts()
    # Add to dict, defaulting to 0 if no experiments found
    derived_results_py['total_exp_per_user'] = total_exp_per_users.get(user_ids, 0)

    # Average experiment count for all users
    avg_experiment_count = round(experiments_df.shape[0]/users_df.shape[0], 2)
    derived_results_py['avg_experiment_count'] = [avg_experiment_count for _ in user_ids]

    # Mean experiment run time
    total_exp_time_per_user = experiments_df.groupby('user_id')['experiment_run_time'].sum()
    # Add mean experiment time, defaulting to 0 for users with no experiments
    derived_results_py['avg_exp_time_per_user'] = round(
        total_exp_time_per_user.get(user_ids, 0)/derived_results_py['total_exp_per_user'], 
        2,
    )

    # Prepare compound data
    derived_results_py = prepare_compound_data(experiments_df, compounds_df, user_ids, derived_results_py)

    # DataFramed for ease of ingestion to pgsql
    derived_results = pd.DataFrame(derived_results_py)
    return derived_results


def prepare_compound_data(
    experiments_df: pd.DataFrame, 
    compounds_df: pd.DataFrame, 
    user_ids: List[str], 
    derived_results_py: dict
) -> dict:
    # Change experiment_compound_ids in-place to list of ints instead of semicolon-delimited str
    experiments_df['experiment_compound_ids'] = experiments_df['experiment_compound_ids'].str.split(';').apply(
        lambda x: list(map(int, x))
    )

    # Concatenate compounds consumed for all experiments, per user, into singular list
    all_compounds_consumed_per_user = experiments_df.groupby('user_id')['experiment_compound_ids'].sum()

    # Create `collections.Counter`-ish object for each user_id to count how many of each compound was consumed
    compound_id_counts_by_user = all_compounds_consumed_per_user.apply(
        lambda x: pd.Series(x).value_counts()
    )

    # Select user's most used compound_id
    most_consumed_compound_id = compound_id_counts_by_user.idxmax(axis=1)
    derived_results_py["most_consumed_compound_id"] = most_consumed_compound_id.get(
        user_ids, None
    ).astype('Int64')

    # Select user's most used compound_name
    most_consumed_compound = most_consumed_compound_id.map(
        compounds_df.set_index('compound_id')['compound_name']
    )
    derived_results_py["most_consumed_compound_name"] = most_consumed_compound.get(user_ids, None)

    return derived_results_py

if __name__ == '__main__':

    users_df, experiments_df, compounds_df = load_dataframes('data')
    print(transform_data(users_df, experiments_df, compounds_df))