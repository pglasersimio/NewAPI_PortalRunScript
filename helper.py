# helper.py
"""
Helper functions for interacting with the Simio Portal Web API.
"""
import sys
import json

def find_modelid_by_projectname(modellist, targetproject):
    """
    Finds the model ID by project name.

    Parameters:
        modellist (list): List of models.
        targetproject (str): Target project name.

    Returns:
        int: The model ID if found, otherwise exits.
    """
    for item in modellist:
        if item.get('projectName') == targetproject:
            return item.get('id')
    print(f"Model '{targetproject}' not found.")
    sys.exit()

def get_id_for_default(json_data):
    """
    Parses a JSON object and returns the id where name is '__Default'.

    Parameters:
        json_data (list): The JSON data to parse.

    Returns:
        int or None: The id if found, otherwise None.
    """
    for item in json_data:
        if item.get('name') == '__Default':
            return item.get('id')
    return None

def get_run_id(json_data, run_name):
    """
    Finds the run ID for a given run name in the JSON data.

    Parameters:
        json_data (list): The JSON data to parse.
        run_name (str): The name of the run to search for.

    Returns:
        int: The ID of the run if found, otherwise 0.
    """
    for item in json_data:
        if item.get('name') == run_name:
            return item.get('id', 0)
    return 0

def get_status_of_highest_additional_run(json_data):
    """
    Finds the status of the maximum 'id' in 'additionalRunsStatus' across all records.

    Parameters:
        json_data (list): List of JSON records.

    Returns:
        str: The status of the maximum 'id' in 'additionalRunsStatus', or None if not found.
    """
    max_entry = None

    for record in json_data:
        additional_runs = record.get('additionalRunsStatus', [])
        if additional_runs:
            current_max = max(additional_runs, key=lambda x: x.get('id', 0))
            if not max_entry or current_max.get('id', 0) > max_entry.get('id', 0):
                max_entry = current_max

    return max_entry.get('status', None) if max_entry else None

def get_max_id_status(json_data):
    """
    Finds the maximum ID and its status and status message.

    Parameters:
        json_data (list): List of JSON records.

    Returns:
        tuple: Max ID, status, and status message.
    """
    max_id = -1
    status_of_max_id = None
    status_message_of_max_id = None

    for run in json_data:
        for additional_run in run.get("additionalRunsStatus", []):
            run_id = additional_run.get("id", -1)
            if run_id > max_id:
                max_id = run_id
                status_of_max_id = additional_run.get("status")
                status_message_of_max_id = additional_run.get("statusMessage")

    return max_id, status_of_max_id, status_message_of_max_id

def set_run_json(experiment_id, description="New Run", name="Default Run", existing_experiment_run_id=0, run_plan=True, run_replications=True, allow_export_at_end_of_replication=True, scenarios=None, external_inputs=None, risk_analysis_confidence_level="Point90", warm_up_period_hours=0, upper_percentile="Percent75", lower_percentile="Percent1", primary_response="", default_replications_required=0, concurrent_replication_limit=0, start_end_time=None):
    if scenarios is None:
        scenarios = [
            {
                "name": "Default Scenario",
                "replicationsRequired": 1,
                "controlValues": [],
                "connectorConfigurations": [],
                "activeTableBindings": []
            }
        ]

    if external_inputs is None:
        external_inputs = []

    if start_end_time is None:
        start_end_time = {
            "isSpecificStartTime": True,
            "specificStartingTime": "2025-01-09T00:00:00Z",
            "startTimeSelection": "Second",
            "isSpecificEndTime": True,
            "isInfinite": False,
            "specificEndingTime": "2025-01-10T00:00:00Z",
            "isRunLength": True,
            "endTimeSelection": "Hours",
            "endTimeRunValue": 24
        }

    run_request = {
        "experimentId": experiment_id,
        "description": description,
        "name": name,
        "existingExperimentRunId": existing_experiment_run_id,
        "runPlan": run_plan,
        "runReplications": run_replications,
        "allowExportAtEndOfReplication": allow_export_at_end_of_replication,
        "createInfo": {
            "scenarios": scenarios,
            "externalInputs": external_inputs,
            "riskAnalysisConfidenceLevel": risk_analysis_confidence_level,
            "warmUpPeriodHours": warm_up_period_hours,
            "upperPercentile": upper_percentile,
            "lowerPercentile": lower_percentile,
            "primaryResponse": primary_response,
            "defaultReplicationsRequired": default_replications_required,
            "concurrentReplicationLimit": concurrent_replication_limit,
            "startEndTime": start_end_time
        }
    }

    return run_request
"""
# Example usage
test_run_request = set_run_json(experiment_id=1, description='test')
print(json.dumps(test_run_request, indent=4))
"""