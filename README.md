
# Scrapy S3 Log Storage

## Description
A Scrapy extension to upload log files to S3.

If you're already exporting your feeds to S3 this extension uses many of the same settings. After adding this extension to your `EXTENSIONS` setting, just set the `LOG_FILE`, `S3_LOG_BUCKET` and an optional `S3_LOG_ACL`settings and you're good to go.

## Installation
You can install scrapy-s3logstorage using pip:
```
    pip install scrapy-s3logstorage
```

## Configuration

This extension still requires that a local log file is written. Once scrapy's engine has stopped, the extension will upload the log file to S3 and optionally delete the local file.

Enable the extension by adding it to your `settings.py`:
```
    from environs import Env

    env = Env()  
    env.read_env() 

    EXTENSIONS = {
        'scrapy_s3logstorage.extension.S3LogStorage': 0,
    }

    LOG_FILE = 'scrapy.log' # Must be a local file
    S3_LOG_BUCKET = 'my-bucket' # Bucket name to store logs
    S3_LOG_DELETE_LOCAL = True # Delete local log file after upload, defaults to False

    # If AWS CLI is configured, and you're using the same credentials the following settings are optional
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN = env("AWS_SESSION_TOKEN") # if required
    AWS_ENDPOINT_URL = None  # or your endpoint URL

    # S3_LOG_ACL takes priority over FEED_STORAGE_S3_ACL.
    # If S3_LOG_ACL is not set, FEED_STORAGE_S3_ACL will be used.
    # Setting one or both of these settings is optional.

    S3_LOG_ACL = ''  # or other S3 ACL
    FEED_STORAGE_S3_ACL = '' # or other S3 ACL
```