import gzip
import hashlib
import os
from urllib.parse import quote, urlparse
import certifi
import pymysql
from curl_cffi import requests
import db_config_1 as db
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import re
from parsel import Selector
import get_datadom_token as dt

datadom_token = dt.update_token()
print(datadom_token)
current_date_for_file = (datetime.now()).strftime("%Y_%m_%d")


def sha256_hash(text):
    if not text:
        return None
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_video_url(url):
    """Normalize video/audio URLs so duplicate embeds become one URL."""
    # Remove query string and fragment
    url = url.split("?")[0].split("#")[0]
    # Spotify
    if "open.spotify.com" in url:
        m = re.search(r"/(?:embed/)?episode/([A-Za-z0-9]+)", url)
        if m:
            return f"https://open.spotify.com/episode/{m.group(1)}"
        m = re.search(r"/(?:embed/)?show/([A-Za-z0-9]+)", url)
        if m:
            return f"https://open.spotify.com/show/{m.group(1)}"
        m = re.search(r"/(?:embed/)?track/([A-Za-z0-9]+)", url)
        if m:
            return f"https://open.spotify.com/track/{m.group(1)}"
    # YouTube
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def insert_article(data):
    conn = db.get_db_connection(db.db_name)
    try:
        with conn.cursor() as cur:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            updates = ", ".join(
                [f"{col}=VALUES({col})" for col in data.keys()]
            )
            query = f"""
                INSERT IGNORE INTO {db.data_table}
                ({columns})
                VALUES ({placeholders})
            """
            cur.execute(query, tuple(data.values()))
        conn.commit()
    finally:
        conn.close()


def update_status(keyword, url, status):
    conn = db.get_db_connection(db.db_name)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE {db.link_table} SET status=%s WHERE article_url=%s",
            (status, url)
        )
        print(f"{keyword} :: {status} Status updated successfully ")
    conn.commit()

