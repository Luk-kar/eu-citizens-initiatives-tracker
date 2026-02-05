# ECI Commission Response Extractor

Processing the European Commission's official responses to successful Citizens' Initiatives. Unlike the structured initiative extractor, this tool deals with highly unstructured text, using regex pattern matching and semantic classification to determine the *actual* political and legislative outcome of each initiative.

## 🚀 Purpose

The extractor parses the free-text "Commission Answer" and "Follow-up" sections to answer critical questions:
- **Did it succeed?** Classifies the highest legislative status reached (e.g., "Law Active", "Law Promised", "Rejected").
- **What happened next?** Tracks post-response actions like roadmaps, impact assessments, and public consultations.
- **Why was it rejected?** Identifies rejection reasoning (e.g., "Already covered", "Outside competence").
- **Is it enforceable?** Extracts specific implementation dates, legal references, and deadlines.

## 📂 Project Structure

The module is organized into specialized extractors handling different semantic domains:

- **`model.py`**: Defines the `ECICommissionResponseRecord` schema.
- **`parser/base/`**:
  - `date_parser.py`: Centralized logic for parsing complex date formats ("end of 2024", "May 2018").
  - `text_utilities.py`: Helpers for normalizing whitespace and cleaning HTML text.
  - `base_extractor.py`: Common functionality shared across all extractors.
- **`parser/extractors/`**:
  - `legislative_outcome.py`: The core logic determining the final status (Adopted, Proposed, Rejected, etc.).
  - `followup.py`: Tracks ongoing work like workshops, roadmaps, and court cases.
  - `structural_analysis.py`: Extracts references to specific EU laws (Regulations/Directives).
  - *and others...*
- **`parser/consts/`**:
  - `eci_status.py`: Defines the hierarchy of outcomes (Applicable > Adopted > Committed > ...).
  - `legislative_status.py`: Definitions for specific legislative stages (e.g., "In Vacatio Legis").
  - `non_legislative_actions.py`: Classifications for non-binding actions (Impact Assessments, Funding).
  - `keywords.py` & `patterns.py`: Centralized regex patterns for detecting commitments, deadlines, and rejections.
  - `dates.py`: Month name mappings for parsing.


## ⚙️ Workflow

1. **Discovery**: Locates the latest run directory containing `responses/` HTML files.
2. **Text Normalization**: Cleans whitespace and normalizes text for consistent pattern matching.
3. **Semantic Classification**:
   - **Status Matching**: Scans text for specific legal phrases ("entered into force", "will table a proposal") to assign a technical status.
   - **Action Categorization**: Distinguishes between *legislative* acts (new laws) and *non-legislative* actions (funding, monitoring, studies).
4. **Data Extraction**:
   - Extracts specific dates (deadlines, meetings, hearings) using a robust date parser.
   - Identifies referenced EU legislation by ID (e.g., "Regulation (EU) 2019/1020").
5. **Output**: Saves the enriched dataset to `eci_responses_{TIMESTAMP}.csv`.

## 📊 Data Fields

The output CSV (`eci_responses_{TIMESTAMP}.csv`) provides a deep-dive analysis of each response:

| Category | Key Fields |
| :--- | :--- |
| **Outcome** | `final_outcome_status` (e.g., "Law Active"), `law_implementation_date` |
| **Commitments** | `commission_promised_new_law` (Bool), `commission_deadlines` (JSON) |
| **Rejection** | `commission_rejected_initiative` (Bool), `commission_rejection_reason` |
| **Actions** | `laws_actions` (JSON), `policies_actions` (JSON) |
| **Follow-up** | `has_roadmap`, `has_workshop`, `has_partnership_programs`, `court_cases_referenced`, `followup_latest_date`, `followup_most_future_date` |
| **References** | `referenced_legislation_by_id` (JSON), `referenced_legislation_by_name` (JSON), `official_communication_document_urls` |
| **Metadata** | `response_url`, `initiative_url`, `registration_number`, `commission_answer_text` |

### Python Dependencies

See the [main project documentation](../../README.ECI_initiatives.md#-quick-start-end-to-end) for detailed installation instructions.

```bash
pip install -r ECI_initiatives/data_pipeline/requirements.prod.txt
```
## 🖥️ Usage

For detailed setup and environment configuration, see the [main project documentation](../../README.ECI_initiatives.md#-quick-start-end-to-end).

**Quick Start:**

```bash
# From project root
cd ECI_initiatives
```
### 1. Setup Environment
Create the virtual environment and install dependencies:
```bash
uv venv
uv pip install -r data_pipeline/requirements.prod.txt
```

### 2. Activate Shell
Load the virtual environment into your current shell session:

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

### 3. Run the Extractor
Once the environment is active (you should see `(.venv)` in your prompt), run the module. It will automatically find the latest data directory:

```bash
python -m data_pipeline.extractor.responses
```

## 🔗 Dependencies

- Depends on the `responses/` HTML files created by `scraper.responses`.
```