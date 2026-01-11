# Fresh Scrape -> Azure Index: Action List

This file turns the verification + causality reports into a concrete remediation checklist.

## Snapshot

- Checked: **212**
- Found in Azure: **203**
- Strict matches: **163**
- Substantive mismatches: **40**
- Missing in Azure: **9**

Source reports:

- Causality: `docs/fresh_vs_index_causality.md`
- Verification: `docs/fresh_vs_index_verification_summary.md`

## A. Update Azure Index (live matches local)

These look like genuine website text drift relative to what is currently indexed.

Count: **14**

| sourcefile | local.updated | azure.updated | azure id | storageUrl |
|---|---:|---:|---|---|
| Part 44 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_44___General_Rules_about_Costs | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-44-general-rules-about-costs |
| Part 46 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_46___Costs_special_cases | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-46-costs-special-cases |
| Part 5 | 2023-07-06T00:00:00Z | 2023-07-06T00:00:00Z | Part_5___Court_Documents | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part05 |
| Part 77 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_77___Provision_in_Support_of_Criminal_Justice | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part77 |
| Part 8 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Part_8___Alternative_Procedure_for_Claims | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part08 |
| Practice Direction 16 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_16 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part16/pd_part16 |
| Practice Direction 27A | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Practice_Direction_27A___Small_Claims_Track | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part27/pd_part27 |
| Practice Direction 41A | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_41A___Provisional_Damages | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part41/pd_part41a |
| Practice Direction 51Z | 2025-10-20T00:00:00Z | 2025-04-07T00:00:00Z | Practice_Direction_51ZG3___Pilot_scheme_for_certain_High_Court_qualified_one-way_costs_shifting__QOC | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/practice-direction-51zh-access-to-public-domain-documents |
| Practice Direction 54D | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_54D___Planning_Court_Claims | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/practice-direction-54e-planning-court-claims |
| Practice Direction 57B | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_57B___Proceedings_under_the_Presumption_of_Death_Act_2013 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part57/practice-direction-57b-proceedings-under-the-presumption-of-death-act-2013 |
| Practice Direction 62 | 2017-11-28T00:00:00Z | 2017-11-28T00:00:00Z | Practice_Direction_62 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part62/pd_part62 |
| Practice Direction 64B | 2017-11-30T00:00:00Z | 2017-11-30T00:00:00Z | Practice_Direction_64B___Applications_to_the_Court_for_Directions_by_Trustees_in_Relation_to_the_Adm | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part64/pd_part64b |
| Practice Direction 74A | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | Practice_Direction_74A___Enforcement_of_Judgments_in_different_Jurisdictions | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part74/pd_part74a |

## B. Investigate Scraper/Extraction (live matches azure)

These are candidates for scraper logic issues or extraction differences.

Count: **1**

| sourcefile | local.updated | azure.updated | azure id | storageUrl |
|---|---:|---:|---|---|
| Part 82 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Part_82___Closed_material_procedure_chunk_001 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-82-closed-material-procedure |

## C. Needs Manual Confirmation (mixed/inconclusive)

The heuristic did not find strong signal lines; review before changing the index or scraper.

Count: **25**

| sourcefile | local.updated | azure.updated | azure id | storageUrl |
|---|---:|---:|---|---|
| Part 2 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_2___Application_and_Interpretation_of_the_Rules | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part02 |
| Part 30 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_30___Transfer | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part30 |
| Part 52 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_52___Appeals_chunk_001 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52 |
| Part 53 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_53___Media_and_Communications_Claims | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part53 |
| Part 62 | 2022-10-01T00:00:00Z | 2022-10-01T00:00:00Z | Part_62___Arbitration_Claims | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part62 |
| Part 65 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_65___Proceedings_Relating_to_Anti-Social_Behaviour_and_Harassment_chunk_001 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part65 |
| Part 74 | 2021-04-14T00:00:00Z | 2021-04-14T00:00:00Z | Part_74___Enforcement_of_Judgments_in_Different_Jurisdictions | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part74 |
| Part 79 | 2021-09-06T00:00:00Z | 2021-09-06T00:00:00Z | Part_79___Proceedings_under_the_counter-terrorism_act_2008__part_1_of_the_terrorist_asset-freezing_e | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part79 |
| Part 80 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Part_80___Proceedings_under_the_Terrorism_Prevention_and_Investigation_Measures_Act_2011 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part80 |
| Practice Direction 30 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_30 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part30/pd_part30 |
| Practice Direction 31A | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_31A___Disclosure_and_Inspection | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/pd_part31a |
| Practice Direction 31B | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_31B___Disclosure_of_Electronic_Documents | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/pd_part31b |
| Practice Direction 31C | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | Practice_Direction_31C___Disclosure_and_inspection_in_relation_to_competition_claims | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/practice-direction-31c-disclosure-and-inspection-in-relation-to-competition-claims |
| Practice Direction 34A | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_34A___Depositions_and_Court_Attendance_by_Witnesses | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part34/pd_part34a |
| Practice Direction 40B | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_40B___Judgments___Orders | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part40/pd_part40b |
| Practice Direction 46 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_46___Costs_Special_Cases | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-46-costs-special-cases/practice-direction-46-costs-special-cases |
| Practice Direction 51R | 2025-10-06T00:00:00Z | 2024-04-15T00:00:00Z | Practice_Direction_51R___Online_Civil_Money_Claims_Pilot_chunk_001 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/practice-direction-51r-online-court-pilot |
| Practice Direction 52C | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_52C___Appeals_to_the_Court_of_Appeal | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52c-appeals-to-the-court-of-appeal |
| Practice Direction 52D | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_52D___Statutory_appeals_and_appeals_subject_to_special_provision_chunk_001 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52d-statutory-appeals-and-appeals-subject-to-special-provision |
| Practice Direction 52E | 2017-03-23T00:00:00Z | 2017-03-23T00:00:00Z | Practice_Direction_52E___Appeals_by_way_of_case_stated | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52e-appeals-by-way-of-case-stated |
| Practice Direction 57 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Practice_Direction_57 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part57/pd_part57 |
| Practice Direction 63 | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_63 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part63/pd_part63 |
| Practice Direction 6B | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | Practice_Direction_6B___Service_out_of_the_Jurisdiction | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part06/pd_part06b |
| Practice Direction 77 | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | Practice_Direction_77 | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part77/pd_part77 |
| Practice Direction 7B | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_7B-_Production_Centre | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part07/pd_part07c |

## D. Missing in Azure Index

These sourcefiles were not found in the Azure index during verification.

Count: **9**

| sourcefile | local.updated | storageUrl |
|---|---:|---|
| Application for a Warrant under The Competition Act 1998 or Part 1 of the Digital Markets, Competition and Consumers Act 2024 | 2023-06-08T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/appforwarrant |
| Cyfarwyddyd Ymarfer 54A | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54a-adolygiad-barnwrol |
| Cyfarwyddyd Ymarfer 54B | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54b-ceisiadau-brys-a-cheisiadau-eraill-am-ryddhad-interim |
| Cyfarwyddyd Ymarfer 54C | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54c-llys-gweinyddol-lleoliad |
| Cyfarwyddyd Ymarfer 54D | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54d-hawliadau-llys-cynllunio |
| Devolution Issues and Crown Office Applications in Wales (Welsh) | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/devolution_issues_welsh |
| Part 48 | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements |
| Practice Direction 48 | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements2 |
| PRACTICE DIRECTION 5C | 2025-08-07T00:00:00Z | https://www.justice.gov.uk/practice-direction-5c-ce-file-electronic-filing-and-case-management-system |

