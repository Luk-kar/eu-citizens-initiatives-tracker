# ECI Data Merge Strategy

## Introduction

This document defines the comprehensive merge strategy for combining two European Citizens' Initiative (ECI) datasets:
- **Response Data (Base)**: Main ECI response data scraped from official Commission response pages (`eci_responses_*.csv`)
- **Followup Data (Followup)**: Updated implementation data from dedicated follow-up websites (`eci_responses_followup_website_*.csv`)

The merge reconciles 36 fields across both datasets, preserving historical accountability (original Commission commitments) while incorporating current implementation status (actual delivery and outcomes).

## Intent

Response Data captures the Commission's initial response with specific deadlines, policy commitments, and procedural milestones—representing what was promised. Followup Data reflects the evolving reality of implementation captured from follow-up websites over time—showing what was actually delivered.

This merge strategy balances immutability (historical facts like registration numbers and hearing dates never change) with updates (implementation dates and legislative outcomes evolve). The goal is to create a comprehensive accountability dataset that tracks Commission commitments versus actual delivery across the multi-year ECI lifecycle.

---

## Complete Column-by-Column Merge Strategy

### **Identity Columns (Keys)**

#### **1. registration_number**
- **Merge Strategy**: Primary key - keep from Response Data
- **Conflict Resolution**: N/A (identical in both)
- **Null Handling**: Never null in either dataset
- **Context & Decision**: Registration number is the immutable legal identifier assigned by the Commission when an ECI is registered; it never changes throughout the initiative's lifecycle. Perfect match across datasets confirms data integrity.

#### **2. initiative_title**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A (identical in both)
- **Null Handling**: Never null
- **Context & Decision**: Official initiative titles are standardized at registration and remain constant, serving as the human-readable identifier alongside the registration number. No variation detected between sources.

---

### **Unique to Response Data (14 columns) - Keep All**

#### **3. response_url**
- **Merge Strategy**: Keep from Response Data (no equivalent in Followup Data)
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: URL to the official Commission response page on the ECI portal; this is structural metadata about where the response is published, not available in follow-up website scrapes.

#### **4. initiative_url**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Canonical URL to the ECI registration page on the official EU portal; structural metadata not duplicated in follow-up datasets.

#### **5. submission_text**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Historical narrative of the submission process (organizers' meetings, hearing dates, press releases); this process documentation is only captured in the main ECI response pages, not on follow-up websites.

#### **6. commission_submission_date**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Official date when organizers submitted the ECI to the Commission after collecting signatures; this is fixed historical data not subject to updates.

#### **7. submission_news_url**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Press release URL announcing the ECI submission; historical reference link not duplicated in follow-up sources.

#### **8. commission_meeting_date**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Date of the official meeting between ECI organizers and Commission officials; fixed procedural milestone in the ECI regulation framework.

#### **9. commission_officials_met**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Names and titles of Commission officials who met with organizers; historical procedural information documenting institutional engagement.

#### **10. parliament_hearing_date**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Date of the mandatory European Parliament public hearing on the ECI; fixed procedural requirement under ECI Regulation.

#### **11. parliament_hearing_video_urls**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Links to archived video recordings of Parliament hearings; this multimedia documentation is specific to the main ECI portal.

#### **12. plenary_debate_date**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Date when Parliament plenary debated the ECI (optional procedural step); historical milestone not subject to revision.

#### **13. plenary_debate_video_urls**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Links to plenary debate recordings; archival multimedia content linked from main ECI pages only.

#### **14. official_communication_adoption_date**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Official date the Commission adopted its formal Communication responding to the ECI; this is the definitive legal timestamp for the Commission's position and never changes.

#### **15. commission_factsheet_url**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: URL to Commission-prepared factsheet summarizing the ECI and response; structural metadata unique to main portal.

#### **16. has_followup_section**
- **Merge Strategy**: Keep from Response Data
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve existing values
- **Context & Decision**: Boolean indicating whether the main ECI response page has a structured follow-up section; this is metadata about the source page structure, not about policy outcomes.

---

### **Overlapping Columns (20 columns) - Requires Decision**

#### **17. followup_dedicated_website**
- **Merge Strategy**: Keep Response Data (identical in both)
- **Conflict Resolution**: N/A (same values)
- **Null Handling**: Preserve existing
- **Context & Decision**: URL to the Commission's dedicated follow-up website for the initiative; both sources reference the same canonical URL, confirming data consistency.

#### **18. commission_answer_text**
- **Merge Strategy**: Merge Response Data with Followup Data (when available)
- **Conflict Resolution**: When conflict, add title for Response Data: **Original Commission Commitments:** and title for Followup Data: **Current Commission Commitments:**
- **Null Handling**: If Followup Data is null, keep Response Data
- **Context & Decision**: Response Data captures the original Commission response with specific deadlines and policy framing (e.g., "by end of 2023"), while Followup Data reflects evolved implementation details from follow-up websites (e.g., actual EFSA opinion publication dates). Both provide accountability value—original promises versus actual delivery—so preserve both with clear labeling to track commitment versus implementation.

