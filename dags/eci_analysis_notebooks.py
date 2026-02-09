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
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.state import DagRunState
from airflow.operators.python import BranchPythonOperator
from airflow.models import DagRun
from airflow.utils.session import provide_session
from airflow.operators.python import ShortCircuitOperator

# Configuration
ECI_PROJECT_DIR = Path("/opt/airflow/ECI_initiatives")
EDA_DIR = f"{ECI_PROJECT_DIR}/exploratory_data_analysis"

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
    schedule=timedelta(days=30),  # Same schedule as data pipeline
    start_date=datetime(2026, 2, 1),
    catchup=False,  # Don't backfill
    tags=["eci", "analysis", "notebooks"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start_analysis")

    # ========== SETUP VENVS (if needed) ==========

    setup_campaigns_venv = BashOperator(
        task_id="setup_campaigns_venv",
        bash_command=f"""
        cd {EDA_DIR}/initiatives_campaigns
        
        # Define a container-specific venv name to avoid conflict with host's .venv
        VENV=".airflow_venv"

        # Check for the python executable specifically
        if [ ! -f "$VENV/bin/python" ]; then
            echo "Creating $VENV for campaigns notebook..."
            rm -rf $VENV
            
            python -m venv $VENV
            
            # Use python -m pip to avoid shebang/script issues
            $VENV/bin/python -m pip install --upgrade pip
            $VENV/bin/python -m pip install -r requirements.prod.txt
        else
            echo "Campaigns venv ($VENV) already exists"
        fi
        
        # Verify Jupyter is installed
        $VENV/bin/python -m pip show jupyter > /dev/null || \\
            $VENV/bin/python -m pip install jupyter nbconvert ipykernel
        """,
        doc_md="Create/verify virtual environment for campaigns notebook with isolated dependencies",
    )

    setup_responses_venv = BashOperator(
        task_id="setup_responses_venv",
        bash_command=f"""
        cd {EDA_DIR}/initiatives_responses
        
        # Define a container-specific venv name to avoid conflict with host's .venv
        VENV=".airflow_venv"
        
        # Check for the python executable specifically
        if [ ! -f "$VENV/bin/python" ]; then
            echo "Creating $VENV for responses notebook..."
            rm -rf $VENV
            
            python -m venv $VENV
            
            # Use python -m pip to avoid shebang/script issues
            $VENV/bin/python -m pip install --upgrade pip
            $VENV/bin/python -m pip install -r requirements.prod.txt
        else
            echo "Responses venv ($VENV) already exists"
        fi
        
        # Verify Jupyter is installed
        $VENV/bin/python -m pip show jupyter > /dev/null || \\
            $VENV/bin/python -m pip install jupyter nbconvert ipykernel
        """,
        doc_md="Create/verify virtual environment for responses notebook with isolated dependencies",
    )

    # ========== RUN NOTEBOOKS ==========

    run_signatures_notebook = BashOperator(
        task_id="run_signatures_notebook",
        bash_command=f"""
        cd {EDA_DIR}/initiatives_campaigns
        
        # Use the container-specific venv
        .airflow_venv/bin/python -m jupyter nbconvert \\
            --to notebook \\
            --execute \\
            --inplace \\
            eci_analysis_signatures.ipynb
        
        echo "✓ Signatures notebook updated (pandas==$(.airflow_venv/bin/python -c 'import pandas; print(pandas.__version__)'))"
        """,
        doc_md="""
        ### Execute Signatures Analysis
        Runs eci_analysis_signatures.ipynb with pandas==3.0.0 in isolated venv.
        Analyzes campaign signatures and geographic patterns.
        """,
    )

    run_responses_notebook = BashOperator(
        task_id="run_responses_notebook",
        bash_command=f"""
        cd {EDA_DIR}/initiatives_responses
        
        # Use the container-specific venv
        .airflow_venv/bin/python -m jupyter nbconvert \\
            --to notebook \\
            --execute \\
            --inplace \\
            eci_analysis_responses.ipynb
        
        echo "✓ Responses notebook updated (pandas==$(.airflow_venv/bin/python -c 'import pandas; print(pandas.__version__)'))"
        """,
        doc_md="""
        ### Execute Responses Analysis
        Runs eci_analysis_responses.ipynb with pandas==2.3.3 in isolated venv.
        Analyzes Commission responses and legislative outcomes.
        """,
    )

    # ========== COMPLETE ==========

    complete = EmptyOperator(
        task_id="analysis_complete",
        doc_md="""
        Analysis notebooks updated successfully.
        
        **View Results:**
        - initiatives_campaigns/eci_analysis_signatures.ipynb
        - initiatives_responses/eci_analysis_responses.ipynb
        
        Each notebook runs with its own isolated dependencies in separate venvs.
        """,
    )

    # ========== TASK DEPENDENCIES ==========

    # Setup venvs after pipeline completes
    start >> [setup_campaigns_venv, setup_responses_venv]

    # Run notebooks with their respective venvs
    setup_campaigns_venv >> run_signatures_notebook
    setup_responses_venv >> run_responses_notebook

    # Complete after both notebooks finish
    [run_signatures_notebook, run_responses_notebook] >> complete
