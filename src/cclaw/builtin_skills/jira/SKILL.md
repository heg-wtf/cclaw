# Jira

Jira issue management via MCP. Search, create, update, and transition issues.

## Prerequisites

- uv installed (`uvx` available)
- Atlassian Cloud account with Jira access
- API token generated from Atlassian account settings

## Setup Guide

1. Go to Atlassian API Token page (https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token" and save the token
3. Note your Jira instance URL (e.g., `https://your-company.atlassian.net`)
4. Run `cclaw skills setup jira` to enter:
   - `JIRA_URL`: Your Jira instance URL
   - `JIRA_USERNAME`: Your Atlassian account email
   - `JIRA_API_TOKEN`: The API token you created

## Safety Rules

- **Always show issue details before creating.** Show project, type, summary, and description, then ask for confirmation.
- **Always confirm before transitioning issues.** Show the current status, target status, and issue key before changing workflow state.
- **Never bulk-modify issues without explicit approval.** When asked to update multiple issues, list them first and confirm.
- **Never delete issues.** Jira issues should be closed or moved, not deleted. If deletion is requested, explain this policy and suggest closing instead.
- When updating an issue, show the fields being changed and ask for confirmation.

## Available Operations

### Search Issues (jira_search)

Search issues using JQL (Jira Query Language).

- Common JQL queries:
  - `project = PROJ` - All issues in a project
  - `assignee = currentUser()` - My issues
  - `status = "In Progress"` - Issues in progress
  - `priority = High AND status != Done` - High priority open issues
  - `created >= -7d` - Created in the last 7 days
  - `text ~ "keyword"` - Full text search
  - `sprint in openSprints()` - Current sprint issues
- Present results in a readable list format (key, summary, status, assignee)

### Get Issue Details (jira_get_issue)

Get detailed information about a specific issue.

- Provide the issue key (e.g., `PROJ-123`)
- Shows summary, description, status, assignee, priority, labels, comments
- Useful for understanding context before updates

### Create Issue (jira_create_issue)

Create a new Jira issue.

- Required: project key, issue type, summary
- Optional: description, assignee, priority, labels, components
- Always show the full issue details and confirm before creating
- Common issue types: Bug, Task, Story, Epic

### Update Issue (jira_update_issue)

Update fields on an existing issue.

- Provide the issue key and fields to update
- Can update: summary, description, assignee, priority, labels, components
- Always show what will change and confirm before updating

### Transition Issue (jira_transition_issue)

Change the workflow status of an issue.

- Provide the issue key and target status
- Common transitions: To Do -> In Progress -> In Review -> Done
- Always show current status and target status before transitioning

## Usage Guidelines

- When searching, use specific JQL to narrow results. Avoid overly broad queries.
- Present issue lists with key information: issue key, summary, status, assignee.
- When the user mentions an issue by key (e.g., "PROJ-123"), fetch details first before acting.
- For status updates, verify the transition is valid (available transitions depend on workflow).
- When creating issues, ask for at least the project and summary if not provided.
- Use Korean for all responses to the user, but keep JQL and issue fields in English.
