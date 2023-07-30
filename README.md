# Eikon Therapeutics Technical Assessment
*Justin Guiel, 2023*

This repo contains a Flask app that is built solely to derive certain features from three CSV files contained within `data/` directory and upload it to a PostgreSQL database. It is deployed via Docker, including handling the install of all required packages. The data output by the ETL/API are queried via a separate Python script to verify these data are correctly extracted, transformed, and loaded.

## Step-by-step guide

### Instantiation w/Docker
1. Clone this repo locally with `git clone https://github.com/jguiel/eikon_technical.git`
2. Enter the repo with `cd eikon_takehome`
3. Ensure Docker daemon is running (download Docker desktop and open app)
4. Run using `docker-compose up`

### Run and validate with Click app

Click commands can be used to trigger ETL API or validate these data have been loaded correctly with `docker exec -it eikon_takehome-api_cli-1 python api_cli.py --<arg>` or in the Docker container interactive terminal directly with `python api_cli.py --<arg>`
```
# api_cli Click app's help section
root@1d2a3b37035c:/api_cli# python api_cli.py --help
Usage: api_cli.py [OPTIONS]

Options:
  --api       Run API call with data in `data/` directory
  --validate  Query the database to validate results
  --help      Show this message and exit.
```

### Output
- `api` arg: Message and HTTP response code
- `validate` arg: rows from postgresql table to your command line, showing the derived data

**A successful api call would look like**
```
➜  eikon_takehome git:(master) ✗ docker-compose run api_cli python api_cli.py --api
[+] Running 2/0
 ✔ Container eikon_takehome-pgdb-1  Running                                                                                                                                                                 0.0s
 ✔ Container eikon_takehome-web-1   Running                                                                                                                                                                 0.0s
{
  "Success": true
}
➜  eikon_takehome git:(master) ✗ docker-compose run api_cli python api_cli.py --validate
[+] Running 2/0
 ✔ Container eikon_takehome-pgdb-1  Running                                                                                                                                                                 0.0s
 ✔ Container eikon_takehome-web-1   Running                                                                                                                                                                 0.0s
+---------+--------------------+-----------------------+------------------------+-----------------------------+
| user_id | total_exp_per_user | avg_exp_time_per_user | most_consumed_compound | most_consumed_compound_name |
+---------+--------------------+-----------------------+------------------------+-----------------------------+
|    1    |         2          |          12.5         |           2            |          Compound B         |
|    2    |         0          |          0.0          |          None          |             None            |
|    3    |         1          |          25.0         |           2            |          Compound B         |
|    4    |         1          |          30.0         |           1            |          Compound A         |
|    5    |         1          |          35.0         |           2            |          Compound B         |
|    6    |         1          |          40.0         |           1            |          Compound A         |
|    7    |         1          |          45.0         |           2            |          Compound B         |
|    8    |         1          |          50.0         |           1            |          Compound A         |
|    9    |         2          |          37.5         |           1            |          Compound A         |
|    10   |         2          |          35.0         |           3            |          Compound C         |
+---------+--------------------+-----------------------+------------------------+-----------------------------+
```

### Closing and/or restarting app
1. Spin down containers by running `docker-compose down` or deleting containers in Docker desktop
2. Delete docker volume with `docker volume rm eikon_takehome_postgres_data`
    - Failure to do so will lead to redundant data in database on subsequent API calls with the same csv input

### Derived data
From these CSVs, the app derives a new table. For each `user_id`:
1. `user_id`: Scientist's ID
2. `total_exp_per_user`: Total experiments ran per user
3. `avg_exp_time_per_user`: The average experiment runtime for each user
4. `most_consumed_compound`: ID for most used compound across all experiments for each user. See *Out of Scope* section for detail on future feature implementation
5. `most_consumed_compound_name`: Human readable compound name

### Data origin
This app works explicitly with the three files below.
```
eikon_takehome/data/* 
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
    - If this were a real app, database creds would be moved into AWS secrets manager or at the very least a dotenv
- All most-used compounds extracted
    - Currently, most used compound by each scientist is earliest indexed compound. Multimodal compounds are disregarded.
    - Future feature would have a list of all compounds most used ie. bimodal, trimodal, multimodal most-used compounds
- Upload data files
    - Currently, this app ingests whatever files are found in the `data/` directory and assumes they are named `users.csv`, `user_experiments.csv`, and `compounds.csv`
    - Future feature would:
        - Accept POST requests of entire csv files
        - AWS Lambda listener for files uploaded to specified AWS S3 bucket; ingest these
        - Handle multiple file extensions ie. xlsx, csv, txt, tsv etc
        - Upstream systems uploading these data directly to this app
- Refine data uploaded to PostgreSQL
    - Currently, only the derived data are uploaded to the database
    - Future feature would upload users, user_experiments, and compound data, depending on scalability
        - Are these CSVs coming from a novel source which should be uploaded? or are these coming from another database
        - Redundancy
        - This would allow querying the origin data to be done by this app or other APIs
        - Use the data currently in the postgres db to calculate new derived features, ie. updated mean experiment time
        - Allow repeated API use; current, calling endpoint twice just appends the same records to the bottom of the table, instead of overwriting or updating current data
- SQLAlchemy
    - Currently, pgsql queries are hardcoded and static
    - Future feature would allow dynamically generated queries for CRUD functions