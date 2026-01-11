# AI Manual Review — FULL Diffs (Jan 4, 2026)

This report is an automated, AI-assisted triage over the FULL normalized Azure-vs-local text (not excerpt-only). It does not call an LLM and is not legal advice.

## Summary

- Substantive mismatches reviewed: **40**
- Missing in Azure (confirmed): **9**
- Impact split: **14 HIGH**, **8 MEDIUM**, **18 LOW**
- Causality split (from live-HTML check):
  - **25**: mixed_or_inconclusive
  - **14**: website_changed (live matches local)
  - **1**: scraper/extraction issue (live matches azure)

## A. Mismatches — Triage Table

| sourcefile | impact | cause | removed | added | change.ratio | local.updated | azure.updated | azure.id |
|---|---:|---|---:|---:|---:|---:|---:|---|
| Practice Direction 51Z | HIGH | website_changed (live matches local) | 27 | 77 | 1.333 | 2025-10-20T00:00:00Z | 2025-04-07T00:00:00Z | Practice_Direction_51ZG3___Pilot_scheme_for_certain_High_Court_qualified_one-way_costs_shifting__QOC |
| Part 77 | HIGH | website_changed (live matches local) | 0 | 175 | 0.559 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_77___Provision_in_Support_of_Criminal_Justice |
| Practice Direction 51R | HIGH | mixed_or_inconclusive | 35 | 43 | 0.424 | 2025-10-06T00:00:00Z | 2024-04-15T00:00:00Z | Practice_Direction_51R___Online_Civil_Money_Claims_Pilot_chunk_001 |
| Practice Direction 31C | HIGH | mixed_or_inconclusive | 5 | 9 | 0.230 | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | Practice_Direction_31C___Disclosure_and_inspection_in_relation_to_competition_claims |
| Part 74 | HIGH | mixed_or_inconclusive | 33 | 26 | 0.210 | 2021-04-14T00:00:00Z | 2021-04-14T00:00:00Z | Part_74___Enforcement_of_Judgments_in_Different_Jurisdictions |
| Practice Direction 30 | HIGH | mixed_or_inconclusive | 1 | 14 | 0.183 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_30 |
| Practice Direction 52D | HIGH | mixed_or_inconclusive | 17 | 17 | 0.158 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_52D___Statutory_appeals_and_appeals_subject_to_special_provision_chunk_001 |
| Practice Direction 31A | HIGH | mixed_or_inconclusive | 4 | 3 | 0.096 | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_31A___Disclosure_and_Inspection |
| Part 8 | HIGH | website_changed (live matches local) | 4 | 4 | 0.079 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Part_8___Alternative_Procedure_for_Claims |
| Part 52 | HIGH | mixed_or_inconclusive | 5 | 4 | 0.045 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_52___Appeals_chunk_001 |
| Practice Direction 54D | HIGH | website_changed (live matches local) | 3 | 9 | 0.036 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_54D___Planning_Court_Claims |
| Practice Direction 57B | HIGH | website_changed (live matches local) | 1 | 1 | 0.024 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_57B___Proceedings_under_the_Presumption_of_Death_Act_2013 |
| Part 2 | HIGH | mixed_or_inconclusive | 1 | 1 | 0.020 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_2___Application_and_Interpretation_of_the_Rules |
| Practice Direction 52C | HIGH | mixed_or_inconclusive | 1 | 1 | 0.007 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_52C___Appeals_to_the_Court_of_Appeal |
| Practice Direction 77 | MEDIUM | mixed_or_inconclusive | 1 | 24 | 0.305 | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | Practice_Direction_77 |
| Practice Direction 62 | MEDIUM | website_changed (live matches local) | 14 | 2 | 0.077 | 2017-11-28T00:00:00Z | 2017-11-28T00:00:00Z | Practice_Direction_62 |
| Part 5 | MEDIUM | website_changed (live matches local) | 1 | 2 | 0.065 | 2023-07-06T00:00:00Z | 2023-07-06T00:00:00Z | Part_5___Court_Documents |
| Part 44 | MEDIUM | website_changed (live matches local) | 5 | 7 | 0.045 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_44___General_Rules_about_Costs |
| Practice Direction 7B | MEDIUM | mixed_or_inconclusive | 2 | 2 | 0.034 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_7B-_Production_Centre |
| Part 82 | MEDIUM | scraper/extraction issue (live matches azure) | 3 | 3 | 0.030 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Part_82___Closed_material_procedure_chunk_001 |
| Practice Direction 6B | MEDIUM | mixed_or_inconclusive | 1 | 1 | 0.012 | 2023-06-08T00:00:00Z | 2023-06-08T00:00:00Z | Practice_Direction_6B___Service_out_of_the_Jurisdiction |
| Practice Direction 31B | MEDIUM | mixed_or_inconclusive | 1 | 1 | 0.009 | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_31B___Disclosure_of_Electronic_Documents |
| Practice Direction 74A | LOW | website_changed (live matches local) | 3 | 5 | 0.105 | 2023-02-07T00:00:00Z | 2023-02-07T00:00:00Z | Practice_Direction_74A___Enforcement_of_Judgments_in_different_Jurisdictions |
| Practice Direction 34A | LOW | mixed_or_inconclusive | 4 | 4 | 0.054 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_34A___Depositions_and_Court_Attendance_by_Witnesses |
| Practice Direction 52E | LOW | mixed_or_inconclusive | 2 | 3 | 0.046 | 2017-03-23T00:00:00Z | 2017-03-23T00:00:00Z | Practice_Direction_52E___Appeals_by_way_of_case_stated |
| Part 53 | LOW | mixed_or_inconclusive | 1 | 1 | 0.036 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_53___Media_and_Communications_Claims |
| Practice Direction 16 | LOW | website_changed (live matches local) | 0 | 6 | 0.028 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_16 |
| Part 30 | LOW | mixed_or_inconclusive | 1 | 1 | 0.024 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Part_30___Transfer |
| Practice Direction 64B | LOW | website_changed (live matches local) | 1 | 1 | 0.022 | 2017-11-30T00:00:00Z | 2017-11-30T00:00:00Z | Practice_Direction_64B___Applications_to_the_Court_for_Directions_by_Trustees_in_Relation_to_the_Adm |
| Practice Direction 41A | LOW | website_changed (live matches local) | 1 | 1 | 0.019 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Practice_Direction_41A___Provisional_Damages |
| Part 65 | LOW | mixed_or_inconclusive | 2 | 2 | 0.019 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_65___Proceedings_Relating_to_Anti-Social_Behaviour_and_Harassment_chunk_001 |
| Practice Direction 27A | LOW | website_changed (live matches local) | 1 | 1 | 0.015 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Practice_Direction_27A___Small_Claims_Track |
| Practice Direction 40B | LOW | mixed_or_inconclusive | 1 | 1 | 0.014 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Practice_Direction_40B___Judgments___Orders |
| Practice Direction 46 | LOW | mixed_or_inconclusive | 1 | 1 | 0.011 | 2024-04-06T00:00:00Z | 2024-04-06T00:00:00Z | Practice_Direction_46___Costs_Special_Cases |
| Practice Direction 57 | LOW | mixed_or_inconclusive | 1 | 1 | 0.010 | 2023-04-06T00:00:00Z | 2023-04-06T00:00:00Z | Practice_Direction_57 |
| Practice Direction 63 | LOW | mixed_or_inconclusive | 1 | 1 | 0.007 | 2020-10-01T00:00:00Z | 2020-10-01T00:00:00Z | Practice_Direction_63 |
| Part 62 | LOW | mixed_or_inconclusive | 1 | 1 | 0.007 | 2022-10-01T00:00:00Z | 2022-10-01T00:00:00Z | Part_62___Arbitration_Claims |
| Part 80 | LOW | mixed_or_inconclusive | 1 | 1 | 0.006 | 2017-01-30T00:00:00Z | 2017-01-30T00:00:00Z | Part_80___Proceedings_under_the_Terrorism_Prevention_and_Investigation_Measures_Act_2011 |
| Part 79 | LOW | mixed_or_inconclusive | 1 | 1 | 0.005 | 2021-09-06T00:00:00Z | 2021-09-06T00:00:00Z | Part_79___Proceedings_under_the_counter-terrorism_act_2008__part_1_of_the_terrorist_asset-freezing_e |
| Part 46 | LOW | website_changed (live matches local) | 0 | 1 | 0.003 | 2023-10-01T00:00:00Z | 2023-10-01T00:00:00Z | Part_46___Costs_special_cases |

## B. Mismatches — Per-Document Notes

### Practice Direction 51Z

