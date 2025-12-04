---
description: AI rules derived by SpecStory from the project AI interaction history
globs: *
---

## HEADERS

## PROJECT RULES

## CODING STANDARDS

## WORKFLOW & RELEASE RULES
- Before starting work on a new feature or bug fix, always perform a `git pull` to update your local workspace.
- Switch to a dedicated branch for your changes.
- After the vector DB is functional and tested, the branch can be uploaded and merged.
- It is recommended to have separate `requirements.txt` files for each component (backend, frontend, telegram-bot) in a multi-component project.

## TECH STACK
- Qdrant (for vector database)
- sentence-transformers (for embeddings)
- pandas
- numpy
- fastapi
- uvicorn[standard]
- langchain
- langchain-community
- python-dotenv
- tqdm

## PROJECT DOCUMENTATION & CONTEXT SYSTEM

## DEBUGGING

## REFERENCES