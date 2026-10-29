# job-tech-trends

A small Python example that analyzes job postings to find which technologies companies are hiring for.

## What it does

`analyze_jobs.py` reads job postings (company, title, country, date posted, technologies) and:

- prints the most requested technologies and the share of postings that mention each one
- counts postings by country
- shows a month-by-month trend for the top 5 technologies
- writes a per-technology summary to `output/summary.csv` (postings, distinct companies, distinct countries, share of jobs)

It runs offline on `data/sample_jobs.csv`, which holds 40 **synthetic** postings from fictional companies. They were generated for this demo and are not real listings.

## Quick start

```bash
git clone <this-repo> job-tech-trends
cd job-tech-trends
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
python analyze_jobs.py
```

Analyze your own CSV with the same columns (`technologies` is `;`-separated):

```bash
python analyze_jobs.py --csv path/to/jobs.csv --top 15
```

## Sample output

Output from `python analyze_jobs.py` on the bundled synthetic data:

```text
Analyzed 40 job postings from 10 companies

=== Top 10 technologies ===
python        22 postings  (55.0% of jobs)
kubernetes    16 postings  (40.0% of jobs)
aws           15 postings  (37.5% of jobs)
sql           12 postings  (30.0% of jobs)
docker         8 postings  (20.0% of jobs)
typescript     7 postings  (17.5% of jobs)
nextjs         7 postings  (17.5% of jobs)
dbt            6 postings  (15.0% of jobs)
css            6 postings  (15.0% of jobs)
react          6 postings  (15.0% of jobs)

=== Postings by country ===
GB    11
FR     7
TW     6
DE     6
US     5
CA     5

=== Monthly trend (top 5 technologies) ===
         python  kubernetes  aws  sql  docker
month                                        
2026-07       6           2    5    5       0
2026-08       6           7    4    3       1
2026-09       3           4    4    1       2
2026-10       7           3    2    3       5

Wrote output/summary.csv (22 technologies)
```

## How to use real data

The script can fetch real, recent job postings from the [TheirStack](https://theirstack.com?aff=oDE1qF3DQFUH) Jobs API (affiliate link: I may earn a commission if you sign up, at no extra cost to you).

1. Create an API key in your TheirStack account.
2. Export it as an environment variable. Don't commit it to the repo.

   ```bash
   export THEIRSTACK_API_KEY="your-key-here"
   ```

3. Run the script against the API:

   ```bash
   # 25 jobs posted in the last 30 days
   python analyze_jobs.py --source theirstack

   # 100 jobs from the last 14 days in the US and Germany
   python analyze_jobs.py --source theirstack --days 14 --limit 100 --country US --country DE
   ```

The script calls `POST https://api.theirstack.com/v1/jobs/search` with Bearer auth and a `posted_at_max_age_days` filter. The API requires a date or company filter on every request. It maps `company`, `job_title`, `country_code`, `date_posted` and `technology_slugs` from each returned job onto the same columns as the sample CSV. **Each returned job uses 1 API credit**, so keep `--limit` small while you experiment. See the [Search Jobs API reference](https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1) for more filters.

## License

MIT. See [LICENSE](LICENSE).
