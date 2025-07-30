# spidercore/spiders/basic.py

import re
import os
import csv
import json
import html
import hashlib
import scrapy
from pathlib import Path
from scrapy import signals
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict
from urllib.parse import urlparse

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
        elif self.export == "xml":
            self.write_xml_sitemap()
        elif self.export == "json":
            self.write_json_sitemap()
        elif self.export == "csv":
            self.write_csv_sitemap()
        else:
            self.logger.warning(f"[!] Unsupported export format: {self.export}")

        if not self._crawl_logged:
            self._crawl_logged = True
            self.logger.info(f"[✓] Crawl complete: {len(self.visited_urls)} pages")

    def write_html_sitemap(self):
        from collections import defaultdict
        import datetime
        from urllib.parse import urlparse

        def build_tree(entries):
            tree = {}
            for entry in entries:
                parsed = urlparse(entry["url"])
                path = parsed.path

                # Group root-level URLs like "/" and "/foo.html" under "/"
                if not path or path == "/" or path.count("/") == 1:
                    node = tree.setdefault("/", {})
                    node.setdefault("__pages__", []).append(entry)
                    continue

                # Split deeper paths and build nested structure
                parts = [p for p in path.strip("/").split("/") if p]
                node = tree
                for i, part in enumerate(parts):
                    is_leaf = i == len(parts) - 1
                    if is_leaf and '.' in part: # Don't create children for files like .html
                        node.setdefault("__pages__", []).append(entry)
                        break
                    node = node.setdefault(part, {})
                else:
                    node.setdefault("__pages__", []).append(entry)
            return tree


        def render_list(tree, level=0):
            html = ""
            for key, subtree in tree.items():
                if key == "__pages__":
                    pages = subtree
                    for i, entry in enumerate(pages):
                        last = " last-page" if i == len(pages) - 1 else ""
                        title = entry["title"].replace('"', "&quot;") if entry["title"] else entry["url"]
                        html += f'<li class="lpage{last}"><a href="{entry["url"]}" title="{title}">{title}</a></li>\n'
                    continue

                count = count_leaf_pages(subtree)
                html += f'<li class="lhead">{key}/  <span class="lcount">{count} pages</span></li>\n'
                html += f'<li><ul class="level-{level+1}">\n'
                html += render_list(subtree, level + 1)
                html += "</ul></li>\n"
            return html

        def count_leaf_pages(subtree):
            count = 0
            for k, v in subtree.items():
                if k == "__pages__":
                    count += len(v)
                else:
                    count += count_leaf_pages(v)
            return count

        if self._html_sitemap_written:
            return
        self._html_sitemap_written = True

        tree = build_tree(self.page_data)
        now = datetime.datetime.utcnow().strftime("%Y, %B %d")

        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
                <html lang="en"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                <title>{self.domain} Site Map</title>
                <meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport">
                <style type="text/css">
                body {{
                    background-color: #fff;
                    font-family: "Roboto", "Helvetica", "Arial", sans-serif;
                    margin: 0;
                }}

                #top {{
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: #fff;
                    text-align: center;
                    padding: 40px 20px 60px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                }}

                .header-wrapper {{
                    max-width: 700px;
                    margin: auto;
                }}

                .site-title {{
                    font-size: 32px;
                    font-weight: bold;
                    margin: 0 0 10px;
                    letter-spacing: 0.5px;
                }}

                .meta {{
                    font-size: 16px;
                    margin-bottom: 20px;
                }}

                .meta span {{
                    display: block;
                    margin: 4px 0;
                }}

                .homepage-button {{
                    display: inline-block;
                    margin-top: 10px;
                    background-color: #ffffff;
                    color: #4facfe;
                    padding: 10px 20px;
                    border-radius: 25px;
                    text-decoration: none;
                    font-weight: bold;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                }}

                .homepage-button:hover {{
                    background-color: #e8f6ff;
                    color: #007acc;
                    box-shadow: 0 6px 14px rgba(0,0,0,0.2);
                }}

                #cont {{
                    position: relative;
                    border-radius: 6px;
                    box-shadow: 0 16px 24px 2px rgba(0, 0, 0, 0.14), 0 6px 30px 5px rgba(0, 0, 0, 0.12), 0 8px 10px -5px rgba(0, 0, 0, 0.2);
                    background: #f3f3f3;
                    margin: -20px 30px 0px 30px;
                    padding: 20px;
                }}

                a:link, a:visited {{ color: #0180AF; text-decoration: underline; }}
                a:hover {{ color: #666; }}
                #footer {{ padding: 10px; text-align: center; }}
                ul {{ margin: 0px; padding: 0px; list-style: none; }}
                li {{ margin: 0px; }}
                li ul {{ margin-left: 20px; }}
                .lhead {{ background: #ddd; padding: 10px; margin: 10px 0px; }}
                .lcount {{ padding: 0px 10px; }}
                .lpage {{ border-bottom: #ddd 1px solid; padding: 5px; }}
                .last-page {{ border: none; }}
                </style>
                </head>
                <body>
                <div id="top">
                    <div class="header-wrapper">
                        <h1 class="site-title">{self.domain} Site Map</h1>
                        <div class="meta">
                            <span>Last updated: {now}</span>
                            <span>Total pages: {len(self.page_data)}</span>
                        </div>
                        <a class="homepage-button" href="{self.start_url}" target="_blank">Go to Target Site</a>
                    </div>
                </div>
                <div id="cont">
                <ul class="level-0">
                """)

                f.write(render_list(tree))
                f.write("</ul></div></body></html>\n")
            self.logger.info(f"[✓] HTML sitemap written to: {self.output_file}")
        except Exception as e:
            self.logger.error(f"[!] Failed to write HTML sitemap: {e}")
    
    def write_xml_sitemap(self):
        try:
            now = datetime.utcnow().replace(microsecond=0).isoformat() + "+00:00"
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

                for entry in self.page_data:
                    url = html.escape(entry["url"])
                    f.write("  <url>\n")
                    f.write(f"    <loc>{url}</loc>\n")
                    f.write(f"    <lastmod>{now}</lastmod>\n")
                    f.write("    <priority>0.80</priority>\n")
                    f.write("  </url>\n")

                f.write("</urlset>\n")
            self.logger.info(f"[✓] XML sitemap written to: {self.output_file}")
        except Exception as e:
            self.logger.error(f"[!] Failed to write XML sitemap: {e}")

    def write_json_sitemap(self):
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.page_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"[✓] JSON sitemap written to: {self.output_file}")
        except Exception as e:
            self.logger.error(f"[!] Failed to write JSON sitemap: {e}")

    def write_csv_sitemap(self):
        try:
            with open(self.output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                header = ["url", "title"] if self.include_content else ["url"]
                writer.writerow(header)
                for entry in self.page_data:
                    if self.include_content:
                        writer.writerow([entry["url"], entry.get("title", "")])
                    else:
                        writer.writerow([entry["url"]])
            self.logger.info(f"[✓] CSV sitemap written to: {self.output_file}")
        except Exception as e:
            self.logger.error(f"[!] Failed to write CSV sitemap: {e}")
