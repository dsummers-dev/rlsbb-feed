#!/usr/bin/env python3
"""
Fetch the RLSBB homepage, extract the 'Recommended movies' sidebar widget,
and write an RSS feed where every item is a poster + link to the movie page.
pubDates are staggered 1 minute apart so item order stays stable across refreshes.
"""
import re
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://rlsbb.ru/"
OUTPUT     = "recommended-movies.rss"
FEED_TITLE = "RLSBB — Recommended Movies"
FEED_DESC  = "Live poster wall from the RLSBB sidebar"


def slug_to_title(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    head = re.split(
        r"-(?:\d{4}|1080p|720p|2160p|480p|web|webrip|web-dl|amzn|nf|dsnp|"
        r"bluray|bdrip|dvdrip|hdtv|hc|x264|x265|hevc|aac|ddp|atmos|multi)",
        slug, maxsplit=1
    )[0]
    t = head.replace("-", " ").replace("_", " ").strip()
    return t.title() if t else slug.replace("-", " ").title()


def main() -> None:
    html = requests.get(
        SOURCE_URL, timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
    ).text
    soup = BeautifulSoup(html, "html.parser")

    widget = None
    for aside in soup.find_all("aside"):
        h2 = aside.find("h2", class_="widget-title")
        if h2 and "Recommended movies" in h2.get_text():
            widget = aside
            break
    if widget is None:
        raise SystemExit("Widget 'Recommended movies' not found.")

    now = datetime.now(timezone.utc)
    items = []
    for i, a in enumerate(widget.select("a[href]")):
        img = a.find("img")
        if not img or not img.get("src"):
            continue
        link  = a["href"]
        image = img["src"]
        title = slug_to_title(link)

        item_date = (now - timedelta(minutes=i)).strftime("%a, %d %b %Y %H:%M:%S +0000")

        items.append(f"""    <item>
      <title>{escape(title)}</title>
      <link>{escape(link)}</link>
      <guid isPermaLink="true">{escape(link)}</guid>
      <description><![CDATA[<a href="{link}"><img src="{image}" alt="{escape(title)}" /></a>]]></description>
      <enclosure url="{escape(image)}" type="image/jpeg" length="0" />
      <pubDate>{item_date}</pubDate>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <link>{SOURCE_URL}</link>
    <description>{escape(FEED_DESC)}</description>
    <language>en-us</language>
    <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Wrote {len(items)} items to {OUTPUT}")


if __name__ == "__main__":
    main()
