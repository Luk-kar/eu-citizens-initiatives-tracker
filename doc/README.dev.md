# 🧩 Maintenance and possible further development

## Maintenance

### Data Source & Methodology

**The Case:**

Although the EU releases official ["Key Figures"](https://citizens-initiative-forum.europa.eu/sites/default/files/2022-05/ECI_Infographic_2022.pdf) and annual statistics on European Citizens' Initiatives (ECIs), these reports largely track administrative metrics—such as total signatures collected, organizer demographics, and geographic distribution. However, they lack the granular, structured data essential for strategic analysis, such as: [eci-lifecycle-statistics_en](https://citizens-initiative.europa.eu/find-initiative/eci-lifecycle-statistics)

- Precise collection timelines
- Historical success rates by policy area
- Specific legislative outcomes of successful initiatives

Currently, the European Commission does not offer a centralized, downloadable dataset that links initiatives directly to their long-term legal results. Critical follow-up data (Commission communications, Parliament hearings, and subsequent legal acts) remains fragmented across separate web pages.

**The Solution:**

Consequently, citizens cannot simply download a "lifecycle" dataset. To analyze the actual impact of initiatives, one must rely on scraping and unifying data from individual official initiative pages—exactly what this project does.

***

### Data Collection Strategy

**Scraping Frequency:**

As ECI updates are incremental and infrequent, a **monthly refresh cycle** is sufficient to keep the dataset up-to-date. This schedule also minimizes the load on EU servers and reduces the risk of rate-limiting or IP blocking.

**Legal Reference Enrichment:**

Beyond web scraping, the project integrates with the public [**EUR-Lex SPARQL endpoint**](https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html) (via the Cellar Knowledge Graph) to resolve cryptic legal references (CELEX IDs, Directives, Regulations) into official, human-readable English titles for clearer analysis.

***

### Data Extraction & Processing

**HTML Parsing:**

To enable local execution without requiring cloud infrastructure or heavy computational resources, the pipeline uses **regex-based extraction** to parse structured data from HTML sources.

**Classification Strategy:**

Policy area classifications and certain categorical fields are determined via regex patterns. To reduce redundant computation, stable classifications—such as policy categories in `eci_categories.csv`—are **precomputed and stored**, since initiative objectives do not change after registration. Given the low volume of new ECIs per month (typically 5-10), manually updating this reference file remains practical.

However, as the dataset grows, this manual approach will become harder to maintain.

***

### Recommended NLP Migration Path

For improved scalability and accuracy, the following columns would benefit from **custom NLP models** trained in consultation with legal domain experts:

#### **In `eci_initiatives_*.csv`:**

- **`primary_policy_area`**: Currently relies on a precomputed manual list (for accuracy) with a keyword-based regex fallback for new or unclassified initiatives. An NLP classifier would eliminate the need for manual list maintenance.

#### **In `eci_merger_responses_and_followup_*.csv`:**

*Note: Due to the lengthy legislative process and delays in Commission responses, the dataset of "successful" initiatives with detailed follow-up is currently small (11 at the time of writing). While this makes manual regex maintenance manageable for now, the following fields are prime candidates for NLP automation as the dataset grows:*

*   **`policies_actions`**: Highly susceptible to false positives/negatives. Non-legislative actions (e.g., *roadmaps*, *public consultations*, *working groups*) lack standardized terminology, making regex patterns quite challenging to maintain and prone to missing subtle commitments.

*   **`laws_actions`**: Moderately susceptible to errors. While legal acts often follow standard patterns (e.g., *adopted*, *proposed*, *entered into force*), extracting structured metadata like exact dates and document types across different phrasing variations remains brittle.
  
- **`referenced_legislation_by_name`**: Legal titles are often abbreviated (e.g., *"GDPR"* vs. *"General Data Protection Regulation"*). Pattern matching struggles with these informal references.

- **`commission_promised_new_law`**: Currently handled via regex. Given the strict, formulatic nature of legal commitments (e.g., *"the Commission commits to adopt..."*), regex may remain sufficient here, though semantic analysis would provide higher confidence.

**Model Maintenance:**

These models would still require periodic fine-tuning as EU legal terminology and Commission response patterns evolve.

***

### Data Enrichment

**Legislation Title Fetcher:**

While a proof-of-concept `LegislationTitleFetcher` has been developed to automate the retrieval of official titles via the EUR-Lex SPARQL endpoint (resolving CELEX IDs for Directives, Regulations, and Court Judgments), this step is currently executed **manually** to avoid hitting public API rate limits during bulk processing.

***

## Refactoring Priorities

### Shared Utility Abstraction

The scraper and extractor modules currently duplicate setup code for:
- Logging configuration
- User-agent management
- Basic string parsing utilities
- Error handling patterns

A dedicated `common/` module would improve consistency, simplify testing, and reduce maintenance overhead.

***

## Possible Further Development

### User Interface

**Interactive Web Dashboard:**

A public-facing dashboard (e.g., using **Dash** or else fitting) to allow non-technical users to explore the "lifecycle" dataset without needing to:
- Run Jupyter notebooks locally
- Rely on external services like [Kaggle](https://www.kaggle.com/)

### Infrastructure & Backend

#### **Database Integration**
Migration from CSV-based storage to a relational database (e.g., **PostgreSQL**) to support:
- Complex queries (e.g., JOIN operations between initiatives and responses)
- Live dashboard updates
- Better concurrency for multi-user access

#### **API Service**
A lightweight backend (e.g., **FastAPI** or **Flask**) to:
- Expose the dataset via a REST API
- Separate data processing pipeline from frontend visualization

#### **Configuration Management**
**Ansible** playbooks to automate:
- Setup of Selenium WebDriver dependencies
- Docker container orchestration
- Linux environment configuration

#### **(Optional) Cloud Provisioning**
**Terraform** scripts to manage cloud resources (e.g., AWS EC2, GCP Compute Engine) if the project scales beyond local execution.

***

## Column Metadata

For detailed schema documentation of the extracted datasets, see:
- [`eci_initiatives_columns_info.csv`](../ECI_initiatives/exploratory_data_analysis/initiatives_campaigns/eci_initiatives_columns_info.csv)
- [`eci_merger_columns_info.csv`](../ECI_initiatives/exploratory_data_analysis/initiatives_responses/eci_merger_columns_info.csv)

***

## Contributing

If you're interested in implementing any of the features listed in this document—particularly NLP models, the Dash dashboard, or database migration—contributions are highly encouraged. This project is open for new maintainers or significant expansions.