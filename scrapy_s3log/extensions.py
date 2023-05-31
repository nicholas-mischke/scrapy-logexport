
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from scrapy import signals
from scrapy.utils.boto import is_botocore_available

import boto3
import io
from scrapy import signals
from scrapy.exceptions import NotConfigured

# EXTENSIONS = {
#     'scrapy-s3logs.extensions.S3Log': 0,
# }

class S3Log:
    
    @classmethod
    def from_crawler(cls, crawler):
        s3_uri = crawler.settings['LOG_FILE']
        if not s3_uri.startswith('s3://'):
            return None # extension should only be enabled when logging to S3
        
        # Redirect log to in-memory buffer
        log_buffer = io.StringIO()
        crawler.settings['LOG_FILE'] = log_buffer
        
        if not is_botocore_available():
            raise NotConfigured("missing botocore library")
        
        extension = cls(
            s3_uri,
            log_buffer,
            access_key=crawler.settings["AWS_ACCESS_KEY_ID"],
            secret_key=crawler.settings["AWS_SECRET_ACCESS_KEY"],
            session_token=crawler.settings["AWS_SESSION_TOKEN"],
            acl=crawler.settings["AWS_S3_ACL"] or None,
            endpoint_url=crawler.settings["AWS_ENDPOINT_URL"] or None,
            default_region=crawler.settings["AWS_DEFAULT_REGION"] or None,
        )
        
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        return extension
    
    
    def __init__(
        self, 
        s3_uri, 
        log_buffer, 
        access_key, 
        secret_key, 
        session_token,
        acl,
        endpoint_url,
        default_region,
    ):
        
        self.s3_uri = s3_uri
        self.log_buffer = log_buffer
        
        u = urlparse(self.s3_uri) # An URI object
        
        self.bucketname = u.hostname
        self.access_key = u.username or access_key
        self.secret_key = u.password or secret_key
        self.session_token = session_token
        self.default_region = default_region
        self.keyname = u.path[1:]  # remove first "/"
        self.acl = acl
        self.endpoint_url = endpoint_url
        
        import botocore.session
        session = botocore.session.get_session()
        self.s3 = session.create_client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=self.session_token,
            endpoint_url=self.endpoint_url
        )
    
    def spider_closed(self, spider):
        self.log_buffer.seek(0)
        kwargs = {"ACL": self.acl} if self.acl else {}
        self.s3_client.put_object(
            Bucket=self.bucketname, 
            Key=self.keyname, 
            Body=self.log_buffer.read(), 
            **kwargs
        )
        self.log_buffer.close()


