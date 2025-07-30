# spidercore/settings.py

BOT_NAME = "spidercore"

SPIDER_MODULES = ["spidercore.spiders"]
NEWSPIDER_MODULE = "spidercore.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5
DEPTH_LIMIT = 5
CLOSESPIDER_PAGECOUNT = 250
FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = 'INFO'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(levelname)s] [%(name)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'basic': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'spidercore': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'scrapy.crawler': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'scrapy.statscollectors': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        # Silence everything else by disabling propagation
        'scrapy.utils.log': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.middleware': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.core.engine': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.extensions.telnet': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.extensions.logstats': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.downloadermiddlewares': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.spidermiddlewares': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.extensions': {
            'level': 'WARNING',
            'propagate': False,
        },
        'scrapy.addons': {
            'level': 'WARNING',
            'propagate': False,
        },
    }
}


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