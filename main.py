# main.py
"""
Main script to interact with the Simio Portal Web API using the pysimio package.
"""
from helper import *
from pysimio import pySimio
from dotenv import load_dotenv
import os
import threading
from pysimio.classes import TimeOptions
import logging

# Load environment variables
load_dotenv(override=True)

# Configuration
simio_portal_url = os.getenv("SIMIO_PORTAL_URL")
personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
project_name = "SchedulingDiscretePartProduction" # Name of the project containing the model
plan_name = "ModelValues_test" # Name of the plan to create (will be deleted and re-created if it already exists under the same experiment)
auth_refresh_time = 500  # Time in seconds to refresh the auth token
run_status_refresh_time = 2
UseSpecificStartTime = True
UseSpecificEndTime = True
plan_start_datetime = '2025-12-13T03:14:00Z'
plan_end_dateTime = '2025-12-20T03:14:00Z'

# Post-run output toggles
show_table_schema = True        # Display table schema after run completes
show_sample_table_data = True   # Display sample table data (first non-empty table, top 10 rows)
show_log_schema = True          # Display log schema after run completes
show_sample_log_data = True     # Display sample log data (first non-empty log, top 10 rows)
show_table_summary = True       # Full paged dump of a specific table
summary_table_name = "ManufacturingOrders"  # Table to dump in full
summary_page_size = 100         # Rows per API page when fetching full table

# Ensure token is loaded
if not personal_access_token:
    raise ValueError("Personal access token not found. Make sure it's set in the environment.")

# API Initialization getting bearer token for authorization
api = pySimio(simio_portal_url)
api.authenticate(personalAccessToken=personal_access_token)

# Start token refresh in a background thread
threading.Thread(target=refresh_auth_token, args=(api, auth_refresh_time), daemon=True).start()

# Get Model ID
models_json = api.getModels()
#print(json.dumps(models_json, indent=4))
model_id = find_modelid_by_projectname(models_json, project_name)
print(f"The model_id for project '{project_name}' is {model_id}")

# Find existing run matching plan_name in scenarioNames for this model
all_runs_json = api.getRuns(modelId=model_id)
#print(json.dumps(all_runs_json, indent=4))

existing_run_id = 0
for run in all_runs_json:
    if plan_name in run.get('scenarioNames', []):
        existing_run_id = run.get('id', 0)
        break

print(f"The existing run_id for plan '{plan_name}' for project '{project_name}' is {existing_run_id}")

# If a plan exists (existing_run_id > 0), delete the existing plan by run_id, otherwise proceed to run creation
if existing_run_id > 0:
    print(f"The existing parent run_id {existing_run_id} for plan '{plan_name}' for project '{project_name}' will be deleted.")
    api.deleteRun(existing_run_id)  # Pass the run_id to delete the correct run
    print(f"The existing parent run_id {existing_run_id} for plan '{plan_name}' for project '{project_name}' was deleted. All additional related child run_ids are deleted too.")
else:
    print(f"No existing plan '{plan_name}' found for project '{project_name}', proceeding to create a new run.")

# Create a new Plan and return the run_id as new_run_id
new_run_id = api.createRun(model_id, plan_name)
if not new_run_id:
    print(f"Failed to create plan '{plan_name}' for project '{project_name}'. Check that the authenticated user is the model owner or an experimenter.")
    exit(1)
print(f"The new parent run_id for '{plan_name}' is {new_run_id} was created successfully")

# Display control values and let the user adjust any before running
display_and_update_control_values(api, new_run_id, plan_name)

# Adjust the start date/time
run_time_options = TimeOptions(runId=new_run_id, isSpecificStartTime=UseSpecificStartTime, specificStartingTime=plan_start_datetime,
                               isSpecificEndTime=UseSpecificEndTime, specificEndingTime=plan_end_dateTime)
api.setRunTimeOptions(run_time_options)
print(f"The control value for run_id {new_run_id} and plan name '{plan_name}' was updated to start at {plan_start_datetime} and end at {plan_end_dateTime}")

# Start new_run_id plan, set runReplications to True for Risk Analysis
new_run_id_start_response = api.startRunFromExisting(existingExperimentRunId=new_run_id,runPlan=True,runReplications=False)
print(f"The plan '{plan_name}' for '{project_name}' was started.")

# Display initial run progress, then poll until complete/failed/canceled
status = display_and_poll_run_progress(api, new_run_id, plan_name, run_status_refresh_time)

if status in ("Failed", "Canceled"):
    print(f"\nSkipping table/log retrieval — run ended with status: {status}")
    exit(1)

# Suppress pysimio internal logger tracebacks for 204 responses
logging.getLogger('pysimio.api').setLevel(logging.CRITICAL)

# Post-run output based on toggles
if show_table_schema:
    table_names = display_table_schema(api, model_id, new_run_id)
if show_sample_table_data:
    if not show_table_schema:
        table_names = display_table_schema(api, model_id, new_run_id)
    display_sample_table_data(api, new_run_id, plan_name, table_names)
if show_log_schema:
    display_log_schema(api, new_run_id)
if show_sample_log_data:
    display_sample_log_data(api, new_run_id)
if show_table_summary:
    display_full_table(api, new_run_id, plan_name, summary_table_name, summary_page_size)
