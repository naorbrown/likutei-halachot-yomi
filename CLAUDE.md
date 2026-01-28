# Likutei Halachot Yomi - Claude Code Instructions

## Project Overview
Daily Likutei Halachot from Reb Noson of Breslov, delivered to Telegram. Uses Ralph Wiggum technique for iterative development.

## Tech Stack
- Python with type hints (mypy strict mode)
- - GitHub Actions for scheduling
  - - Telegram Bot API
    - - pytest for testing
     
      - ## Development Workflow
     
      - ### Using Ralph Wiggum Loop
      - ```bash
        # Simple task
        ./ralph.sh "Your task description. Output COMPLETE when done." --max-iterations 20

        # Using a prompt file
        ./ralph.sh --prompt-file prompts/feature.md --verbose

        # With specific model
        ./ralph.sh --model opus "Complex task requiring deeper reasoning"
        ```

        ### Completion Signals
        - `<promise>COMPLETE</promise>` - Task finished successfully
        - - `<promise>BLOCKED</promise>` - Stuck, needs human input
         
          - ## Code Standards
          - - All Python code must pass mypy strict mode
            - - Tests required for new functionality
              - - Follow existing patterns in src/
               
                - ## Key Files
                - - `src/` - Main application code
                  - - `data/` - Halachot content and mappings
                    - - `scripts/` - Utility scripts
                      - - `tests/` - Test files
                        - - `.github/workflows/` - CI/CD pipelines
