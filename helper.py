# helper.py
"""
Helper functions for interacting with the Simio Portal Web API.
"""
import sys
import time
import os
import json

def refresh_auth_token(api, refresh_interval):
    """
    Refreshes the authentication token at regular intervals.

    :param api: The pySimio API object.
    :param refresh_interval: Time in seconds between token refreshes.
    """
    while True:
        try:
            print("Refreshing authentication token...")
            api.authenticate(personalAccessToken=os.getenv("PERSONAL_ACCESS_TOKEN"))
            print("Token refreshed successfully.")
        except Exception as e:
            print(f"Error refreshing token: {e}")
        time.sleep(refresh_interval)
def find_modelid_by_projectname(modellist_json, targetproject):
    """
    Finds the model ID by project name. When multiple projects share the same
    name, returns the model ID for the one with the highest projectId.

    Parameters:
        modellist (list): List of models.
        targetproject (str): Target project name.

    Returns:
        int: The model ID if found, otherwise exits.
    """
    matches = [item for item in modellist_json if item.get('projectName') == targetproject]
    if not matches:
        print(f"Model '{targetproject}' not found.")
        sys.exit()
    best = max(matches, key=lambda x: x.get('projectId', 0))
    return best.get('id')

def find_parent_run_id(json_data, run_name):
    """
    Finds the parent run ID for a given run name in the JSON data.

    Parameters:
        json_data (list): The JSON data to parse.
        run_name (str): The name of the run to search for.

    Returns:
        int: The parent run ID if found, otherwise 0.
    """
    for item in json_data:
        if item.get('name') == run_name:
            return item.get('id', 0)
    return 0

def check_run_id_status(api, experiment_id, run_id, sleep_time):
    """
    Continuously checks the status of a specific run by its run_id,
    including checking the max ID within additionalRunsStatus.

    Parameters:
        api (object): The API object used to call getRuns().
        experiment_id (int): The experiment ID to retrieve runs from.
        run_id (int): The specific run ID to check.
        sleep_time (int): The time to wait (in seconds) between status checks.

    Returns:
        None
    """
    while True:
        time.sleep(sleep_time)
        try:
            # Fetch the list of runs for the given experiment ID
            run_status_response = api.getRuns(experiment_id)

            # Print the raw response for troubleshooting
            #print("\n--- Run Status Response (JSON) ---")
            #print(json.dumps(run_status_response, indent=4))

            # Search for the parent run_id in the response
            run_status = next((run for run in run_status_response if run['id'] == run_id), None)

            # Check if the run_id was found
            if run_status is None:
                print(f"Run ID {run_id} not found in the experiment {experiment_id}.")
                break

            # Search for the child id (max ID) within additionalRunsStatus portion of JSON
            additional_runs = run_status.get('additionalRunsStatus', [])
            if additional_runs:
                # Find the run with the max ID in additionalRunsStatus
                max_additional_run = max(additional_runs, key=lambda x: x['id'])
                status = max_additional_run.get('status', 'Unknown')
                status_message = max_additional_run.get('statusMessage', '')
            else:
                # If no additional runs, use the top-level run status
                status = run_status.get('status', 'Unknown')
                status_message = run_status.get('statusMessage', '')

            # Print the current status
            if status_message:
                print(f"Status = {status}, Message = {status_message}")
            else:
                print(f"Status = {status}")

            # Continue checking if the run is still "Running" or "NotStarted"
            if status in ["Running", "NotStarted"]:
                continue
            else:
                # Run completed or failed
                if status_message:
                    print(f"Status: {status}, Message = {status_message}")
                else:
                    print(f"Done")
                break
        except Exception as e:
            print(f"Error checking run status: {str(e)}")
            break

def get_parent_experiment_id(data, project_name):
    # Retrieves the experiment ID for a given project name from the JSON dataset.
    #
    # Parameters:
    #     data (list): A list of dictionaries representing JSON data.
    #     project_name (str): The name of the project to find the experiment ID for.
    #
    # Returns:
    #     int or None: The experiment ID if found, otherwise None.
    for entry in data:
        if entry.get("projectName") == project_name:
            return entry.get("experimentId")
    return None  # Return None if no match is found


