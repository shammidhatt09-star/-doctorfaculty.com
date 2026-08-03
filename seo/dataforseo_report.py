#!/usr/bin/env python3
"""
One-off SEO report for doctorfaculty.com using the DataForSEO API.

Runs four checks:
  1. Keyword research  - dataforseo_labs/google/keyword_ideas
  2. Rank tracking      - serp/google/organic (does doctorfaculty.com appear?)
  3. Site audit         - on_page/instant_pages (per key page)
  4. Competitors/backlinks - dataforseo_labs/google/competitors_domain + backlinks/summary

Reads credentials from a local .env file (DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD).
Never commit .env - it's in .gitignore.

Usage: python3 seo/dataforseo_report.py
"""
import base64
import json
import os
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_BASE = "https://api.dataforseo.com/v3"
TARGET_DOMAIN = "doctorfaculty.com"
LOCATION_CODE = 2356  # India
LANGUAGE_CODE = "en"

# Seed keywords derived from the site's own pages (homepage, join-faculty,
# eligibility-check, nmc-updates, for-institutions).
SEED_KEYWORDS = [
    "medical college faculty jobs india",
    "join as medical faculty",
    "faculty eligibility medical college",
    "nmc faculty eligibility criteria",
    "medical teaching post india",
    "medical college faculty vacancy",
]

PAGES_TO_AUDIT = [
    "https://doctorfaculty.com/",
    "https://doctorfaculty.com/join-faculty.html",
    "https://doctorfaculty.com/eligibility-check.html",
    "https://doctorfaculty.com/nmc-updates.html",
    "https://doctorfaculty.com/for-institutions.html",
]


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(f"Missing {env_path}. Create it with DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD.")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

    login = os.environ.get("DATAFORSEO_LOGIN")
    password = os.environ.get("DATAFORSEO_PASSWORD")
    if not login or not password:
        raise SystemExit("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set in .env")
    return login, password


def api_post(path, payload, auth_header):
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"DataForSEO API error {e.code} on {path}: {body}")


def keyword_research(auth_header):
    payload = [{
        "keywords": SEED_KEYWORDS,
        "location_code": LOCATION_CODE,
        "language_code": LANGUAGE_CODE,
        "limit": 50,
    }]
    data = api_post("/dataforseo_labs/google/keyword_ideas/live", payload, auth_header)
    results = []
    for task in data.get("tasks", []):
        for result in (task.get("result") or []):
            for item in (result.get("items") or []):
                info = item.get("keyword_info") or {}
                results.append({
                    "keyword": item.get("keyword"),
                    "search_volume": info.get("search_volume"),
                    "cpc": info.get("cpc"),
                    "competition": info.get("competition"),
                })
    results.sort(key=lambda x: (x["search_volume"] or 0), reverse=True)
    return results


def rank_tracking(auth_header):
    rankings = []
    for kw in SEED_KEYWORDS:
        payload = [{
            "keyword": kw,
            "location_code": LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "device": "mobile",
            "depth": 100,
        }]
        data = api_post("/serp/google/organic/live/advanced", payload, auth_header)
        position = None
        url = None
        for task in data.get("tasks", []):
            for result in (task.get("result") or []):
                for item in (result.get("items") or []):
                    if item.get("type") == "organic" and TARGET_DOMAIN in (item.get("domain") or ""):
                        position = item.get("rank_absolute")
                        url = item.get("url")
                        break
                if position:
                    break
        rankings.append({"keyword": kw, "position": position, "url": url})
    return rankings


def site_audit(auth_header):
    audits = []
    for url in PAGES_TO_AUDIT:
        payload = [{"url": url, "enable_javascript": True}]
        data = api_post("/on_page/instant_pages", payload, auth_header)
        for task in data.get("tasks", []):
            for result in (task.get("result") or []):
                item = (result.get("items") or [{}])[0]
                meta = item.get("meta") or {}
                checks = item.get("checks") or {}
                failed_checks = [name for name, ok in checks.items() if ok is True and "error" in name.lower()]
                audits.append({
                    "url": url,
                    "status_code": item.get("status_code"),
                    "title": (meta.get("title") or "")[:80],
                    "onpage_score": item.get("onpage_score"),
                    "flagged_checks": [name for name, val in checks.items() if val],
                })
    return audits


