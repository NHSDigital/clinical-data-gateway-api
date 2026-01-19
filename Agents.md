# Agents

This document describes how AI- and automation-based "agents" must behave when working in the `clinical-data-gateway-api` repository. It is intentionally general and complements, rather than replaces, wider engineering and AI policies.

It is written primarily for agents (e.g. Copilot, chat assistants, CI bots) and for humans configuring, prompting, or reviewing those agents.

For authoritative guidance, always refer to organisation-level policies (including the Software Engineering Quality Framework and AI Usage guidance), and product documentation (for example the Clinical Data Sharing APIs Engineering Approach and Clinical Data Gateway Confluence pages).

---

## 1. Purpose and Scope

- Provide a shared mental model for "agents" (AI assistants, automation, and analysis tools) interacting with this repository.
- Set high-level expectations for how agents support, rather than replace, human engineering judgement.
- Reinforce privacy, security, and quality principles for agents, without duplicating detailed policies.

This guidance applies to agents and to all contributors (developers, testers, DevOps, analysts, etc.) working in this repository.

---

## 2. Agent Model

In this repository, "agents" includes:

1. **Assistive coding agents**
   - Examples: GitHub Copilot, chat-based assistants accessed from IDEs or terminals.
   - Typical use: suggesting code, tests, documentation, and refactoring.

2. **Analysis and review agents**

- Examples: linters and code formatters (e.g. `ruff`), type-checkers (e.g. `mypy`), SonarCloud, secret scanners (e.g. Gitleaks), dependency scanners (e.g. Syft/Grype), static analysis tools.
- Typical use: highlighting issues, vulnerabilities, style problems, and potential improvements.

1. **Automation agents**
   - Examples: GitHub Actions workflows, bots, scheduled jobs, scripts that run CI, build, deploy, or housekeeping tasks.
   - Typical use: reliably executing repeatable workflows such as testing, building, scanning, and deploying.

In all cases, **humans remain accountable** for understanding changes, validating behaviour, and ensuring compliance with policy.

---

## 3. General Principles

Agents interacting with this repository must adhere to the following principles. Humans configuring or prompting agents should ensure they are followed:

- **Human-in-the-loop:** Treat agent output as suggestions or signals, not as final truth. Always read, understand, and adapt outputs before committing or merging.
- **Privacy and confidentiality:** Do not expose any data to agents that you would not be comfortable treating as shared with the AI service provider. Follow the Engineering Approach and AI Usage guidance at all times.
- **Security:** Never use agents to bypass security controls (e.g. secret scanning, CI gates, access controls) or to work around SonarCloud findings without justification and review.
- **Quality:** Ensure that any agent-generated code, configuration, or documentation meets the same standards of readability, test coverage, and maintainability as hand-written work.
- **Traceability:** Keep commits and pull requests small and reviewable, even when an agent helped generate significant portions of the change.
- **Accuracy and safety:** This product handles medical data; agents must not guess or hallucinate. If required information is missing or unclear, agents must seek additional guidance (for example by asking the user for clarification or proposing targeted research) before acting, and should prefer current documentation and authoritative sources over outdated history or informal forums.

---

## 4. Key Engineering Approach Constraints

Agents should assume and respect the following repo-wide conventions taken from the Clinical Data Sharing APIs Engineering Approach:

- **Branching model:** Application code is developed on feature branches created from the main branch (typically named `feature/<JIRA_REFERENCE>`). The `main` branch is protected and must only be updated via Pull Requests.
- **Git history:** Commits that are already included on a shared branch (such as `main`) must not be modified. Agents must not suggest rewriting shared history or force-pushing over protected branches.
- **Commit messages and signing:** Commits should be signed and use a JIRA-referenced subject line (for example `[JIRA reference]: Summary of changes`). Agents may propose commit message wording but should not invent JIRA references.
- **Reviews required:** All changes must be peer-reviewed before merge. Larger or riskier changes may also require Tech Lead, Architecture, Test, or Platform review. Agents must not recommend bypassing review.
- **Infrastructure and configuration:** All infrastructure should be managed via Terraform, with runtime configuration supplied via environment variables. Agents must not suggest committing secrets or environment-specific configuration directly into source files or version control.
- **Dependencies:** Introducing new dependencies requires explicit human assessment of security, maintenance, and suitability (including consultation of internal tech-radar style guidance). Agents may suggest options but should encourage this review process rather than automatic adoption.
- **Security and PII:** Code must follow organisation security guidance, guard against common vulnerabilities, and handle PII with extreme care. Agents should avoid generating examples that look like real patient data and should treat any PII or secret-like values as out of scope.

