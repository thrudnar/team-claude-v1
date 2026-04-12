# ERD — team.db (Job Hunting Schema)

Last updated: 2026-04-02 (added applications.source; backfilled job_id for 27 active applications; jobs.status enum changed to new/scored/skip/duplicate; added jobs.archived)

---

## jobs
- PK  id
-     job_board
-     job_id
-     company
-     job_title
-     location
-     work_type
-     job_url
-     description_text
-     source_collection
-     source_email_id
-     is_new
-     status  (new | scored | skip | duplicate)
-     apply_flag
-     archived  (0=visible, 1=soft-deleted)
-     first_date_seen
-     most_recent_date_seen
-     created_at

## job_scores
- PK  id
- FK  job_id → jobs.id
-     score_version
-     overall_score
-     skills_score
-     seniority_score
-     work_type_score
-     work_arrangement
-     salary_range
-     match_summary
-     strengths
-     gaps
-     recommendation
-     reasoning
-     cover_letter
-     resume_customizations
-     scored_at

## score_tests
- PK  id
- FK  job_id → jobs.id
-     prompt_version
-     model
-     overall_score
-     skills_score
-     seniority_score
-     work_type_score
-     work_arrangement
-     salary_range
-     match_summary
-     strengths
-     gaps
-     recommendation
-     reasoning
-     scored_at

## score_prompts
- PK  id
-     version
-     model
-     system_prompt
-     user_prompt_template
-     cover_letter_threshold
-     notes
-     created_at

## applications
- PK  id
- FK  job_id → jobs.id
-     status
-     apply_date
-     company
-     job_title
-     job_board
-     board_job_id
-     match_assessment
-     application_link
-     salary_range_top
-     salary_range_source
-     resume_link
-     contact
-     notes
-     cover_letter
-     source
-     created_at
-     updated_at

## application_responses
- PK  id
- FK  application_id → applications.id
-     sequence
-     question
-     response

## cover_letter_prompts
- PK  id
-     version
-     model
-     system_prompt
-     user_prompt_template
-     notes
-     created_at

## interesting_companies
- PK  id
-     list_source
-     name
-     description
-     my_interest_drivers
-     my_apprehensions
-     my_interest_level
-     size
-     round
-     sector
-     culture
-     purpose_impact
-     evilness
-     tech_centric
-     up_or_out
-     why
-     who_i_know
-     careers_url
-     created_at

## gmail_events
- PK  id
- FK  application_id → applications.id
-     gmail_message_id
-     company
-     subject
-     received_at
-     characterization
-     action_taken
-     processed_at
