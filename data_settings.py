EXPECTED_FIELDS = {
    "user_id",
    "app_version",
    "device_type",
    "ip",
    "locale",
    "device_id",
}
PII_CONFIG = {"ip": "masked_ip", "device_id": "masked_device_id"}

QUEUE_URL = "http://localhost:4566/000000000000/login-queue"

POSTGRES_CONNECTION_CONF = {
    "host": "pg_container",
    "user": "postgres",
    "password": "postgres",
    "database": "postgres",
}

