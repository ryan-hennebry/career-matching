# Project Profile: Job Search Agent (JSA)

## Project Type
type: cli-agent

## Tech Stack
stack: python/bash

## Test Layers
test-layers:
  - pytest (unit + integration)

## Verify Commands
verify-commands:
  unit: "pytest tests/ -v"
  lint: "ruff check ."
  type-check: "mypy . --ignore-missing-imports"

## Feedback Sources (what /analyze reads)
feedback-sources:
  - conversation-transcript

## Analysis Mode
analysis-mode: transcript
analysis-command: /analyze <path-to-transcript>

## Reviewer Personas
reviewer-personas:
  - architecture-strategist
  - code-simplicity-reviewer
  - regression-checker

## Build Readiness
build-readiness:
  - Code tests pass (pytest)
  - Agent runs without crash
  - Key workflows complete (search, verify, brief, deliver)
  - No regression items unaddressed

## Build Handoff Message
build-complete-message: "Build complete. Test the agent, then run `/analyze <transcript>` for session analysis."

## Notes
This is the original workflow. All commands default to this behavior when no profile is found.
