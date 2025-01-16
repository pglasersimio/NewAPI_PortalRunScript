# Simio Portal Web API Demo

This repository contains a Python script to interact with the Simio Portal Web API using the `pysimio` package. The script allows you to start a simulation run, check its status periodically, and handle both existing and newly created runs.

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
- Authenticate with the Simio Portal API.
- Retrieve model, experiment, and run IDs.
- Start an existing run or create a new run if the specified plan is not found.
- Periodically check the status of a run until it completes.

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
   PROJECT_NAME=your_project_name
   SIMIO_PORTAL_URL=your_url
   ```

4. Add the `.env` file to `.gitignore` to ensure it is not committed to the repository:
   ```gitignore
   # Ignore environment file
   .env
   ```

## Usage

1. Update the `main.py` file with your Simio Portal URL, project name, and plan name.

2. Run the script:
   ```bash
   python main.py
   ```

## Helper Functions
The `helper.py` file contains the following functions:

- `refresh_auth_token(api, refresh_interval)`  
  Refreshes the API authentication token at regular intervals using the `PERSONAL_ACCESS_TOKEN` environment variable.

- `find_modelid_by_projectname(modellist_json, targetproject)`  
  Finds the model ID for a given project name. Exits if the project is not found.

- `get_id_for_default(experiment_json)`  
  Retrieves the experiment ID for the default experiment (`__Default`).

- `find_parent_run_id(json_data, run_name)`  
  Finds the parent run ID for a specified run name within JSON data.

- `check_run_id_status(api, experiment_id, run_id, sleep_time)`  
  Monitors the status of a specific run ID and its associated child runs, providing detailed status updates until completion or failure.


## Environment Variables
This project uses the `python-dotenv` package to load environment variables from a `.env` file.

### Example `.env` File:
```env
PERSONAL_ACCESS_TOKEN=your_personal_access_token
PROJECT_NAME=your_project_name
SIMIO_PORTAL_URL=your_url
```

## Requirements
- Python 3.8+
- `pysimio`
- `requests`
- `tenacity`
- `decorator`
- `python-dotenv`
- `load_dotenv`

## Adding Dependencies
If you need to add more Python packages, update the `requirements.txt` file:
```bash
pip freeze > requirements.txt
```

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request.

## License
This project is licensed under the Apache License 2.0 License. See the `LICENSE` file for more information.

## Contact
For any questions or issues, please contact [pglaser@simio.com].

