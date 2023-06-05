
# Scrapy Log Export

## Description
A scrapy extension that allows for a LOG_URI setting, similar to a FEED_URI setting.
The same FEED_STORAGE classes that are used in the feedexport extensions are used here.

This extension is useful if you're running scrapy in a container and want to store your logs with a cloud service provider.

Please note that this extension still requires that a local log file is written. Once scrapy's engine has stopped, the extension will upload the log file to the cloud and optionally delete the local file.

## Installation
You can install scrapy-logexporter using pip:
```
    pip install scrapy-logexporter
```

## Configuration

Enable the extension by adding it to your `settings.py`:
```
    from environs import Env

    env = Env()  
    env.read_env() 

    # Enable the extension
    EXTENSIONS = {
        "scrapy_logexport.LogExporter": 0,
    }

    LOG_FILE = 'scrapy.log' # Must be a local file
    LOG_EXPORTER_DELETE_LOCAL = True # Delete local log file after upload, defaults to False
    LOG_URI = f"s3://your-bucket/%(name)s %(time)s.log" # Store on S3
    
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

```

## Setting LOG_URI

The FEED_STORAGE class used for the LOG_URI is determined by the URI scheme. The following schemes are supported, by default:

```
FEED_STORAGES_BASE = {
    "": "scrapy.extensions.feedexport.FileFeedStorage",
    "file": "scrapy.extensions.feedexport.FileFeedStorage",
    "ftp": "scrapy.extensions.feedexport.FTPFeedStorage",
    "gs": "scrapy.extensions.feedexport.GCSFeedStorage",
    "s3": "scrapy.extensions.feedexport.S3FeedStorage",
    "stdout": "scrapy.extensions.feedexport.StdoutFeedStorage",
}
```
If you've already added more to FEED_STORAGES they're be available for use with LOG_URI.
Additionally a LOG_STORAGES setting is available to add more storage classes for use with LOG_URI.

Also not that similar to FEED_URI, the LOG_URI can be a template string. By default
any spider attr (such as `name`) or `time` are available. You can additionally 
add any other attributes to the template by declaring the LOG_URI_PARAMS setting.

The LOG_URI_PARAMS settings should be a function, or a string that's a path to a function.
The function needs to take `spider` as an argument and return a dictionary of the parameters.

```
LOG_URI_PARAMS: Optional[Union[str, Callable[[dict, Spider], dict]]] = {'my_attr': 'my_value'}

def uri_params_func(spider):
    return {
        'custom_param': 'my_value',
        'another_param': 'another_value',
    }

# takes the spider's name, the time the spider started, and the custom_param and another_param
LOG_URI = f"s3://your-bucket/%(name)s_%(time)s_%(custom_param)s_%(another_param)s.log"
LOG_URI_PARAMS = uri_params_func

```

## Overriding feedexport settings

Because much of the backend is the same, you can override some feedexport settings, if you wish them to be different for logexport.

| FeedExport              | LogExport                       |
| ----------------------- | ------------------------------- |
| FEED_STORAGE_S3_ACL     | LOG_STORAGE_S3_ACL              |
| AWS_ENDPOINT_URL        | LOG_STORAGE_AWS_ENDPOINT_URL    |
| GCS_PROJECT_ID          | LOG_STORAGE_GCS_PROJECT_ID      |
| FEED_STORAGE_GCS_ACL    | LOG_STORAGE_GCS_ACL             |
| FEED_STORAGE_FTP_ACTIVE | LOG_STORAGE_FTP_ACTIVE          |


Additionally if there's shared keys in FEED_STORAGES and LOG_STORAGES, the LOG_STORAGES key will be used.

## All possible settings

```
LOG_FILE # Required
LOG_URI # Required

LOG_EXPORTER_DELETE_LOCAL
LOG_URI_PARAMS

# Overrides for feedexport settings
LOG_STORAGES
LOG_STORAGE_S3_ACL
LOG_STORAGE_AWS_ENDPOINT_URL
LOG_STORAGE_GCS_PROJECT_ID
LOG_STORAGE_GCS_ACL
LOG_STORAGE_FTP_ACTIVE

# S3FeedStorage settings
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
FEEDEXPORT_S3_ACL # Overridden by LOG_STORAGE_S3_ACL
AWS_ENDPOINT_URL # Overridden by LOG_STORAGE_AWS_ENDPOINT_URL

# GCFeedStorage settings
GCS_PROJECT_ID # Overridden by LOG_STORAGE_GCS_PROJECT_ID
FEED_EXPORT_GCS_ACL # Overridden by LOG_STORAGE_GCS_ACL

# FTPFeedStorage settings
FEED_STORAGE_FTP_ACTIVE # Overridden by LOG_STORAGE_FTP_ACTIVE

FEED_TEMPDIR # Not used by logexport directly
```