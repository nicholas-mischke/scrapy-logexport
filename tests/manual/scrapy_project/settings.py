
from environs import Env
from pathlib import Path

env = Env()
env.read_env()

BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["scrapy_project.spiders"]
NEWSPIDER_MODULE = "scrapy_project.spiders"

EXTENSIONS = {
    "scrapy_logexport.LogExporter": 0,
}

LOG_FILE = 'scrapy.log'
Path(LOG_FILE).unlink(missing_ok=True) # Make sure it's new each crawl. 

LOG_EXPORTER_DELETE_LOCAL = False
# LOG_URI = "spider.name=%(name)s utc_time=%(time)s.log" # Store local file
LOG_URI = f"s3://{env('S3_LOG_BUCKET')}/%(name)s %(time)s.log" # Store on S3

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
