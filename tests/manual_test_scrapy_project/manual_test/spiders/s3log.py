
import scrapy


class S3LogSpider(scrapy.Spider):
    name = "s3logs"
    start_urls = ["https://www.google.com/"]

    def parse(self, response):
        yield {
            "url": response.url,
            "status": response.status,
            "headers": response.headers,
        }
