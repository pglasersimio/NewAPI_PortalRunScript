# example_table_queries.py — Demonstrates table data queries with filtering & paging
"""
Shows three ways to query table data from the Simio Portal API:
  1. pysimio — filter by columns (client-side) with full paging
  2. pysimio — filter rows by value (server-side OData filter) with full paging
  3. Direct REST API — filter by columns (server-side query param) with full paging

Edit the variables below, then run:  python example_table_queries.py
"""
import os
from dotenv import load_dotenv
from helper import print_table

load_dotenv(override=True)

simio_portal_url = os.getenv("SIMIO_PORTAL_URL")
personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")

# ── Edit these for each test ────────────────────────────────────────────────
run_id = 785
scenario_name = "ModelValues_test"
table_name = "Materials"
columns = ["MaterialName"]                          # columns to return
filter_expression = "MaterialName eq 'MaterialX'"   # OData-style row filter
page_size = 100                                     # rows per page
# ────────────────────────────────────────────────────────────────────────────


def flatten_rows(data, filter_columns=None):
    """Convert nested properties/states format into flat dicts."""
    flat = []
    for row in (data or []):
        r = {}
        for p in (row.get('properties') or []):
            r[p['name']] = p.get('value', '')
        for s in (row.get('states') or []):
            r[s['name']] = s.get('value', '')
        if filter_columns:
            r = {k: v for k, v in r.items() if k in filter_columns}
        flat.append(r)
    return flat if flat else data  # fall back to raw if not nested format


def fetch_all_pages(api, run_id, scenario_name, table_name, page_size, **kwargs):
    """Page through getTableData and return all rows."""
    all_rows = []
    page = 1
    while True:
        result = api.getTableData(
            runId=run_id, scenarioName=scenario_name, tableName=table_name,
            page=page, pageSize=page_size, **kwargs
        )
        if not result or not isinstance(result, list) or len(result) == 0:
            break
        all_rows.extend(result)
        print(f"  Fetched page {page} ({len(result)} rows)")
        if len(result) < page_size:
            break
        page += 1
    return all_rows


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  EXAMPLE 1: pysimio — return specific columns (client-side filter)      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

from pysimio import pySimio

api = pySimio(simio_portal_url)
api.authenticate(personalAccessToken=personal_access_token)

print(f"\n  Example 1: pysimio column filter — {table_name}  |  Columns: {columns}")
print(f"  {'─' * 60}")

result = fetch_all_pages(api, run_id, scenario_name, table_name, page_size)
print_table(flatten_rows(result, filter_columns=columns), max_rows=len(result))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  EXAMPLE 2: pysimio — filter rows by value (server-side OData filter)   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

print(f"\n  Example 2: pysimio row filter — {table_name}  |  Filter: {filter_expression}")
print(f"  {'─' * 60}")

result = fetch_all_pages(api, run_id, scenario_name, table_name, page_size,
                         filter=filter_expression)
print_table(flatten_rows(result), max_rows=len(result))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  EXAMPLE 3: Direct REST API — columns via query param (server-side)     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

from simio_api_helper import SimioAPI

api2 = SimioAPI(simio_portal_url)
api2.authenticate(personalAccessToken=personal_access_token)

print(f"\n  Example 3: Direct API column filter — {table_name}  |  Columns: {columns}")
print(f"  {'─' * 60}")

endpoint = f"/v1/runs/{run_id}/scenarios/{scenario_name}/table-data/{table_name}"

all_rows = []
page = 1
while True:
    params = [("page", page), ("page_size", page_size)]
    for col in columns:
        params.append(("columns", col))
    result = api2._get(endpoint, params=params)
    if not result or not isinstance(result, list) or len(result) == 0:
        break
    all_rows.extend(result)
    print(f"  Fetched page {page} ({len(result)} rows)")
    if len(result) < page_size:
        break
    page += 1

print_table(flatten_rows(all_rows), max_rows=len(all_rows))
