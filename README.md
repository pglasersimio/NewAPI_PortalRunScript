# Simio Portal Web API Demo

This repository contains a Python script to interact with the Simio Portal Web API using the `pysimio` package. The script creates a simulation run, optionally adjusts control values and time options, monitors progress, and retrieves post-run data (table schemas, table data, log schemas, and log data).

## Project Structure

```
.
├── main.py           # Main script to interact with the Simio Portal
├── helper.py         # Contains helper functions used in main.py
├── .env              # Environment variables file (not included in the repo)
├── README.md         # Project documentation
└── requirements.txt  # Python dependencies
```

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
  - **Full table dump** — page through and display all rows of a specific table (e.g. `ManufacturingOrders`).

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

3. Create a `.env` file in the project root to store your personal access token:
   ```env
   PERSONAL_ACCESS_TOKEN=your_personal_access_token_here
   SIMIO_PORTAL_URL=your_url
   ```

4. Add the `.env` file to `.gitignore` to ensure it is not committed to the repository:
   ```gitignore
   # Ignore environment file
   .env
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
summary_table_name = "ManufacturingOrders"
summary_page_size = 100
```

## Usage

1. Update the configuration in `main.py` with your project name, plan name, and time options.

2. Run the script:
   ```bash
   python main.py
   ```

3. When prompted, review the control values and either adjust them or press Enter to proceed with defaults.

4. The script will start the plan, display real-time progress, and (on success) show post-run data based on your toggle settings.

## Helper Functions
The `helper.py` file contains the following functions:

- `refresh_auth_token(api, refresh_interval)` — Refreshes the API authentication token at regular intervals.
- `find_modelid_by_projectname(modellist_json, targetproject)` — Finds the model ID for a given project name.
- `find_parent_run_id(json_data, run_name)` — Finds the parent run ID for a specified run name.
- `check_run_id_status(api, experiment_id, run_id, sleep_time)` — Monitors run status including child runs in `additionalRunsStatus`.
- `get_parent_experiment_id(data, project_name)` — Retrieves the experiment ID for a given project name.
- `display_and_update_control_values(api, run_id, scenario_name)` — Fetches control values and prompts the user to adjust any before running.
- `display_full_table(api, run_id, scenario_name, table_name, page_size)` — Pages through and displays all rows of a specific table.
- `print_table(data, max_rows, indent)` — Pretty-prints a list of flat dicts as an aligned table.
- `display_table_schema(api, model_id, run_id)` — Fetches and displays table schemas (with fallback to scenario bindings).
- `display_sample_table_data(api, run_id, plan_name, table_names)` — Displays sample rows from the first non-empty table.
- `display_log_schema(api, run_id)` — Fetches and displays log schemas with column names and types.
- `display_and_poll_run_progress(api, run_id, plan_name, refresh_interval)` — Displays initial run progress then polls until complete/failed/canceled.
- `display_sample_log_data(api, run_id)` — Displays sample rows from the first non-empty log endpoint.

## Environment Variables
This project uses the `python-dotenv` package to load environment variables from a `.env` file.

### Example `.env` File:
```env
PERSONAL_ACCESS_TOKEN=your_personal_access_token
SIMIO_PORTAL_URL=your_url
```

## Requirements
- Python 3.8+
- `pysimio`
- `requests`
- `tenacity`
- `decorator`
- `python-dotenv`

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request.

## License
This project is licensed under the Apache License 2.0 License. See the `LICENSE` file for more information.

## Contact
For any questions or issues, please contact [pglaser@simio.com].