#### **19. official_communication_document_urls**
- **Merge Strategy**: Merge (union) - combine unique URLs from both sources
- **Conflict Resolution**: Parse JSON/dict structure, combine all unique URLs with descriptive keys; when URLs recur in different keys, preserve the key from Response Data
- **Null Handling**: If either is null, use the other
- **Context & Decision**: Response Data provides official Commission documents (Communications, main press releases, Q&A PDFs) while Followup Data adds contextual links from follow-up websites (earlier press releases from submission phase, navigation paths). Combining creates comprehensive documentation trail spanning submission → response → follow-up phases.

#### **20. final_outcome_status**
- **Merge Strategy**: Prioritize Followup Data (when available, with validation)
- **Conflict Resolution**: Followup Data appears more current (e.g., "Being Studied" → "Law Approved" for 2022/000002)
- **Null Handling**: If Followup Data is null, keep Response Data
- **Validation**: Flag for manual review when values differ significantly, especially when there are cases that should not make sense because of the order of tabling law like (e.g., "Being Studied" → "Law Approved")
- **Context & Decision**: Outcome status evolves as Commission implements (or doesn't implement) commitments over years; follow-up websites are updated more frequently than main ECI portal. Followup Data reflects current reality, but validation prevents illogical transitions.

#### **21. law_implementation_date**
- **Merge Strategy**: Keep Response Data if Followup Data is null; update with Followup Data when exists
- **Conflict Resolution**: Update with Followup Data when exists
- **Null Handling**: Preserve nulls
- **Context & Decision**: Implementation dates become known only after legislation is adopted and enters into force; follow-up websites capture these actual dates as they occur. Prioritize Followup Data as it reflects observed reality rather than projections.

#### **22. commission_promised_new_law**
- **Merge Strategy**: When Response Data is False and Followup Data is True set True; if both False then False; if Response Data is True and Followup Data is False keep True
- **Conflict Resolution**: N/A
- **Null Handling**: N/A (boolean)
- **Context & Decision**: A Commission promise to legislate is a one-way commitment—once made, it doesn't become "unmade" even if later abandoned (which would be tracked in outcome status instead). This field captures whether the promise was ever made, so True in either source means True in merged result.

#### **23. commission_deadlines**
- **Merge Strategy**: Merge (append newer dates) - combine both
- **Conflict Resolution**: Parse JSON, merge all unique date-action pairs; when conflict, add title for Response Data: **Original Commission Deadlines:** and title for Followup Data: **Current Commission Deadlines:**
- **Null Handling**: If either is null, use the other; if both have data, merge
- **Context & Decision**: Original deadlines represent Commission accountability commitments at response time, while follow-up websites add intermediate milestones (e.g., consultation closures) and updated timeline language. Example: 2022/000002 original "March 2026 decision" becomes more specific in Followup Data with August 2025 consultation deadline added plus refined March 2026 language.

#### **24. commission_rejected_initiative**
- **Merge Strategy**: When Response Data is True keep it; when Response Data is False and Followup Data is True keep Followup Data
- **Conflict Resolution**: Response Data overwrites Followup Data
- **Null Handling**: N/A (boolean)
- **Context & Decision**: Commission rejections are permanent political decisions that cannot be reversed (as demonstrated by cases like Minority SafePack and One of Us remaining rejected 7-13 years later). This field follows one-way logic where rejection status can only be added, never removed, with Response Data priority as the authoritative source.

#### **25. commission_rejection_reason**
- **Merge Strategy**: Combine both Response Data and Followup Data
- **Conflict Resolution**: When conflict, add title for Response Data: **Original Commission Rejection Reason:** and title for Followup Data: **Current Commission Rejection Reason:**
- **Null Handling**: Preserve nulls
- **Context & Decision**: Rejection reasoning may be elaborated or refined in follow-up documentation as legal and political context evolves (though the rejection decision itself stands). Preserving both captures the original justification and any subsequent clarifications.

#### **26. laws_actions**
- **Merge Strategy**: Merge (append) - combine unique legislative actions
- **Conflict Resolution**: Parse JSON arrays, deduplicate by (type + date + description similarity)
- **Null Handling**: If Response Data is null, use Followup Data; otherwise merge arrays
- **Context & Decision**: Response Data often has null or only initial legislative promises, while Followup Data adds concrete later actions like specific regulation adoptions with CELEX numbers (e.g., 2022/000002 Followup Data adds July 2025 Invasive Alien Species Regulation). Combining creates complete legislative outcome timeline from promise to implementation.

#### **27. policies_actions**
- **Merge Strategy**: Merge (append with deduplication)
- **Conflict Resolution**: Parse JSON arrays, deduplicate by (type + date + description)
- **Null Handling**: If either is null, use the other
- **Context & Decision**: Both datasets contain policy actions but Followup Data typically has more granular detail (specific consultation dates, named research projects) versus Response Data's broader categories. Merging creates the most comprehensive non-legislative action timeline.

#### **28. has_roadmap**
- **Merge Strategy**: If any True then True, else False
- **Conflict Resolution**: N/A
- **Null Handling**: N/A (boolean)
- **Context & Decision**: Boolean presence indicator for whether Commission published a policy roadmap in follow-up; once a roadmap exists, it exists regardless of which source detected it, so logical OR is appropriate.

#### **29. has_workshop**
- **Merge Strategy**: If any True then True, else False
- **Conflict Resolution**: N/A
- **Null Handling**: N/A (boolean)
- **Context & Decision**: Boolean presence indicator for stakeholder workshops held as follow-up; logical OR captures whether workshops occurred regardless of which scraping source documented them.

#### **30. has_partnership_programs**
- **Merge Strategy**: If any True then True, else False
- **Conflict Resolution**: N/A
- **Null Handling**: N/A (boolean)
- **Context & Decision**: Boolean presence indicator for partnership programs established as follow-up mechanism; logical OR ensures any documented partnership is captured in merged result.

#### **31. court_cases_referenced**
- **Merge Strategy**: Combine both, deduplicate
- **Conflict Resolution**: N/A
- **Null Handling**: Preserve nulls
- **Context & Decision**: References to court cases challenging the Commission's ECI response (like Minority SafePack's General Court and CJEU challenges); combining sources ensures comprehensive legal challenge documentation, though currently null for the two ECIs in Followup Data.

