#!/usr/bin/env python3
"""Analyze job postings to see which technologies companies are hiring for.

Offline (default):  python analyze_jobs.py
Real data (opt.):   THEIRSTACK_API_KEY=... python analyze_jobs.py --source theirstack

Outputs: top technologies, postings by country, monthly technology trends,
and writes output/summary.csv.
"""
import argparse
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SAMPLE_CSV = ROOT / "data" / "sample_jobs.csv"
OUTPUT_DIR = ROOT / "output"

# TheirStack Jobs API, checked against https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1
# (POST /v1/jobs/search, Bearer auth, at least one date/company filter required,
# 1 API credit per job returned).
THEIRSTACK_URL = "https://api.theirstack.com/v1/jobs/search"


def load_sample(path: Path = SAMPLE_CSV) -> pd.DataFrame:
    return pd.read_csv(path, comment="#")


def load_theirstack(max_age_days: int, limit: int, countries: list[str]) -> pd.DataFrame:
    """Fetch recent jobs from TheirStack and normalize them to the sample CSV schema."""
    import requests  # only needed for the optional API path

    api_key = os.environ.get("THEIRSTACK_API_KEY")
    if not api_key:
        raise SystemExit("Set the THEIRSTACK_API_KEY environment variable to use --source theirstack.")

    payload = {
        "posted_at_max_age_days": max_age_days,  # required-type filter (date or company)
        "limit": limit,                          # each returned job costs 1 credit
        "page": 0,
    }
    if countries:
        payload["job_country_code_or"] = countries

    resp = requests.post(
        THEIRSTACK_URL,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    jobs = resp.json().get("data", [])

    rows = [
        {
            "company": job.get("company"),
            "title": job.get("job_title"),
            "country": job.get("country_code"),
            "date_posted": job.get("date_posted"),
            "technologies": ";".join(job.get("technology_slugs") or []),
        }
        for job in jobs
    ]
    return pd.DataFrame(rows, columns=["company", "title", "country", "date_posted", "technologies"])


def explode_technologies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["technology"] = out["technologies"].fillna("").str.split(";")
    out = out.explode("technology")
    out["technology"] = out["technology"].str.strip().str.lower()
    return out[out["technology"] != ""]


def analyze(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["date_posted"], errors="coerce").dt.strftime("%Y-%m")
    techs = explode_technologies(df)

    print(f"Analyzed {len(df)} job postings from {df['company'].nunique()} companies\n")

    top = techs["technology"].value_counts().head(top_n)
    share = (top / len(df) * 100).round(1)
    print(f"=== Top {top_n} technologies ===")
    for tech, count in top.items():
        print(f"{tech:<12} {count:>3} postings  ({share[tech]}% of jobs)")

    print("\n=== Postings by country ===")
    for country, count in df["country"].value_counts().items():
        print(f"{country:<4} {count:>3}")

    print("\n=== Monthly trend (top 5 technologies) ===")
    top5 = top.index[:5]
    trend = (
        techs[techs["technology"].isin(top5)]
        .pivot_table(index="month", columns="technology", values="title", aggfunc="count", fill_value=0)
        .reindex(columns=top5)
    )
    trend.columns.name = None
    print(trend.to_string())

    summary = (
        techs.groupby("technology")
        .agg(postings=("title", "count"), companies=("company", "nunique"), countries=("country", "nunique"))
        .sort_values(["postings", "companies"], ascending=False)
        .reset_index()
    )
    summary["share_of_jobs_pct"] = (summary["postings"] / len(df) * 100).round(1)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["sample", "theirstack"], default="sample")
    parser.add_argument("--csv", type=Path, default=SAMPLE_CSV, help="CSV to analyze when --source sample")
    parser.add_argument("--days", type=int, default=30, help="TheirStack: max posting age in days")
    parser.add_argument("--limit", type=int, default=25, help="TheirStack: number of jobs (1 credit each)")
    parser.add_argument("--country", action="append", default=[], help="TheirStack: ISO2 code, repeatable")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    if args.source == "theirstack":
        df = load_theirstack(args.days, args.limit, args.country)
    else:
        df = load_sample(args.csv)

    if df.empty:
        raise SystemExit("No job postings to analyze.")

    summary = analyze(df, top_n=args.top)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "summary.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nWrote {out_path.relative_to(ROOT)} ({len(summary)} technologies)")


if __name__ == "__main__":
    main()
