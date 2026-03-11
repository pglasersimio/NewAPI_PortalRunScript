# Simio Portal Web API Demo

This repository contains a Python script to interact with the Simio Portal Web API. It supports two modes — using the `pysimio` library or making direct REST API calls — switchable via a single toggle in the `.env` file.

## Project Structure

```
.
├── main.py               # Main script (reads USE_PYSIMIO toggle to pick API mode)
├── shared_helper.py      # Shared helper functions (works with either API mode)
├── simio_api_helper.py   # Direct REST API client (SimioAPI class, no pysimio dependency)
├── helper.py             # Original helper functions (kept for reference)
├── .env                  # Environment variables (not included in repo)
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
└── LICENSE.txt           # Apache License 2.0
```

## API Modes

| Mode | Toggle | Description |
|------|--------|-------------|
| **pysimio** | `USE_PYSIMIO=True` | Uses the `pysimio` library (default) |
| **Direct REST** | `USE_PYSIMIO=False` | Uses `SimioAPI` class with direct `requests` calls — no pysimio dependency needed |

Both modes share the same helpers (`shared_helper.py`) and produce identical behavior. The `SimioAPI` class mirrors pysimio's method signatures exactly.

## Features
- Authenticate with the Simio Portal API with automatic token refresh.
- Retrieve model ID by project name.
- Find and delete existing runs by matching `scenarioNames` for a given model.
- Create a new run, display control values, and let the user interactively adjust them before starting.
- Configure run start/end time options.
- Start a plan run and poll progress until completion (with detailed stage/import/run/export tracking).
- Post-run output (each controlled by a toggle):
  - **Table schema** — display column and state schemas for all model tables.
  - **Sample table data** — show the first 10 rows of the first non-empty table.
  - **Log schema** — display log names and column definitions.
  - **Sample log data** — show the first 10 rows of the first non-empty log.
  - **Full table dump** — page through and display all rows of a user-selected table.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pglasersimio/NewAPI_PortalRunScript.git
   cd NewAPI_PortalRunScript
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```env
   PERSONAL_ACCESS_TOKEN=your_personal_access_token_here
   SIMIO_PORTAL_URL=your_url
   USE_PYSIMIO=True
   ```

## Configuration

Edit the configuration section at the top of `main.py`:

```python
# Configuration
project_name = "SchedulingDiscretePartProduction"
plan_name = "ModelValues_test"
auth_refresh_time = 500
run_status_refresh_time = 2
UseSpecificStartTime = True
UseSpecificEndTime = True
plan_start_datetime = '2025-12-13T03:14:00Z'
plan_end_dateTime = '2025-12-20T03:14:00Z'

# Post-run output toggles
show_table_schema = True
show_sample_table_data = True
show_log_schema = True
show_sample_log_data = True
show_table_summary = True
summary_page_size = 100
```

## Usage

1. Update the configuration in `main.py` with your project name, plan name, and time options.

2. Set `USE_PYSIMIO` in `.env` to `True` (pysimio library) or `False` (direct REST API).

3. Run the script:
   ```bash
   python main.py
   ```

4. When prompted, review the control values and either adjust them or press Enter to proceed with defaults.

5. The script will start the plan, display real-time progress, and (on success) show post-run data based on your toggle settings.

## Shared Helper Functions

The `shared_helper.py` file contains functions used by both API modes:

- `refresh_auth_token(api, refresh_interval)` — Refreshes the API authentication token at regular intervals.
- `find_modelid_by_projectname(modellist_json, targetproject)` — Finds the model ID for a given project name.
- `find_parent_run_id(json_data, run_name)` — Finds the parent run ID for a specified run name.
- `check_run_id_status(api, experiment_id, run_id, sleep_time)` — Monitors run status including child runs in `additionalRunsStatus`.
- `get_parent_experiment_id(data, project_name)` — Retrieves the experiment ID for a given project name.
- `display_and_update_control_values(api, run_id, scenario_name)` — Fetches control values and prompts the user to adjust any before running.
- `prompt_table_selection(api, model_id, run_id)` — Displays available tables and lets the user pick one.
- `display_full_table(api, run_id, scenario_name, table_name, page_size)` — Pages through and displays all rows of a specific table.
- `print_table(data, max_rows, indent)` — Pretty-prints a list of flat dicts as an aligned table.
- `display_table_schema(api, model_id, run_id)` — Fetches and displays table schemas (with fallback to scenario bindings).
- `display_sample_table_data(api, run_id, plan_name, table_names)` — Displays sample rows from the first non-empty table.
- `display_log_schema(api, run_id)` — Fetches and displays log schemas with column names and types.
- `display_and_poll_run_progress(api, run_id, plan_name, refresh_interval)` — Displays initial run progress then polls until complete/failed/canceled.
- `display_sample_log_data(api, run_id)` — Displays sample rows from the first non-empty log endpoint.

## Direct REST API Client

The `simio_api_helper.py` file provides `SimioAPI` — a standalone REST client that mirrors pysimio's interface using only the `requests` library. It also includes a `TimeOptions` dataclass. Use this mode when you want to avoid the pysimio dependency.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PERSONAL_ACCESS_TOKEN` | Your Simio Portal personal access token |
| `SIMIO_PORTAL_URL` | Base URL of your Simio Portal instance |
| `USE_PYSIMIO` | `True` to use pysimio library, `False` for direct REST calls (default: `True`) |

## Requirements
- Python 3.9+
- `python-dotenv`
- `requests`
- `pysimio` (only when `USE_PYSIMIO=True`)

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request.

## License
This project is licensed under the Apache License 2.0 License. See the `LICENSE` file for more information.

## Contact
For any questions or issues, please contact [pglaser@simio.com].
