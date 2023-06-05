
import scrapy


class S3LogSpider(scrapy.Spider):
    name = "log"
    start_urls = ["https://www.google.com/"]

    def parse(self, response):
        yield {
            "scrapy logexport": "test"
        }
