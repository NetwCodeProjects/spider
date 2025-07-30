# spidercore/items.py

import scrapy

class SitemapItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    depth = scrapy.Field()