def competitors_and_backlinks(auth_header):
    comp_payload = [{
        "target": TARGET_DOMAIN,
        "location_code": LOCATION_CODE,
        "language_code": LANGUAGE_CODE,
        "limit": 10,
    }]
    comp_data = api_post("/dataforseo_labs/google/competitors_domain/live", comp_payload, auth_header)
    competitors = []
    for task in comp_data.get("tasks", []):
        for result in (task.get("result") or []):
            for item in (result.get("items") or []):
                competitors.append({
                    "domain": item.get("domain"),
                    "common_keywords": item.get("intersections"),
                    "avg_position": item.get("avg_position"),
                })

    bl_payload = [{"target": TARGET_DOMAIN}]
    bl_data = api_post("/backlinks/summary/live", bl_payload, auth_header)
    backlinks_summary = {}
    for task in bl_data.get("tasks", []):
        for result in (task.get("result") or []):
            backlinks_summary = {
                "backlinks": result.get("backlinks"),
                "referring_domains": result.get("referring_domains"),
                "rank": result.get("rank"),
            }
    return competitors, backlinks_summary


def write_report(keyword_ideas, rankings, audits, competitors, backlinks_summary):
    report_path = ROOT / "seo" / "reports" / f"report-{date.today().isoformat()}.md"
    lines = [f"# Dr. Faculty SEO report - {date.today().isoformat()}", ""]

    lines += ["## Keyword research (top ideas by volume)", ""]
    lines += ["| Keyword | Volume | CPC | Competition |", "|---|---|---|---|"]
    for k in keyword_ideas[:30]:
        lines.append(f"| {k['keyword']} | {k['search_volume']} | {k['cpc']} | {k['competition']} |")

    lines += ["", "## Rank tracking (current seed keywords)", ""]
    lines += ["| Keyword | Position | URL |", "|---|---|---|"]
    for r in rankings:
        pos = r["position"] if r["position"] else "Not in top 100"
        lines.append(f"| {r['keyword']} | {pos} | {r['url'] or '-'} |")

    lines += ["", "## Site audit (instant page checks)", ""]
    for a in audits:
        lines.append(f"### {a['url']}")
        lines.append(f"- Status: {a['status_code']}, on-page score: {a['onpage_score']}")
        lines.append(f"- Title: {a['title']}")
        lines.append(f"- Flagged checks: {', '.join(a['flagged_checks']) or 'none'}")
        lines.append("")

    lines += ["## Competitors (auto-discovered)", ""]
    lines += ["| Domain | Common keywords | Avg position |", "|---|---|---|"]
    for c in competitors:
        lines.append(f"| {c['domain']} | {c['common_keywords']} | {c['avg_position']} |")

    lines += ["", "## Backlink summary", ""]
    lines.append(f"- Referring domains: {backlinks_summary.get('referring_domains')}")
    lines.append(f"- Total backlinks: {backlinks_summary.get('backlinks')}")
    lines.append(f"- Domain rank: {backlinks_summary.get('rank')}")

    report_path.write_text("\n".join(lines))
    print(f"Report written to {report_path}")


def main():
    login, password = load_env()
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    auth_header = f"Basic {token}"

    print("Running keyword research...")
    keyword_ideas = keyword_research(auth_header)
    print("Running rank tracking...")
    rankings = rank_tracking(auth_header)
    print("Running site audit...")
    audits = site_audit(auth_header)
    print("Running competitor/backlink analysis...")
    competitors, backlinks_summary = competitors_and_backlinks(auth_header)

    write_report(keyword_ideas, rankings, audits, competitors, backlinks_summary)


if __name__ == "__main__":
    main()
