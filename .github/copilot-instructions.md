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
- It is recommended to have separate `requirements.txt` files for each component (backend, frontend, telegram-bot) in a multi-component project like this.
- Exclude large data files, `.specstory/` directories, and vector database storage from commits by adding them to the `.gitignore` file.
- Per project README, PRs should target `develop` (not `main`).
- Create a PR: `feature/vector-db-setup` → `develop`
  - Title suggestion: `feat: vector DB setup (Qdrant + sentence-transformers)`
  - Include a brief summary:
    - Scripts to build and verify vector DB
    - Persistent storage in `backend/qdrant_storage` (gitignored)
    - Docs and backend requirements
    - Tested semantic search on full DB successfully

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
- Data sources include:
  - Google Books Dataset
  - Books Dataset
  - Goodreads 100k books
  - CMU Books Summary Dataset
- EDA and preprocessing details are documented separately.
- Preprocessing steps:
  - Tables were unified to a common format with the following columns:
    - title: title of the work
    - author: author(s) of the work
    - description: description of the work
    - page_count: number of pages in the book
    - publication_date: date of publication of the book
  - Missing values were handled using:
    - Google Books API to retrieve missing data
    - (Failed attempt) LLM generation of descriptions
  - Rows with missing title, author, or description after attempting to fill them were removed.
  - Author column was preprocessed to standardize formatting.
- The final dataset contains 174467 rows in a unified format.
- A vector database was created for the RAG system using Qdrant. All 174467 books were converted into embeddings using sentence-transformers (model all-MiniLM-L6-v2, 384 dimensions). The database is stored locally and is ready for semantic search and recommendation generation.
- Data sources (summarized):
  - Google Books Dataset
  - Books Dataset
  - Goodreads 100k books
  - CMU Books Summary Dataset
- EDA and preprocessing details are documented separately.
- Preprocessing:
  - Tables unified to a common format with columns:
    - title: title of the work
    - author: author(s) of the work
    - description: description of the work
    - page_count: number of pages in the book
    - publication_date: date of publication of the book
  - Missing values handled:
    - Google Books API was used to retrieve missing data
    - (Failed) LLM generation of descriptions
  - Rows with missing title, author, or description were removed.
  - Author column was preprocessed for standardization.
- The final dataset contains 174467 rows in a unified format.
- A vector database was created for the RAG system using Qdrant. All 174467 books were converted into embeddings using sentence-transformers (model all-MiniLM-L6-v2, 384 dimensions). The database is stored locally and is ready for semantic search and recommendation generation.
- For the RAG system, a vector database was created using Qdrant. All 174467 books were converted into embeddings using sentence-transformers (model all-MiniLM-L6-v2, 384 dimensions). The database is stored locally and is ready for semantic search and recommendation generation.

## DEBUGGING

## REFERENCES