def display_and_update_control_values(api, run_id, scenario_name):
    """Fetch control values via getScenarios, display them, and prompt the user to adjust any before running."""
    scenario_data = api.getScenarios(run_id=run_id)
    controls = []
    if scenario_data and isinstance(scenario_data, list):
        for sc in scenario_data:
            if sc.get('scenarioName') == scenario_name:
                controls = sc.get('controlValues') or []
                break

    print(f"\n  {'─' * 60}")
    print(f"  Control Values for '{scenario_name}' (Run ID: {run_id})")
    print(f"  {'─' * 60}")

    if not controls:
        print("  (no control values found)")
        return

    # Display numbered list
    name_width = max(len(c.get('name', '')) for c in controls)
    for i, ctrl in enumerate(controls, 1):
        print(f"  {i:>3}. {ctrl.get('name', '?'):<{name_width}}  =  {ctrl.get('value', '')}")
    print(f"  {'─' * 60}")

    # Prompt loop
    while True:
        choice = input("\n  Enter control # to change (or press Enter to run as-is): ").strip()
        if not choice:
            print("  Proceeding with current control values.")
            break
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(controls):
                print(f"  Invalid selection. Enter a number 1-{len(controls)}.")
                continue
        except ValueError:
            print(f"  Invalid input. Enter a number 1-{len(controls)} or press Enter to continue.")
            continue

        ctrl_name = controls[idx].get('name')
        old_value = controls[idx].get('value', '')
        new_value = input(f"  New value for '{ctrl_name}' (current: {old_value}): ").strip()
        if not new_value:
            print("  No change made.")
            continue

        api.setControlValues(runId=run_id, scenarioName=scenario_name, controlName=ctrl_name, controlValue=new_value)
        controls[idx]['value'] = new_value
        print(f"  Updated '{ctrl_name}' = '{new_value}'")

        # Redisplay
        print(f"\n  {'─' * 60}")
        print(f"  Control Values for '{scenario_name}' (Run ID: {run_id})")
        print(f"  {'─' * 60}")
        for i, ctrl in enumerate(controls, 1):
            print(f"  {i:>3}. {ctrl.get('name', '?'):<{name_width}}  =  {ctrl.get('value', '')}")
        print(f"  {'─' * 60}")


def display_full_table(api, run_id, scenario_name, table_name, page_size=100):
    """Fetch all rows of a table via paging and display the full result."""
    print("\n" + "=" * 80)
    print(f"  FULL TABLE: {table_name}")
    print("=" * 80)

    all_rows = []
    page = 1
    while True:
        result = api.getTableData(runId=run_id, scenarioName=scenario_name, tableName=table_name, page=page, pageSize=page_size)
        if not result or not isinstance(result, list) or len(result) == 0:
            break
        all_rows.extend(result)
        print(f"  Fetched page {page} ({len(result)} rows)...")
        if len(result) < page_size:
            break
        page += 1

    if not all_rows:
        print(f"  Table '{table_name}' returned no data (empty or 204).")
        return

    # Flatten properties + states into flat dicts
    flat_rows = []
    for row in all_rows:
        flat = {}
        for p in (row.get('properties') or []):
            flat[p['name']] = p.get('value', '')
        for s in (row.get('states') or []):
            flat[s['name']] = s.get('value', '')
        flat_rows.append(flat)

    print(f"\n  Table: {table_name}  |  Scenario: {scenario_name}  |  Run ID: {run_id}")
    print(f"  Total rows: {len(flat_rows)}")
    print(f"  {'─' * 60}")
    print_table(flat_rows, max_rows=len(flat_rows))


def print_table(data, max_rows=10, indent=2):
    """Pretty-print a list of flat dicts as an aligned table (top N rows)."""
    if not data:
        print(f"{' ' * indent}(no data returned)")
        return
    prefix = " " * indent
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [[str(row.get(h, '')) for h in headers] for row in data[:max_rows]]
    else:
        return
    col_widths = [min(28, max(len(h), max((len(r[i]) for r in rows), default=0))) for i, h in enumerate(headers)]
    print(prefix + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)))
    print(prefix + "-+-".join("-" * w for w in col_widths))
    for rv in rows:
        print(prefix + " | ".join(v.ljust(w)[:w] for v, w in zip(rv, col_widths)))
    print(f"{prefix}({min(len(data), max_rows)} of {len(data)} rows shown)")


def display_table_schema(api, model_id, run_id):
    """Fetch and display table schema, returning list of table names discovered."""
    print("\n" + "=" * 80)
    print("  TABLE SCHEMA")
    print("=" * 80)

    table_schema_json = api.getModelTable(model_id)
    table_names = []

    if table_schema_json and isinstance(table_schema_json, list):
        for table in table_schema_json:
            tname = table.get('name', '?')
            cols = table.get('columnSchemas') or []
            states = table.get('stateSchemas') or []
            keys = [c['name'] for c in cols if c.get('isKey')]
            table_names.append(tname)
            print(f"\n  Table: {tname}")
            print(f"  {'─' * 60}")
            if keys:
                print(f"  Key Column(s): {', '.join(keys)}")
            if cols:
                print(f"  Property Columns:")
                for c in cols:
                    fk = c.get('foreignKeyInfo')
                    fk_str = f"  -> {fk['toTableName']}.{fk['toColumnName']}" if fk else ""
                    print(f"    - {c.get('displayName') or c.get('name')}{fk_str}")
            if states:
                print(f"  State Columns:")
                for s in states:
                    print(f"    - {s.get('displayName') or s.get('name')}")
    else:
        print("  Table schema returned 204 (no schemas). Discovering tables from scenario data...")
        scenario_data = api.getScenarios(run_id=run_id)
        if scenario_data and isinstance(scenario_data, list):
            for sc in scenario_data:
                bindings = sc.get('activeTableBindings') or []
                for b in bindings:
                    tname = b.get('tableName', '?')
                    table_names.append(tname)
                    binding_name = b.get('activeBindingName') or '(none)'
                    last_import = b.get('lastTableImport') or 'never'
                    print(f"    - {tname}  [binding: {binding_name}, last import: {last_import}]")
            if not table_names:
                print("  No activeTableBindings found in scenario data.")
        else:
            print("  No scenario data returned.")

    return table_names


