-- Seed Data for Bug Reproducer Assistant

INSERT INTO issues (id, source, source_id, repository_url, title, body, raw_logs)
VALUES 
(
    'a0000000-0000-0000-0000-000000000001',
    'github',
    'GH-409',
    'https://github.com/acme/user-service',
    'Auth token generator throws KeyNotFound exception when scope is empty array',
    'When requesting a JWT token with scope=[] in POST /v1/auth/token, the auth service crashes with KeyError: default_scope instead of issuing a scope-less token.',
    'Traceback (most recent call last):\n  File "services/token.py", line 88, in generate_jwt\n    scope_val = scopes[0] if len(scopes)>0 else config["default_scope"]\nKeyError: "default_scope"'
),
(
    'a0000000-0000-0000-0000-000000000002',
    'jira',
    'BUG-902',
    'https://github.com/acme/web-frontend',
    'Hydration mismatch error on UserProfile Header component after upgrade',
    'After upgrading to Next.js 14, rendering the UserProfile Header component throws hydration warning in browser console when client side date formatting runs.',
    'Error: Text content does not match server-rendered HTML.\nServer: "2026-07-28T06:00:00Z" Client: "7/28/2026, 11:30:00 AM"\n  at div\n  at UserProfileHeader (components/Header.tsx:18)'
);