- Impact: **HIGH** (score 18)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Access to public domain documents`
- local.updated: `2025-10-20T00:00:00Z`
- azure.updated: `2025-04-07T00:00:00Z`
- azure.id: `Practice_Direction_51ZG3___Pilot_scheme_for_certain_High_Court_qualified_one-way_costs_shifting__QOC`
- Signals: updated date differs (local vs azure), high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, costs/assessment mechanics changed, appeals/permission mechanics changed, time-limit language changed, diff magnitude (removed+added lines) ~= 104
- Full-diff stats: removed=27, added=77, change.ratio=1.333

Top removed (Azure-only) lines:

- 4.Unless the court orders otherwise, all parties except litigants in person shall file andserve a simplified costs budget by no later than 21 days before the first casemanagement conference.
- (b) unless the court orders otherwise, each party shall file and serve an updatedsimplified costs budget no later than 28 days before-
- 6.The defendant shall by no later than 14 days before the first case managementconference file and serve a simplified budget discussion report.
- 9.Where the court makes a costs management order using a simplified costs budget theprovisions of rules 3.15 (costs management orders), 3.15 A (revision and variation ofbudgets), 3.16 (costs management conferences), 3.17 (having regard to budgets) and 3.18 (assessing costs on the standard basis), shall apply with necessary modificationsuch that references to a "budget" in those provisions shall include a simplified costsbudget and references to Precedent T shall include Precedent TZ.
- (a) the provisions of Part 44 and paragraphs 3.2 to 3.7 of Practice Direction 44 shall apply as if reference in those paragraphs to a budget is reference to the simplified costs budget filed in accordance with paragraph 4 and any updatedsimplified costs budget; and
- 5.Unless the court orders otherwise paragraph 6 will not apply if any party gives noticeto the court and any other party by no later than 21 days before the first casemanagement conference that they intend to seek a direction for either-
- 2.The provisions of Section II of Part 3 (costs management) and Practice Direction 3 Dshall apply, save as modified by this Practice Direction. Rules 3.13 and 3.14 shall notapply.
- 11.If a party has failed to comply with its obligations under this Practice Direction, including the failure to file a simplified costs budget or Precedent H, the court mayimpose sanctions which may include limiting the recovery of the costs to be incurred to the applicable court fees.
- (c) giving costs management directions in respect of either or both the claimantand the defendant which may include a requirement to file and serve Precedent H or an updated simplified costs budget and the listing of a costs managementconference before the same or another Judge.
- 8.At the first case management conference the court may give case managementdirections, and may give costs management directions including-

Top added (Local-only) lines:

- 10.Irrespective of whether the document has already been filed on CE-File website, the party which has produced any document which becomes a Public Domain Document under paragraphs 7 and 8 must, subject to paragraphs 13 to 19, file that document on CE-File website under the relevant CE-File designations listed in Table A within the Filing Period.
- 15.Where a party seeks an FMO in relation to a document that is expected to become a Public Domain Document under paragraphs 7 and 8, as soon as practicable and before the commencement of the expected Filing Period they must file on CE-File website and, where applicable, with the clerk to the judge who presided over the hearing, a written request and a proposed FMO on notice to the other parties containing reasons (and where necessary, evidence) in support of the proposed FMO.
- 16.Where a Non-party named in a document that is expected to become a Public Domain Document under paragraphs 7 and 8 seeks an FMO, they must file an application notice under Part 23 on notice to the parties as soon as practicable and before the commencement of the expected Filing Period for that document.
- 4.In addition to the power in this practice direction to make an FMO in relation to a document that has become or is expected to become a Public Domain Document, the court may make any other order in relation to that document that it would otherwise be able to make, and any obligation, right or permission in this practice direction is subject to any such order.
- 19.Where the court makes an FMO, a Non-party may apply for a copy of any document or an unedited copy of any document to which the order applies by making an application under Part 23 on notice to all parties and to any person named in that document who obtained the FMO in relation to that document.
- 18.Where any party or a Non-party named or referred to in a document seeks an FMO in relation to a document that has already become a Public Domain Document they must apply under Part 23 on notice to the other parties and any person named in that document who has previously applied for an FMO.
- (b) in relation to documents within paragraph 8 below other than skeleton arguments and written opening and closing submissions the period beginning on the day when the relevant document is used or referred to in a hearing and ending at 16.00 on the fourteenth day after that, unless the court orders otherwise (for example in relation to a multi-day hearing or trial) or the parties agree to earlier filing;
- (a) in relation to skeleton arguments and written opening and closing submissions two clear days after the start of the hearing or hearing day at which the skeleton argument or written submission is relied upon;
- "the Filing Requirement" means the requirement in paragraph 10 to file, within the Filing Period, a document that has become a Public Domain Document; "Non-party" means a person who is not a party to the case;
- 17.Where such a request is made under paragraph 15 or an application is made under paragraph 16 the relevant Filing Period will not commence until the request or application has been determined and the document the subject of the request or application must not be filed until it has been determined and subject to that determination.

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 77

- Impact: **HIGH** (score 15)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Provision in Support of Criminal Justice`
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- azure.id: `Part_77___Provision_in_Support_of_Criminal_Justice`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed, time-limit language changed, diff magnitude (removed+added lines) ~= 175
- Full-diff stats: removed=0, added=175, change.ratio=0.559

Top added (Local-only) lines:

- (3) Where the court makes a direction under rule 77.23(2)(b), within 7 days after the date on which the defendant is notified of the court's decision or such other period as the court may direct, the legal representative must-
- (5) Where the court does not give permission to withhold relevant material from the defendant, or has made a direction under rule 77.23(2)(c), within seven days after the date on which they are notified of the court's decision or such other period as the court may direct, the claimant must-
- (b)the claimant must, within two days or such other period as may be directed by the court, file and serve on the special advocate notice of any objection to the proposed communication, or to the form in which it is proposed to be made.
- (3) Where paragraph (2)(c) applies, the special advocate may file and serve on the claimant written submissions regarding the application within 14 days of service of the application.
- (b)the time within which a certificate of service must be filed under rule 6.17(2)(a) shall be within 7 days of service of the claim form.
- (a)gives the required undertaking under paragraph (3), the claimant must, within two days of the date on which it is served on them-
- (2) Rule 8.5(1) is modified such that, not later than two days after the date on which the claim form is filed, the claimant must file with the court and, together with the claim form, serve on the defendant-
- (b)does not give the required undertaking within the time specified in paragraph (3) or informs the court of their decision not to give undertakings, the claimant must seek further directions from the court.
- (2) After the relevant material has been served on the special advocate, they must not communicate with any person about any matter connected with the proceedings, except in accordance with paragraphs (3), (4) or (8)(b) or with a direction of the court pursuant to a request under paragraph (5).
- (2) Unless the court directs otherwise, the court shall serve notice of the date, time and place fixed for a hearing on every party and, if one has been appointed for the purposes of the proceedings, the special advocate or those instructing the special advocate.

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 51R

