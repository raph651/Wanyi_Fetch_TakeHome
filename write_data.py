import localstack_client.session as boto3
import psycopg2
import queue
import json
import logging

from hashlib import sha256
from typing import Tuple
from threading import Thread
from datetime import datetime
from data_settings import EXPECTED_FIELDS, PII_CONFIG, POSTGRES_CONNECTION_CONF


queue_url = "http://localhost:4566/000000000000/login-queue"
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s"
)
sqs_client = boto3.client("sqs")


class SQLProcessor(Thread):
    """Class based thread that store messages to a queue. Run the thread to 
    write transformed data to sql database
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.que = queue.Queue()
        self.conn = None
        self.cursor = None
        self.task_count = 0

    def connect(self):
        """connect to the postgreSQL database based on configuration provided
        """
        try:
            self.conn = psycopg2.connect(**POSTGRES_CONNECTION_CONF)
            self.cursor = self.conn.cursor()
            logger.info("Connection to postgrSQL database successful")
        except:
            logger.exception("Connection to postgrSQL database failed")
            raise

    def reset(self):
        """reset queue and task count
        """
        self.que = queue.Queue()
        self.task_count = 0

    def sql_insert_query(self, json_msg):
        """construct sql insert query based on the transformed data and
        insert the data to sql database. If not successful, roll back.

        Possible optimization: use bulk insert instead of per record insert

        Args:
            json_msg: the transformed data in json(dict) format

        """
        now = datetime.now().isoformat()
        sql_query = "\n".join(
            [
                "INSERT INTO user_logins (",
                ",".join([key for key in json_msg] + ["create_date"]),
                ") VALUES (",
                ",".join([f"'{val}'" for val in json_msg.values()] + [f"'{now}'"]),
                ");",
            ]
        )
        print(sql_query, " sql query")
        try:
            self.cursor.execute(sql_query)
            self.conn.commit()
        except:
            logger.exception("Writing to SQL database failed")
            self.conn.rollback()

    def run(self):
        """The thread running process gets transformed data from queue
        and inserts records
        """
        while True:
            try:
                json_msg = self.que.get()
                try:
                    self.sql_insert_query(json_msg)
                finally:
                    self.task_count += 1
                    self.que.task_done()
            except queue.Empty():
                pass
            except:
                logger.exception("error while inserting sql query")


class MessageProcessor(Thread):
    def __init__(self, queue, *args, **kwargs):
        """ Set up the message processor.

        Attributes:
            expected_fields: fields that are expected to exist in a message body, see data_settings.py
            pii_fields_dict: a dict object (keys: pii fields to mask, values: transformed fields), see data_settings.py
            masker: a function that uses sha256 to encode a field string
        """
        super().__init__(*args, **kwargs)
        self.expected_fields = EXPECTED_FIELDS
        self.pii_fields_dict = PII_CONFIG

        # use sha256 to encrypt a PII field
        self.masker = lambda field: sha256(field.encode()).hexdigest()
        self.que = queue

    def jsonfy_msg_body(self, msg_body: str) -> Tuple[bool, dict]:
        """Validate the message body. First, check if all the expected fields exist in the message body. Then check if the PII fields
        exist in the message body. If valid, mask the personal identity information and return 
        a corresponding dict (json) object.

        Args: 
            msg_body: Message body string receivede from the sqs client

        Output:
            A tuple consisting is_valid (bool) and json_msg_body (empty dict if invalid)
        """

        json_msg = json.loads(msg_body)
        # check if the message body matches all expected fields
        if not set(json_msg) == self.expected_fields:
            print(
                "Message body not expected! (missing fields or having unexpected fields)"
            )
            return False, {}

        # check if the PII fields exist in message body and mask them using sha256
        for field, masked_field in self.pii_fields_dict.items():
            if field not in json_msg:
                print(f"PII config not expected! (message has no {field} field)")
                logger.warning(f"PII {field} info not found in message body")
                return False, {}
            json_msg[masked_field] = self.masker(json_msg[field])
            del json_msg[field]

        json_msg["app_version"] = json_msg["app_version"][
            0
        ]  # only keep the first version integer

        return True, json_msg

    def get_sqs_response(self):
        """A sqs response generator that efficiently long pulls the sqs queue by 10 seconds 
        with maximum 1000 messages (can be modified based on application needs)
        """
        stop = False  # can be other conditions as well
        while not stop:
            try:
                response = sqs_client.receive_message(
                    QueueUrl=queue_url, MaxNumberOfMessages=1000, WaitTimeSeconds=10
                )
            except:
                print("error receiving message")
                logger.exception("Could not receive message")
                stop = False
                raise
            else:
                yield response

    def run(self):
        """The thread process fetch responses from sqs queue, transforms the data,
        and enqueues them to the sql_processor queue instance
        """
        for response in self.get_sqs_response():
            try:
                msgs = response["Messages"]

                print(f"Processing {len(msgs)} messages...")
                logger.info(f"Processing {len(msgs)} messages...")

                for msg in msgs:
                    msg_body = msg["Body"]
                    is_valid, json_msg = self.jsonfy_msg_body(msg_body)
                    if is_valid:
                        self.que.put(json_msg)
            except:
                logger.exception("Response not valid. Abandon the thread now.")
                raise


if __name__ == "__main__":
    print("Hello running")

    sql_processor = SQLProcessor()
    sql_processor.connect()
    message_processor = MessageProcessor(queue=sql_processor.que)

    message_processor.start()
    sql_processor.start()

    message_processor.join()
    sql_processor.join()

