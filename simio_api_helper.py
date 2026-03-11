# simio_api_helper.py
"""
Direct REST API wrapper for the Simio Portal Web API.
Provides SimioAPI class with identical method signatures to pysimio's pySimio,
so shared_helper.py functions work interchangeably with either.
"""
import requests
import logging
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes (mirrors pysimio.classes)
# ---------------------------------------------------------------------------

@dataclass
class TimeOptions:
    """Mirrors pysimio.classes.TimeOptions"""
    runId: int
    endTimeRunValue: Optional[int] = None
    specificStartingTime: Optional[str] = None
    startTimeSelection: Optional[str] = None
    specificEndingTime: Optional[str] = None
    endTimeSelection: Optional[str] = None
    isSpecificStartTime: Optional[bool] = None
    isSpecificEndTime: Optional[bool] = None
    isInfinite: Optional[bool] = None
    isRunLength: Optional[bool] = None

    def as_json(self, include_null: bool = False) -> dict:
        return {
            key: value
            for key, value in asdict(self).items()
            if value is not None or include_null
        }


# ---------------------------------------------------------------------------
# Retry-on-401 decorator
# ---------------------------------------------------------------------------

def _retry_on_unauthorized(method):
    """Decorator that retries once after re-authenticating on 401."""
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except _UnauthorizedError:
            # Re-authenticate and retry once
            try:
                self._reauthenticate()
                return method(self, *args, **kwargs)
            except Exception:
                logger.exception("Re-authentication retry failed")
                return None
    return wrapper


class _UnauthorizedError(Exception):
    """Internal sentinel for 401 responses."""
    pass


# ---------------------------------------------------------------------------
# SimioAPI class
# ---------------------------------------------------------------------------

