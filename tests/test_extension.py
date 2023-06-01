
import pytest

from pathlib import Path

from scrapy.settings import Settings
from scrapy_s3logstorage.extension import S3LogStorage


@pytest.fixture
def crawler():

    class Signals:

        def connect(self, *args, **kwargs):
            pass

    class Crawler:

        def __init__(self, settings: dict):
            self.settings = Settings(settings)
            self.signals = Signals()

    return Crawler  # Return the class, intialize with settings dict


@pytest.fixture
def s3_client():

    class S3Client:

        def __init__(self):
            self.last_put_object_kwargs = None

        def put_object(self, **kwargs):
            self.last_put_object_kwargs = kwargs

    return S3Client()


class TestS3LogStorage:

    @pytest.fixture
    def temp_log(self, tmp_path):
        log_path = tmp_path / 'log.log'
        log_path.touch()
        return log_path

    @pytest.fixture
    def settings(self, temp_log):
        return Settings({
            'LOG_FILE': str(temp_log),
            'S3_LOG_BUCKET': 'my-bucket',
            'S3_LOG_DELETE_LOCAL': False,
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
            'AWS_SESSION_TOKEN': 'test-session-token',
            'S3_LOG_ACL': 'public-read',
            'AWS_ENDPOINT_URL': 'https://s3.amazonaws.com',

            # Set settings whose default value is deprecated to a future-proof value
            'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
            'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
            'FEED_EXPORT_ENCODING': 'utf-8'
        })

    @pytest.fixture
    def s3_log_storage_extension(self, crawler, settings):
        return S3LogStorage.from_crawler(crawler(settings))

    def test_extension_attrs(
        self,
        s3_log_storage_extension,
        temp_log
    ):
        temp_log = Path(temp_log)
        assert temp_log.exists()

        assert s3_log_storage_extension.log == temp_log
        assert s3_log_storage_extension.delete_log == False
        assert s3_log_storage_extension.s3_log_bucket == 'my-bucket'
        assert s3_log_storage_extension.s3_uri == 's3://my-bucket/log.log'
        assert s3_log_storage_extension.access_key == 'test-access-key'
        assert s3_log_storage_extension.secret_key == 'test-secret-key'
        assert s3_log_storage_extension.session_token == 'test-session-token'
        assert s3_log_storage_extension.acl == 'public-read'
        assert s3_log_storage_extension.endpoint_url == 'https://s3.amazonaws.com'

        assert hasattr(s3_log_storage_extension, 's3')

    @pytest.mark.parametrize("delete_log", [True, False])
    def test_engine_stopped(
        self,
        s3_log_storage_extension,
        s3_client,
        delete_log
    ):
        s3_log_storage_extension.delete_log = delete_log
        s3_log_storage_extension.s3 = s3_client

        # Has to be read before engine_stopped() is called
        # because engine_stopped() may delete the log
        with s3_log_storage_extension.log.open('rb') as f:
            log_bytes = f.read()

        s3_log_storage_extension.engine_stopped()

        # Check that the log was uploaded to S3
        assert s3_client.last_put_object_kwargs == {
            'Bucket': 'my-bucket',
            'Key': 'log.log',
            'Body': log_bytes,
            'ACL': 'public-read'
        }

        # If delete_log is True, check that the log was deleted
        if delete_log:
            assert not s3_log_storage_extension.log.exists()
        else:
            assert s3_log_storage_extension.log.exists()
