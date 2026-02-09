"""
European Citizens' Initiatives (ECI) Data Pipeline DAG

This DAG orchestrates the complete ECI data collection and processing pipeline:
1. Scrape initiatives registry pages
2. Extract structured data from initiatives HTML
3. Scrape Commission response pages
4. Extract legislative outcomes from responses
5. Scrape follow-up websites
6. Extract implementation data from follow-up sites
7. Merge all data into master CSV

The pipeline alternates between scraping and extraction. This task ordering
provides natural delays between scraping sessions, giving the server time to
"forget" requests and reducing the risk of rate limiting or blacklisting.
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

# Pipeline configuration
ECI_PROJECT_DIR = Path("/opt/airflow/ECI_initiatives")

# NOTE: Use dedicated venv for better dependency isolation and easier maintenance.
# The .venv must be pre-created in ECI_initiatives/ with dependencies installed.
# Benefits: no conflicts with Airflow's packages, easier to update/test independently.
PYTHON_VENV = f"{ECI_PROJECT_DIR}/.venv/bin/python"

# Default arguments for all tasks
default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="eci_data_pipeline",
    default_args=default_args,
    description="ECI scraping, extraction, and merging pipeline",
    schedule=timedelta(days=30),  # Run monthly to capture new initiatives
    start_date=datetime(2026, 2, 1),
    catchup=False,  # Don't backfill - only scrape current state, not historical
    tags=["eci", "scraping", "data-pipeline", "eu"],
    doc_md=__doc__,
) as dag:

    # ========== STAGE 1: INITIATIVES ==========

    scrape_initiatives = BashOperator(
        task_id="scrape_initiatives",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.scraper.initiatives",
        doc_md="""
        ### Scrape Initiatives Registry
        Downloads raw HTML pages from the ECI registry containing:
        - Initiative titles and descriptions
        - Signature counts by country
        - Registration and deadline dates
        """,
    )

    extract_initiatives = BashOperator(
        task_id="extract_initiatives",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.extractor.initiatives",
        doc_md="""
        ### Extract Initiatives Data
        Parses HTML into structured CSV files with:
        - Campaign metadata
        - Signature geography
        - Timeline information
        """,
    )

    # ========== STAGE 2: COMMISSION RESPONSES ==========

    scrape_responses = BashOperator(
        task_id="scrape_responses",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.scraper.responses",
        doc_md="""
        ### Scrape Commission Responses
        Downloads HTML pages containing Commission's official responses to successful initiatives.
        """,
    )

    extract_responses = BashOperator(
        task_id="extract_responses",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.extractor.responses",
        doc_md="""
        ### Extract Response Data
        Parses response pages to extract:
        - Legislative proposals
        - Legal act references
        - Implementation status
        """,
    )

    # ========== STAGE 3: FOLLOW-UP WEBSITES ==========

    scrape_followup = BashOperator(
        task_id="scrape_followup_websites",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.scraper.responses_followup_website",
        doc_md="""
        ### Scrape Follow-up Websites
        Downloads dedicated follow-up sites tracking long-term implementation of initiatives.
        """,
    )

    extract_followup = BashOperator(
        task_id="extract_followup_data",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.extractor.responses_followup_website",
        doc_md="""
        ### Extract Follow-up Implementation Data
        Parses follow-up sites to extract detailed implementation tracking information.
        """,
    )

    # ========== STAGE 4: DATA MERGING ==========

    merge_data = BashOperator(
        task_id="merge_all_data",
        bash_command=f"cd {ECI_PROJECT_DIR} && {PYTHON_VENV} -m data_pipeline.csv_merger.responses",
        doc_md="""
        ### Merge Master Dataset
        Combines all extracted data into the master accountability CSV:
        `eci_merger_responses_and_followup_*.csv`
        
        This dataset answers: "Do citizens' initiatives actually lead to new EU laws?"
        """,
    )

    # ========== PIPELINE SUCCESS ==========

    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        doc_md="""
        Pipeline completed successfully. 
        
        **View Results:**
        - Data: Check output in: `ECI_initiatives/data/YYYY-MM-DD_HH-MM-SS/
        - Analysis: Run notebooks in `ECI_initiatives/exploratory_data_analysis/`
        """,
    )

    # ========== TASK DEPENDENCIES ==========

    # Stage 1: Initiatives
    scrape_initiatives >> extract_initiatives

    # Stage 2: Responses (depends on initiatives completion)
    (extract_initiatives >> scrape_responses >> extract_responses)

    # Stage 3: Follow-up (depends on responses completion)
    extract_responses >> scrape_followup >> extract_followup

    # Stage 4: Merge (depends on all extractions)
    extract_followup >> merge_data >> pipeline_complete
