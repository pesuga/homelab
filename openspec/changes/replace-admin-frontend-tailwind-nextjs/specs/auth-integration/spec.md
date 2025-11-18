## ADDED Requirements
### Requirement: Integrate authentication against existing backend
- The frontend SHALL authenticate users via the backend login API and store a session token.
#### Scenario: Integrate authentication against existing backend
- **WHEN** the user submits login credentials to the backend
- **THEN** a session token is stored and the user is authenticated for subsequent requests

### Requirement: Token refresh and logout
- The frontend SHALL refresh/clear tokens per backend support; logout clears locally stored tokens
#### Scenario: Token refresh and logout
- **WHEN** the backend provides a refresh token and the user initiates logout
- **THEN** the token is refreshed or cleared and the user is redirected to the login page
