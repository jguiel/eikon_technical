# Eikon Therapeutics Technical Assessment
*Justin Guiel, 2023*

This repo contains a Flask app that is built solely to derive certain features from three CSV files contained withing `data/` directory and upload it to a PostgreSQL database. It is deployed via Docker, including handling the install of all required packages. The data output by the ETL/API are queried via a separate Python script to verify these data are correctly extracted, transformed, and loaded.

## Step-by-step instantiation w/Docker
1. Clone this repo locally with `git clone https://github.com/jguiel/eikon_technical.git`
2. Enter the repo with `cd eikon_takehome`
3. Run using `docker-compose up`

### Output
This script will output a table to your command line, showing the derived data

### Derived data
From these CSVs, the app derives a new table. For each `user_id`:
1. `experiments_per_user`: Total experiments ran per user
2. `avg_experiments_per_user`: The average experiment account for users. Because an average for users was asked, it will be the same number for every `user_id` record
3. `most_consumed_compound`: The most used compound across all experiments for every user. See *Out of Scope* section for detail on future feature implementation

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
    - If this were a real app, I would move the database creds into AWS secrets manager or at the very least a dotenv
- All most-used compounds extracts
    - Currently, the most used compound by each scientist is shown as the earliest indexed compound
    - Future feature would have a list of all compounds most used ie. bimodal, trimodal, multimodal most-used compounds
- Upload data files
    - Currently, this app ingests whatever files are found in the `data/` directory, and assumes they are named `users.csv`, `user_experiments.csv`, and `compounds.csv`
    - Future feature would:
        - Accept POST requests of entire csv files
        - AWS Lambda listener for files uploaded to specified AWS S3 bucket, ingest these
        - Handle multiple file extensions ie. Pandas xlsx to csv, etc
        - Upstream systems uploading these data directly to this app
- Refine data uploaded to PostgreSQL
    - Currently, only the derived data is uploaded to the database
    - Future feature would upload users, user_experiments, and compounds data, depending on scalability
        - Are these CSVs coming from a novel source which should be uploaded? or are these coming from another database
        - Redundancy
        - This would allow querying the origin data to be done by this app—other APIs
- SQLAlchemy
    - Currently, pgsql queries are hardcoded and static
    - Future feature would allow dynamically generated queries for CRUD functions