- Impact: **HIGH** (score 15)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Online Civil Money Claims Pilot`
- local.updated: `2025-10-06T00:00:00Z`
- azure.updated: `2024-04-15T00:00:00Z`
- azure.id: `Practice_Direction_51R___Online_Civil_Money_Claims_Pilot_chunk_001`
- Signals: updated date differs (local vs azure), high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, costs/assessment mechanics changed, time-limit language changed, diff magnitude (removed+added lines) ~= 78
- Full-diff stats: removed=35, added=43, change.ratio=0.424

Top removed (Azure-only) lines:

- (5)If, within 33 days after being asked by the court, the claimant uses the OCMC website to tell the court that they wish to continue with the claim the claimant must, at the same time, also submit their completed online directions questionnaire to the court, to tell the court what requirements the claimant would have, should a court hearing be necessary, including, if the claim appears suitable for the fast track, intermediate track or multi-track, proposed directions.
- (4)If the claimant fails to respond online within the 33 days, the court must "stay" the proceedings (as defined).
- (3)If, within 33 days after being asked by the court, the claimant uses the OCMC website to tell the court that they do not wish to continue with the claim, the claim will be automatically "stayed" (as defined).
- 4 A.3(1)If, after a claim has been issued, a party provides information to the court by using screens completed and submitted in Welsh, the court must send them for translation into English ("the English translation"), and then provide a copy of the English translation to the parties. (2) If a party has submitted screens in Welsh, any time period calculated by reference to the date of submission or notification of the completed screens starts on the date on which the court provides the English translation to the party subject to the time period. SECTION 5 - PARTIES ACTING IN PERSON - DEFENDANT'S RESPONSE ONLINE - GENERAL
- (2) At the same time that the defendant submits the completed response form to the court in accordance with paragraph 5.1, the defendant must also submit their completed online directions questionnaire to the court, to tell the court what requirements the defendant would have, should a court hearing be necessary, including, if the claim appears suitable for the fast track, intermediate track or multi-track, proposed directions. SECTION 6 - PARTIES ACTING IN PERSON - DEFENDANT'S RESPONSE ONLINE - DEFENDANT ONLY DEFENDS THE WHOLE OF THE CLAIM, AND MAKES NO OTHER RESPONSE
- "early adopter court" means a County Court hearing centre that has been selected to trial more advanced features within Online Civil Money Claims and is listed on the HCMTS Reform Civil Fact Sheet which can be found atwww.gov.uk/government/publications/hmcts-reform-civil-fact-sheets;
- 2.1(7)If both the claimant and the defendant are represented, and the claim is suitable for the pilot except that the defendant's legal representative is not registered with My HMCTS, the claimant may nevertheless start the claim using the OCMC website and Sections 2 A to 4 of this practice direction apply, but the claim will be sent out of Online Civil Money Claims as soon as it has been issued. SECTION 2 A - PAYMENT OF COURT FEES Payment of court fees
- 2.1(1)The purpose of this practice direction is to establish a pilot to test an online claims process, called "Online Civil Money Claims". Claimants may use the pilot to make their claim, if their claim is suitable for the pilot. (Sub-paragraph (3) sets out the conditions that need to be met for a claim to be suitable for the pilot). The pilot is to run from 7 th August 2017 to 1 October 2025. The pilot applies in the County Court.
- (4) If a time extension has been agreed and recorded under subparagraph, the defendant must respond to the claim usingthe OCMC website by 4 pm on the last day of the agreed extended time.
- (2)The court must ask the claimant whether they accept the defendant's defence, or whether they do not accept it and wish to continue with the claim.

Top added (Local-only) lines:

- 2 B.2.Where the defendant pays the money claimed within 28 days from the date of issue of the claim together with the court fee and, where the claimant is legally represented, fixed commencement costs included in the claim form, the defendant is not liable for any further costs unless the court orders otherwise. SECTION 3 - COURT TO KEEP THE PARTIES UPDATED ON THE PROGRESS OF THE PROCEEDINGS
- (a) the claimant gives the defendant at least 14 days' notice of their intention to bring a claim under this Practice Direction; and (b) the defendant has instructed a legal representative before the claim is started.
- 2.1(1)The purpose of this practice direction is to establish a pilot to test an online claims process, called "Online Civil Money Claims". Sub-paragraph (3) sets out the conditions that need to be met for a claim to be within the scope of the pilot. Where a claim is within the scope of the pilot-
- (b) the claimant must give the defendant the notice referred to in sub-paragraph (5 C) unless it is impractical to do so; and
- 4 A.3(1)If, after a claim has been issued, a party provides information to the court by using screens completed and submitted in Welsh, the court must send them for translation into English ("the English translation"), and then provide a copy of the English translation to the parties.
- (b) If the claimant is legally represented, the pilot must be used to make the claim if sub-paragraph 2.1(5 A) applies. The pilot is to run from 7 th August 2017 to 1 st October 2026. The pilot applies in the County Court.
- (4) If a time extension has been agreed and recorded under subparagraph, the defendant must respond to the claim using the OCMC website by 4 pm on the last day of the agreed extended time.
- (c) the claimant must provide the defendant's legal representative's email address when completing the online claim form.
- (a) where judgment in default is entered, the relevant amount shown in Table 3 in the circumstances specified where judgment is entered in default of an acknowledgment of service under Civil Procedure Rule 12.4 (1); or
- (3) Unless the court orders otherwise, the only costs allowed for the claimant's legal representative's charges and included in the judgment are the fixed commencement costs and-

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 31C

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Disclosure and inspection in relation to competition claims`
- local.updated: `2023-06-08T00:00:00Z`
- azure.updated: `2023-06-08T00:00:00Z`
- azure.id: `Practice_Direction_31C___Disclosure_and_inspection_in_relation_to_competition_claims`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, disclosure/inspection mechanics changed
- Full-diff stats: removed=5, added=9, change.ratio=0.230

Top removed (Azure-only) lines:

- Disclosure and inspection of evidence in relation to a competition claim - evidence in the file of the competition authority
- Disclosure and inspection of evidence in relation to a competition claim
- (d) "reasoned justification" means a statement containing reasonably available facts and evidence sufficient to support the plausibility of the claim for damages to which the relevant evidence relates;
- (e) "relevant evidence" means evidence that a person is seeking to have disclosed or is seeking to inspect that relates to a competition claim.
- (i) a competition authority has closed the investigation to which the request for its investigation materials relates; and

Top added (Local-only) lines:

- 2.8 A Where the competition authority evidence includes a competition authority's digital markets investigation information, the application for disclosure or inspection must be supported by evidence that the competition authority has given notice of the closure or outcome of each investigation to which the information relates.
- (i) a competition authority has closed the investigation to which the request for its investigation materials relates or a competition authority has given notice of the closure or outcome of each investigation to which the request for its digital markets investigation information relates; and
- Disclosure and inspection of evidence in relation to a competition claim or digital markets proceedings - evidence in the file of the competition authority
- Disclosure and inspection of evidence in relation to a competition claim or digital markets proceedings
- (d) "reasoned justification" means a statement containing reasonably available facts and evidence sufficient to support the plausibility of the claim to which the relevant evidence relates;
- (e) "relevant evidence" means evidence that a person is seeking to have disclosed or is seeking to inspect that relates to a competition claim or digital markets proceedings.
- (ca) "digital markets investigation information" has the same meaning as in section 116(4) of the 2024 Act;
- (ba) "digital markets proceedings" has the same meaning as in section 116(4) of the 2024 Act;
- (aa) "the 2024 Act" means the Digital Markets, Competition and Consumers Act 2024;

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 74

- Impact: **HIGH** (score 12)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Enforcement of Judgments in Different Jurisdictions`
- local.updated: `2021-04-14T00:00:00Z`
- azure.updated: `2021-04-14T00:00:00Z`
- azure.id: `Part_74___Enforcement_of_Judgments_in_Different_Jurisdictions`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed, time-limit language changed, diff magnitude (removed+added lines) ~= 59
- Full-diff stats: removed=33, added=26, change.ratio=0.210

Top removed (Azure-only) lines:

- (d) the period within which such an application or appeal may be made; and
- (1) An appeal against the granting or the refusal of registration under the 1982 Act must be made in accordance with Part 52, subject to the following provisions of this rule.
- (1) An application to set aside registration under the 1920 or the 1933 Act must be made within the period set out in the registration order.
- (b) where the appeal is against the refusal of registration, within one month of the decision on the application for registration.
- (b) an application to extend the time for appealing is made within two months of service of the registration order
- (ii) where service is to be effected on a party not domiciled within the jurisdiction, two months
- (a) where the appeal is against the granting of registration, within -
- (4) The appellant's notice must be served -
- the court may extend the period for filing an appellant's notice against the order granting registration, but not on grounds of distance.
- (5 A) Written evidence in support of an application under section 4 B of the 1982 Act (registration and enforcement of judgments under the 2005 Hague Convention) must also include any other evidence required by Article 13 of the 2005 Hague Convention.

Top added (Local-only) lines:

- (1) An application to set aside a decision on a registration application under the 1920 Act, the 1933 Act or the 1982 Act must be made within the period set out in the registration order or decision.
- (d) the period within which such an application may be made; and
- (6) Written evidence in support of an application under section 4 B of the 1982 Act (registration and enforcement of judgments under the 2005 Hague Convention) must also-
- (7) Written evidence in support of an application under section 4 C of the 1982 Act (registration and enforcement of judgments under the 2019 Hague Convention) must also-
- (ii) meets at least one condition in Article 5 or 6 of the 2019 Hague Convention; and
- (2) An application for registration of a judgment made under section 4 B or 4 C of the 1982 Act for the purposes of recognition is governed by the same rules as an application for registration of a judgment for the purposes of recognition and enforcement, except that rule 74.4(5)(a) and (c) do not apply.
- The rules governing the registration of judgments under the 1982 Act apply as appropriate and with any necessary modifications for the enforcement of court settlements which are subject to article 12 of the 2005 Hague Convention or article 11 of the 2019 Hague Convention.
- (1) Registration of a judgment on an application made under section 4 B or 4 C of the 1982 Act serves as a decision that the judgment is recognised for the purposes of the 2005 Hague Convention or the 2019 Hague Convention, respectively.
- (c) the right of the judgment debtor in the case of registration following an application under the 1920 Act, the 1933 Act or the 1982 Act, to apply to have the registration set aside;
- (h) "the 2019 Hague Convention" means the Convention on the Recognition and Enforcement of Foreign Judgments in Civil or Commercial Matters concluded on 2 nd July 2019 at The Hague.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 30

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Practice Direction 30`
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- azure.id: `Practice_Direction_30`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, appeals/permission mechanics changed, time-limit language changed
- Full-diff stats: removed=1, added=14, change.ratio=0.183

Top removed (Azure-only) lines:

- 8.9 A party to a claim which has been transferred under paragraph 8.7 may apply to transfer it to the Commercial Court if it otherwise falls within the scope of rule 58.2(1), in accordance with the procedure set out in rules 58.4(2) and 30.5(3).

Top added (Local-only) lines:

- 8.9 A party to a claim which has been transferred under paragraph 8.7 may apply to transfer it to the Commercial Court if it otherwise falls within the scope of rule 58.2(2), in accordance with the procedure set out in rules 58.4(2) and 30.5(3).
- 10.3 A party to a claim which has been transferred under paragraph 10.2 may apply to the Commercial Court for transfer into the Commercial List if the claim falls within the scope of rule 58.1(2).
- 10.4 The court may make an order under section 101(5) of the 2024 Act, on its own initiative or on application by the claimant or defendant, transferring any part of the proceedings before it, which relates to a claim under section 101 of the 2024 Act, to the CAT.
- Transfer from the Competition Appeal Tribunal to the High Court under section 101(5) of the 2024 Act
- Transfer from the High Court to the Competition Appeal Tribunal under section 101(5) of the 2024 Act
- 10.2 Where the CAT pursuant to section 101(5) of the 2024 Act directs transfer of a claim made in proceedings under section 101 of the 2024 Act to the High Court, the claim should be transferred to the Chancery Division of the High Court at the Royal Courts of Justice.
- • rules 30.1, 30.4 and 30.5 and paragraphs 3 and 6 of this Practice Direction apply.
- • "the 2024 Act" means the Digital Markets, Competition and Consumers Act 2024; and
- Part 1 of the Digital Markets, Competition and Consumers Act 2024
- • "the CAT" has the same meaning as in paragraph 8.1(3);

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 52D

- Impact: **HIGH** (score 11)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Statutory appeals and appeals subject to special provision`
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- azure.id: `Practice_Direction_52D___Statutory_appeals_and_appeals_subject_to_special_provision_chunk_001`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed, time-limit language changed
- Full-diff stats: removed=17, added=17, change.ratio=0.158

Top removed (Azure-only) lines:

- (2) The appellant's notice must be filed at the Court of Appeal within 21 days of the date on which the Investigatory Powers Tribunal's decision granting or refusing leave to appeal to the Court of Appeal is given.
- (b) state the date on which the appellant gave to the Board notice of appeal under section 222(1) of the 1984 Act or regulation 8(1) of the 1986 Regulations and, if notice was not given within the time permitted, whether HM Revenue and Customs (HMRC) have given their consent or the tribunal has given permission for notice to be given after the time permitted, and where applicable, the date of such consent or permission; and
- (3) Any party whose appeal notice raises an issue relating to the application of Chapter I or II of Part I of the Act, must -
- (c) where the appellant's notice contains an application for permission to appeal, written evidence setting out the grounds on which it is alleged that the matters to be decided on the appeal are likely to be substantially confined to questions of law.
- (a) state the date on which the Commissioners for HM Revenue and Customs (the 'Board') gave notice to the appellant under section 221 of the 1984 Act or regulation 6 of the 1986 Regulations of the determination that is the subject of the appeal;
- (5) A competition authority may make written observations to the Court of Appeal, or apply for permission to make oral observations, on issues relating to the application of Chapter I or II.
- (c) either state that the appellant and the Board have agreed that the appeal may be to the High Court or contain an application for permission to appeal to the High Court.
- (b) 2 copies of the notice of appeal (under section 222(1) of the 1984 Act or regulation 8(1) of the 1986 Regulations) referred to in paragraph 2(b); and
- (3) The appellant must file the following documents with the appellant's notice -
- (2) The appellant's notice must -

Top added (Local-only) lines:

- (2) The appellant's notice must be filed at the Court of Appeal within 21 days of the date on which the Investigatory Powers Tribunal's decision granting or refusing leave to appeal to the Court of Appeal is given. Appeals concerning claims brought within section 13 or 118 of the Planning Act 2008 (Nationally Significant Infrastructure Project Appeals)
- (d) the respondent may file and serve reasons why permission to appeal should not be granted, if so advised, within seven days of service of the appellant's notice and appellant's skeleton argument.
- (3) Any party whose appeal notice raises an issue relating to the application of Chapter I or II of Part I of the 1998 Act or to a claim under section 101 of the 2024 Act, must -
- (b) the appellant's notice and appellant's skeleton argument are to be served on the respondent within seven days of the appellant's notice being sealed;
- (c) the appellant is to file a core bundle and serve a core bundle index on the respondent within seven days of the appellant's notice being sealed; and
- (5 A) The Competition and Markets Authority may make written observations to the Court of Appeal, or apply for permission to make oral observations, on issues relating to a claim under section 101 of the 2024 Act.
- (5) A competition authority may make written observations to the Court of Appeal, or apply for permission to make oral observations, on issues relating to the application of Chapter I or II of the 1998 Act.
- (1) The target timescale for determining an application for permission to appeal in a nationally significant infrastructure project appeal is four weeks from the filing of an appellant's notice.
- (a) the appellant's notice is to be filed within seven days of the decision being
- (3) The target timescale for the hearing of nationally significant infrastructure project appeals, which the parties should be prepared to meet, is four months from the filing of an appellant's notice. APPEALS TO THE HIGH COURT Reference of question of law by Agricultural Land Tribunal

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 31A

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Disclosure and Inspection`
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- azure.id: `Practice_Direction_31A___Disclosure_and_Inspection`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, disclosure/inspection mechanics changed, time-limit language changed
- Full-diff stats: removed=4, added=3, change.ratio=0.096

Top removed (Azure-only) lines:

- 1.2 In order to give standard disclosure the disclosing party must make a reasonable search for documents falling within the paragraphs of rule 31.6.
- 1.3 Having made the search the disclosing party must (unless rule 31.10(8) applies) make a list of the documents of whose existence the party is aware that fall within those paragraphs and which are or have been in the party's control (see rule 31.8).
- 1.4 The obligations imposed by an order for standard disclosure may be dispensed with or limited either by the court or by written agreement between the parties. Any such written agreement should be lodged with the court.
- 1.1 The normal order for disclosure will be an order that the parties give standard disclosure.

Top added (Local-only) lines:

- 1.1 In order to give standard disclosure the disclosing party must make a reasonable search for documents falling within the paragraphs of rule 31.6.
- 1.2 Having made the search the disclosing party must (unless rule 31.10(8) applies) make a list of the documents of whose existence the party is aware that fall within those paragraphs and which are or have been in the party's control (see rule 31.8).
- 1.3 The obligations imposed by an order for standard disclosure may be dispensed with or limited either by the court or by written agreement between the parties. Any such written agreement should be lodged with the court.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 8

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Alternative Procedure for Claims`
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- azure.id: `Part_8___Alternative_Procedure_for_Claims`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, time-limit language changed
- Full-diff stats: removed=4, added=4, change.ratio=0.079

Top removed (Azure-only) lines:

- (3) A defendant who wishes to rely on written evidence must file it when they file their acknowledgment of service.
- (4) If they do so, they must also, at the same time, serve a copy of their evidence on the other parties.
- 8.2 Where the claimant uses the Part 8 procedure the claim form must state -
- (Rule 7.5 provides for service of the claim form)

Top added (Local-only) lines:

- (3) A defendant who wishes to rely on written evidence must file it when they file their acknowledgment of service unless the defendant has indicated on their acknowledgement of service an intention to contest jurisdiction, in which case the evidence must be filed within fourteen days of filing the acknowledgment of service if no such application is made.
- (2) Except where another rule or practice direction applies, rule 7.5 and rule 7.6 shall apply with regard to the service of the claim form.
- (4) If a defendant files their evidence, they must also, at the same time, serve a copy of their evidence on the other parties.
- 8.2(1) Where the claimant uses the Part 8 procedure the claim form must state -

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 52

- Impact: **HIGH** (score 11)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Appeals`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Part_52___Appeals_chunk_001`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed, time-limit language changed
- Full-diff stats: removed=5, added=4, change.ratio=0.045

Top removed (Azure-only) lines:

- (3) Subject to paragraph (4) and unless the appeal court orders otherwise, an appellant's notice must be served on each respondent-
- (b) in any event not later than 7 days,
- (1) Where permission to apply for judicial review has been refused at a hearing in the High Court, an application for permission to appeal may be made to the Court of Appeal except where precluded by section 18(1)(a) of the Senior Courts Act 198.
- (1) In this rule, "Aarhus Convention claim" and "prohibitively expensive" have the same meanings as in Section IX of Part 46, and "claimant" means a claimant to whom rules 46.26 to 46.28 apply.
- after it is filed.

Top added (Local-only) lines:

- (3) Subject to paragraph (4) and unless the appeal court orders otherwise, a sealed copy of the appellant's notice must be served on each respondent-
- (b) in any event where it is served by the appellant not later than 14 days,
- (1) Where permission to apply for judicial review has been refused at a hearing in the High Court, an application for permission to appeal may be made to the Court of Appeal except where precluded by section 18(1) of the Senior Courts Act 198.
- after it is sealed.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 54D

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Planning Court Claims`
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- azure.id: `Practice_Direction_54D___Planning_Court_Claims`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, appeals/permission mechanics changed, time-limit language changed
- Full-diff stats: removed=3, added=9, change.ratio=0.036

Top removed (Azure-only) lines:

- 6.16 An appeal brought by virtue of sections 289(1) or (2) of the TCP Act or section 65(1) of the PLBCA Act will be treated as if it is a revie w under statute for the purposes of rules 45.41 to 45.44 and may therefore be an Aarhus Convention claim for the purposes of those rules.
- (d)by virtue of the volume or nature of technical material, are best dealt with by judges with significant experience of handling such matters.
- (c)generate significant public interest; or

Top added (Local-only) lines:

- 3.8 Where the Planning Court grants permission in a nationally significant infrastructure project challenge, the court may give directions about the future management of the claim immediately or convene a case management conference on an application or of its own initiative
- 6.16 An appeal brought by virtue of sections 289(1) or (2) of the TCP Act or section 65(1) of the PLBCA Act will be treated as if it is a review under statute for the purposes of rules 45.41 to 45.44 and may therefore be an Aarhus Convention claim for the purposes of those rules.
- 1.4 In this Practice Direction "nationally significant infrastructure project challenge" means a claim brought within sections 13 or 118 of the Pl.anning Act 2008
- 3.7 The Planning Court will consider any disputed question of permission in nationally significant infrastructure project challenges at an oral permission hearing only.
- (d)by virtue of the volume or nature of technical material, are best dealt with by judges with significant experience of handling such matters; or
- (e) concern a nationally significant infrastructure project challenge.
- Nationally significant infrastructure project challenges
- (c)generate significant public interest;
- ---

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 57B

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Proceedings under the Presumption of Death Act 2013`
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- azure.id: `Practice_Direction_57B___Proceedings_under_the_Presumption_of_Death_Act_2013`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed
- Full-diff stats: removed=1, added=1, change.ratio=0.024

Top removed (Azure-only) lines:

- (b) where the claim form has been served outside the jurisdiction, more than 7 days (but where practicable no more than 35 days) after the period forfiling provided for by rule 57.19(7), to allow for time for those served with notice of the claim or who respond to the advertisement of the claim to file notice of intention to intervene or an application for permission to intervene as the case may be.

Top added (Local-only) lines:

- (b) where the claim form has been served outside the jurisdiction, more than 7 days (but where practicable no more than 35 days) after the period for filing provided for by rule 57.19(7), to allow for time for those served with notice of the claim or who respond to the advertisement of the claim to file notice of intention to intervene or an application for permission to intervene as the case may be.

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 2

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Application and Interpretation of the Rules`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Part_2___Application_and_Interpretation_of_the_Rules`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, time-limit language changed
- Full-diff stats: removed=1, added=1, change.ratio=0.020

Top removed (Azure-only) lines:

- (1) This rule shows how to calculate any period of time for doing any act which is specified -(a) by these Rules;(b) by a practice direction; or(c) by a judgment or order of the court.(2) A period of time expressed as a number of days shall be computed as clear days.(3) In this rule 'clear days' means that in computing the number of days -(a) the day on which the period begins; and(b) if the end of the period is defined by reference to an event, the day on which that event occursare not included.Examples(i) Notice of an application must be served at least 3 days before the hearing.An application is listed to be heard on Friday 20 October.The last date for service is Monday 16 October.(ii) The court is to fix a date for a hearing.The hearing must be at least 28 days after the date of notice.If the court gives notice of the date of the hearing on 1 October, the earliest date for the hearing is 30 October.(iii) Particulars of claim must be served within 14 days of service of the claim form.The claim form is served on 2 October.The last day for service of the particulars of claim is 16 October.(4) Where the specified period -(a) is 5 days or less; and(b) includes -(i) a Saturday or Sunday; or(ii) a Bank Holiday, Christmas Day or Good Friday,that day does not count.Example Notice of an application must be served at least 3 days before the hearing.An application is to be heard on Monday 20 October.The last date for service is Tuesday 14 October.(5) Subject to the provisions of Practice Direction 5 C, when the period specified -(a) by these Rules or a practice direction; or(b) by any judgment or court order,for doing any act at the court office ends on a day on which the office is closed, that act shall be in time under these rules if done on the next day on which the court office is open.

Top added (Local-only) lines:

- (1) This rule shows how to calculate any period of time for doing any act which is specified -(a) by these Rules;(b) by a practice direction; or(c) by a judgment or order of the court.(2) A period of time expressed as a number of days shall be computed as clear days.(3) In this rule 'clear days' means that in computing the number of days -(a) the day on which the period begins; and(b) if the end of the period is defined by reference to an event, the day on which that event occursare not included.Examples(i) Notice of an application must be served at least 3 days before the hearing.An application is listed to be heard on Friday 20 October.The last date for service is Monday 16 October.(ii) The court is to fix a date for a hearing.The hearing must be at least 28 days after the date of notice.If the court gives notice of the date of the hearing on 1 October, the earliest date for the hearing is 30 October.(iii) Particulars of claim must be served within 14 days of service of the claim form.The claim form is served on 2 October.The last day for service of the particulars of claim is 16 October.(4) Where the specified period -(a) is 5 days or less; and(b) includes -(i) a Saturday or Sunday; or(ii) a Bank Holiday, Christmas Day or Good Friday,that day does not count.Example Notice of an application must be served at least 3 days before the hearing.An application is to be heard on Monday 20 October.The last date for service is Tuesday 14 October.(5) When the period specified -(a) by these Rules or a practice direction; or(b) by any judgment or court order,for doing any act at the court office ends on a day on which the office is closed, that act shall be in time under these rules if done on the next day on which the court office is open.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 52C

- Impact: **HIGH** (score 9)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Appeals to the Court of Appeal`
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- azure.id: `Practice_Direction_52C___Appeals_to_the_Court_of_Appeal`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed, appeals/permission mechanics changed
- Full-diff stats: removed=1, added=1, change.ratio=0.007

Top removed (Azure-only) lines:

- (11) Size of supplementary bundle: No supplementary bundle (whether for permission to appeal or for an appeal hearing) may exceed one lever arch file of 350 pages in size, unless the court gives permission. An application for permission to file a supplementary bundle of more than 350 pages must be made by application notice in accordance with CPR Part 23 and specify exactly what additional documents the party wishes to include; why it is necessary to put the additional documents before the court; and whether there isagreement between the parties as to their inclusion.

Top added (Local-only) lines:

- (11) Size of supplementary bundle: No supplementary bundle (whether for permission to appeal or for an appeal hearing) may exceed one lever arch file of 350 pages in size, unless the court gives permission. An application for permission to file a supplementary bundle of more than 350 pages must be made by application notice in accordance with CPR Part 23 and specify exactly what additional documents the party wishes to include; why it is necessary to put the additional documents before the court; and whether there is agreement between the parties as to their inclusion.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 77

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Practice Direction 77`
- local.updated: `2023-02-07T00:00:00Z`
- azure.updated: `2023-02-07T00:00:00Z`
- azure.id: `Practice_Direction_77`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed
- Full-diff stats: removed=1, added=24, change.ratio=0.305

Top removed (Azure-only) lines:

- PRACTICE DIRECTION 77 - APPLICATIONS FOR AND RELATING TO SERIOUS CRIME PREVENTION ORDERS

Top added (Local-only) lines:

- If the court makes an order requiring the applicant to give effect to the Parole Board's direction to release the prisoner on licence, before deciding whether to include directions as to the conditions to be included in the respondent's licence on release, the court shall have regard to the guidance in the Ministry of Justice's and His Majesty's Prison and Probation Service's Licence Conditions Policy Framework:Licence conditions policy framework - GOV.UK.
- (2) Where a VPS is read in court under paragraph (1), neither the maker nor the reader shall be cross-examined on it.
- 5.1 Any application concerning the referral of a release decision must be filed in the Administrative Court at the Royal Courts of Justice.
- • the potential for any harm to the victim or any other person which may arise from the VPS being read in court.
- 6.1-(1) The court may allow the victim personal statement (VPS) to be read in court-
- PRACTICE DIRECTION 77 - APPLICATIONS FOR AND RELATING TO SERIOUS CRIME PREVENTION ORDERS AND REFERRAL OF RELEASE DECISIONS
- (3) Practice Direction 1 A applies to any person referred to in this paragraph.
- • in person or through a video link or recording or by some other means,
- • by the maker of the VPS or another person;
- SECTION 1 - SERIOUS CRIME PREVENTION ORDERS

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 62

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Practice Direction 62`
- local.updated: `2017-11-28T00:00:00Z`
- azure.updated: `2017-11-28T00:00:00Z`
- azure.id: `Practice_Direction_62`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, appeals/permission mechanics changed
- Full-diff stats: removed=14, added=2, change.ratio=0.077

Top removed (Azure-only) lines:

