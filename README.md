# Wanyi_Fetch_TakeHome

The application runs python scripts to fetch messages from SQS queue and write data entries to postgreSQL database. Thanks a lot for the detailed take home instruction! I do feel that there are a handful of ways to optimize my codes, although I've tried hard to deliver the best results. Please let me know if you have any questions or comments for the project! Any feedback is very much appreciated. I had fun with this project and thanks again!

## Usage:
  Clone the repo:
  
    git clone https://github.com/raph651/Wanyi_Fetch_TakeHome.git
    
  Use ```docker-compose``` to create two containers from the localstack image and the postgres image:

    docker-compose up -d
  
  After container initialization, execute the ```run.sh``` file on the container (ls_container) created from localstack image:
  
    docker exec -it ls_container bash -c "etl-python/run.sh"

  Wait for the setup and changes in the postgreSQL database until sql query messages apear in terminal. (Most likely you see a KeyError message afterwards, please safely exit with ```Ctrl+C``` )

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

1. docker-compose.yaml :<br/>
        The docker-compose.yaml is referenced from the take home instruction (Project Setup). Two containers will be created from the localstack and postgrs images, respectively. Since the localstack container (ls_container) is fully capable of connecting the SQS Message Queue, for quickest result, I mount the current directory to a volume located at /opt/code/localstack/etl-python. For the rest of the project, I let the container run a bash scipt `run.sh` to install packages and run a python script `write_date.py` to start processing the data.
    
2. run.sh:<br/>
        This bash script tells the container to get the `libpq-dev` package and install pip requirements (currently only 'psycopg2-binary'). Then it runs python script `write_date.py`
  
3. data_settings.py:<br/>
        Contains variables that influence the sql data processing behavior. It makes future changes (adding database fields, pii fields, database connection) easier.
4. write_data.py:<br/>
        The actual object-oriented python script that creates a Thread instance for retrieving sqs messages and a different Thread instance for writing the data to sql database
  </url>
  
## Solutions to following questions:
● How will you read messages from the queue?

 -- I use python boto3 client (contained in localstack.client.session) to connect to the SQS queue with given Queue URL. To read messages more efficiently, I allow the application to long pulls messages within an interval (10 seconds) to form a batch of messages using a thread. These messages will be pushed in a python queue as unfinished tasks.
 
● What type of data structures should be used?

-- I use python Queue data structure, which is inheritly a deque. The FIFO behavior is preserved in this case. And python Queue has methods such as task_done, all_tasks_done. These methods become effective in multi-threading.

● How will you mask the PII data so that duplicate values can be identified?

-- The PII data is masked using sha256 algorithm. Although I don't understand the algorithm in depth, it creates hashable strings that can be used to detect duplicate values.

● What will be your strategy for connecting and writing to Postgres?

-- Connecting to Postgres it accomplished via python pacakge `psycopg2`. The connection parameters are set in `data_setting.py` so later the any modification to the connection can be done by just configuring `data_settings.py`. Writing to Postgres is accomplished by a Thread that creates sql insert query strings and a cursor to execute these strings. 

● Where and how will your application run?

-- The application runs a `run.sh` bash file on the localstack container using docker exec command. It only requires a `libpq-dev`package and a `psycopg2` python package for postgreSQL connection-client. Then data processing and writing are accomplished by a python script that tries to optimize efficiency using multi-threading.


## Follow-up questions:

● How would you deploy this application in production?

-- This application is contained in the localstack container (created from localstack image). However, in the future if we want to stream the SQS message queue and insert data to database. I think I can use AWS Lambda to automate the process with dedicated instance or container. The current logging is not ideal for production, either. Other error handlers are critical too, for example, create a buffer that stores undelivered messages to a different database. 

● What other components would you want to add to make this production ready?

-- One component I think can boost up the application a little bit is python `Celery`. `Celery` is an efficient task scheduler that supports message brokers like Redis and RabbitMQ. It now also supports AWS SQS as a dedicated message broker. I believe with this component, the multi-processing part can be very impressively efficient.
Since it also supports task scheduling (like AWS Lambda in a way), in the future we can also consider automating data-cleaning tasks.

● How can this application scale with a growing dataset.

-- If the dataset grows, one thing I think we can do is allocate the database on AWS RDS with flexible storage configurations. If the real-time messages grow exponentially, we might consider create region-based databases and serverless applications. 

● How can PII be recovered later on?

-- I don't think the current sha256 algorithm will make it easy to recover. I'm actually very interested in this answer to the question. Very lookforward to hearing a better solution!

● What are the assumptions you made?

-- We don't delete read messages from SQS queue now, but can do it in production.
   The SQS message queue is small in size. So two seperate threads (one for reading and one for writing) should be sufficient.
   The app_version number is a string actually, but we only care about the first version number.
