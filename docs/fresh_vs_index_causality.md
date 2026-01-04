# Fresh vs Azure Index — Cause Analysis (Jan 4, 2026)

This report attempts to distinguish **website changes** vs **scraper/extraction differences**.
Heuristic: fetch current HTML from `storageUrl` and check whether the diff lines appear in live HTML text.

## Summary
- Substantive mismatches analyzed: **40**
- Missing from Azure (confirmed): **9**

## Missing from Azure
These are **index coverage gaps** (not a scraper vs HTML question).
| sourcefile | local.updated | storageUrl |
|---|---|---|
| Application for a Warrant under The Competition Act 1998 or Part 1 of the Digital Markets, Competition and Consumers Act 2024 |  |  |
| Cyfarwyddyd Ymarfer 54A | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54a-adolygiad-barnwrol |
| Cyfarwyddyd Ymarfer 54B | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54b-ceisiadau-brys-a-cheisiadau-eraill-am-ryddhad-interim |
| Cyfarwyddyd Ymarfer 54C | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54c-llys-gweinyddol-lleoliad |
| Cyfarwyddyd Ymarfer 54D | 2021-05-27T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/cyfarwyddyd-ymarfer-54d-hawliadau-llys-cynllunio |
| Devolution Issues and Crown Office Applications in Wales (Welsh) | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/devolution_issues_welsh |
| PRACTICE DIRECTION 5C | 2025-08-07T00:00:00Z | https://www.justice.gov.uk/practice-direction-5c-ce-file-electronic-filing-and-case-management-system |
| Part 48 | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements |
| Practice Direction 48 | 2017-01-30T00:00:00Z | https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements/part-48-part-2of-the-legal-aid,-sentencing-and-punishment-of-offenders-act-2012-relating-to-civil-litigation-funding-and-costs-transitional-provision-in-relation-to-pre-commencement-funding-arrangements2 |

## Mismatch classifications
| sourcefile | local.updated | azure.updated | classification | added_hits | removed_hits | live_url_ok |
|---|---|---|---|---:|---:|---|
| Part 2 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Part 30 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Part 44 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | website_changed (live matches local) | 2/4 | 0/4 | yes |
| Part 46 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | website_changed (live matches local) | 1/1 | 0/0 | yes |
| Part 5 | 2023-07-06T00:00:00Z | 2023-07-06T00:00:00Z | website_changed (live matches local) | 1/2 | 0/1 | yes |
| Part 52 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 2/3 | 2/4 | yes |
| Part 53 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Part 62 | 2022-10-01T00:00:00Z | 2022-10-01T00:00:00Z | mixed_or_inconclusive | 0/0 | 0/1 | yes |
| Part 65 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 0/2 | 0/2 | yes |
| Part 74 | 2021-04-14T00:00:00Z | 2021-04-14T00:00:00Z | mixed_or_inconclusive | 1/4 | 1/4 | yes |
| Part 77 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | website_changed (live matches local) | 2/4 | 0/0 | yes |
| Part 79 | 2021-09-06T00:00:00Z | 2021-09-06T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Part 8 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | website_changed (live matches local) | 3/4 | 0/4 | yes |
| Part 80 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Part 82 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | scraper/extraction issue (live matches azure) | 1/3 | 2/3 | yes |
| Practice Direction 16 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | website_changed (live matches local) | 2/4 | 0/0 | yes |
| Practice Direction 27A | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | website_changed (live matches local) | 1/1 | 0/1 | yes |
| Practice Direction 30 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | mixed_or_inconclusive | 1/4 | 0/1 | yes |
| Practice Direction 31A | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | mixed_or_inconclusive | 0/3 | 0/4 | yes |
| Practice Direction 31B | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Practice Direction 31C | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | mixed_or_inconclusive | 1/4 | 1/4 | yes |
| Practice Direction 34A | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 1/4 | 0/4 | yes |
| Practice Direction 40B | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 1/1 | 1/1 | yes |
| Practice Direction 41A | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | website_changed (live matches local) | 1/1 | 0/1 | yes |
| Practice Direction 46 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Practice Direction 51R | 2025-10-06T00:00:00Z | 2024-04-15T00:00:00Z | mixed_or_inconclusive | 1/4 | 1/4 | yes |
| Practice Direction 51Z | 2025-10-20T00:00:00Z | 2025-04-07T00:00:00Z | website_changed (live matches local) | 3/4 | 0/4 | yes |
| Practice Direction 52C | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | mixed_or_inconclusive | 1/1 | 1/1 | yes |
| Practice Direction 52D | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | mixed_or_inconclusive | 1/4 | 0/4 | yes |
| Practice Direction 52E | 2017-03-23T00:00:00Z | 2017-03-23T00:00:00Z | mixed_or_inconclusive | 0/2 | 0/2 | yes |
| Practice Direction 54D | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | website_changed (live matches local) | 3/4 | 0/3 | yes |
| Practice Direction 57 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Practice Direction 57B | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | website_changed (live matches local) | 1/1 | 0/1 | yes |
| Practice Direction 62 | 2017-11-28T00:00:00Z | 2017-11-28T00:00:00Z | website_changed (live matches local) | 1/1 | 0/4 | yes |
| Practice Direction 63 | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | mixed_or_inconclusive | 0/0 | 0/0 | yes |
| Practice Direction 64B | 2017-11-30T00:00:00Z | 2017-11-30T00:00:00Z | website_changed (live matches local) | 1/1 | 0/1 | yes |
| Practice Direction 6B | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | mixed_or_inconclusive | 0/1 | 0/1 | yes |
| Practice Direction 74A | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | website_changed (live matches local) | 3/4 | 1/3 | yes |
| Practice Direction 77 | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | mixed_or_inconclusive | 1/4 | 0/1 | yes |
| Practice Direction 7B | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | mixed_or_inconclusive | 0/2 | 0/2 | yes |

