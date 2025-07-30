# spidercore/settings.py

BOT_NAME = "spidercore"

SPIDER_MODULES = ["spidercore.spiders"]
NEWSPIDER_MODULE = "spidercore.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5
DEPTH_LIMIT = 5
CLOSESPIDER_PAGECOUNT = 250
LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"

# Enable custom middlewares (optional)
'''
SPIDER_MIDDLEWARES = {
    "spidercore.middlewares.SpidercoreSpiderMiddleware": 543,
}

DOWNLOADER_MIDDLEWARES = {
    "spidercore.middlewares.SpidercoreDownloaderMiddleware": 543,
}

# Enable custom pipeline (optional)
ITEM_PIPELINES = {
    "spidercore.pipelines.SpidercorePipeline": 300,
}
'''