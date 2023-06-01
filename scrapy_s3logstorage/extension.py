
# Standard library imports
from pathlib import Path
from urllib.parse import urlparse

# Related third party imports
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.utils.boto import is_botocore_available


# Adding to scrapy project settings
# EXTENSIONS = {
#     'scrapy_s3logstorage.extension.S3LogStorage': 0,
# }


class S3LogStorage:

    @classmethod
    def from_crawler(cls, crawler):
        log = crawler.settings.get('LOG_FILE')
        s3_log_bucket = crawler.settings.get('S3_LOG_BUCKET')
        s3_log_delete_local = crawler.settings.get(
            'S3_LOG_DELETE_LOCAL', False)

        if not is_botocore_available():
            raise NotConfigured("missing botocore library")

        if s3_log_bucket is None and log is not None:
            raise NotConfigured(
                "S3_LOG_BUCKET appeared in settings but not LOG_FILE. "
                "A log file is required to upload to S3."
            )

        if s3_log_bucket is None:
            raise NotConfigured(
                "scrapy_s3logstorage.extensions.S3LogStorage in EXTENSIONS but "
                "S3_LOG_BUCKET is not set. "
            )

        extension = cls(
            log,
            s3_log_bucket,
            s3_log_delete_local,
            access_key=crawler.settings["AWS_ACCESS_KEY_ID"],
            secret_key=crawler.settings["AWS_SECRET_ACCESS_KEY"],
            session_token=crawler.settings["AWS_SESSION_TOKEN"],
            acl=crawler.settings["S3_LOG_ACL"] or crawler.settings["FEED_STORAGE_S3_ACL"] or None,
            endpoint_url=crawler.settings["AWS_ENDPOINT_URL"] or None,
        )

        crawler.signals.connect(extension.engine_stopped,
                                signal=signals.engine_stopped)
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
        endpoint_url
    ):

        self.log = Path(log)
        self.delete_log = s3_log_delete_local

        self.s3_log_bucket = s3_log_bucket
        if self.s3_log_bucket.startswith("s3://"):
            self.s3_uri = f'{self.s3_log_bucket}/{self.log.name}'
        else:
            self.s3_uri = f's3://{self.s3_log_bucket}/{self.log.name}'

        u = urlparse(self.s3_uri)  # An URI object
        self.access_key = u.username or access_key
        self.secret_key = u.password or secret_key
        self.session_token = session_token
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

    def engine_stopped(self):
        with self.log.open('rb') as f:
            log_bytes = f.read()

        kwargs = {"ACL": self.acl} if self.acl else {}

        self.s3.put_object(
            Bucket=self.s3_log_bucket,
            Key=self.keyname,
            Body=log_bytes,
            **kwargs
        )

        if self.delete_log:
            self.log.unlink()
