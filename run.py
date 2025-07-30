# run.py

import argparse
import logging
import time
import sys
from scrapy.utils.log import configure_logging
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from spidercore.spiders.basic import BasicSpider
from spidercore import settings as project_settings

def main():
    parser = argparse.ArgumentParser(description="Run the basic sitemap spider.")
    parser.add_argument("--url", required=True, help="Start URL for the crawl")
    parser.add_argument("--filter-url", help="Only keep URLs matching this substring")
    parser.add_argument("--pattern", help="Regex pattern to match URLs")
    parser.add_argument("--download", action="store_true", help="Download matching assets (PDF, ZIP, etc)")
    parser.add_argument("--max-pages", type=int, default=250, help="Maximum number of pages to crawl")
    parser.add_argument("--export", choices=["json", "csv", "xml", "html"], default="html", help="Export format")
    parser.add_argument("--content", action="store_true", help="Also extract page titles for context")

    args = parser.parse_args()

    # 1. Disable Scrapy's default root handler
    configure_logging(install_root_handler=False)

    # 2. Remove any existing root handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 3. Define the custom formatter and handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(levelname)s] [%(name)s] %(message)s'))

    # 4. Define only the loggers you want active
    allowed_loggers = {
        "scrapy.crawler": logging.INFO,
        "scrapy.statscollectors": logging.INFO,
        "basic": logging.INFO,
    }

    for name in logging.root.manager.loggerDict.keys():
        logger = logging.getLogger(name)
        if name in allowed_loggers:
            logger.handlers = [handler]
            logger.setLevel(allowed_loggers[name])
            logger.propagate = False
        else:
            logger.handlers = []
            logger.setLevel(logging.CRITICAL + 1)
            logger.propagate = False

    # 5. Load Scrapy project settings
    settings = Settings()
    for key in dir(project_settings):
        if key.isupper():
            settings.set(key, getattr(project_settings, key))

    # ASCII flair
    print(r"""
                  :                        ___
                  :                       -   ---___- ,,
       ,,         :         ,,               (' ||    ||
       ::         :         ::              ((  ||    ||/\\  _-_
,,     ::         :         ::     ,,      ((   ||    || || || \\
::     ::         :         ::     ::       (( //     || || ||/
 '::.   '::.      :      .::'   .::'          -____-  \\ |/ \\,/
    '::.  '::.  _/~\_  .::'  .::'       -_-/            |\
      '::.  :::/     \:::  .::'        (_ /          '   \\
        ':::::(       ):::::'         (_ --_  -_-_  \\  / \\  _-_  ,._-_
               \ ___ /                  --_ ) || \\ || || || || \\  ||
         .:::::/`   `\:::::.           _/  )) || || || || || ||/    ||
       .::'   .:\o o/:.   '::.        (_-_-   ||-'  \\  \\/  \\,/   \\,
     .::'   .::  :":  ::.   '::.              |/
   .::'    ::'   ' '   '::    '::.      -_-/  '                 ,,
  ::      ::             ::      ::    (_ /                 _   ||
  ^^      ::             ::      ^^   (_ --_  -_-_   _-_   ( \, ||/\  _-_,
          ::             ::             --_ ) || \\ || \\  /-|| ||_( ||_.
          ^^             ^^            _/  )) || || ||/   (( || || |  ~ ||
                                      (_-_-   ||-'  \\,/   \/\\ \\,\ ,-_-
                                              |/
                                              '
    """)
    print("[*] Spider is crawling")
    time.sleep(2)

    process = CrawlerProcess(settings)
    process.crawl(
        BasicSpider,
        url=args.url,
        filter=args.filter_url,
        pattern=args.pattern,
        download=args.download,
        max_pages=args.max_pages,
        export=args.export,
        content=args.content,
    )
    process.start()

if __name__ == "__main__":
    main()