def clean(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_article(html, keyword, hash_key, search_hash_key):
    sel = Selector(text=html)
    # --------------------------------------------------------
    # Basic Metadata
    # --------------------------------------------------------

    permalink = sel.xpath('//link[@rel="canonical"]/@href').get("")
    domain = "constructionweekonline.com"
    # Title
    title = sel.xpath('normalize-space(//h1[contains(@class,"entry-title")])').get("")
    # Description / Subtitle
    media_title = sel.xpath('normalize-space(//h1[contains(@class,"entry-title")]/following-sibling::p[1])').get("")
    if not media_title:
        media_title = title

    print(title)
    print(media_title)

    title = title.replace(" - Construction Week Online", "").strip()

    subtitle = (
        sel.xpath('normalize-space((//*[contains(@class,"entry-subtitle")])[1])').get()
        or sel.xpath('normalize-space((//*[contains(@class,"excerpt")])[1])').get()
        or sel.xpath('//meta[@property="og:description"]/@content').get("")
    )

    description = sel.xpath('//meta[@name="description"]/@content').get("")

    publication_name = "constructionweekonline"

    created_time = (
        sel.xpath('//meta[@property="article:published_time"]/@content').get("")
    )
    if created_time:
        dt = datetime.fromisoformat(created_time)
        created_time = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(created_time)
    modified_time = (
        sel.xpath('//meta[@property="article:modified_time"]/@content').get("")
    )
    if modified_time:
        dt = datetime.fromisoformat(modified_time)
        modified_time = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(modified_time)
    author = (
        # sel.xpath('normalize-space((//*[contains(@class,"author")]//a)[1])').get()
        sel.xpath('normalize-space(//div[contains(@class,"entry-meta")]//a[contains(@class,"author-link")])').get()
        or sel.xpath('//meta[@name="twitter:data1"]/@content').get("")
    )

    # category = (sel.xpath('//meta[@property="article:section"]/@content').get(""))
    category = ", ".join(sel.xpath('//span[contains(@class,"cat-links")]//a[@rel="category tag"]/text()').getall())

    tags = sel.xpath('//meta[@property="article:tag"]/@content').getall()
    reading_time = (sel.xpath('//meta[@name="twitter:data2"]/@content').get(""))
    # --------------------------------------------------------
    # Main Article Node
    # --------------------------------------------------------
    article = (
        sel.xpath('(//div[contains(@class,"entry-content")])[1]')
        or sel.xpath('(//article)[1]')
    )
    # --------------------------------------------------------
    # Article Text
    # --------------------------------------------------------
    paragraphs = article.xpath('''
        .//*[
            self::p
            or self::h2
            or self::h3
            or self::h4
            or self::blockquote
            or self::li
        ]
    ''')
    body = []
    for p in paragraphs:
        txt = " ".join(
            p.xpath('.//text()[normalize-space()]').getall()
        )
        txt = clean(txt)
        if not txt:
            continue
        lower = txt.lower()
        if lower.startswith("read more"):
            continue
        if "read more below" in lower:
            continue
        if "recommended" == lower:
            continue
        body.append(txt)
    message = " ".join(body)
    message = re.sub(r'\s+', ' ', message).strip()
    footer_text = sel.xpath(
        'normalize-space(.//footer[contains(@class,"entry-footer")])'
    ).get("")
    if footer_text:
        message += " " + footer_text
    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------
    json_text = sel.xpath(
        '//script[@type="application/ld+json" and contains(@class,"rank-math-schema-pro")]/text()').get()
    featured_image = None
    if json_text:
        data = json.loads(json_text)
        graph = data.get("@graph", [])
        image_id = None
        # Find the WebPage object
        for item in graph:
            if item.get("@type") == "WebPage":
                image = item.get("primaryImageOfPage", {})
                image_id = image.get("@id")
                break
        # Find the corresponding ImageObject
        if image_id:
            for item in graph:
                if item.get("@type") == "ImageObject" and item.get("@id") == image_id:
                    featured_image = item.get("url")
                    break
    print(featured_image)
    # Article images
    article = sel.xpath('//article[1]')
    article_images = article.xpath("""
    .//figure[contains(@class,"wp-block-image")]//img/@data-lazy-src |
    .//figure[contains(@class,"wp-block-image")]//img/@src |
    .//div[contains(@class,"wp-block-image")]//img/@data-lazy-src |
    .//div[contains(@class,"wp-block-image")]//img/@src
    """).getall()
    # Merge
    images = []
    if featured_image and featured_image.startswith("http"):
        images.append(featured_image)
    images.extend([
        img for img in article_images
        if img and img.startswith("http")
    ])
    # Remove duplicates while preserving order
    images = list(dict.fromkeys(images))

    # # --------------------------------------------------------
    # # Images
    # # --------------------------------------------------------
    # json_text = sel.xpath(
    #     '//script[@type="application/ld+json" '
    #     'and contains(@class,"rank-math-schema-pro")]/text()'
    # ).get()
    # featured_image = None
    # featured_image_alt = None
    # if json_text:
    #     data = json.loads(json_text)
    #     graph = data.get("@graph", [])
    #     image_id = None
    #     # Find WebPage -> primaryImageOfPage
    #     for item in graph:
    #         if item.get("@type") == "WebPage":
    #             image = item.get("primaryImageOfPage", {})
    #             image_id = image.get("@id")
    #             break
    #     # Find ImageObject -> URL
    #     if image_id:
    #         for item in graph:
    #             if (
    #                     item.get("@type") == "ImageObject"
    #                     and item.get("@id") == image_id
    #             ):
    #                 featured_image = item.get("url")
    #                 break
    # # --------------------------------------------------------
    # # Get ALT of featured image from page source
    # # --------------------------------------------------------
    # if featured_image:
    #     featured_image_alt = sel.xpath(
    #         '//img[@src=$image_url]/@alt | '
    #         '//img[@data-lazy-src=$image_url]/@alt',
    #         image_url=featured_image
    #     ).get()
    #     # If exact match is not found, try URL without query string
    #     if not featured_image_alt:
    #         featured_image_clean = featured_image.split("?")[0]
    #         featured_image_alt = sel.xpath(
    #             '//img[@src=$image_url]/@alt | '
    #             '//img[@data-lazy-src=$image_url]/@alt',
    #             image_url=featured_image_clean
    #         ).get()
    # # --------------------------------------------------------
    # # Article images
    # # --------------------------------------------------------
    # article = sel.xpath('//article[1]')
    # article_image_nodes = article.xpath("""
    #     .//figure[contains(@class,"wp-block-image")]//img |
    #     .//div[contains(@class,"wp-block-image")]//img
    # """)
    # # --------------------------------------------------------
    # # Create image objects
    # # --------------------------------------------------------
    # image_data = []
    # # Featured image
    # if featured_image and featured_image.startswith("http"):
    #     image_data.append({
    #         "link": featured_image,
    #         "content": featured_image_alt if featured_image_alt else None
    #     })
    # # Article images
    # for img_node in article_image_nodes:
    #     img_url = (
    #             img_node.xpath('./@data-lazy-src').get()
    #             or img_node.xpath('./@src').get()
    #     )
    #     alt = img_node.xpath('./@alt').get()
    #     if img_url and img_url.startswith("http"):
    #         image_data.append({
    #             "link": img_url,
    #             "content": alt if alt else None
    #         })
    # # --------------------------------------------------------
    # # Remove duplicate images
    # # --------------------------------------------------------
    # seen = set()
    # images = []
    # for item in image_data:
    #     if item["link"] not in seen:
    #         seen.add(item["link"])
    #         images.append(item)
    # print("Images:")
    # print(json.dumps(images, ensure_ascii=False, indent=2))
    # --------------------------------------------------------
    # Videos
    # --------------------------------------------------------
    videos = []
    # --------------------------------------------------------
    # Method 1: Level4 embedded video
    # --------------------------------------------------------
    script = article.xpath(
        './/script[contains(@src,"media.level4.pw/embed")]/@src'
    ).get()

    video_id = None

    if script:
        m = re.search(r'/embed/([A-Za-z0-9]+)\.js', script)
        if m:
            video_id = m.group(1)
    if not video_id:
        iframe_id = article.xpath('.//iframe[contains(@id,"pjsfrrsl4")]/@id').get()
        if iframe_id:
            m = re.search(r'-(.+)$', iframe_id)
            if m:
                video_id = m.group(1)
    if video_id:
        videos.append(
            f"https://media.level4.pw/play/{video_id}/{video_id}.m3u8"
        )

    # --------------------------------------------------------
    # Method 2: Any iframe embeds (Spotify, YouTube, Vimeo, etc.)
    # --------------------------------------------------------
    videos.extend(article.xpath('//iframe[@data-testid="embed-iframe"]/@src').getall())
    videos = list(dict.fromkeys(
        url.strip()
        for url in videos
        if url and url.startswith("http")
    ))
    # --------------------------------------------------------
    # Audio
    # --------------------------------------------------------
    audios = article.xpath('''
        .//audio/@src
        |
        .//audio/source/@src
    ''').getall()
    audios = list(dict.fromkeys(audios))
    # --------------------------------------------------------
    # Article ID
    # --------------------------------------------------------
    post_id = sel.xpath('//*[@id[starts-with(.,"post-")]]/@id').get("")
    article_id = ""
    if post_id:
        m = re.search(r'post-(\d+)', post_id)
        if m:
            article_id = m.group(1)
    print(article_id)
    # --------------------------------------------------------
    # Country
    # --------------------------------------------------------
    country = "AE"
    # -------------------------------------------------------
    # Return Dictionary
    # --------------------------------------------------------
    images = images if images else None
    videos = videos if videos else None
    audios = audios if audios else None
    data =  {
        "title": clean(title),
        "subtitle": clean(subtitle),
        "message": message,
        "created_time": created_time,
        "modified_time": modified_time,
        "source": "News",
        "domain": domain,
        "publication_name": publication_name,
        "journalist": author,
        "country": country,
        "description": clean(description),
        "conversation_stream": message,
        "permalink": permalink,
        "media_title": media_title,
        "category": category,
        "tags": ", ".join(tags),
        "reading_time": reading_time,
        "keyword": keyword,
        "article_id": article_id,
        "image_urls": json.dumps(images) if images else None,
        "video_urls": json.dumps(videos) if videos else None,
        "audio_urls": json.dumps(audios) if audios else None,
        "reach": "",
        "web_shares": "",
        "engagement": "",
        "hash_key": hash_key,
        "search_hash_key": search_hash_key,
        "scrape_status": f"extract_{current_date_for_file}_{db.slot}"
    }
    print(json.dumps(data, ensure_ascii=False))
    return data

def fetch_article_data(url, article_id, keyword, search_hash_key):
    hash_key = sha256_hash(url)
    cookies = {
        'datadome': '***HIDDEN***',
    }
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.constructionweekonline.com/',
        'sec-ch-device-memory': '32',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.7871.127", "Google Chrome";v="150.0.7871.127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    }
    file_path = os.path.join(db.PDP_pagesave_path, f"{article_id}.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            html = f.read()
    else:
        response = requests.get(url, cookies=cookies, headers=headers)
        # response = requests.get(
        #     url,
        #     proxies=proxy,
        #     verify=False,
        #     timeout=60
        # )
        # print(response.headers)
        print(response.status_code)
        if response.status_code == 200:
            html = response.text
            file_path = os.path.join(db.PDP_pagesave_path, f"{article_id}.html.gz")
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                f.write(html)
            # file_path = os.path.join(db.PDP_pagesave_path, f"{article_id}.html")
            # with open(file_path, "w", encoding='utf-8') as f:
            #     f.write(html)
        if response.status_code == 405:
            proxy = {
                "http": f'http://{db.proxy_token}:super=true@proxy.scrape.do:8080',
                "https": f'http://{db.proxy_token}:super=true@proxy.scrape.do:8080',
            }
            response = requests.get(url, proxies=proxy, verify=False, timeout=60)
            # print(response.headers)
            print(response.status_code)
            html = response.text
            file_path = os.path.join(db.PDP_pagesave_path, f"{article_id}.html.gz")
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                f.write(html)
        # extract_article(html, keyword)
    try:
        article = extract_article(html, keyword, hash_key, search_hash_key)
        insert_article(article)
        update_status(keyword, url, f"completed_{current_date_for_file}_{db.slot}")
    except Exception as e:
        print(e)
        update_status(keyword, url, "failed")


MAX_THREADS = 3
def main(rows):
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for r in rows:
            futures.append(
                executor.submit(
                    fetch_article_data,
                    r["article_url"], r["article_id"], r['keyword'], r['hash_key']
                )
            )
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("❌ Thread error:", e)


if __name__ == "__main__":
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'pending' ORDER BY ID ASC")
    # cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'failed' ORDER BY ID ASC")
    rows = cur.fetchall()
    print(len(rows))
    main(rows)
    cur.close()
    conn.close()