# main.py
"""
Main script to interact with the Simio Portal Web API using the pysimio package.
"""
from helper import *
from pysimio import pySimio
from dotenv import load_dotenv
import os
import json
import time

# Load environment variables
load_dotenv()

# Configuration
simio_portal_url = "https://servicestest1.internal.simioportal.com:8443"
personal_access_token = os.getenv("PERSONAL_ACCESS_TOKEN")
project_name = os.getenv("PROJECT_NAME")
plan_name = "_ModelValues4"

# Ensure token is loaded
if not personal_access_token:
    raise ValueError("Personal access token not found. Make sure it's set in the environment.")

# API Initialization
api = pySimio(simio_portal_url)
api.authenticate(personalAccessToken=personal_access_token)

# Get Model ID
model_id = find_modelid_by_projectname(api.getModels(), project_name)
print(f"The id for project '{project_name}' is {model_id}")

# Get Experiment ID
experiment_id = get_id_for_default(api.getExperiments(model_id))
print(f"The experiment id for __default for project '{project_name}' is {experiment_id}")

# Get Run ID
run_id = get_run_id(api.getRuns(experiment_id), plan_name)

if run_id == 0:
    # If plan name is not found, create a new run plan
    print(f"Plan '{plan_name}' not found. Creating a new plan...")
    new_run = api.createRun(modelId=model_id, experimentRunName=plan_name)
    print(f"New run created with ID: {new_run}")

    # Start the newly created run
    run_started = api.startRunFromExisting(new_run, runPlan=True, runReplications=False)
    print(f"Run started: {json.dumps(run_started, indent=4)}")

    # Check new run status every 30 seconds until it is not 'Running'
    while True:
        time.sleep(30)
        run_status_response = api.getRuns(experiment_id)
        max_id, status, status_message = get_max_id_status(run_status_response)
        print(f"Checking new run status: {status}, Status Message: {status_message}")

        if status == "Running":
            continue
        else:
            print(f"New run completed with Status: {status}, Status Message: {status_message}")
            break
else:
    print(f"The run id for __default for project '{project_name}' with experiment id {experiment_id} for plan named '{plan_name}' is {run_id}")

    # Start the run if run_id exists
    if run_id > 0:
        run_started = api.startRunFromExisting(run_id, runPlan=True, runReplications=False)
        print(f"Run started: {json.dumps(run_started, indent=4)}")

        # Check existing run status every 30 seconds until it is not 'Running'
        while True:
            time.sleep(30)
            run_status_response = api.getRuns(experiment_id)
            max_id, status, status_message = get_max_id_status(run_status_response)
            print(f"Checking existing run status: {status}, Status Message: {status_message}")

            if status == "Running":
                continue
            else:
                print(f"Existing run completed with Status: {status}, Status Message: {status_message}")
                break
    else:
        print("No valid run_id found to start.")