def display_sample_table_data(api, run_id, plan_name, table_names):
    """Fetch and display sample table data for the first non-empty table."""
    print("\n" + "=" * 80)
    print("  SAMPLE TABLE DATA (top 10 rows)")
    print("=" * 80)

    if not table_names:
        print("  No tables discovered — skipping.")
        return

    sample_table_data = None
    sampled_table = None
    for tname in table_names:
        result = api.getTableData(runId=run_id, scenarioName=plan_name, tableName=tname, page=1, pageSize=10)
        if result and isinstance(result, list) and len(result) > 0:
            sample_table_data = result
            sampled_table = tname
            break

    if sample_table_data:
        print(f"\n  Table: {sampled_table}  |  Scenario: {plan_name}  |  Run ID: {run_id}")
        print(f"  {'─' * 60}")
        flat_rows = []
        for row in sample_table_data:
            flat = {}
            for p in (row.get('properties') or []):
                flat[p['name']] = p.get('value', '')
            for s in (row.get('states') or []):
                flat[s['name']] = s.get('value', '')
            flat_rows.append(flat)
        print_table(flat_rows, max_rows=10)
    else:
        print(f"  Tried tables {table_names} — all returned empty (204).")


def display_log_schema(api, run_id):
    """Fetch and display log schema."""
    print("\n" + "=" * 80)
    print("  LOG SCHEMA")
    print("=" * 80)

    log_schema_json = api.getScenariosLogSchemas(runId=run_id)

    # Normalize response: API may return a single dict or a list of dicts
    if isinstance(log_schema_json, dict):
        schema_entries = [log_schema_json]
    elif isinstance(log_schema_json, list):
        schema_entries = log_schema_json
    else:
        schema_entries = []

    found_any = False
    for entry in schema_entries:
        if not isinstance(entry, dict):
            continue
        scenario_nm = entry.get('scenarioName', '?')
        run_id_val = entry.get('experimentRunId', '?')
        print(f"\n  Scenario: {scenario_nm}  |  Run ID: {run_id_val}")

        log_schemas = entry.get('logSchema') or []
        if log_schemas:
            for log in log_schemas:
                lname = log.get('logName') or '(unnamed)'
                props = log.get('logProperties') or []
                print(f"\n  Log: {lname}")
                print(f"  {'─' * 60}")
                if props:
                    print(f"  {'Column':<30} {'Type'}")
                    print(f"  {'─' * 30} {'─' * 20}")
                    for p in props:
                        if isinstance(p, dict):
                            col_name = p.get('name', '?')
                            col_type = p.get('type', '?')
                            if isinstance(col_type, list):
                                col_type = ', '.join(str(t) for t in col_type)
                            print(f"  {col_name:<30} {col_type}")
                else:
                    print(f"  (no columns)")
                found_any = True
        else:
            print(f"  (no log schemas for this scenario)")

    if not found_any and not schema_entries:
        print("  No log schemas returned (model may not produce log data).")