## Per-document details
(Signal lines are truncated/heuristic; use as indicators, not proof.)

### Part 2

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part02
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (1) This rule shows how to calculate any period of time for doing any act which is specified -(a) by these Rules;(b) by a practice direction; or(c) by a judgment or order of the court.(2) A period of time expressed as a number of days shall be computed as clear days.(3) In this rule 'clear days' means that in computing the number of days -(a) the day on which the period begins; and(b) if the end of the period is defined by reference to an event, the day on which that event occursare not included.Examples(i) Notice of an application must be served at least 3 days before the hearing.An application is listed to be heard on Friday 20 October.The last date for service is Monday 16 October.(ii) The court is to fix a date for a hearing.The hearing must be at least 28 days after the date of notice.If the court gives notice of the date of the hearing on 1 October, the earliest date for the hearing is 30 October.(iii) Particulars of claim must be served within 14 days of service of the claim form.The claim form is served on 2 October.The last day for service of the particulars of claim is 16 October.(4) Where the specified period -(a) is 5 days or less; and(b) includes -(i) a Saturday or Sunday; or(ii) a Bank Holiday, Christmas Day or Good Friday,that day does not count.Example Notice of an application must be served at least 3 days before the hearing.An application is to be heard on Monday 20 October.The last date for service is Tuesday 14 October.(5) When the period specified -(a) by these Rules or a practice direction; or(b) by any judgment or court order,for doing any act at the court office ends on a day on which the office is closed, that act shall be in time under these rules if done on the next day on which the court office is open.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (1) This rule shows how to calculate any period of time for doing any act which is specified -(a) by these Rules;(b) by a practice direction; or(c) by a judgment or order of the court.(2) A period of time expressed as a number of days shall be computed as clear days.(3) In this rule 'clear days' means that in computing the number of days -(a) the day on which the period begins; and(b) if the end of the period is defined by reference to an event, the day on which that event occursare not included.Examples(i) Notice of an application must be served at least 3 days before the hearing.An application is listed to be heard on Friday 20 October.The last date for service is Monday 16 October.(ii) The court is to fix a date for a hearing.The hearing must be at least 28 days after the date of notice.If the court gives notice of the date of the hearing on 1 October, the earliest date for the hearing is 30 October.(iii) Particulars of claim must be served within 14 days of service of the claim form.The claim form is served on 2 October.The last day for service of the particulars of claim is 16 October.(4) Where the specified period -(a) is 5 days or less; and(b) includes -(i) a Saturday or Sunday; or(ii) a Bank Holiday, Christmas Day or Good Friday,that day does not count.Example Notice of an application must be served at least 3 days before the hearing.An application is to be heard on Monday 20 October.The last date for service is Tuesday 14 October.(5) Subject to the provisions of Practice Direction 5 C, when the period specified -(a) by these Rules or a practice direction; or(b) by any judgment or court order,for doing any act at the court office ends on a day on which the office is closed, that act shall be in time under these rules if done on the next day on which the court office is open.


### Part 30

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part30
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (1) This rule applies if, in any proceedings in the King's Bench Division, (other than proceedings in the Commercial or Admiralty Courts) a district registry of the High Court or a county court, a party's statement of case raises an issue relating to the application of of Chapter I or II of Part I of the Competition Act 19982 or to a claim under section 101 of the Digital Markets, Competition and Consumers Act 2024.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (1) This rule applies if, in any proceedings in the King's Bench Division, (other than proceedings in the Commercial or Admiralty Courts) a district registry of the High Court or a county court, a party's statement of case raises an issue relating to the application of of Chapter I or II of Part I of the Competition Act 19982.


### Part 44

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-44-general-rules-about-costs
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- 'summary assessment' means the procedure whereby costs are assessed by the judge who has decided the case or application or where rule 44.6(2) applies;
- (1) Where the court orders a party to pay costs to another party (other than fixed costs) it may -
- (a) make a summary assessment of the costs;
- (b) give directions for the summary assessment of the costs to be made at a later date; or

Azure-only signal lines (should appear in live HTML if scraper issue):
- 'summary assessment' means the procedure whereby costs are assessed by the judge who has heard the case or application;
- (1) Where the court orders a party to pay costs to another party (other than fixed costs) it may either -
- (a) make a summary assessment of the costs; or
- (b) order detailed assessment of the costs by a costs officer,


