
from environs import Env
from datetime import datetime, timezone

env = Env()
env.read_env()

CURRENT_UTC_TIME = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

BOT_NAME = "manual_test"

SPIDER_MODULES = ["manual_test.spiders"]
NEWSPIDER_MODULE = "manual_test.spiders"

EXTENSIONS = {
    "scrapy_s3logstorage.extension.S3LogStorage": 0,
}

LOG_FILE = f"scrapy_s3logstorage_manual_test_{CURRENT_UTC_TIME}.log"
S3_LOG_DELETE_LOCAL = False  # Good to make sure they match

# S3_LOG_BUCKET doesn't need to be .env
# Just doing so, so I don't forget to edit this before publishing.
S3_LOG_BUCKET = env("S3_LOG_BUCKET")

# If AWS CLI is configured, these can be omitted
# AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
