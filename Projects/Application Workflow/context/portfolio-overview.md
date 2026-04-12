# Job Hunting Portfolio — Owner's Overview

*Captured verbatim from owner on 2026-03-31. This is the authoritative context for all four projects.*

---

The overall portfolio is about job hunting. The owner is looking for a new job and has used Claude and spreadsheets in a variety of ways already. This team is the right approach to consolidate those efforts. There are 4 distinct projects, listed in the order they should be taken on:

## 1. Job Listing Harvester
Will need to scrape and parse emails and websites from a handful of sources, starting with LinkedIn. The output will be rows in a cross-project DB schema — one row per job with the source (e.g. LinkedIn) and their job ID number as the unique identifier.

## 2. Job Description Match Score
Will look at the content of the job description for each job listing and compare it to context of the owner's experience, skills, expertise, and preferences. Will return scores about the level of match, comments about the quality of fit, etc. The prompt for this matching will probably evolve. Scoring feedback will be stored in the database as additional columns on the job listing table. State must be managed so each listing is only scored once.

## 3. Application Workflow
Mostly about record keeping on the job application workflow. Apps may be a separate table from Jobs.

## 4. Gmail Monitoring
A smart email filter, powered by a DB and some AI. Should frequently evaluate incoming mail on a low-volume email account, check if each new message is from a company with an active application, characterize the email contents and, in some cases, alert the owner or modify Gmail tags.

---

*Overlaps between projects are managed in the database. Work product from one project is used as input for another via well-managed state. Projects are kept separate to allow specialized agent skills and limit heavy background context to only the project(s) that require it.*
