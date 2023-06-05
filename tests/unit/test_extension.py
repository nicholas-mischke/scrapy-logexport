import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapy_logexport.extension import DummyCrawler, LogExporter

from pathlib import Path

from scrapy.settings import Settings

from scrapy.settings import Settings
from scrapy import Spider
from scrapy.extensions.feedexport import (
    FileFeedStorage,
    FTPFeedStorage,
    S3FeedStorage,
    GCSFeedStorage,
)


@pytest.fixture
def bare_bone_settings():
    return Settings(
        {
            "LOG_FILE": str(Path("scrapy.log")),
            "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "FEED_EXPORT_ENCODING": "utf-8",
        }
    ).copy_to_dict()


@pytest.fixture
def mock_crawler():
    class Signals:
        def connect(self, *args, **kwargs):
            pass

    class Crawler:
        spidercls = Spider(name="test_spider")

        def __init__(self, settings: dict):
            self.settings = Settings(settings)
            self.signals = Signals()

    return Crawler  # Return the class, intialize with settings dict


@pytest.fixture
def mock_storage(tmp_path):
    class Storage:
        def __init__(self):
            self.called_open = 0
            self.called_store = 0

        def open(self, *args, **kwargs):
            self.called_open += 1
            storage_file = Path(tmp_path) / 'temp.log'
            return storage_file.open('wb') # Don't return Path object, return file object

        def store(self, file):
            file.close()
            self.called_store += 1

    return Storage()


class TestDummyCrawler:
    def test_settings(self):
        settings = Settings(
            {
                "FEED_STORAGE_S3_ACL": "default",
                "LOG_STORAGE_S3_ACL": "not-default",
                "AWS_ENDPOINT_URL": "default",
                "LOG_STORAGE_AWS_ENDPOINT_URL": "not-default",
                "GCS_PROJECT_ID": "default",
                "LOG_STORAGE_GCS_PROJECT_ID": "not-default",
                "FEED_STORAGE_GCS_ACL": "default",
                "LOG_STORAGE_GCS_ACL": "not-default",
                "FEED_STORAGE_FTP_ACTIVE": "default",
                "LOG_STORAGE_FTP_ACTIVE": "not-default",
            }
        )
        dummy_crawler = DummyCrawler(settings)

        assert isinstance(dummy_crawler.settings, Settings)
        assert dummy_crawler.settings.get("FEED_STORAGE_S3_ACL") == "not-default"
        assert dummy_crawler.settings.get("AWS_ENDPOINT_URL") == "not-default"
        assert dummy_crawler.settings.get("GCS_PROJECT_ID") == "not-default"
        assert dummy_crawler.settings.get("FEED_STORAGE_GCS_ACL") == "not-default"
        assert dummy_crawler.settings.get("FEED_STORAGE_FTP_ACTIVE") == "not-default"


class TestLogExporter:
    @pytest.mark.parametrize(
        "settings, expected_storage, expected_delete_local",
        [
            (
                {
                    "LOG_URI": str(Path(__file__).parent / "test.log"),
                    "LOG_EXPORTER_DELETE_LOCAL": True,
                },
                FileFeedStorage,
                True,
            ),
            ({"LOG_URI": "s3://bucket/test.log"}, S3FeedStorage, False),
            ({"LOG_URI": "gs://bucket/test.log"}, GCSFeedStorage, False),
            (
                {"LOG_URI": "ftp://user:password@example.com:21/path/to/file.log"},
                FTPFeedStorage,
                False,
            ),
        ],
    )
    def test__init__(
        self,
        mock_crawler,
        bare_bone_settings,
        settings,
        expected_storage,
        expected_delete_local,
    ):
        settings.update(bare_bone_settings)

        crawler = mock_crawler(settings)
        exporter = LogExporter.from_crawler(crawler)

        assert exporter.log_file == Path("scrapy.log")
        assert exporter.delete_local == expected_delete_local
        assert exporter.uri == settings.get("LOG_URI")

        assert isinstance(exporter.storage, expected_storage)

    def test_spider_opened(self, mock_crawler, mock_storage, bare_bone_settings):
        settings = {
            "LOG_URI": str(Path(__file__).parent / "test.log")
        }
        settings.update(bare_bone_settings)

        crawler = mock_crawler(settings)
        exporter = LogExporter.from_crawler(crawler)
        exporter.storage = mock_storage

        exporter.spider_opened(Spider(name="test_spider"))

        assert exporter.storage.called_open == 1

    def test_engine_stopped(
        self, mock_crawler, mock_storage, bare_bone_settings, tmp_path
    ):
        log_file = Path(tmp_path / "LOG_FILE.log")
        with open(log_file, "w") as f:
            f.write("test")

        store_file = Path(tmp_path / "LOG_URI.log").open("wb")

        settings = {
            "LOG_FILE": str(log_file),
            "LOG_EXPORTER_DELETE_LOCAL": True,
            "LOG_URI": str(store_file),
            "LOG_EXPORTER_DELETE_LOCAL": True,
        }
        del bare_bone_settings["LOG_FILE"]
        settings.update(bare_bone_settings)

        crawler = mock_crawler(settings)
        exporter = LogExporter.from_crawler(crawler)

        exporter.log_file = log_file
        exporter.storage_file = store_file
        exporter.storage = mock_storage

        exporter.engine_stopped()

        assert Path(tmp_path / "LOG_URI.log").read_text() == "test"
        assert exporter.storage.called_store == 1
        assert not log_file.exists()