- Where an arbitration claim is made without the agreement in writing of all the other parties to the arbitral proceedings but with the permission of the arbitral tribunal, the written evidence or witness statements filed by the parties must set out any evidence relied on by the parties in support of their contention that the court should, or should not, consider the claim.
- Having regard to the overriding objective the court may decide particular issues without a hearing. For example, as set out in paragraph 9.3, the question whether the court is satisfied as to the matters set out in section 32(2)(b) or section 45(2)(b) of the 1996 Act.
- As soon as practicable after the written evidence is filed, the court will decide whether or not it should consider the claim and, unless the court otherwise directs, will so decide without a hearing.
- (1) a question as to the substantive jurisdiction of the arbitral tribunal under section 32 of the 1996 Act; and
- This paragraph applies to arbitration claims for the determination of -
- (2) a preliminary point of law under section 45 of the 1996 Act.
- Applications under sections 32 and 45 of the 1996 Act
- ---
- 9.1
- 9.2

Top added (Local-only) lines:

- Having regard to the overriding objective the court may decide particular issues without a hearing.
- 9.1 Omitted

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 5

- Impact: **MEDIUM** (score 5)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Court Documents`
- local.updated: `2023-07-06T00:00:00Z`
- azure.updated: `2023-07-06T00:00:00Z`
- azure.id: `Part_5___Court_Documents`
- Signals: high-signal procedural language changed, moderate-signal legal language changed
- Full-diff stats: removed=1, added=2, change.ratio=0.065

Top removed (Azure-only) lines:

- 5.5(1) A practice direction may make provision for documents to be filed or sent to the court by -(a) facsimile; or(b) other electronic means.(2) Any such practice direction may -(a) provide that only particular categories of documents may be filed or sent to the court by such means;(b) provide that particular provisions only apply in specific courts; and(c) specify the requirements that must be fulfilled for any document filed or sent to the court by such means.

Top added (Local-only) lines:

- 5.5(1) A practice direction may make provision for documents to be filed or sent to the court by -(a) the use of an electronic filing and case management system; or(b) other electronic means.(2) Any such practice direction may -(a) provide that only particular categories of documents may be filed or sent to the court by such means;(b) provide that particular provisions only apply in specific courts;(c) specify the requirements that must be fulfilled for any document filed or sent to the court by such means; and
- (d) modify or disapply any provision of these rules in relation to the use of any court electronic filing and case management system.

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 44

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `General Rules about Costs`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Part_44___General_Rules_about_Costs`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, costs/assessment mechanics changed
- Full-diff stats: removed=5, added=7, change.ratio=0.045

Top removed (Azure-only) lines:

- (1) Where the court orders a party to pay costs to another party (other than fixed costs) it may either -
- (2) A party may recover the fixed costs specified in Part 45 in accordance with that Part.
- 'summary assessment' means the procedure whereby costs are assessed by the judge who has heard the case or application;
- (b) order detailed assessment of the costs by a costs officer,
- (a) make a summary assessment of the costs; or

Top added (Local-only) lines:

- (2) Where a direction has been given under paragraph (1)(b), another judge who could have decided the claim or application which gave rise to the costs order may make the summary assessment if there is good reason to do so.
- 'summary assessment' means the procedure whereby costs are assessed by the judge who has decided the case or application or where rule 44.6(2) applies;
- (1) Where the court orders a party to pay costs to another party (other than fixed costs) it may -
- (3) A party may recover the fixed costs specified in Part 45 in accordance with that Part.
- (b) give directions for the summary assessment of the costs to be made at a later date; or
- (c) order detailed assessment of the costs by a costs officer,
- (a) make a summary assessment of the costs;

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 7B

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Production Centre`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Practice_Direction_7B-_Production_Centre`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed
- Full-diff stats: removed=2, added=2, change.ratio=0.034

Top removed (Azure-only) lines:

- 'Code of Practice' means any code of practice which may at any time be issued by Her Majesty's Courts and Tribunals Service relating to the discharge by the Centre of its functions and the way in which a Centre user is to conduct business with the Centre; and
- 4.2 Her Majesty's Courts and Tribunals Service may change the Code of Practice from time to time.

Top added (Local-only) lines:

- 'Code of Practice' means any code of practice which may at any time be issued by His Majesty's Courts and Tribunals Service relating to the discharge by the Centre of its functions and the way in which a Centre user is to conduct business with the Centre; and
- 4.2 His Majesty's Courts and Tribunals Service may change the Code of Practice from time to time.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 82

- Impact: **MEDIUM** (score 5)
- Cause (live-HTML heuristic): scraper/extraction issue (live matches azure)
- sourcepage: `Closed material procedure`
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- azure.id: `Part_82___Closed_material_procedure_chunk_001`
- Signals: high-signal procedural language changed, moderate-signal legal language changed
- Full-diff stats: removed=3, added=3, change.ratio=0.030

Top removed (Azure-only) lines:

- (b) the special advocate must not reply to the communication other than in accordance with directions of the court, except that the special advocate may without such directions send a written acknowledgment of receipt to the specially represented party's legal representative. Evidence in proceedings to which this Part applies
- (2) After the relevant person serves sensitive material on the special advocate, the special advocate must not communicate with any person about any matter connected with the proceedings, except in accordance with paragraph (3) or (6)(b) or with a direction of the court pursuant to a request under paragraph (4).
- (c) the details of any special advocate already appointed under rule 82.9 (appointment of a special advocate).

Top added (Local-only) lines:

- (b) the special advocate must not reply to the communication other than in accordance with paragraph (3 A) or directions of the court, except that the special advocate may without such directions send a written acknowledgment of receipt to the specially represented party's legal representative. Evidence in proceedings to which this Part applies
- (2) After the relevant person serves sensitive material on the special advocate, the special advocate must not communicate with any person about any matter connected with the proceedings, except in accordance with paragraph (3), (3 A) or (6)(b) or with a direction of the court pursuant to a request under paragraph (4).
- (3 A) The special advocate may communicate with the specially represented party or the specially represented party's legal representative with the express agreement of the relevant person and (where the relevant person is not the Secretary of State) the Secretary of State.

Recommended action: inspect the scraper extraction for this page; the live page looked closer to Azure than to local.

### Practice Direction 6B

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Service out of the Jurisdiction`
- local.updated: `2023-06-08T00:00:00Z`
- azure.updated: `2023-06-08T00:00:00Z`
- azure.id: `Practice_Direction_6B___Service_out_of_the_Jurisdiction`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, service/notice mechanics changed
- Full-diff stats: removed=1, added=1, change.ratio=0.012

Top removed (Azure-only) lines:

- 4.2 Some countries require legalisation of the document to be served and some require a formal letter of request which must be signed by the Senior Master. Any queries on this should be addressed to the Foreign Process Section (Room E 02) at the Royal Courts of Justice.

Top added (Local-only) lines:

- 4.2 Some countries require legalisation of the document to be served and some require a formal letter of request which must be signed by the Senior Master. Any queries on this should be addressed to the Foreign Process Section at the Royal Courts of Justice.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 31B

- Impact: **MEDIUM** (score 7)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Disclosure of Electronic Documents`
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- azure.id: `Practice_Direction_31B___Disclosure_of_Electronic_Documents`
- Signals: high-signal procedural language changed, moderate-signal legal language changed, disclosure/inspection mechanics changed
- Full-diff stats: removed=1, added=1, change.ratio=0.009

Top removed (Azure-only) lines:

- • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • State the geographical location (if known). Consider (at least) servers, desktop PCs, laptops, notebooks, handheld devices, PDA devices, off-site storage, removable storage media (for example, CD-ROMs, DVDs, USB drives, memory sticks) and databases. • Consider all types of e-mail system (for example, Outlook, Lotus Notes, web-based accounts), whether stored on personal computers, portable devices or in web-based accounts (for example, Yahoo, Hotmail, Gmail). • For example, instant messaging, voicemail, VOIP (Voice Over Internet Protocol), recorded telephone lines, text messaging, audio files, video files. • State the geographical location (if known). Consider (at least) servers, desktops and laptops. • For example, .pdf. .tif, .jpg. • For example, Powerpoint or equivalent, specialist documents (such as CAD Drawings). • Where Keyword Searches are used in order to identify irrelevant documents which are to be excluded from disclosure (for example a confidential name of a client or customer), a general description of the type of search may be given. • See Practice Direction 31 B, which refers to the following matters which may be relevant: (a) the number of documents involved; (b) the nature and complexity of the proceedings; (c) the ease and expense of retrieval of any particular document; (d) the availability of documents or contents of documents from other sources; and (e) the significance of any document which is likely to be located during the search. • For example, back-ups, archives, off-site or outsourced document storage, documents created by former employees, documents stored in other jurisdictions, documents in foreign languages. • There is no requirement that you should obtain OCR versions of documents, and this question is directed only to OCR versions which you have available or expect to have available to you. If you do provide OCR versions to another party, they will be provided by you on an 'as is' basis, with no assurance to the other party that the OCR versions are complete or accurate. You may wish to exclude provision of OCR versions of documents which have been redacted. • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • 'Metadata' is information about the document or file which is recorded in the computer, such as the date and time of creation or modification of a word-processing file, or the author and the date and time of sending of an e-mail. The question is directed to the more extensive Metadata which may be relevant where for example authenticity is disputed.

Top added (Local-only) lines:

- • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • State the geographical location (if known). Consider (at least) servers, desktop PCs, laptops, notebooks, handheld devices, PDA devices, off-site storage, removable storage media (for example, CD-ROMs, DVDs, USB drives, memory sticks) and databases. • Consider all types of e-mail system (for example, Outlook, Lotus Notes, web-based accounts), whether stored on personal computers, portable devices or in web-based accounts (for example, Yahoo, Hotmail, Gmail). • For example, instant messaging, voicemail, VOIP (Voice Over Internet Protocol), recorded telephone lines, text messaging, audio files, video files. • State the geographical location (if known). Consider (at least) servers, desktops and laptops. • For example, .pdf. .tif, .jpg. • For example, Power Point or equivalent, specialist documents (such as CAD Drawings). • Where Keyword Searches are used in order to identify irrelevant documents which are to be excluded from disclosure (for example a confidential name of a client or customer), a general description of the type of search may be given. • See Practice Direction 31 B, which refers to the following matters which may be relevant: (a) the number of documents involved; (b) the nature and complexity of the proceedings; (c) the ease and expense of retrieval of any particular document; (d) the availability of documents or contents of documents from other sources; and (e) the significance of any document which is likely to be located during the search. • For example, back-ups, archives, off-site or outsourced document storage, documents created by former employees, documents stored in other jurisdictions, documents in foreign languages. • There is no requirement that you should obtain OCR versions of documents, and this question is directed only to OCR versions which you have available or expect to have available to you. If you do provide OCR versions to another party, they will be provided by you on an 'as is' basis, with no assurance to the other party that the OCR versions are complete or accurate. You may wish to exclude provision of OCR versions of documents which have been redacted. • Include names of all those who may have or have had custody of disclosable documents, including secretaries, personal assistants, former employees and/or former participants. It may be helpful to identify different dates for particular custodians. • 'Metadata' is information about the document or file which is recorded in the computer, such as the date and time of creation or modification of a word-processing file, or the author and the date and time of sending of an e-mail. The question is directed to the more extensive Metadata which may be relevant where for example authenticity is disputed.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 74A

- Impact: **LOW** (score 4)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Enforcement of Judgments in different Jurisdictions`
- local.updated: `2023-02-07T00:00:00Z`
- azure.updated: `2023-02-07T00:00:00Z`
- azure.id: `Practice_Direction_74A___Enforcement_of_Judgments_in_different_Jurisdictions`
- Signals: moderate-signal legal language changed, time-limit language changed
- Full-diff stats: removed=3, added=5, change.ratio=0.105

Top removed (Azure-only) lines:

- (2) registers of certificates issued for the enforcement in foreign countries of High Court judgments under the 1920, 1933 and 1982 Acts, and under article 13 of the 2005 Hague Convention;
- (3) section 1(2) of the 1933 Act, which limits enforcement under that Act to money judgments.
- (c) section 4 B of the 1982 Act;

Top added (Local-only) lines:

- (4) section 15 (1) of the 1982 Act, which limits enforcement under Part I of that Act to judgments within the meaning given by article 4(1) of the 2005 Hague Convention and article 3(1) of the 2019 Hague Convention.
- 7.7 In an application under section 12 of the 1982 Act relating to recognition and enforcement of a judgment under the 2019 Hague Convention, the certificate will be in the form recommended and published by the Hague Conference on Private International Law, which is available at:http://www.hcch.net/.
- (2) registers of certificates issued for the enforcement in foreign countries of High Court judgments under the 1920, 1933 and 1982 Acts, and under article 13 of the 2005 Hague Convention, article 12 of the 2019 Hague Convention;
- (3) section 1(2) of the 1933 Act, which limits enforcement under that Act to money judgments;
- (c) sections 4, 4 B and 4 C of the 1982 Act;

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 34A

- Impact: **LOW** (score 2)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Depositions and Court Attendance by Witnesses`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Practice_Direction_34A___Depositions_and_Court_Attendance_by_Witnesses`
- Signals: moderate-signal legal language changed
- Full-diff stats: removed=4, added=4, change.ratio=0.054

Top removed (Azure-only) lines:

- 6.3 An application under rule 34.17 must include or exhibit-
- 5.4 The above documents should be filed with the Foreign Process Section of the Royal Courts of Justice, by post to "Foreign Process Section Royal Courts of Justice, Strand London WC 2 A 2 LL" or left in person at the document drop box in the Main Hall of the Royal Courts of Justice marked for the attention of the Foreign Process Section.
- (1) apply to the Foreign Process Section at the Royal Courts of Justice atforeignprocess.rcj@justice.gov.ukfor the allocation of an examiner; alternatively engage a person who satisfies the criteria in CPR 34.8 (3) (a) or (c);
- 4.2 The party who obtains an order for the examination of a deponentbefore an examiner of the courtmust:

Top added (Local-only) lines:

- 4.2 The party who obtains an order for the examination of a deponent before an examiner of the court must:
- 6.3 An application under rule 34.17 must be filed with the Foreign Process Section at the Royal Courts of Justice and include or exhibit-
- (1) apply to the Foreign Process Section at the Royal Courts of Justice for the allocation of an examiner; alternatively engage a person who satisfies the criteria in CPR 34.8 (3) (a) or (c);
- 5.4 The above documents should be filed with the Foreign Process Section of the Royal Courts of Justice..

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 52E

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Appeals by way of case stated`
- local.updated: `2017-03-23T00:00:00Z`
- azure.updated: `2017-03-23T00:00:00Z`
- azure.id: `Practice_Direction_52E___Appeals_by_way_of_case_stated`
- Full-diff stats: removed=2, added=3, change.ratio=0.046

Top removed (Azure-only) lines:

- The procedure for applying to the Crown Court or a Magistrates' Court to have a case stated for the opinion of the High Court is set out in the Criminal Procedure Rules.
- SECTION II - CASE STATED BY CROWN COURT OR MAGISTRATES'COURT

Top added (Local-only) lines:

- The procedure for applying to the Crown Court or a Magistrates' Court to have a case stated for the opinion of the High Court differs according to whether the proceedings are criminal or civil. For criminal proceedings, the procedure is set out in the Criminal Procedure Rules. For civil proceedings, the procedure for applying to the Crown Court is set out in the Crown Court Rules 1982, and for applying to a magistrates' court, the Magistrates' Courts Rules 1981.
- SECTION II - CASE STATED BY CROWN COURT OR MAGISTRATES' COURT
- ---

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 53

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Media and Communications Claims`
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- azure.id: `Part_53___Media_and_Communications_Claims`
- Full-diff stats: removed=1, added=1, change.ratio=0.036

Top removed (Azure-only) lines:

- (3) A Media and Communications List Judge is a judge authorised by the President of the KIng's Bench Division, in consultation with the Chancellor of the High Court, to hear claims in the Media and Communications List.

Top added (Local-only) lines:

- (3) A Media and Communications List Judge is a judge authorised by the President of the King's Bench Division, in consultation with the Chancellor of the High Court, to hear claims in the Media and Communications List.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 16

- Impact: **LOW** (score 2)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Practice Direction 16`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Practice_Direction_16`
- Signals: moderate-signal legal language changed
- Full-diff stats: removed=0, added=6, change.ratio=0.028

Top added (Local-only) lines:

- A party who relies on a CMA breach decision (which has the same meaning as in section 102(5) of the Digital Markets, Competition and Consumers Act 2024), must state that in their statement of case, and must-
- indicate whether the CMA breach decision is final (in accordance with section 102(2) of the 2024 Act)
- Digital Markets, Competition and Consumers Act 2024 ("the 2024 Act")
- • identify the CMA breach decision; and
- 13 A.1
- ---

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 30

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Transfer`
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- azure.id: `Part_30___Transfer`
- Full-diff stats: removed=1, added=1, change.ratio=0.024

Top removed (Azure-only) lines:

- (1) This rule applies if, in any proceedings in the King's Bench Division, (other than proceedings in the Commercial or Admiralty Courts) a district registry of the High Court or a county court, a party's statement of case raises an issue relating to the application of of Chapter I or II of Part I of the Competition Act 19982.

Top added (Local-only) lines:

- (1) This rule applies if, in any proceedings in the King's Bench Division, (other than proceedings in the Commercial or Admiralty Courts) a district registry of the High Court or a county court, a party's statement of case raises an issue relating to the application of of Chapter I or II of Part I of the Competition Act 19982 or to a claim under section 101 of the Digital Markets, Competition and Consumers Act 2024.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 64B

