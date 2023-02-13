# Wanyi_Fetch_TakeHome

The application runs python scripts to fetch messages from SQS queue and write data entries to postgreSQL database. Thanks a lot for the detailed take home instruction! I do feel that there are a handful of ways to optimize my codes, although I've tried hard to deliver the best results. Please let me know if you have any questions or comments for the project! Any feedback is very much appreciated. I had fun with this project and thanks again!

## Usage:
  Clone the repo:

    ```bash 
    git clone https://github.com/raph651/Wanyi_Fetch_TakeHome.git
    ```
  Use ```docker-compose``` to create two containers from the localstack image and the postgres image:

    ```bash
    docker-compose up -d
    ```
  
  After container initialization, execute the ```run.sh``` file on the container (ls_container) created from localstack image:

    ```bash
    docker exec -it ls_container bash -c "etl-python/run.sh"
    ```

  Wait for the setup and changes in the postgreSQL database until sql query messages apear in terminal. (Most likely you see a KeyError message afterwards, please safely exit with Ctrl+C )

  Now 99 records will be added to the postgreSQL database.

## Idea:
    the working tree:
    .
    ├── README.md
    ├── data_settings.py
    ├── docker-compose.yaml
    ├── requirements.txt
    ├── run.sh
    └── write_data.py

    ## Docker-compose configuration:
        The docker-compose.yaml is referenced from the take home instruction (Project Setup). Two containers will be created from the localstack and postgrs images, respectively. Since the localstack container (ls_container) is fully capable of connecting the SQS Message Queue, for quickest result, I mount the current directory to a volume located at /opt/code/localstack/etl-python. For the rest of the project, I let the container run a bash scipt```run.sh``` to install packages and run a python script ```write_date.py``` to start processing the data.
    
    ## run.sh:
        This bash script tells the container to get the ```libpq-dev``` package and install pip requirements (currently only psycopg2-binary). Then it runs python script ```write_date.py```
    
    ## data_settings.py:
        Contains variables that influence the sql data processing behavior. It makes future changes (adding database fields, pii fields, database connection) easier.
    
    ## write_data.py:
        The actual object-oriented python script that creates a Thread class for retrieving 