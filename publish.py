import glob
import json
import os
import sys

import requests

WP_URL = "https://tilaaiptv.com/wp-json/wp/v2/posts"
QUEUE_DIR = "queue"
PUBLISHED_FILE = "published.json"


def load_published():
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_published(published):
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(published, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    wp_auth = os.environ.get("WP_AUTH")
    if not wp_auth:
        print("ERROR: WP_AUTH is not set")
        sys.exit(1)

    published = load_published()
    published_set = set(published)

    files = sorted(glob.glob(os.path.join(QUEUE_DIR, "*.json")))
    if not files:
        print("No files in queue/")
        return

    headers = {
        "Authorization": f"Basic {wp_auth}",
        "Content-Type": "application/json; charset=utf-8",
    }

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            meta = json.load(f)

        slug = meta["slug"]

        if slug in published_set:
            print(f'Skipping {filepath} (slug "{slug}" already published) - removing stale queue file')
            os.remove(filepath)
            continue

        print(f'Publishing: {meta["title"]}')
        payload = {
            "title": meta["title"],
            "content": meta["content"],
            "slug": slug,
            "status": "publish",
            "excerpt": meta.get("meta_desc", ""),
        }

        try:
            r = requests.post(WP_URL, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            body = e.response.text[:400] if e.response is not None else str(e)
            print(f"ERROR publishing {slug}: {body}")
            sys.exit(1)

        data = r.json()
        print(f'SUCCESS: id={data["id"]} url={data["link"]}')

        published.append(slug)
        published_set.add(slug)
        save_published(published)
        os.remove(filepath)


if __name__ == "__main__":
    main()
