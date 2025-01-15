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
    Finds the model ID by project name.

    Parameters:
        modellist (list): List of models.
        targetproject (str): Target project name.

    Returns:
        int: The model ID if found, otherwise exits.
    """
    for item in modellist_json:
        if item.get('projectName') == targetproject:
            return item.get('id')
    print(f"Model '{targetproject}' not found.")
    sys.exit()

def get_id_for_default(experiment_json):
    """
    Parses a JSON object and returns the id where name is '__Default'.

    Parameters:
        json_data (list): The JSON data to parse.

    Returns:
        int or None: The id if found, otherwise None.
    """
    for item in experiment_json:
        if item.get('name') == '__Default':
            return item.get('id')
    return None


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
                print(f"Checking run ID {run_id}: Status = {status}, Message = {status_message}")
            else:
                print(f"Checking run ID {run_id}: Status = {status}")

            # Continue checking if the run is still "Running" or "NotStarted"
            if status in ["Running", "NotStarted"]:
                continue
            else:
                # Run completed or failed
                print(f"Run ID {run_id} completed with Status: {status}, Message = {status_message}")
                break
        except Exception as e:
            print(f"Error checking run status: {str(e)}")
            break

