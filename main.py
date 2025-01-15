# main.py
"""
Main script to interact with the Simio Portal Web API using the pysimio package.
"""
from helper import *
from pysimio import pySimio
from dotenv import load_dotenv
import os
import threading
import json

# Load environment variables
load_dotenv()

# Configuration
simio_portal_url = "https://servicestest1.internal.simioportal.com:8443"
personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
project_name = os.getenv("PROJECT_NAME")
plan_name = "ModelValues_test"
auth_refresh_time = 500  # Time in seconds to refresh the auth token
run_status_refresh_time = 10

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

# Get Experiment ID for __Default -- this is where plans are located
experiments_json = api.getExperiments(model_id)
#print(json.dumps(experiments_json, indent=4))
experiment_id = get_id_for_default(experiments_json)
print(f"The experiment id for '{plan_name}' for project '{project_name}' is {experiment_id}")

# Get parent run_id
additionalruns_json = api.getRuns(experiment_id)
#print(json.dumps(additionalruns_json, indent=4))
existing_run_id = find_parent_run_id(additionalruns_json, plan_name)
print(f"The run_id for '{plan_name}' for project '{project_name}' is {existing_run_id}")

# If a plan exists (existing_run_id > 0)), delete the existing plan by parent run_id, otherwise proceed to run creation
if existing_run_id > 0:
    print(f"The existing plan '{plan_name}' for project '{project_name}' will be deleted")
    api.deleteRun(existing_run_id)  # Pass the run_id to delete the correct run
    time.sleep(2)
    print(f"The existing plan '{plan_name}' for project '{project_name}' was deleted")
else:
    print(f"No existing plan '{plan_name}' found for project '{project_name}', proceeding to create a new run.")

# Create a new Plan and return the run_id as new_run_id
new_run_id = api.createRun(model_id, plan_name)
print(f"The run_id for '{plan_name}' is {new_run_id } was created successfully")

# Start new_run_id plan
new_run_id_start_response = api.startRunFromExisting(existingExperimentRunId=new_run_id,runPlan=True,runReplications=True)
print(f"The run_id for '{plan_name}' is {new_run_id } was started")

# Check new run status every 10 seconds until it is not 'Running'
check_run_id_status(api, experiment_id, new_run_id, run_status_refresh_time)