def display_and_poll_run_progress(api, run_id, plan_name, refresh_interval):
    """Display initial run progress then poll until complete/failed/canceled. Returns final status."""
    progress = api.getRunProgress(run_id)
    if progress and isinstance(progress, dict):
        status = progress.get('status', '?')
        run_type = progress.get('runType', '?')
        stage = progress.get('activeStage', '?')
        submitted = progress.get('submissionTime', '?')
        creator = progress.get('creatorName', '?')
        load_ok = progress.get('loadModelSucceeded')

        print(f"\n  {'─' * 60}")
        print(f"  Run Progress for '{progress.get('name', '?')}' (ID: {progress.get('id', '?')})")
        print(f"  {'─' * 60}")
        print(f"  Status:       {status}")
        print(f"  Run Type:     {run_type}")
        print(f"  Active Stage: {stage}")
        print(f"  Submitted:    {submitted}")
        print(f"  Creator:      {creator}")
        print(f"  Model Loaded: {'Yes' if load_ok else 'No' if load_ok is False else 'Pending'}")

        imp = progress.get('importProgress')
        if imp:
            imp_done = imp.get('completed') or 0
            imp_total = imp.get('total') or 0
            imp_ok = imp.get('isSucceeded')
            print(f"  Import:       {imp_done}/{imp_total} {'(done)' if imp_ok else '(in progress)' if imp_ok is None else '(failed)'}")

        run_prog = progress.get('runProgress')
        if run_prog:
            rp_done = run_prog.get('completed') or 0
            rp_total = run_prog.get('total') or 0
            rp_ok = run_prog.get('isSucceeded')
            print(f"  Run:          {rp_done}/{rp_total} {'(done)' if rp_ok else '(in progress)' if rp_ok is None else '(failed)'}")

        exp = progress.get('exportProgress')
        if exp:
            exp_done = exp.get('completed') or 0
            exp_total = exp.get('total') or 0
            exp_ok = exp.get('isSucceeded')
            print(f"  Export:       {exp_done}/{exp_total} {'(done)' if exp_ok else '(in progress)' if exp_ok is None else '(failed)'}")

        pub = progress.get('publishSucceeded')
        if pub is not None:
            print(f"  Publish:      {'Yes' if pub else 'No'}")

        usage = progress.get('usageSnapshot')
        if usage:
            mem_mb = (usage.get('privateMemorySize') or 0) / (1024 * 1024)
            cpu_used = usage.get('cpuTimeUsed') or 0
            cpu_avail = usage.get('cpuTimeAvailable') or 1
            print(f"  Memory:       {mem_mb:.1f} MB")
            print(f"  CPU:          {cpu_used:.1f}s / {cpu_avail:.1f}s ({(cpu_used/cpu_avail*100):.0f}%)")
        print(f"  {'─' * 60}")

    # Poll until complete/failed/canceled
    status = '?'
    while True:
        time.sleep(refresh_interval)
        progress = api.getRunProgress(run_id)
        if not progress or not isinstance(progress, dict):
            print("  Unable to retrieve run progress.")
            break

        status = progress.get('status', '?')
        stage = progress.get('activeStage', '?')
        load_ok = progress.get('loadModelSucceeded')

        parts = [f"Status: {status}", f"Stage: {stage}"]
        if load_ok is not None:
            parts.append(f"Model: {'Loaded' if load_ok else 'Loading'}")

        imp = progress.get('importProgress')
        if imp:
            parts.append(f"Import: {imp.get('completed') or 0}/{imp.get('total') or 0}")

        run_prog = progress.get('runProgress')
        if run_prog:
            parts.append(f"Run: {run_prog.get('completed') or 0}/{run_prog.get('total') or 0}")

        exp = progress.get('exportProgress')
        if exp:
            parts.append(f"Export: {exp.get('completed') or 0}/{exp.get('total') or 0}")

        usage = progress.get('usageSnapshot')
        if usage:
            mem_mb = (usage.get('privateMemorySize') or 0) / (1024 * 1024)
            parts.append(f"Mem: {mem_mb:.0f}MB")

        print(f"  {' | '.join(parts)}")

        if status == "Complete":
            print(f"\n  Plan '{plan_name}' completed successfully.")
            break
        elif status in ("Failed", "Canceled"):
            print(f"\n  Plan '{plan_name}' ended with status: {status}")
            break

    return status


def display_sample_log_data(api, run_id):
    """Fetch and display sample log data from the first non-empty log endpoint."""
    print("\n" + "=" * 80)
    print("  SAMPLE LOG DATA (top 10 rows)")
    print("=" * 80)
    print(f"  Run ID: {run_id}")
    print(f"  {'─' * 60}")

    log_attempts = [
        ("Resource Usage Log",    lambda: api.getScenariosResourceUsageLogData(runId=run_id, page=1, pageSize=10)),
        ("Resource State Log",    lambda: api.getScenariosResourceStateLogData(runId=run_id, page=1, pageSize=10)),
        ("Resource Capacity Log", lambda: api.getScenariosResourceCapacityLogData(runId=run_id, page=1, pageSize=10)),
        ("Task Log",              lambda: api.getScenariosTaskLogData(runId=run_id, page=1, pageSize=10)),
        ("Constraint Log",        lambda: api.getScenariosConstraintLogData(runId=run_id, page=1, pageSize=10)),
    ]

    found_log = False
    for log_label, log_fn in log_attempts:
        log_data = log_fn()
        if isinstance(log_data, list) and len(log_data) > 0:
            print(f"\n  {log_label}:")
            print_table(log_data, max_rows=10)
            found_log = True
            break

    if not found_log:
        print("  No log data found (all log endpoints returned 204/empty).")
        print("  This can happen when input tables are empty or the model doesn't produce log events.")


