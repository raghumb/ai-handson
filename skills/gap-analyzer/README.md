
# Gap Analyzer
Reusable skill which can analyze the requirements and ask follow-up questions to disambiguate assumptions, open ended/vauge points and bring clarify before implementation.


# How to deploy this skill (Works with Codex/Claude)
- Create a new folder 'gap-analyzer in your agent's skills directory. (You can createt this globally or in your project root)
- Copy the SKILL.md file into that folder

your-project-root/
└── .claude/
    └── skills/
        └── gap-analyzer/
            └── SKILL.md

# How to use this skill
Use the skill invocation command ('slash') and provide your requirements
eg. /gap-analyzer 'Build me a tax calculator service to calculate tax such that if revenue R > X, then tax = (R-X)/30, otherwise tax = X/20. X is a threshold value.

