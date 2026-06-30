#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
update_stats.py — refresh the Booksy review count + rating in index.html
straight from the business's Booksy page.

It reads the authoritative aggregateRating JSON-LD that Booksy embeds in the
page HTML (no browser / JS needed), then rewrites every place the numbers
appear in index.html:
    * the <meta name="description"> snippet
    * the JSON-LD schema  (reviewCount / ratingValue)  -> Google star snippet
    * the hero stat        (count + rating)
    * the "O nas" big number
    * the reviews badge

Safe to run repeatedly (idempotent) and on a daily schedule.

Usage:
    python update_stats.py                          # defaults to index.html
    python update_stats.py --html other.html --url <booksy-url>
    python update_stats.py --dry-run                # show changes, write nothing
"""
import sys, io, os, re, argparse
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_HTML = os.path.join(HERE, 'index.html')
DEFAULT_URL = ("https://booksy.com/pl-pl/"
               "251939_barberowiec-barbershop-bialoleka_barber-shop_3_warszawa")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_booksy_stats(url):
    """Return (review_count:int, rating:float) from the Booksy page's
    aggregateRating JSON-LD. Raises on anything missing or implausible."""
    r = requests.get(url,
                     headers={"User-Agent": UA,
                              "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"},
                     timeout=30)
    r.raise_for_status()
    block = re.search(r'"aggregateRating"\s*:\s*\{[^}]*\}', r.text)
    if not block:
        raise RuntimeError("aggregateRating block not found on Booksy page "
                           "(their layout may have changed).")
    block = block.group(0)
    rc = re.search(r'"reviewCount"\s*:\s*(\d+)', block)
    rv = re.search(r'"ratingValue"\s*:\s*([\d.]+)', block)
    if not (rc and rv):
        raise RuntimeError("reviewCount / ratingValue missing in aggregateRating.")
    count = int(rc.group(1))
    rating = float(rv.group(1))
    if not (1 <= count <= 1_000_000) or not (1.0 <= rating <= 5.0):
        raise RuntimeError(f"Implausible values: count={count} rating={rating}")
    return count, rating


def patch_html(text, count, rating):
    """Rewrite every spot the numbers appear. Returns (new_text, report)."""
    rating_str = f"{round(rating, 1):.1f}"            # 4.95 -> "5.0"
    report = []

    def sub(label, pattern, repl, s):
        new, n = re.subn(pattern, repl, s)
        report.append((label, n))
        return new

    # 1. <meta name="description">  "... 489 opinii, ocena 5.0★ na Booksy."
    text = sub("meta description",
               r'\d+ opinii, ocena [\d.]+★ na Booksy',
               f'{count} opinii, ocena {rating_str}★ na Booksy', text)

    # 2. JSON-LD schema (drives Google's rich-snippet star rating)
    text = sub("JSON-LD reviewCount",
               r'("reviewCount"\s*:\s*")\d+(")',
               rf'\g<1>{count}\g<2>', text)
    text = sub("JSON-LD ratingValue",
               r'("ratingValue"\s*:\s*")[\d.]+(")',
               rf'\g<1>{rating_str}\g<2>', text)

    # 3. Hero stats — count is digits-only, rating ends with a star
    text = sub("hero stat (count)",
               r'(<span class="stat__num">)\d+(</span>)',
               rf'\g<1>{count}\g<2>', text)
    text = sub("hero stat (rating)",
               r'(<span class="stat__num">)[\d.]+★(</span>)',
               rf'\g<1>{rating_str}★\g<2>', text)

    # 4. "O nas" big number
    text = sub('"O nas" big number',
               r'(<span class="about__bignum">)\d+(</span>)',
               rf'\g<1>{count}\g<2>', text)

    # 5. Reviews badge  "489 opinii · 5.0★ na Booksy"
    text = sub("reviews badge",
               r'(<span class="reviews__badge">)\d+ opinii · [\d.]+★( na Booksy</span>)',
               rf'\g<1>{count} opinii · {rating_str}★\g<2>', text)

    return text, report


def main():
    ap = argparse.ArgumentParser(description="Refresh Booksy stats in the site.")
    ap.add_argument("--html", default=DEFAULT_HTML, help="target .html file")
    ap.add_argument("--url", default=DEFAULT_URL, help="business Booksy URL")
    ap.add_argument("--dry-run", action="store_true", help="show changes, write nothing")
    args = ap.parse_args()

    count, rating = fetch_booksy_stats(args.url)
    print(f"Booksy -> {count} reviews, rating {rating:.4f} "
          f"(displayed as {round(rating, 1):.1f})")

    with open(args.html, "r", encoding="utf-8", newline="") as f:
        original = f.read()
    updated, report = patch_html(original, count, rating)

    print("Replacements:")
    for label, n in report:
        print(f"  {n:>2}  {label}" + ("" if n else "   <-- NO MATCH (check template)"))

    if updated == original:
        print(f"{os.path.basename(args.html)} already up to date — nothing to write.")
        return
    if args.dry_run:
        print("[dry-run] file not written.")
        return

    with open(args.html, "w", encoding="utf-8", newline="") as f:
        f.write(updated)
    print(f"Updated {os.path.basename(args.html)}.")


if __name__ == "__main__":
    main()
