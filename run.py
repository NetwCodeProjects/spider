# run.py

import argparse
import subprocess

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

    # Map arguments to -a key=value format
    cmd = [
        "scrapy", "crawl", "basic",
        "-a", f"url={args.url}",
        "-a", f"max_pages={args.max_pages}",
        "-a", f"export={args.export}",
        "-a", f"download={'true' if args.download else 'false'}",
        "-a", f"content={'true' if args.content else 'false'}"
    ]

    if args.filter_url:
        cmd += ["-a", f"filter={args.filter_url}"]
    if args.pattern:
        cmd += ["-a", f"pattern={args.pattern}"]

    print("[*] Running:", " ".join(cmd))
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
