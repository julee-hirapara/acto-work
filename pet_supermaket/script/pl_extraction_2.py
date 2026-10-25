import os
import traceback
from curl_cffi import  requests
from lxml import etree
import hashlib
import db_config_1 as db


# ================================
# HASH GENERATOR
# ================================
def generate_hash(url):
    h = hashlib.sha256(url.encode()).hexdigest()
    num = int(h, 16)
    short_id = str(num)[0:12]
    return short_id

# ================================
# FETCH SITEMAP LINKS
# ================================
def fetch_sitemap_links(sitemap_url, index):
    try:
        print(f"🔍 Fetching: {sitemap_url}")
        FILE_PATH = os.path.join(db.PL_PAGESAVE, f"sitemap_{index}.xml")
        response = requests.get(sitemap_url, timeout=30, impersonate="chrome110")
        if response.status_code == 200:
            html_content = response.text
            with open(FILE_PATH, "w", encoding='UTF-8') as f:
                f.write(html_content)
        else:
            response.raise_for_status()
        root = etree.fromstring(response.content)
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        links = root.xpath("//ns:loc/text()", namespaces=ns)
        links = [link for link in links if ".html" in link]
        print(f"✅ Found {len(links)} links")
        return links
    except Exception as e:
        print(f"❌ Error fetching {sitemap_url}: {e}")
        traceback.print_exc()
        return []

# ================================
# INSERT INTO DB
# ================================
def insert_links(links):
    conn = None
    cursor = None
    try:
        conn = db.get_db_connection(db.db_name)
        cursor = conn.cursor()
        insert_query = f"""
        INSERT IGNORE INTO `{db.link_table}` (url, status, hash_key)
        VALUES (%s, %s, %s)
        """
        data = [(link, "pending", generate_hash(link)) for link in links]
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"💾 Inserted: {cursor.rowcount} new links")
    except Exception as e:
        print("❌ Insert Error:", e)
        traceback.print_exc()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ================================
# MAIN RUNNER
# ================================
def run():
    all_links = set()
    for i in range(0, 5):
        sitemap_url = f"https://www.petsupermarket.com/sitemap_{i}-product.xml"
        links = fetch_sitemap_links(sitemap_url, i)
        if not links:
            print(f"⛔ No more sitemaps at index {i}, stopping...")
            break
        all_links.update(links)
    print(f"\n📊 Total unique links collected: {len(all_links)}")
    insert_links(list(all_links))
    print("\n🚀 DONE")

# ================================
# ENTRY POINT
# ================================
if __name__ == "__main__":
    run()