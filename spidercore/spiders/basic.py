# spidercore/spiders/basic.py

import scrapy
from scrapy import signals
from urllib.parse import urlparse
import re
import os
from pathlib import Path
import hashlib

class BasicSpider(scrapy.Spider):
    name = "basic"

    def __init__(
        self,
        url=None,
        filter=None,
        pattern=None,
        download=False,
        max_pages=250,
        export="html",
        content=False,
        *args,
        **kwargs
    ):
        if not url:
            raise ValueError("Missing required argument: url")
        if url and not urlparse(url).scheme:
            url = "https://" + url  # default to HTTPS if missing

        parsed = urlparse(url)
        self._html_sitemap_written = False
        self._crawl_logged = False
        self.domain = parsed.netloc
        self.allowed_domains = [self.domain]
        self.start_urls = [url]
        self.filter = filter
        self.pattern = pattern
        self.download = download in ["1", "true", "True"]
        self.max_pages = int(max_pages)
        self.export = export.lower()
        self.include_content = content in ["1", "true", "True"]
        self.visited_urls = set()
        self.assets = set()
        self.page_data = []
        self.asset_hashes = set()
        self.start_url = url
        self.output_dir = Path(f"downloads_{self.domain.replace('.', '_')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.unusual_log_path = self.output_dir / "unusual-links.txt"
        self.unusual_log_file = open(self.unusual_log_path, "w", encoding="utf-8")
        self.output_file = self.output_dir / f"sitemap_{self.domain.replace('.', '_')}.{self.export}"
        self.asset_dir = f"downloads_{self.domain.replace('.', '_')}"
        Path(self.asset_dir).mkdir(exist_ok=True)

        super().__init__(*args, **kwargs)

    def log_unusual_link(self, url, reason):
        self.unusual_log_file.write(f"{url}  # Skipped due to: {reason}\n")

    def parse(self, response):
        url = response.url

        if url in self.visited_urls:
            return
        self.visited_urls.add(url)
        self.logger.info(f"[+] Parsed page: {url}")

        # Skip non-HTML responses
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", "ignore")
        if "text/html" not in content_type:
            self.log_unusual_link(response.url, f"skipped non-HTML content ({content_type})")
            return

        if self.filter and self.filter not in url:
            return

        if self.pattern and not re.search(self.pattern, url, re.IGNORECASE):
            return

        title = response.xpath("//title/text()").get() if self.include_content else ""
        self.page_data.append({"url": url, "title": title.strip() if title else ""})

        if self.download:
            for asset in response.css("a::attr(href), link::attr(href), script::attr(src), img::attr(src)"):
                asset_url = response.urljoin(asset.get())
                if re.search(r"\.(pdf|zip|docx|xlsx|pptx)$", asset_url, re.IGNORECASE):
                    if asset_url not in self.assets:
                        self.assets.add(asset_url)
                        yield scrapy.Request(asset_url, callback=self.download_file)

        if len(self.visited_urls) < self.max_pages:
            for href in response.css("a::attr(href)").getall():
                if not href:
                    continue

                if href.startswith("tel:"):
                    self.log_unusual_link(href, "tel link")
                    continue
                if href.startswith("mailto:"):
                    self.log_unusual_link(href, "mailto link")
                    continue
                if href.startswith("javascript:"):
                    self.log_unusual_link(href, "javascript link")
                    continue

                full_url = response.urljoin(href)
                parsed = urlparse(full_url)

                if parsed.scheme not in ["http", "https"]:
                    self.log_unusual_link(full_url, f"non-http scheme: {parsed.scheme}")
                    continue

                yield response.follow(full_url, callback=self.parse)

    def download_file(self, response):
        file_hash = hashlib.sha256(response.body).hexdigest()

        if file_hash in self.asset_hashes:
            self.logger.info(f"[-] Skipped duplicate file (hash matched): {response.url}")
            return

        self.asset_hashes.add(file_hash)
        filename = os.path.basename(urlparse(response.url).path)
        path = os.path.join(self.asset_dir, filename)

        with open(path, "wb") as f:
            f.write(response.body)

        self.logger.info(f"[✓] Downloaded asset: {filename}")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.closed, signal=signals.spider_closed)
        return spider

    def closed(self, reason):
        if hasattr(self, "unusual_log_file"):
            self.unusual_log_file.close()

        if self.export == "html":
            self.write_html_sitemap()

        if not self._crawl_logged:
            self._crawl_logged = True
            self.logger.info(f"[✓] Crawl complete: {len(self.visited_urls)} pages")


    def write_html_sitemap(self):
        if self._html_sitemap_written:
            return
        self._html_sitemap_written = True
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(f"<html><head><title>Sitemap for {self.domain}</title></head><body>\n")
                f.write(f"<h1>Sitemap for {self.domain}</h1>\n")
                f.write(f"<p>Total pages: {len(self.page_data)}</p>\n")
                f.write("<ul>\n")
                for entry in self.page_data:
                    f.write(f'<li><a href="{entry["url"]}">{entry["url"]}</a>')
                    if self.include_content and entry["title"]:
                        f.write(f" — {entry['title']}")
                    f.write("</li>\n")
                f.write("</ul></body></html>\n")
            self.logger.info(f"[✓] HTML sitemap written to: {self.output_file}")
        except Exception as e:
            self.logger.error(f"[!] Failed to write HTML sitemap: {e}")
