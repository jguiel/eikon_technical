# Eikon Therapeutics Technical Assessment
*Justin Guiel, 2023*

This repo contains a Flask app that is built solely to derive certain features from three CSV files contained within `app/data/` directory and upload it to a PostgreSQL database. It is deployed via Docker, including handling the install of all required packages. The data output by the ETL/API are queried via a separate Python script to verify these data are correctly extracted, transformed, and loaded. 

**Note: This is the MVP for the assignment. Please read the "Out of Scope" section at bottom of readme for all future features I would recommend and implement in future epics.**

*Additionally, you can try uploading your own `users.csv` and `user_experiments.csv` to `app/data/`. I expanded on the CSVs in the assigned material by doubling the randomized user and experiment data, however it is still a relatively limited amount.*

Happy deploying!

## Step-by-step guide

### Prerequisites
1. Docker desktop app/daemon downloaded and running
2. Port 5001 available *(use of port 5000 deprecated due to AirPlay on MacOS)*
3. Git command line

### Instantiation w/Docker
1. Clone this repo locally with `git clone https://github.com/jguiel/eikon_technical.git`
2. Enter the repo with `cd eikon_technical`
3. Ensure Docker daemon is running (open Docker app)
4. Run using `docker-compose up -d`
5. PostgreSQL database and Flask API are now running and awaiting requests across two containers

### Run and validate with Click app

A click app was made in a third Docker container and can be used to trigger the ETL API with files in the `app/data/` subdirectory and to validate that these data have been loaded accurately. Note that the name of the docker container in the commands below may differ machine-to-machine. use `docker ps` or check the Docker desktop app for container names
  1. `docker exec -it eikon_technical-api_cli-1 python api_cli.py --api`
      - Triggers ETL on files in data directory
  2. `docker exec -it eikon_technical-api_cli-1 python api_cli.py --validate`
      - Query and display the transformed data in command line

```
# api_cli.py --help output
root@1d2a3b37035c:/api_cli# python api_cli.py --help
Usage: api_cli.py [OPTIONS]

Options:
  --api       Run API call with data in `app/data/` directory
  --validate  Query the database to validate results
  --help      Show this message and exit.
```

### Output
- `api` arg: Message and HTTP response code
- `validate` arg: rows from postgresql table to your command line, showing the derived data

**A successful api call would look like**
```
➜  eikon_technical git:(master) ✗ docker exec -it eikon_technical-api_cli-1 python api_cli.py --api
{
  "Success": true
}
➜  eikon_technical git:(master) ✗ docker exec -it eikon_technical-api_cli-1 python api_cli.py --validate
+---------+--------------------+----------------------+-----------------------+------------------------+-----------------------------+
| user_id | total_exp_per_user | avg_experiment_count | avg_exp_time_per_user | most_consumed_compound | most_consumed_compound_name |
+---------+--------------------+----------------------+-----------------------+------------------------+-----------------------------+
|    1    |         2          |         2.05         |          12.5         |           2            |          Compound B         |
|    2    |         2          |         2.05         |          25.0         |           3            |          Compound C         |
    ...
+---------+--------------------+----------------------+-----------------------+------------------------+-----------------------------+
```

### Closing and/or restarting app
1. Spin down containers by running `docker-compose down` or deleting containers in Docker desktop
2. Delete docker volume with `docker volume rm eikon_technical_postgres_data`
    - Failure to do so will lead to redundant data in database on subsequent API calls with the same csv input

### Derived data
From these CSVs, the app derives a new table. For each `user_id`:
1. `user_id`: Scientist's ID
2. `total_exp_per_user`: Total experiments ran per user
3. `avg_experiment_count`: Average experiment count across *all* users, will be the same for every record in table (per API call)
4. `avg_exp_time_per_user`: The average experiment runtime for each user
5. `most_consumed_compound`: ID for most used compound across all experiments for each user. See *Out of Scope* section for detail on future feature implementation
6. `most_consumed_compound_name`: Human readable compound name

### Data origin
This app works explicitly with the three files below.
```
eikon_technical/app/data/* 
# This subdirectory contains only the three files below
users.csv
user_experiments.csv
compounds.csv
```
If desired, the user can upload their own CSVs. The standard of file name, column name, and value of the CSV should be identical to:
```
# users.csv
"user_id","name","email","signup_date"
1,STR,"alice@example.com","2023-01-01"
...

# user_experiments.csv
"experiment_id","user_id","experiment_compound_ids","experiment_run_time"
1,"1","1;2","10"
...

# compounds.csv
"compound_id","compound_name","compound_structure"
1,"Compound A","C20H25N3O"
...
```

## Out of Scope 
Fixes and features that I would implement in later refined epics
- Security
    - Database creds would be moved into AWS secrets manager, rather than in the .env file commited to the remote repo
- Async utility
    - Currently, this API works synchronously; uploading the data and sending back an HTTP response when ETL is complete. If the files are large, this could lead to an HTTP timeout.
    - Future feature would make this an async API, implementing ECS workers or a fargate/celery task to ingest the data and immediately send response code once *upload* portion is complete. Subsequent transformation and loading can occur asynchronously while user goes about their workday.
- Multimodal `most_consumed_compound` extracted
    - Currently, `most_consumed_compound` for each `user_id` is the earliest-indexed compound. Multimodal compounds are disregarded.
    - Future feature would load all `most_consumed_compound`'s to the database as a list for each user i.e. `[Compound 1, Compound 2]` bimodal, trimodal, multimodal
- User can upload files to `app/data/`
    - Currently, this app ingests whatever files are already found in the `app/data/` directory and assumes they are named `users.csv`, `user_experiments.csv`, and `compounds.csv`
    - Future feature would:
        - Accept POST requests of entire csv files
        - Have AWS Lambda listener function awaiting files uploaded to specified AWS S3 bucket
        - Handle multiple file extensions i.e. xlsx, csv, txt, tsv, et cetera
        - Allow upstream system to upload the files directly to this app, part of larger data pipeline
- Refine which data are uploaded to PostgreSQL
    - Currently, only the derived data are uploaded to the database
    - Future feature would possibly upload exiting files i.e. `users.csv`, `user_experiments.csv`, and `compounds.csv` (depending on need and scalability)
        - Are these CSVs coming from a novel source and should be uploaded, or are they redundant coming from another database?
        - Redundancy; would the storage cost of multiple copies across different DBs help with availability and efficiency?
        - This would allow querying of the origin data to be done by this app or other APIs here
        - Use the data currently in the postgres db to calculate *new* derived features, i.e. *updated* `avg_exp_run_time` and `most_consumed_compounds` for each `user_id`
        - Allow repeated API use; currently, calling this endpoint twice just appends the same records to the table instead of overwriting or updating current data
- SQLAlchemy
    - Currently, pgsql queries are hardcoded and static
    - Future feature would allow dynamically generated queries for CRUD functions
