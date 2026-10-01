# FINTRACK

A self-hosted, containerized personal expense tracker built using open-source tools and a DevOps workflow.

## Problem Statement

Managing daily expenses manually can make it difficult to track spending and understand where money is being used.

FinTrack provides a simple self-hosted web application where users can add, view, and delete expenses while seeing their total spending.

## Project Objectives

- Track personal expenses digitally
- Store expense data in a PostgreSQL database
- Provide a simple web-based interface
- Use a Flask REST API for backend operations
- Containerize the application using Docker
- Use Docker Compose to manage multiple containers
- Demonstrate Git and GitHub version control
- Follow a reproducible open-source development workflow

## Architecture

FinTrack uses a three-container architecture:

```text
                USER
                  |
                  v
        +-------------------+
        | Frontend Container |
        |   HTML/CSS/JS      |
        |      Nginx         |
        |     Port 8080      |
        +---------+---------+
                  |
                  v
        +-------------------+
        | Backend Container |
        | Python + Flask API|
        |     Port 5000     |
        +---------+---------+
                  |
                  v
        +-------------------+
        | Database Container|
        |    PostgreSQL     |
        |     Port 5432     |
        +-------------------+