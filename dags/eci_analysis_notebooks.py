"""
ECI Analysis Notebooks Execution

Runs Jupyter notebooks in sequence after data pipeline completes:
1. Wait for eci_data_pipeline to finish
2. Execute initiatives_campaigns/eci_analysis_signatures.ipynb
3. Execute initiatives_responses/eci_analysis_responses.ipynb

Notebooks are updated in-place with fresh outputs (no HTML/PDF generation).
Each notebook uses its own virtual environment to avoid dependency conflicts.
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

# ----------------------------------------------------------------------
# GLOBAL CONFIGURATION
# ----------------------------------------------------------------------

# Paths
ECI_PROJECT_DIR = Path("/opt/airflow/ECI_initiatives")
EDA_DIR = f"{ECI_PROJECT_DIR}/exploratory_data_analysis"
CAMPAIGNS_DIR = f"{EDA_DIR}/initiatives_campaigns"
RESPONSES_DIR = f"{EDA_DIR}/initiatives_responses"

# Virtual Environment Configuration
# Extracting these allows you to change the venv name globally in one place
VENV_NAME = ".airflow_venv"
VENV_PYTHON = f"{VENV_NAME}/bin/python"

# ----------------------------------------------------------------------
# BASH COMMAND TEMPLATES
# ----------------------------------------------------------------------

# Template for creating/updating the virtual environment
SETUP_VENV_TEMPLATE = """
    cd {directory}

    # 1. Check if the python executable exists
    if [ ! -f "{venv_python}" ]; then
        echo "Creating {venv_name} in $(pwd)..."
        rm -rf {venv_name}
        
        python -m venv {venv_name}
        
        # Use generated python to call pip (avoids shebang issues)
        "{venv_python}" -m pip install --upgrade pip
        "{venv_python}" -m pip install -r requirements.prod.txt
    else
        echo "Venv already exists at {venv_name}"
    fi
    
    # 2. Ensure Jupyter is installed
    "{venv_python}" -m pip show jupyter > /dev/null || \\
        "{venv_python}" -m pip install jupyter nbconvert ipykernel
"""

# Template for running the notebook
RUN_NOTEBOOK_TEMPLATE = """
    cd {directory}
    
    echo "Executing {notebook_name} using {venv_name}..."
    
    # Run nbconvert via the venv's python module
    "{venv_python}" -m jupyter nbconvert \\
        --to notebook \\
        --execute \\
        --inplace \\
        {notebook_name}
    
    echo "✓ {notebook_name} updated successfully."
    echo "  (Using pandas==$("{venv_python}" -c 'import pandas; print(pandas.__version__)'))"
"""

# ----------------------------------------------------------------------
# DAG DEFINITION
# ----------------------------------------------------------------------

default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}

with DAG(
    dag_id="eci_analysis_notebooks",
    default_args=default_args,
    description="Execute EDA notebooks after pipeline completion",
    schedule=timedelta(days=30),
    start_date=datetime(2026, 2, 1),
    catchup=False,
    tags=["eci", "analysis", "notebooks"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start_analysis")

    # ========== SETUP VENVS ==========

    setup_campaigns_venv = BashOperator(
        task_id="setup_campaigns_venv",
        bash_command=SETUP_VENV_TEMPLATE.format(
            directory=CAMPAIGNS_DIR, venv_name=VENV_NAME, venv_python=VENV_PYTHON
        ),
        doc_md="Create container-specific venv for campaigns notebook",
    )

    setup_responses_venv = BashOperator(
        task_id="setup_responses_venv",
        bash_command=SETUP_VENV_TEMPLATE.format(
            directory=RESPONSES_DIR, venv_name=VENV_NAME, venv_python=VENV_PYTHON
        ),
        doc_md="Create container-specific venv for responses notebook",
    )

    # ========== RUN NOTEBOOKS ==========

    run_signatures_notebook = BashOperator(
        task_id="run_signatures_notebook",
        bash_command=RUN_NOTEBOOK_TEMPLATE.format(
            directory=CAMPAIGNS_DIR,
            notebook_name="eci_analysis_signatures.ipynb",
            venv_name=VENV_NAME,
            venv_python=VENV_PYTHON,
        ),
        doc_md="### Execute Signatures Analysis\nRuns eci_analysis_signatures.ipynb",
    )

    run_responses_notebook = BashOperator(
        task_id="run_responses_notebook",
        bash_command=RUN_NOTEBOOK_TEMPLATE.format(
            directory=RESPONSES_DIR,
            notebook_name="eci_analysis_responses.ipynb",
            venv_name=VENV_NAME,
            venv_python=VENV_PYTHON,
        ),
        doc_md="### Execute Responses Analysis\nRuns eci_analysis_responses.ipynb",
    )

    # ========== COMPLETE ==========

    complete = EmptyOperator(
        task_id="analysis_complete",
        doc_md="Analysis notebooks updated successfully.",
    )

    # ========== DEPENDENCIES ==========

    start >> [setup_campaigns_venv, setup_responses_venv]
    setup_campaigns_venv >> run_signatures_notebook
    setup_responses_venv >> run_responses_notebook
    [run_signatures_notebook, run_responses_notebook] >> complete
