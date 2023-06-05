# Standard library imports
from collections import ChainMap
from pathlib import Path
import logging
from urllib.parse import urlparse

# Related third party imports
from scrapy import signals
from scrapy.extensions.feedexport import FeedExporter
from scrapy.extensions.feedexport import build_storage
from scrapy.exceptions import NotConfigured
from scrapy.settings import Settings


logger = logging.getLogger(__name__)


class DummyCrawler:
    """
    Used to initalize a FeedStorage object, with FEEED_STORAGES settings
    overridden by LOG_STORAGES settings.
    """

    s3_feed_storage_settings = {
        "FEED_STORAGE_S3_ACL": "LOG_STORAGE_S3_ACL",
        "AWS_ENDPOINT_URL": "LOG_STORAGE_AWS_ENDPOINT_URL",
    }
    gcs_feed_storage_settings = {
        "GCS_PROJECT_ID": "LOG_STORAGE_GCS_PROJECT_ID",
        "FEED_STORAGE_GCS_ACL": "LOG_STORAGE_GCS_ACL",
    }
    ftp_feed_storage_settings = {"FEED_STORAGE_FTP_ACTIVE": "LOG_STORAGE_FTP_ACTIVE"}
    defaults = {
        **s3_feed_storage_settings,
        **gcs_feed_storage_settings,
        **ftp_feed_storage_settings,
    }

    def __init__(self, settings):
        # Update FEED_EXPORT settings with LOG_EXPORT settings
        settings = settings.copy_to_dict()

        for feed_setting, log_setting in self.defaults.items():
            if log_setting in settings:
                settings[feed_setting] = settings.get(log_setting)

        self.settings = Settings(settings)


class LogExporter(FeedExporter):
    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(crawler)
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.engine_stopped, signal=signals.engine_stopped)
        return extension

    def __init__(self, crawler):
        self.crawler = crawler
        self.spidercls = crawler.spidercls
        self.settings = crawler.settings

        self.log_file = Path(self.settings.get("LOG_FILE"))
        self.delete_local = self.settings.getbool("LOG_EXPORTER_DELETE_LOCAL", False)

        uri = self.settings.get("LOG_URI")
        uri = str(uri)  # handle pathlib.Path objects
        uri_params = self._get_uri_params(
            self.spidercls, self.settings.get("LOG_URI_PARAMS")
        )
        self.uri = uri % uri_params
        self.scheme = urlparse(uri).scheme

        if not self.uri or not self.log_file:
            raise NotConfigured(
                "To use the SCRAPY LOG EXPORTER extension, "
                "you must set the LOG_URI setting."
            )

        # Load storages
        self.feed_storages = self._load_components("FEED_STORAGES")
        self.log_storages = self._load_components("LOG_STORAGES")
        self.storages = ChainMap(self.log_storages, self.feed_storages)

        if not self._storage_supported():
            raise NotConfigured

        self.storage = self._get_storage()

    def spider_opened(self, spider):
        self.storage_file = self.storage.open(spider)

    def engine_stopped(self):
        with self.log_file.open("rb") as log:
            self.storage_file.write(log.read())

        self.storage.store(self.storage_file)

        if self.delete_local:
            self.log_file.unlink()

    def _storage_supported(self) -> bool:
        if self.scheme in self.storages:
            try:
                self._get_storage()
                return True
            except NotConfigured as e:
                logger.error(
                    f"Disabled log storage scheme: {self.scheme}. Reason: {str(e)}"
                )
        else:
            logger.error(f"Unknown log storage scheme: {self.scheme}")
        return False

    def _get_storage(self) -> object:
        storagecls = self.storages[self.scheme]
        # override feed options with log options
        storagecls_crawler = DummyCrawler(self.settings)

        def build_instance(builder, *preargs):
            return build_storage(builder, self.uri, feed_options={}, preargs=preargs)

        if storagecls_crawler and hasattr(storagecls, "from_crawler"):
            instance = build_instance(storagecls.from_crawler, storagecls_crawler)
            method_name = "from_crawler"
        elif hasattr(storagecls, "from_settings"):
            instance = build_instance(
                storagecls.from_settings, storagecls_crawler.settings
            )
            method_name = "from_settings"
        else:
            instance = build_instance(storagecls)
            method_name = "__new__"
        if instance is None:
            raise TypeError(f"{storagecls.__qualname__}.{method_name} returned None")
        return instance
