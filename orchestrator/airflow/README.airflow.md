# Orchestration with Apache Airflow

## 1. What is an Orchestrator? (The Simple Explanation)

Think of an orchestrator as a **fancy wrapper around your scripts**.

In this project, we have Python scripts that scrape websites and Jupyter notebooks that analyze data. You *could* run them manually by typing `python my_script.py` in your terminal every day. But as the project grows, you need something that:
1. Runs them automatically on a schedule (e.g., every month).
2. Remembers to run script B only after script A finishes successfully.
3. Gives you a handy visual dashboard (UI) to check logs and restart failed tasks.

**Airflow** is just the tool we use to handle that "wrapping." It defines the *order* of tasks and provides the UI, but the actual "brain" of the work is still in your regular Python files.

## 2. How to Run It

### Prerequisites
You do not need to install Airflow on your laptop. It runs entirely inside Docker containers defined in the root `docker-compose.yaml`.

### Start the Orchestrator
From the root of the project repository, run:

```bash
docker-compose up -d
```

### Access the UI
Once the containers are running, open your browser:
- **URL:** [http://localhost:8080](http://localhost:8080)
- **Username:** `airflow`
- **Password:** `airflow`

## 3. What is Running?
You will see two main pipelines (DAGs) in the dashboard:

1. **`eci_data_pipeline`**:
   - **What it does:** Runs the scrapers (Selenium) to get data from EU websites, extracts it, and merges it into CSVs.
   - **Schedule:** Monthly.

2. **`eci_analysis_notebooks`**:
   - **What it does:** Runs the Jupyter notebooks found in `ECI_initiatives/exploratory_data_analysis`. It ensures the analysis is always based on the freshest scraped data.
   - **Schedule:** Runs monthly, scheduled 1 hour after the data pipeline starts, and waits for the pipeline to finish before executing.

## 4. How to Trigger a Run Manually
If you don't want to wait for the schedule:
1. Go to the UI ([localhost:8080](http://localhost:8080)).
1. Click **Dags** in the left sidebar (the workflow icon) to view all available pipelines.
1. Find the DAG you want (e.g., `eci_data_pipeline`).
2. Click the button (▶) in the right upper corner of the dag.
3. Click "▶ Trigger" with the selected "Single Run".
4. Click on the DAG to see how the workflow goes.
5. Click on any step to see logs.

## 5. Directory Structure
`orchestrator/airflow`, what the folders do:

- **`dags/`**: (Directed Acyclic Graphs) This is just a fancy name for "Workflows." This folder contains the Python files that tell Airflow *what* to run and *when*.
- **`logs/`**: If a script crashes, the error text is saved here. You can view it in the UI.
- **`config/`**: Configuration files for the Airflow server itself.
- **`plugins/`**: Custom extensions (we mostly rely on standard Python operators).
  
## 6. A Note on Tool Choice & Open Source
We are using Airflow here, but the specific tool doesn't matter as much as the concept. You could replace this directory with **Dagster**, **Prefect**, or simple **Cron** jobs, and the data logic would remain the same. It really depends on your unique current or legacy requirements.

## 7. A Warning on "Open Source" Orchestrators
When choosing an orchestration tool, be careful. Many modern "open-source" tools operate on an "Open Core" model.
- **The Trap:** They offer a basic open-source version but entangle it with closed-source, remote API dependencies or "Cloud" features. They often try to force you into a paid SaaS subscription to get essential security or usability features.
- **Version Control Risk:** Companies can downgrade features in the next open-source version if core development becomes tied to their commercial interests, effectively forcing you to upgrade to their paid tier to maintain functionality you previously had for free.
- **Chosen One:** We use Airflow here because the community edition is fully functional and self-hosted. It runs entirely on your machine via Docker without phoning home to a paid cloud service. Dagster is another valid option that fits this criteria, as its open-source core is feature-complete and allows for full self-hosting without forced cloud dependencies.