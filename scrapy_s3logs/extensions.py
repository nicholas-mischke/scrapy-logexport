
from pathlib import Path
from urllib.parse import urlparse
from scrapy import signals
from scrapy.utils.boto import is_botocore_available

from scrapy import signals
from scrapy.exceptions import NotConfigured

# EXTENSIONS = {
#     'scrapy_s3log.extensions.S3Log': 0,
# }


class S3Log:

    @classmethod
    def from_crawler(cls, crawler):
        log = crawler.settings['LOG_FILE']
        s3_log_bucket = crawler.settings.get('S3_LOG_BUCKET')
        s3_log_delete_local = crawler.settings.getbool('S3_LOG_DELETE_LOCAL')
        
        if not is_botocore_available():
            raise NotConfigured("missing botocore library")

        extension = cls(
            log,
            s3_log_bucket,
            s3_log_delete_local,
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
        log,
        s3_log_bucket,
        s3_log_delete_local,
        access_key,
        secret_key,
        session_token,
        acl,
        endpoint_url,
        default_region,
    ):

        self.log = Path(log)
        self.delete_log = s3_log_delete_local
        
        self.s3_log_bucket = s3_log_bucket
        if self.s3_log_bucket is None:
            return # nothing to do
        
        if self.s3_log_bucket.startswith("s3://"):
            self.s3_uri = f'{self.s3_log_bucket}/{self.log.name}'
        else:
            self.s3_uri = f's3://{self.s3_log_bucket}/{self.log.name}'

        u = urlparse(self.s3_uri)  # An URI object

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
        if self.s3_log_bucket is None:
            return # nothing to do

        with self.log.open('rb') as f:
            file_content = f.read()
            
        kwargs = {"ACL": self.acl} if self.acl else {}
        
        self.s3.put_object(
            Bucket=self.bucketname,
            Key=self.keyname,
            Body=file_content,
            **kwargs
        )

        if self.delete_log:
            self.log.unlink()