### Part 46

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-46-costs-special-cases
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- (3) Neither rule 19.4 nor rule 20.7 applies to the joinder of a person under paragraph (1).


### Part 5

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part05
- local.updated: `2023-07-06T00:00:00Z`
- azure.updated: `2023-07-06T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- 5.5(1) A practice direction may make provision for documents to be filed or sent to the court by -(a) the use of an electronic filing and case management system; or(b) other electronic means.(2) Any such practice direction may -(a) provide that only particular categories of documents may be filed or sent to the court by such means;(b) provide that particular provisions only apply in specific courts;(c) specify the requirements that must be fulfilled for any document filed or sent to the court by such means; and
- (d) modify or disapply any provision of these rules in relation to the use of any court electronic filing and case management system.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 5.5(1) A practice direction may make provision for documents to be filed or sent to the court by -(a) facsimile; or(b) other electronic means.(2) Any such practice direction may -(a) provide that only particular categories of documents may be filed or sent to the court by such means;(b) provide that particular provisions only apply in specific courts; and(c) specify the requirements that must be fulfilled for any document filed or sent to the court by such means.


### Part 52

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (1) Where permission to apply for judicial review has been refused at a hearing in the High Court, an application for permission to appeal may be made to the Court of Appeal except where precluded by section 18(1) of the Senior Courts Act 198.
- (3) Subject to paragraph (4) and unless the appeal court orders otherwise, a sealed copy of the appellant's notice must be served on each respondent-
- (b) in any event where it is served by the appellant not later than 14 days,

Azure-only signal lines (should appear in live HTML if scraper issue):
- (1) Where permission to apply for judicial review has been refused at a hearing in the High Court, an application for permission to appeal may be made to the Court of Appeal except where precluded by section 18(1)(a) of the Senior Courts Act 198.
- (3) Subject to paragraph (4) and unless the appeal court orders otherwise, an appellant's notice must be served on each respondent-
- (b) in any event not later than 7 days,
- (1) In this rule, "Aarhus Convention claim" and "prohibitively expensive" have the same meanings as in Section IX of Part 46, and "claimant" means a claimant to whom rules 46.26 to 46.28 apply.


### Part 53

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part53
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (3) A Media and Communications List Judge is a judge authorised by the President of the King's Bench Division, in consultation with the Chancellor of the High Court, to hear claims in the Media and Communications List.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (3) A Media and Communications List Judge is a judge authorised by the President of the KIng's Bench Division, in consultation with the Chancellor of the High Court, to hear claims in the Media and Communications List.


### Part 62

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part62
- local.updated: `2022-10-01T00:00:00Z`
- azure.updated: `2022-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Azure-only signal lines (should appear in live HTML if scraper issue):
- (a) the preliminary question of whether the court is satisfied of the matters set out in section 45(2)(b); or


### Part 65

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part65
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (2) In this Section 'the 2003 Act' means the Anti-social Behaviour Act 2003.
- (3) In this Section 'the 2006 Act' means the Police and Justice Act 2006. Applications under section 91(3) of the 2003 Act or section 27(3) of the 2006 Act for a power of arrest to be attached to any provision of an injunction

Azure-only signal lines (should appear in live HTML if scraper issue):
- (2) In this Section 'the 2003 Act'means the Anti-social Behaviour Act 2003.
- (3) In this Section 'the 2006 Act'means the Police and Justice Act 2006. Applications under section 91(3) of the 2003 Act or section 27(3) of the 2006 Act for a power of arrest to be attached to any provision of an injunction


### Part 74

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part74
- local.updated: `2021-04-14T00:00:00Z`
- azure.updated: `2021-04-14T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (d) to (f) Omitted(g) 'the 2005 Hague Convention' means the Convention on Choice of Court Agreements concluded on 30 th June 2005 at The Hague;
- (h) "the 2019 Hague Convention" means the Convention on the Recognition and Enforcement of Foreign Judgments in Civil or Commercial Matters concluded on 2 nd July 2019 at The Hague.
- for the registration of foreign judgments for enforcement in England and Wales; and
- (d) section 4 C of the 1982 Act.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (d) to (f) Omitted(g) 'the 2005 Hague Convention' means the Convention on Choice of Court Agreements concluded on 30 th June 2005 at the Hague.
- for the registration of foreign judgments for enforcement in England and Wales.
- (5 A) Written evidence in support of an application under section 4 B of the 1982 Act (registration and enforcement of judgments under the 2005 Hague Convention) must also include any other evidence required by Article 13 of the 2005 Hague Convention.
- (a) the application for registration;


### Part 77

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part77
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- SECTION 3 Referral of Release Decisions
- 77.16.This Section applies where the Secretary of State directs the Parole Board to refer a release decision to the High Court under section 32 ZAA of the Crime (Sentences) Act 1997 ("the 1997 Act") or section 256 AZBA of the Criminal Justice Act 2003 ("the 2003 Act").
- 77.17.The Part 8 procedure applies to proceedings under this Section with the following modifications.
- Proceedings under this Section


### Part 79

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part79
- local.updated: `2021-09-06T00:00:00Z`
- azure.updated: `2021-09-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (i) 'specially represented party' means a party, other than the appropriate Minister, whose interests a special advocate represents.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (i) 'specially represented party'means a party, other than tthe appropriate Minister, whose interests a special advocate represents.