- Impact: **LOW** (score 2)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Applications to the Court for Directions by Trustees in Relation to the Administration of the Trusts`
- local.updated: `2017-11-30T00:00:00Z`
- azure.updated: `2017-11-30T00:00:00Z`
- azure.id: `Practice_Direction_64B___Applications_to_the_Court_for_Directions_by_Trustees_in_Relation_to_the_Adm`
- Signals: moderate-signal legal language changed
- Full-diff stats: removed=1, added=1, change.ratio=0.022

Top removed (Azure-only) lines:

- The master or district judge may give the directions sought though, if the directions relate to actual or proposed litigation, only if it is a plain case, and therefore the master or district judge may think it appropriate to give the directions without a hearing: see Practice Direction 2 B, para 4.1 and para. 5.1(e), and see also paragraph 6 above. Otherwise the case will be referred to the judge.

Top added (Local-only) lines:

- A Master may give the directions sought, whether at a hearing or on paper pursuant to paragraph 6. They will ordinarily do so, but may refer the matter to a High Court Judge if they consider it appropriate. District Judges may give the directions sought only with the consent of their Supervising Judge or their nominee (see PD 2 B para. 7 B.2(c)).

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 41A

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Provisional Damages`
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- azure.id: `Practice_Direction_41A___Provisional_Damages`
- Full-diff stats: removed=1, added=1, change.ratio=0.019

Top removed (Azure-only) lines:

- (1) ensure that the case file documents are provided by the parties where necesary and filed on the court file,

Top added (Local-only) lines:

- (1) ensure that the case file documents are provided by the parties where necessary and filed on the court file,

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Part 65

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Proceedings Relating to Anti-Social Behaviour and Harassment`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Part_65___Proceedings_Relating_to_Anti-Social_Behaviour_and_Harassment_chunk_001`
- Full-diff stats: removed=2, added=2, change.ratio=0.019

Top removed (Azure-only) lines:

- (3) In this Section 'the 2006 Act'means the Police and Justice Act 2006. Applications under section 91(3) of the 2003 Act or section 27(3) of the 2006 Act for a power of arrest to be attached to any provision of an injunction
- (2) In this Section 'the 2003 Act'means the Anti-social Behaviour Act 2003.

Top added (Local-only) lines:

- (3) In this Section 'the 2006 Act' means the Police and Justice Act 2006. Applications under section 91(3) of the 2003 Act or section 27(3) of the 2006 Act for a power of arrest to be attached to any provision of an injunction
- (2) In this Section 'the 2003 Act' means the Anti-social Behaviour Act 2003.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 27A

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Small Claims Track`
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- azure.id: `Practice_Direction_27A___Small_Claims_Track`
- Full-diff stats: removed=1, added=1, change.ratio=0.015

Top removed (Azure-only) lines:

- (2) He will normally do so orally at the hearing, but he may give them later at a hearing either orally or in writting.

Top added (Local-only) lines:

- (2) He will normally do so orally at the hearing, but he may give them later at a hearing either orally or in writing.

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

### Practice Direction 40B

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Judgments & Orders`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Practice_Direction_40B___Judgments___Orders`
- Full-diff stats: removed=1, added=1, change.ratio=0.014

Top removed (Azure-only) lines:

- (1) Unless the [claimant][defendant] serves his list of documents by 4.00 p.m. on Friday, January 22, 1999 his [claim][defence] will be struck out and judgment entered for the [defendent][claimant], or

Top added (Local-only) lines:

- (1) Unless the [claimant][defendant] serves his list of documents by 4.00 p.m. on Friday, January 22, 1999 his [claim][defence] will be struck out and judgment entered for the [defendant][claimant], or

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 46

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Costs Special Cases`
- local.updated: `2024-04-06T00:00:00Z`
- azure.updated: `2024-04-06T00:00:00Z`
- azure.id: `Practice_Direction_46___Costs_Special_Cases`
- Full-diff stats: removed=1, added=1, change.ratio=0.011

Top removed (Azure-only) lines:

- 3.4 The amount, which may be allowed to a self represented litigant under rule 46.5(4)(b), is £19 per hour.

Top added (Local-only) lines:

- 3.4 The amount, which may be allowed to a self represented litigant under rule 46.5(4)(b), is £24 per hour.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 57

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Practice Direction 57`
- local.updated: `2023-04-06T00:00:00Z`
- azure.updated: `2023-04-06T00:00:00Z`
- azure.id: `Practice_Direction_57`
- Full-diff stats: removed=1, added=1, change.ratio=0.010

Top removed (Azure-only) lines:

- (4) any facts which might affect the exercise of the court"s powers under the Act.

Top added (Local-only) lines:

- (4) any facts which might affect the exercise of the court's powers under the Act.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Practice Direction 63

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Practice Direction 63`
- local.updated: `2020-10-01T00:00:00Z`
- azure.updated: `2020-10-01T00:00:00Z`
- azure.id: `Practice_Direction_63`
- Full-diff stats: removed=1, added=1, change.ratio=0.007

Top removed (Azure-only) lines:

- (5) experts'reports;

Top added (Local-only) lines:

- (5) experts' reports;

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 62

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Arbitration Claims`
- local.updated: `2022-10-01T00:00:00Z`
- azure.updated: `2022-10-01T00:00:00Z`
- azure.id: `Part_62___Arbitration_Claims`
- Full-diff stats: removed=1, added=1, change.ratio=0.007

Top removed (Azure-only) lines:

- (a) the preliminary question of whether the court is satisfied of the matters set out in section 45(2)(b); or

Top added (Local-only) lines:

- (a) Omitted

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 80

- Impact: **LOW** (score 2)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Proceedings under the Terrorism Prevention and Investigation Measures Act 2011`
- local.updated: `2017-01-30T00:00:00Z`
- azure.updated: `2017-01-30T00:00:00Z`
- azure.id: `Part_80___Proceedings_under_the_Terrorism_Prevention_and_Investigation_Measures_Act_2011`
- Signals: service/notice mechanics changed
- Full-diff stats: removed=1, added=1, change.ratio=0.006

Top removed (Azure-only) lines:

- (c) rule 52.13 (responden's notice); and

Top added (Local-only) lines:

- (c) rule 52.13 (respondent's notice); and

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 79

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): mixed_or_inconclusive
- sourcepage: `Proceedings under the counter-terrorism act 2008, part 1 of the terrorist asset-freezing etc. act 2010 and part 1 of the sanctions and anti-money laundering act 2018`
- local.updated: `2021-09-06T00:00:00Z`
- azure.updated: `2021-09-06T00:00:00Z`
- azure.id: `Part_79___Proceedings_under_the_counter-terrorism_act_2008__part_1_of_the_terrorist_asset-freezing_e`
- Full-diff stats: removed=1, added=1, change.ratio=0.005

Top removed (Azure-only) lines:

- (i) 'specially represented party'means a party, other than tthe appropriate Minister, whose interests a special advocate represents.

Top added (Local-only) lines:

- (i) 'specially represented party' means a party, other than the appropriate Minister, whose interests a special advocate represents.

Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.

### Part 46

- Impact: **LOW** (score 0)
- Cause (live-HTML heuristic): website_changed (live matches local)
- sourcepage: `Costs special cases`
- local.updated: `2023-10-01T00:00:00Z`
- azure.updated: `2023-10-01T00:00:00Z`
- azure.id: `Part_46___Costs_special_cases`
- Full-diff stats: removed=0, added=1, change.ratio=0.003

Top added (Local-only) lines:

- (3) Neither rule 19.4 nor rule 20.7 applies to the joinder of a person under paragraph (1).

Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.

## C. Missing in Azure (confirmed)

These have no matching `sourcefile` found in the Azure index (per verifier).

| sourcefile | sourcepage | local.updated |
|---|---|---:|
| Application for a Warrant under The Competition Act 1998 or Part 1 of the Digital Markets, Competition and Consumers Act 2024 | Application for a Warrant under The Competition Act 1998 or Part 1 of the Digital Markets, Competition and Consumers Act 2024 | 2023-06-08T00:00:00Z |
| Cyfarwyddyd Ymarfer 54A | Adolygiad Barnwrol | 2021-05-27T00:00:00Z |
| Cyfarwyddyd Ymarfer 54B | Ceisiadau Brys a Cheisiadau Eraill am Ryddhad Interim | 2021-05-27T00:00:00Z |
| Cyfarwyddyd Ymarfer 54C | Llys Gweinyddol (Lleoliad) | 2021-05-27T00:00:00Z |
| Cyfarwyddyd Ymarfer 54D | Hawliadau Llys Cynllunio | 2021-05-27T00:00:00Z |
| Devolution Issues and Crown Office Applications in Wales (Welsh) | Devolution Issues and Crown Office Applications in Wales (Welsh) | 2017-01-30T00:00:00Z |
| PRACTICE DIRECTION 5C | CE-File electronic filing and case management system | 2025-08-07T00:00:00Z |
| Part 48 | Part 2 of the Legal Aid, Sentencing and Punishment of Offenders Act 2012, elating to civil litigation funding and costs: transitional provision in relation to pre-commencement funding | 2017-01-30T00:00:00Z |
| Practice Direction 48 | Part 2 of the Legal Aid, Sentencing and Punishment of Offenders Act 2012, elating to civil litigation funding and costs: transitional provision and exceptions | 2017-01-30T00:00:00Z |

Recommended action: ingest/upload these into the Azure index (staging first if you have that workflow), then re-run the verifier.