#### **32. followup_latest_date**
- **Merge Strategy**: Use maximum date from both sources
- **Conflict Resolution**: Parse dates, select most recent; write warning when data in second dataset is earlier than in the first one
- **Null Handling**: Use whichever is not null
- **Context & Decision**: Tracks the most recent follow-up activity to show whether Commission engagement is ongoing or stalled; temporal maximum reflects current reality, but backward date movement triggers warning as it suggests data quality issue. Followup Data consistently has later dates (e.g., 2022/000002: 2024-02-09 → 2025-08-01).

#### **33. followup_most_future_date**
- **Merge Strategy**: Use maximum date from both sources
- **Conflict Resolution**: Parse dates, select furthest future date; write warning when data in second dataset is earlier than in the first one
- **Null Handling**: Use whichever is not null
- **Context & Decision**: Tracks the furthest scheduled future activity (consultations, promised decisions) to show horizon of Commission commitments; temporal maximum captures longest-term accountability, with warnings for backward movement. Followup Data has better future projections (e.g., 2022/000002: 2024-02-09 → 2027-08-31).

#### **34. referenced_legislation_by_id**
- **Merge Strategy**: Merge (union) - combine all unique IDs
- **Conflict Resolution**: Parse JSON/dict, combine all unique legislation IDs
- **Null Handling**: If either is null, use the other
- **Context & Decision**: Structured extraction of legislation references (CELEX numbers, Regulation numbers, Article numbers) from follow-up text; follow-up websites often contain richer legislative context than initial responses. Union ensures comprehensive regulatory framework documentation.

#### **35. referenced_legislation_by_name**
- **Merge Strategy**: Merge (union) - combine all unique names
- **Conflict Resolution**: Parse JSON/dict, combine all unique legislation names
- **Null Handling**: If either is null/empty, use the other
- **Context & Decision**: Human-readable legislation names (directives, regulations by common name) complementing the ID-based references; combining provides both technical precision (IDs) and accessibility (common names) for regulatory framework.

#### **36. followup_events_with_dates**
- **Merge Strategy**: Merge, deduplicate if same date and description
- **Conflict Resolution**: Parse JSON arrays, deduplicate by same key and value; when conflict, add title for Response Data: **Original Commission Event:** and title for Followup Data: **Current Commission Event:**
- **Null Handling**: If either is null, use the other
- **Context & Decision**: Response Data captures historical events from initial scraping while Followup Data adds more recent events and updated descriptions from follow-up websites. Both provide valuable temporal data for complete accountability timeline, with conflicts preserved to show evolution of event descriptions over time (e.g., generic vs. specific details).

---

## Summary Statistics

- **Total columns**: 36
- **Identity columns**: 2 (keep Response Data)
- **Unique to Response Data**: 14 (keep all)
- **Overlapping columns**: 20 (merge with various strategies)
  - Keep Response Data only: 1
  - Merge/union: 11
  - Prioritize Followup Data with validation: 2
  - Logical OR (booleans): 3
  - Complex merge with labeling: 3

**Merge philosophy**: Response Data provides authoritative historical record of Commission's initial response; Followup Data adds implementation reality and updated details from follow-up websites. Combining creates comprehensive accountability dataset tracking Commission commitments versus actual delivery over time.