class SimioAPI:
    """
    Direct REST API client for Simio Portal.
    Method signatures match pysimio.pySimio exactly.
    """

    def __init__(self, baseURL: str):
        self.apiURL = f"{baseURL}/api"
        self.authToken = None
        self.headers = {
            "accept": "application/json",
            "Authorization": ""
        }
        self.personalAccessToken = None

    # -- Auth ---------------------------------------------------------------

    def authenticate(self, personalAccessToken: str = None, samlResponse: str = None):
        try:
            self.personalAccessToken = personalAccessToken
            authBody = {"personalAccessToken": personalAccessToken}
            resp = requests.post(f"{self.apiURL}/auth", json=authBody)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("token"):
                    self.authToken = data["token"]
                    self.headers["Authorization"] = f"Bearer {self.authToken}"
                else:
                    raise RuntimeError("Authentication response missing token")
            else:
                raise RuntimeError(f"Authentication failed: {resp.status_code} {resp.text}")
        except Exception:
            logger.exception("Authentication error")

    def _reauthenticate(self):
        if self.personalAccessToken:
            self.authenticate(personalAccessToken=self.personalAccessToken)

    # -- Helpers ------------------------------------------------------------

    def _get(self, path, params=None):
        """GET request, returns parsed JSON or None. Raises _UnauthorizedError on 401."""
        resp = requests.get(f"{self.apiURL}{path}", params=params, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 204:
            return {}
        elif resp.status_code == 401:
            raise _UnauthorizedError()
        else:
            raise RuntimeError(f"GET {path} failed: {resp.status_code} {resp.text}")

    def _post(self, path, body):
        """POST request, returns parsed JSON or True. Raises _UnauthorizedError on 401."""
        resp = requests.post(f"{self.apiURL}{path}", json=body, headers=self.headers)
        if resp.status_code in (200, 201):
            try:
                return resp.json()
            except Exception:
                return True
        elif resp.status_code == 204:
            return True
        elif resp.status_code == 401:
            raise _UnauthorizedError()
        else:
            raise RuntimeError(f"POST {path} failed: {resp.status_code} {resp.text}")

    def _put(self, path, body):
        """PUT request, returns True on success. Raises _UnauthorizedError on 401."""
        resp = requests.put(f"{self.apiURL}{path}", json=body, headers=self.headers)
        if resp.status_code in (200, 204):
            return True
        elif resp.status_code == 401:
            raise _UnauthorizedError()
        else:
            raise RuntimeError(f"PUT {path} failed: {resp.status_code} {resp.text}")

    def _delete(self, path):
        """DELETE request, returns True on success. Raises _UnauthorizedError on 401."""
        resp = requests.delete(f"{self.apiURL}{path}", headers=self.headers)
        if resp.status_code in (200, 204):
            return True
        elif resp.status_code == 401:
            raise _UnauthorizedError()
        else:
            raise RuntimeError(f"DELETE {path} failed: {resp.status_code} {resp.text}")

    # -- Models -------------------------------------------------------------

    @_retry_on_unauthorized
    def getModels(self, project_id: int = None, owned_models: bool = False, include_published: bool = False):
        params = []
        if project_id is not None:
            params.append(('project_id', project_id))
        if owned_models:
            params.append(('owned_models', owned_models))
        if include_published:
            params.append(('include_published', include_published))
        return self._get("/v1/models", params=params or None)

    @_retry_on_unauthorized
    def getModelTable(self, model_id: int, table_name: str = None):
        params = []
        if table_name is not None:
            params.append(("table_name", table_name))
        return self._get(f"/v1/models/{model_id}/table-schemas", params=params or None)

    # -- Runs ---------------------------------------------------------------

    @_retry_on_unauthorized
    def getRuns(self, experimentId: int = None, experimentName: str = None, modelId: int = None):
        params = []
        if experimentId is not None:
            params.append(('experiment_id', experimentId))
        if experimentName is not None:
            params.append(('name', experimentName))
        if modelId is not None:
            params.append(('model_id', modelId))
        return self._get("/v1/runs", params=params or None)

    @_retry_on_unauthorized
    def getRun(self, runId: int = None):
        return self._get(f"/v1/runs/{runId}")

    @_retry_on_unauthorized
    def getRunProgress(self, runId: int = None):
        return self._get(f"/v1/runs/{runId}/progress")

    @_retry_on_unauthorized
    def createRun(self, modelId: int, experimentRunName: str):
        body = {
            "modelId": modelId,
            "experimentRunName": experimentRunName
        }
        return self._post("/v1/runs/create", body)

    @_retry_on_unauthorized
    def deleteRun(self, runId: int):
        return self._delete(f"/v1/runs/{runId}")

    @_retry_on_unauthorized
    def cancelRun(self, runId: int):
        body = {"status": "cancelled"}
        resp = requests.patch(f"{self.apiURL}/v1/runs/{runId}", headers=self.headers, json=body)
        if resp.status_code == 204:
            return True
        elif resp.status_code == 401:
            raise _UnauthorizedError()
        else:
            raise RuntimeError(f"cancelRun failed: {resp.status_code} {resp.text}")

    @_retry_on_unauthorized
    def startRunFromExisting(self, existingExperimentRunId: int, runPlan: bool = True, runReplications: bool = True):
        body = {
            "existingExperimentRunId": existingExperimentRunId,
            "runPlan": runPlan,
            "runReplications": runReplications
        }
        return self._post("/v1/runs/start-existing-plan-run", body)

    @_retry_on_unauthorized
    def setRunTimeOptions(self, timeOptions: TimeOptions):
        runId = timeOptions.runId
        body = timeOptions.as_json()
        return self._put(f"/v1/runs/{runId}/time-options", body)

    # -- Scenarios ----------------------------------------------------------

    @_retry_on_unauthorized
    def getScenarios(self, run_id: int = None, include_observations: bool = False):
        params = []
        if run_id is not None:
            params.append(('run_id', run_id))
        if include_observations:
            params.append(('include_observations', include_observations))
        return self._get(f"/v1/runs/{run_id}/scenarios", params=params or None)

    @_retry_on_unauthorized
    def setControlValues(self, runId: int, scenarioName: str, controlName: str, controlValue: str):
        body = {"value": controlValue}
        return self._put(f"/v1/runs/{runId}/scenarios/{scenarioName}/control-values/{controlName}", body)

    # -- Table Data ---------------------------------------------------------

    @_retry_on_unauthorized
    def getTableData(self, runId: int, scenarioName: str, tableName: str,
                     page: int = None, pageSize: int = None, filter: str = None):
        params = []
        if runId is not None:
            params.append(('run_id', runId))
        if scenarioName is not None:
            params.append(('scenario_name', scenarioName))
        if tableName is not None:
            params.append(('table_name', tableName))
        if page is not None:
            params.append(('page', page))
        if pageSize is not None:
            params.append(('page_size', pageSize))
        if filter is not None:
            params.append(('filter', filter))
        return self._get(f"/v1/runs/{runId}/scenarios/{scenarioName}/table-data/{tableName}", params=params or None)

    # -- Log Schemas --------------------------------------------------------

    @_retry_on_unauthorized
    def getScenariosLogSchemas(self, runId: int, logName: str = None):
        params = [('run_id', runId)]
        if logName is not None:
            params.append(('log_name', logName))
        return self._get(f"/v1/runs/{runId}/scenarios/log-schemas", params=params)

    # -- Log Data -----------------------------------------------------------

    def _get_log_data(self, runId: int, log_type: str, page: int = None, pageSize: int = None):
        """Shared helper for all log data endpoints."""
        params = [('run_id', runId)]
        if page is not None:
            params.append(('page', page))
        if pageSize is not None:
            params.append(('page_size', pageSize))
        return self._get(f"/v1/runs/{runId}/scenarios/log-data/{log_type}", params=params)

    @_retry_on_unauthorized
    def getScenariosResourceUsageLogData(self, runId: int, page: int = None, pageSize: int = None):
        return self._get_log_data(runId, "resource-usage-log", page, pageSize)

    @_retry_on_unauthorized
    def getScenariosResourceStateLogData(self, runId: int, page: int = None, pageSize: int = None):
        return self._get_log_data(runId, "resource-state-log", page, pageSize)

    @_retry_on_unauthorized
    def getScenariosResourceCapacityLogData(self, runId: int, page: int = None, pageSize: int = None):
        return self._get_log_data(runId, "resource-capacity-log", page, pageSize)

    @_retry_on_unauthorized
    def getScenariosTaskLogData(self, runId: int, page: int = None, pageSize: int = None):
        return self._get_log_data(runId, "task-log", page, pageSize)

    @_retry_on_unauthorized
    def getScenariosConstraintLogData(self, runId: int, page: int = None, pageSize: int = None):
        return self._get_log_data(runId, "constraint-log", page, pageSize)