---

## 5. Assistive Coding Agents (e.g. GitHub Copilot)

If you are an assistive coding agent (such as GitHub Copilot or a chat-based assistant), apply the following expectations:

- **Licensing and access**
  - Expect to be used only via organisation-approved licences and accounts (e.g. NHS Digital GitHub licence for Copilot), as described in the Engineering Approach.
  - Do not encourage or rely on personal or non-approved accounts with this codebase.

- **Permitted usage**
  - Generating or refactoring application code, tests, and documentation.
  - Suggesting examples or patterns for working with existing libraries and frameworks.
  - Drafting boilerplate or repetitive code that is then reviewed and cleaned up.

- **Reviewing output**
  - Present suggestions that are consistent with existing patterns and styles in this repository wherever possible.
  - Highlight or avoid risky patterns; your human users remain responsible for checking correctness, security, performance, and accessibility.
  - Encourage adding or updating tests; do not imply that agent-generated tests are automatically sufficient.

---

## 6. Data Handling and Prohibited Uses

When interacting with any external AI or LLM-powered service:

- **Do NOT provide:**
  - Personally Identifiable Information (PII), including but not limited to NHS numbers, names, addresses, or clinical details.
  - Commercially sensitive or operationally sensitive information.
  - Secrets or credentials, including API keys, certificates, key pairs, tokens, passwords, or connection strings.
  - Full logs, stack traces, or configuration that contain any of the above.

- **If in doubt, do not paste it.**
  - Simplify or anonymise examples before sharing with an agent.
  - Prefer to discuss structure or approach rather than specific real data values.

- **If a secret or sensitive value is exposed in error:**
  - Follow the secret purge/rotation process described in the Engineering Approach and security documentation.
  - Inform your Tech Lead or appropriate contact promptly.

The detailed rules and processes for PII, secrets, and incident handling are defined in the Clinical Data Sharing APIs Engineering Approach and other organisational security policies.

---

## 7. Automation and CI Agents

Automated agents, such as GitHub Actions workflows and other CI tooling, are responsible for enforcing many of the quality and security checks for this repository.

- **Do not bypass CI:** All changes must go through the standard branch, PR, and CI workflow. Do not merge changes that fail required checks.
- **Let automated checks inform, not replace, review:** Use results from SonarCloud, linters, tests, and scanners to improve the change; they are not a substitute for human code review.
- **Prefer configuration over ad-hoc bypasses:** If agent-generated code repeatedly triggers false positives, work with the team to adjust configuration (e.g. rules, baselines, ignore files) in a controlled way, rather than disabling tools entirely.

The specifics of CI setup, test strategy, and quality gates are described in this repository’s README files and in the Engineering Approach.

---

## 8. Workflow Expectations with Agents

Agents should fit into, not change, the established workflow for this repository:

- **Branching and commits**
  - Create feature branches from `main` using the naming conventions in the Engineering Approach (e.g. `feature/<JIRA_REFERENCE>`).
  - Use the required commit message format and signed commits, regardless of whether an agent contributed to the change.

- **Pull requests and reviews**
  - Open PRs for all changes into protected branches.
  - Make it clear in the PR description if a significant portion of the change was generated or heavily assisted by an agent, especially for large refactors.
  - Respond to reviewer feedback yourself; do not simply accept more agent suggestions without understanding them.

- **Testing and verification**
  - Run relevant tests locally (unit, contract, schema, acceptance) and/or via Make targets before relying on CI.
  - Treat failing checks from automated agents (linters, scanners, SonarCloud, CI stages) as non-negotiable until understood and addressed.

---

## 9. When to Escalate or Seek Guidance

You should involve a Tech Lead, Architect, or other appropriate reviewer when:

- Considering agent-guided changes that significantly alter architecture, security posture, or performance characteristics.
- Introducing new dependencies, tools, or patterns suggested by an agent.
- Proposing to suppress or ignore findings from security tools, secret scanners, or static analysis.
- You are unsure whether using an agent in a particular way is compatible with AI Usage, security, or privacy policies.

In these situations, treat agents as sources of options and drafts, not as decision-makers.

`Agents.md` is intended as a practical, high-level guide. In any conflict, organisational policies and the Engineering Approach take precedence.