### Part 8

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part08
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- 8.2(1) Where the claimant uses the Part 8 procedure the claim form must state -
- (2) Except where another rule or practice direction applies, rule 7.5 and rule 7.6 shall apply with regard to the service of the claim form.
- (3) A defendant who wishes to rely on written evidence must file it when they file their acknowledgment of service unless the defendant has indicated on their acknowledgement of service an intention to contest jurisdiction, in which case the evidence must be filed within fourteen days of filing the acknowledgment of service if no such application is made.
- (4) If a defendant files their evidence, they must also, at the same time, serve a copy of their evidence on the other parties.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 8.2 Where the claimant uses the Part 8 procedure the claim form must state -
- (Rule 7.5 provides for service of the claim form)
- (3) A defendant who wishes to rely on written evidence must file it when they file their acknowledgment of service.
- (4) If they do so, they must also, at the same time, serve a copy of their evidence on the other parties.


### Part 80

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part80
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (c) rule 52.13 (respondent's notice); and

Azure-only signal lines (should appear in live HTML if scraper issue):
- (c) rule 52.13 (responden's notice); and


### Part 82

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-82-closed-material-procedure
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- classification: **scraper/extraction issue (live matches azure)**

Local-only signal lines (should appear in live HTML if website changed):
- (2) After the relevant person serves sensitive material on the special advocate, the special advocate must not communicate with any person about any matter connected with the proceedings, except in accordance with paragraph (3), (3 A) or (6)(b) or with a direction of the court pursuant to a request under paragraph (4).
- (3 A) The special advocate may communicate with the specially represented party or the specially represented party's legal representative with the express agreement of the relevant person and (where the relevant person is not the Secretary of State) the Secretary of State.
- (b) the special advocate must not reply to the communication other than in accordance with paragraph (3 A) or directions of the court, except that the special advocate may without such directions send a written acknowledgment of receipt to the specially represented party's legal representative. Evidence in proceedings to which this Part applies

Azure-only signal lines (should appear in live HTML if scraper issue):
- (2) After the relevant person serves sensitive material on the special advocate, the special advocate must not communicate with any person about any matter connected with the proceedings, except in accordance with paragraph (3) or (6)(b) or with a direction of the court pursuant to a request under paragraph (4).
- (b) the special advocate must not reply to the communication other than in accordance with directions of the court, except that the special advocate may without such directions send a written acknowledgment of receipt to the specially represented party's legal representative. Evidence in proceedings to which this Part applies
- (c) the details of any special advocate already appointed under rule 82.9 (appointment of a special advocate).


### Practice Direction 16

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part16/pd_part16
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- Digital Markets, Competition and Consumers Act 2024 ("the 2024 Act")
- A party who relies on a CMA breach decision (which has the same meaning as in section 102(5) of the Digital Markets, Competition and Consumers Act 2024), must state that in their statement of case, and must-
- • identify the CMA breach decision; and
- indicate whether the CMA breach decision is final (in accordance with section 102(2) of the 2024 Act)


### Practice Direction 27A

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part27/pd_part27
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- (2) He will normally do so orally at the hearing, but he may give them later at a hearing either orally or in writing.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (2) He will normally do so orally at the hearing, but he may give them later at a hearing either orally or in writting.


### Practice Direction 30

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part30/pd_part30
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 8.9 A party to a claim which has been transferred under paragraph 8.7 may apply to transfer it to the Commercial Court if it otherwise falls within the scope of rule 58.2(2), in accordance with the procedure set out in rules 58.4(2) and 30.5(3).
- Part 1 of the Digital Markets, Competition and Consumers Act 2024
- • "the CAT" has the same meaning as in paragraph 8.1(3);
- • "the 2024 Act" means the Digital Markets, Competition and Consumers Act 2024; and

Azure-only signal lines (should appear in live HTML if scraper issue):
- 8.9 A party to a claim which has been transferred under paragraph 8.7 may apply to transfer it to the Commercial Court if it otherwise falls within the scope of rule 58.2(1), in accordance with the procedure set out in rules 58.4(2) and 30.5(3).


### Practice Direction 31A

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/pd_part31a
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 1.1 In order to give standard disclosure the disclosing party must make a reasonable search for documents falling within the paragraphs of rule 31.6.
- 1.2 Having made the search the disclosing party must (unless rule 31.10(8) applies) make a list of the documents of whose existence the party is aware that fall within those paragraphs and which are or have been in the party's control (see rule 31.8).
- 1.3 The obligations imposed by an order for standard disclosure may be dispensed with or limited either by the court or by written agreement between the parties. Any such written agreement should be lodged with the court.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 1.1 The normal order for disclosure will be an order that the parties give standard disclosure.
- 1.2 In order to give standard disclosure the disclosing party must make a reasonable search for documents falling within the paragraphs of rule 31.6.
- 1.3 Having made the search the disclosing party must (unless rule 31.10(8) applies) make a list of the documents of whose existence the party is aware that fall within those paragraphs and which are or have been in the party's control (see rule 31.8).
- 1.4 The obligations imposed by an order for standard disclosure may be dispensed with or limited either by the court or by written agreement between the parties. Any such written agreement should be lodged with the court.


### Practice Direction 31B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/pd_part31b
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • State the geographical location (if known). Consider (at least) servers, desktop PCs, laptops, notebooks, handheld devices, PDA devices, off-site storage, removable storage media (for example, CD-ROMs, DVDs, USB drives, memory sticks) and databases. • Consider all types of e-mail system (for example, Outlook, Lotus Notes, web-based accounts), whether stored on personal computers, portable devices or in web-based accounts (for example, Yahoo, Hotmail, Gmail). • For example, instant messaging, voicemail, VOIP (Voice Over Internet Protocol), recorded telephone lines, text messaging, audio files, video files. • State the geographical location (if known). Consider (at least) servers, desktops and laptops. • For example, .pdf. .tif, .jpg. • For example, Power Point or equivalent, specialist documents (such as CAD Drawings). • Where Keyword Searches are used in order to identify irrelevant documents which are to be excluded from disclosure (for example a confidential name of a client or customer), a general description of the type of search may be given. • See Practice Direction 31 B, which refers to the following matters which may be relevant: (a) the number of documents involved; (b) the nature and complexity of the proceedings; (c) the ease and expense of retrieval of any particular document; (d) the availability of documents or contents of documents from other sources; and (e) the significance of any document which is likely to be located during the search. • For example, back-ups, archives, off-site or outsourced document storage, documents created by former employees, documents stored in other jurisdictions, documents in foreign languages. • There is no requirement that you should obtain OCR versions of documents, and this question is directed only to OCR versions which you have available or expect to have available to you. If you do provide OCR versions to another party, they will be provided by you on an 'as is' basis, with no assurance to the other party that the OCR versions are complete or accurate. You may wish to exclude provision of OCR versions of documents which have been redacted. • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • 'Metadata' is information about the document or file which is recorded in the computer, such as the date and time of creation or modification of a word-processing file, or the author and the date and time of sending of an e-mail. The question is directed to the more extensive Metadata which may be relevant where for example authenticity is disputed.

Azure-only signal lines (should appear in live HTML if scraper issue):
- • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • State the geographical location (if known). Consider (at least) servers, desktop PCs, laptops, notebooks, handheld devices, PDA devices, off-site storage, removable storage media (for example, CD-ROMs, DVDs, USB drives, memory sticks) and databases. • Consider all types of e-mail system (for example, Outlook, Lotus Notes, web-based accounts), whether stored on personal computers, portable devices or in web-based accounts (for example, Yahoo, Hotmail, Gmail). • For example, instant messaging, voicemail, VOIP (Voice Over Internet Protocol), recorded telephone lines, text messaging, audio files, video files. • State the geographical location (if known). Consider (at least) servers, desktops and laptops. • For example, .pdf. .tif, .jpg. • For example, Powerpoint or equivalent, specialist documents (such as CAD Drawings). • Where Keyword Searches are used in order to identify irrelevant documents which are to be excluded from disclosure (for example a confidential name of a client or customer), a general description of the type of search may be given. • See Practice Direction 31 B, which refers to the following matters which may be relevant: (a) the number of documents involved; (b) the nature and complexity of the proceedings; (c) the ease and expense of retrieval of any particular document; (d) the availability of documents or contents of documents from other sources; and (e) the significance of any document which is likely to be located during the search. • For example, back-ups, archives, off-site or outsourced document storage, documents created by former employees, documents stored in other jurisdictions, documents in foreign languages. • There is no requirement that you should obtain OCR versions of documents, and this question is directed only to OCR versions which you have available or expect to have available to you. If you do provide OCR versions to another party, they will be provided by you on an 'as is' basis, with no assurance to the other party that the OCR versions are complete or accurate. You may wish to exclude provision of OCR versions of documents which have been redacted. • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • 'Metadata' is information about the document or file which is recorded in the computer, such as the date and time of creation or modification of a word-processing file, or the author and the date and time of sending of an e-mail. The question is directed to the more extensive Metadata which may be relevant where for example authenticity is disputed.


### Practice Direction 31C

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part31/practice-direction-31c-disclosure-and-inspection-in-relation-to-competition-claims
- local.updated: `2023-06-08T00:00:00Z`
- azure.updated: `2023-06-08T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- Disclosure and inspection of evidence in relation to a competition claim or digital markets proceedings
- (aa) "the 2024 Act" means the Digital Markets, Competition and Consumers Act 2024;
- (ba) "digital markets proceedings" has the same meaning as in section 116(4) of the 2024 Act;
- (d) "reasoned justification" means a statement containing reasonably available facts and evidence sufficient to support the plausibility of the claim to which the relevant evidence relates;

Azure-only signal lines (should appear in live HTML if scraper issue):
- Disclosure and inspection of evidence in relation to a competition claim
- (d) "reasoned justification" means a statement containing reasonably available facts and evidence sufficient to support the plausibility of the claim for damages to which the relevant evidence relates;
- (e) "relevant evidence" means evidence that a person is seeking to have disclosed or is seeking to inspect that relates to a competition claim.
- Disclosure and inspection of evidence in relation to a competition claim - evidence in the file of the competition authority


### Practice Direction 34A

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part34/pd_part34a
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 4.2 The party who obtains an order for the examination of a deponent before an examiner of the court must:
- (1) apply to the Foreign Process Section at the Royal Courts of Justice for the allocation of an examiner; alternatively engage a person who satisfies the criteria in CPR 34.8 (3) (a) or (c);
- 5.4 The above documents should be filed with the Foreign Process Section of the Royal Courts of Justice..
- 6.3 An application under rule 34.17 must be filed with the Foreign Process Section at the Royal Courts of Justice and include or exhibit-

Azure-only signal lines (should appear in live HTML if scraper issue):
- 4.2 The party who obtains an order for the examination of a deponentbefore an examiner of the courtmust:
- (1) apply to the Foreign Process Section at the Royal Courts of Justice atforeignprocess.rcj@justice.gov.ukfor the allocation of an examiner; alternatively engage a person who satisfies the criteria in CPR 34.8 (3) (a) or (c);
- 5.4 The above documents should be filed with the Foreign Process Section of the Royal Courts of Justice, by post to "Foreign Process Section Royal Courts of Justice, Strand London WC 2 A 2 LL" or left in person at the document drop box in the Main Hall of the Royal Courts of Justice marked for the attention of the Foreign Process Section.
- 6.3 An application under rule 34.17 must include or exhibit-


### Practice Direction 40B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part40/pd_part40b
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (1) Unless the [claimant][defendant] serves his list of documents by 4.00 p.m. on Friday, January 22, 1999 his [claim][defence] will be struck out and judgment entered for the [defendant][claimant], or

Azure-only signal lines (should appear in live HTML if scraper issue):
- (1) Unless the [claimant][defendant] serves his list of documents by 4.00 p.m. on Friday, January 22, 1999 his [claim][defence] will be struck out and judgment entered for the [defendent][claimant], or


### Practice Direction 41A

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part41/pd_part41a
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- (1) ensure that the case file documents are provided by the parties where necessary and filed on the court file,

Azure-only signal lines (should appear in live HTML if scraper issue):
- (1) ensure that the case file documents are provided by the parties where necesary and filed on the court file,


### Practice Direction 46

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part-46-costs-special-cases/practice-direction-46-costs-special-cases
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 3.4 The amount, which may be allowed to a self represented litigant under rule 46.5(4)(b), is £24 per hour.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 3.4 The amount, which may be allowed to a self represented litigant under rule 46.5(4)(b), is £19 per hour.


### Practice Direction 51R

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/practice-direction-51r-online-court-pilot
- local.updated: `2025-10-06T00:00:00Z`
- azure.updated: `2024-04-15T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 2.1(1)The purpose of this practice direction is to establish a pilot to test an online claims process, called "Online Civil Money Claims". Sub-paragraph (3) sets out the conditions that need to be met for a claim to be within the scope of the pilot. Where a claim is within the scope of the pilot-
- (a) Claimants who are not represented by a legal representative may use the pilot to make their claim; and
- (b) If the claimant is legally represented, the pilot must be used to make the claim if sub-paragraph 2.1(5 A) applies. The pilot is to run from 7 th August 2017 to 1 st October 2026. The pilot applies in the County Court.
- (i). the claimant will not be getting help with bringing the claim from a "legal representative" (as defined) and the claimant believes that the defendant will not be getting help with defending the claim from a "legal representative"; or

Azure-only signal lines (should appear in live HTML if scraper issue):
- "early adopter court" means a County Court hearing centre that has been selected to trial more advanced features within Online Civil Money Claims and is listed on the HCMTS Reform Civil Fact Sheet which can be found atwww.gov.uk/government/publications/hmcts-reform-civil-fact-sheets;
- 2.1(1)The purpose of this practice direction is to establish a pilot to test an online claims process, called "Online Civil Money Claims". Claimants may use the pilot to make their claim, if their claim is suitable for the pilot. (Sub-paragraph (3) sets out the conditions that need to be met for a claim to be suitable for the pilot). The pilot is to run from 7 th August 2017 to 1 October 2025. The pilot applies in the County Court.
- (l). the claim is conducted in English, save that a party acting in person may view and complete screens, and submit the completed screens, in Welsh;
- (l). the claim is conducted in English, save that in a case to which paragraph (d)(iii) applies the defendant may respond to the claim in Welsh;


### Practice Direction 51Z

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/practice-direction-51zh-access-to-public-domain-documents
- local.updated: `2025-10-20T00:00:00Z`
- azure.updated: `2025-04-07T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- PRACTICE DIRECTION 51 ZH - ACCESS TO PUBLIC DOMAIN DOCUMENTS
- PLEASE NOTE THIS PD COMES INTO FORCE 1 JANUARY 2026
- Contents of this Practice Direction
- Scope of this practice direction and interpretation

Azure-only signal lines (should appear in live HTML if scraper issue):
- PRACTICE DIRECTION 51 ZG 3 - PILOT SCHEME FOR CERTAIN HIGH COURT QUALIFIED ONE-WAY COSTS SHIFTING (QOCS) CASES
- 1. This Practice Direction establishes a pilot schemes to test a new approach to costbudgeting in relevant claims issued on or after 6 April 2025 and before 6 April 2028.
- 2.The provisions of Section II of Part 3 (costs management) and Practice Direction 3 Dshall apply, save as modified by this Practice Direction. Rules 3.13 and 3.14 shall notapply.
- 3.In this Practice Direction-


### Practice Direction 52C

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52c-appeals-to-the-court-of-appeal
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (11) Size of supplementary bundle: No supplementary bundle (whether for permission to appeal or for an appeal hearing) may exceed one lever arch file of 350 pages in size, unless the court gives permission. An application for permission to file a supplementary bundle of more than 350 pages must be made by application notice in accordance with CPR Part 23 and specify exactly what additional documents the party wishes to include; why it is necessary to put the additional documents before the court; and whether there is agreement between the parties as to their inclusion.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (11) Size of supplementary bundle: No supplementary bundle (whether for permission to appeal or for an appeal hearing) may exceed one lever arch file of 350 pages in size, unless the court gives permission. An application for permission to file a supplementary bundle of more than 350 pages must be made by application notice in accordance with CPR Part 23 and specify exactly what additional documents the party wishes to include; why it is necessary to put the additional documents before the court; and whether there isagreement between the parties as to their inclusion.


### Practice Direction 52D

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52d-statutory-appeals-and-appeals-subject-to-special-provision
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (c) the Principal Registry of the Family Division, the senior District Judge of that division. Appeals relating to the application of Chapters I and II of Part I of the Competition Act 1998 or to a claim under section 101 of the Digital Markets, Competition and Consumers Act 2024
- (a) 'the 1988 Act' means the Competition Act 1998 or to a claim under section 101 of the Digital Markets, Competition and Consumers Act 2024;
- (aa) 'the 2024 Act' means the Digital Markets, Competition and Consumers Act 2024;
- (ii) a regulator as defined in section 54 of the 1988 Act;

Azure-only signal lines (should appear in live HTML if scraper issue):
- (c) the Principal Registry of the Family Division, the senior District Judge of that division. Appeals relating to the application of Chapters I and II of Part I of the Competition Act 1998
- (a) 'the Act' means the Competition Act 1998;
- (ii) a regulator as defined in section 54 of the Act;
- (3) Any party whose appeal notice raises an issue relating to the application of Chapter I or II of Part I of the Act, must -


### Practice Direction 52E

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part52/practice-direction-52e-appeals-by-way-of-case-stated
- local.updated: `2017-03-23T00:00:00Z`
- azure.updated: `2017-03-23T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- SECTION II - CASE STATED BY CROWN COURT OR MAGISTRATES' COURT
- The procedure for applying to the Crown Court or a Magistrates' Court to have a case stated for the opinion of the High Court differs according to whether the proceedings are criminal or civil. For criminal proceedings, the procedure is set out in the Criminal Procedure Rules. For civil proceedings, the procedure for applying to the Crown Court is set out in the Crown Court Rules 1982, and for applying to a magistrates' court, the Magistrates' Courts Rules 1981.

Azure-only signal lines (should appear in live HTML if scraper issue):
- SECTION II - CASE STATED BY CROWN COURT OR MAGISTRATES'COURT
- The procedure for applying to the Crown Court or a Magistrates' Court to have a case stated for the opinion of the High Court is set out in the Criminal Procedure Rules.


### Practice Direction 54D

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part54/practice-direction-54e-planning-court-claims
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- 1.4 In this Practice Direction "nationally significant infrastructure project challenge" means a claim brought within sections 13 or 118 of the Pl.anning Act 2008
- (c)generate significant public interest;
- (d)by virtue of the volume or nature of technical material, are best dealt with by judges with significant experience of handling such matters; or
- (e) concern a nationally significant infrastructure project challenge.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (c)generate significant public interest; or
- (d)by virtue of the volume or nature of technical material, are best dealt with by judges with significant experience of handling such matters.
- 6.16 An appeal brought by virtue of sections 289(1) or (2) of the TCP Act or section 65(1) of the PLBCA Act will be treated as if it is a revie w under statute for the purposes of rules 45.41 to 45.44 and may therefore be an Aarhus Convention claim for the purposes of those rules.


### Practice Direction 57

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part57/pd_part57
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- (4) any facts which might affect the exercise of the court's powers under the Act.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (4) any facts which might affect the exercise of the court"s powers under the Act.


### Practice Direction 57B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part57/practice-direction-57b-proceedings-under-the-presumption-of-death-act-2013
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- (b) where the claim form has been served outside the jurisdiction, more than 7 days (but where practicable no more than 35 days) after the period for filing provided for by rule 57.19(7), to allow for time for those served with notice of the claim or who respond to the advertisement of the claim to file notice of intention to intervene or an application for permission to intervene as the case may be.

Azure-only signal lines (should appear in live HTML if scraper issue):
- (b) where the claim form has been served outside the jurisdiction, more than 7 days (but where practicable no more than 35 days) after the period forfiling provided for by rule 57.19(7), to allow for time for those served with notice of the claim or who respond to the advertisement of the claim to file notice of intention to intervene or an application for permission to intervene as the case may be.


### Practice Direction 62

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part62/pd_part62
- local.updated: `2017-11-28T00:00:00Z`
- azure.updated: `2017-11-28T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- Having regard to the overriding objective the court may decide particular issues without a hearing.

Azure-only signal lines (should appear in live HTML if scraper issue):
- Applications under sections 32 and 45 of the 1996 Act
- This paragraph applies to arbitration claims for the determination of -
- (1) a question as to the substantive jurisdiction of the arbitral tribunal under section 32 of the 1996 Act; and
- (2) a preliminary point of law under section 45 of the 1996 Act.


### Practice Direction 63

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part63/pd_part63
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**


### Practice Direction 64B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part64/pd_part64b
- local.updated: `2017-11-30T00:00:00Z`
- azure.updated: `2017-11-30T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- A Master may give the directions sought, whether at a hearing or on paper pursuant to paragraph 6. They will ordinarily do so, but may refer the matter to a High Court Judge if they consider it appropriate. District Judges may give the directions sought only with the consent of their Supervising Judge or their nominee (see PD 2 B para. 7 B.2(c)).

Azure-only signal lines (should appear in live HTML if scraper issue):
- The master or district judge may give the directions sought though, if the directions relate to actual or proposed litigation, only if it is a plain case, and therefore the master or district judge may think it appropriate to give the directions without a hearing: see Practice Direction 2 B, para 4.1 and para. 5.1(e), and see also paragraph 6 above. Otherwise the case will be referred to the judge.


### Practice Direction 6B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part06/pd_part06b
- local.updated: `2023-06-08T00:00:00Z`
- azure.updated: `2023-06-08T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 4.2 Some countries require legalisation of the document to be served and some require a formal letter of request which must be signed by the Senior Master. Any queries on this should be addressed to the Foreign Process Section at the Royal Courts of Justice.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 4.2 Some countries require legalisation of the document to be served and some require a formal letter of request which must be signed by the Senior Master. Any queries on this should be addressed to the Foreign Process Section (Room E 02) at the Royal Courts of Justice.


### Practice Direction 74A

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part74/pd_part74a
- local.updated: `2023-02-07T00:00:00Z`
- azure.updated: `2023-02-07T00:00:00Z`
- classification: **website_changed (live matches local)**

Local-only signal lines (should appear in live HTML if website changed):
- (3) section 1(2) of the 1933 Act, which limits enforcement under that Act to money judgments;
- (4) section 15 (1) of the 1982 Act, which limits enforcement under Part I of that Act to judgments within the meaning given by article 4(1) of the 2005 Hague Convention and article 3(1) of the 2019 Hague Convention.
- (c) sections 4, 4 B and 4 C of the 1982 Act;
- (2) registers of certificates issued for the enforcement in foreign countries of High Court judgments under the 1920, 1933 and 1982 Acts, and under article 13 of the 2005 Hague Convention, article 12 of the 2019 Hague Convention;

Azure-only signal lines (should appear in live HTML if scraper issue):
- (3) section 1(2) of the 1933 Act, which limits enforcement under that Act to money judgments.
- (c) section 4 B of the 1982 Act;
- (2) registers of certificates issued for the enforcement in foreign countries of High Court judgments under the 1920, 1933 and 1982 Acts, and under article 13 of the 2005 Hague Convention;


### Practice Direction 77

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part77/pd_part77
- local.updated: `2023-02-07T00:00:00Z`
- azure.updated: `2023-02-07T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- PRACTICE DIRECTION 77 - APPLICATIONS FOR AND RELATING TO SERIOUS CRIME PREVENTION ORDERS AND REFERRAL OF RELEASE DECISIONS
- SECTION 1 - SERIOUS CRIME PREVENTION ORDERS
- SECTION 3 - REFERRAL OF RELEASE DECISIONS
- Where to make an application

Azure-only signal lines (should appear in live HTML if scraper issue):
- PRACTICE DIRECTION 77 - APPLICATIONS FOR AND RELATING TO SERIOUS CRIME PREVENTION ORDERS


### Practice Direction 7B

- storageUrl: https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part07/pd_part07c
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- classification: **mixed_or_inconclusive**

Local-only signal lines (should appear in live HTML if website changed):
- 'Code of Practice' means any code of practice which may at any time be issued by His Majesty's Courts and Tribunals Service relating to the discharge by the Centre of its functions and the way in which a Centre user is to conduct business with the Centre; and
- 4.2 His Majesty's Courts and Tribunals Service may change the Code of Practice from time to time.

Azure-only signal lines (should appear in live HTML if scraper issue):
- 'Code of Practice' means any code of practice which may at any time be issued by Her Majesty's Courts and Tribunals Service relating to the discharge by the Centre of its functions and the way in which a Centre user is to conduct business with the Centre; and
- 4.2 Her Majesty's Courts and Tribunals Service may change the Code of Practice from time to time.


