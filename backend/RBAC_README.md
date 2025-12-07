## RBAC in this Project – Human-Friendly Explanation

### 1. What is RBAC and why is it in this project?

**RBAC (Role-Based Access Control)** is a system that decides **“who is allowed to do what”** inside your application.

Think of the app as a company:
- **Users** are people (employees).
- **Roles** are job titles (GRC Admin, Auditor, Risk Owner, Incident User, etc.).
- **Permissions** are specific powers (can view all incidents, can create policies, can approve audits, can see analytics dashboards…).

Instead of hard‑coding rules in every screen (e.g. `if username == "admin"`), RBAC stores permissions in one place and checks them the same way everywhere.  
This makes the system:
- **Safer** – hard to forget a check.
- **Easier to change** – you can change a role’s powers without editing 100 files.
- **Easier to explain** – you can say “Audit Manager can do X, Y, Z” and see that in data.

#### Very simple example

Imagine three users:
- **Alice** – GRC Administrator
- **Bob** – Auditor
- **Charlie** – Incident User

And three actions:
- **A1: View all incidents**
- **A2: Approve an incident**
- **A3: See incident analytics dashboard**

With RBAC you define:
- Alice: A1 = allowed, A2 = allowed, A3 = allowed  
- Bob:   A1 = allowed, A2 = allowed, A3 = allowed  
- Charlie: A1 = allowed, A2 = not allowed, A3 = not allowed

When Charlie opens the “Approve Incident” page, the backend checks RBAC and says:
- “Charlie does **not** have ‘approve incident’ permission → return 403 Forbidden.”

The same rules are used everywhere (API, UI, reports). That is exactly what your RBAC code is trying to do.

---

### 2. How your current RBAC works (conceptual, not technical)

Your system has **one central RBAC record per user** (in the `RBAC` table).  
That record stores many **yes/no flags** like:
- `view_all_policy`, `create_policy`, `edit_policy`, `approve_policy`
- `view_all_compliance`, `create_compliance`, `edit_compliance`, …
- `view_all_incident`, `create_incident`, `edit_incident`, `assign_incident`, …
- `view_all_risk`, `create_risk`, …
- `view_audit_reports`, `assign_audit`, `conduct_audit`, `review_audit`, …
- `view_all_event`, `create_event`, `edit_event`, `event_performance_analytics`, …

In plain words:
- For every user, you store **a big list of switches**:
  - “Can this person see all incidents?” yes/no  
  - “Can this person create a policy?” yes/no  
  - “Can this person see risk analytics?” yes/no  
  - and so on.

When a request comes in (for example “GET /api/incidents/”), your RBAC flow does:
1. **Who is this?**  
   Read the user id from the JWT token or the session.
2. **Get the RBAC row** for that user.
3. **Look up the right switch** for that endpoint. For example:
   - For listing incidents → check `view_all_incident`.
   - For approving a policy → check `approve_policy`.
4. If the switch is **True** → allow the request.  
   If it is **False** → return a 403 “Access denied” error.

The same idea is used through:
- Decorators on views (for normal Django views).
- Permission classes (for DRF API views).
- Utility functions that map endpoint names to the right switches.

The frontend can also ask the backend:
- “Give me all permissions for this user” (your `/api/rbac/user-permissions/` endpoint).
- Then it hides or shows buttons/menus based on those permissions.

So in simple language:  
**Your RBAC is a big permissions matrix. Every API call first checks that matrix before doing anything important.**

---

### 3. What “production‑ready” RBAC usually looks like

When a company tests an RBAC system in a serious product, they typically expect:

- **Clear separation of concerns**
  - **Authentication**: “Who is this user?” (login, JWT, sessions).
  - **Authorization / RBAC**: “Is this user allowed to do this?”  
  Your code should not mix these too much.

- **Single way to identify the user in APIs**
  - For example: “All `/api/*` endpoints are authenticated with JWT tokens; every request has `request.user` set correctly.”
  - RBAC code then always gets the user id from one place (e.g. `request.user`), not by re‑parsing JWT in many different functions.

- **Consistent RBAC checks on every sensitive endpoint**
  - Every endpoint that reads or writes important data:
    - Uses an RBAC decorator, or
    - Uses a DRF permission class.
  - It is easy to answer: “Which permission controls this endpoint?”

- **Well‑defined permissions and roles**
  - A short list of **roles**: e.g. `GRC Admin`, `Audit Manager`, `Incident User`.
  - A clear list of **permissions**: e.g. `policy.view`, `policy.create`, `incident.view_all`, `incident.approve`, `incident.analytics`.
  - A documented mapping: “Role X has permissions A, B, C…”

- **Least privilege**
  - New users start with minimal permissions.
  - Powerful roles (admins) are rare and usually audited.

- **Object‑level and tenant‑level rules (optional but common)**
  - Not just “Can this user view incidents?” but “Can this user view **these** incidents?” (for their own company, their own department, their own tasks).

- **Logging and auditability**
  - Important allow/deny decisions are logged.
  - Admins can see “who accessed what” and “who changed which permissions”.

Your current design is already close on many points (centralized permissions, helpers, frontend integration), but you can still tighten it and make it easier to review.

---

### 4. Step‑by‑step: what to implement in your current product

Below is a practical checklist you can follow to move from “working” to “production‑grade”.

#### Step 1 – Use one standard way to get the current user

- **Goal**: RBAC should not care whether the user came from session or JWT; it just asks one function.
- **Action**:
  - In all RBAC-related code (decorators, permissions, views), call **only** a single helper (you already have `RBACUtils.get_user_id_from_request`).
  - Remove or stop using custom copies like `get_user_id_from_jwt` in `rbac/views.py` and decorators.
  - Make sure your authentication middleware / DRF authentication sets `request.user` correctly for JWT.

Result: every RBAC decision is based on the same reliable user identity.

#### Step 2 – Make sure every sensitive endpoint is protected

- **Goal**: No “forgotten” URL that bypasses RBAC.
- **Action**:
  - Go through your URL list (`backend/grc/urls.py`).
  - For each endpoint that:
    - Reads important data,
    - Changes something (create/edit/delete),
    - Exports data,
    - Runs an AI/upload/test function,
    decide:
    - “Which permission controls this?”
  - Then:
    - Add the correct **RBAC decorator** on the view, or
    - Add the correct **DRF permission class** on the view.

Result: an external tester will see that every important endpoint returns 403 when the user has no permission.

#### Step 3 – Clean and centralize permission names

- **Goal**: Avoid typos and confusion (“is it `view_all_incident` or `view_incident`?”).
- **Action**:
  - Create a small file (e.g. `rbac/constants.py`) with all permission codes:
    - `POLICY_VIEW = "view_all_policy"`, `INCIDENT_VIEW = "view_all_incident"`, etc.
  - Use these constants in:
    - Decorators (`@rbac_required(required_permission=POLICY_VIEW)`),
    - Permission classes,
    - Utility mappings.

Result: easier to maintain and easier for reviewers to understand the full permission set.

#### Step 4 – Simplify endpoint → permission mapping

- **Goal**: It should be obvious which permission each endpoint uses.
- **Action**:
  - Prefer **explicit declarations**:
    - e.g. `@rbac_required(required_permission='view_all_incident', endpoint_name='incident_list')`
  - Gradually shrink the big dictionary inside `RBACUtils.check_endpoint_permission` by:
    - Moving logic to per‑view decorators or per‑view permission classes.

Result: you don’t depend on fragile string names of functions; RBAC rules are closer to the view that uses them.

#### Step 5 – Describe roles and their permissions

- **Goal**: Business and testers can understand your RBAC without reading code.
- **Action**:
  - For each role (e.g. `GRC Administrator`, `Audit Manager`, `Incident User`):
    - List which permissions must be true on the RBAC row.
  - Store this as documentation (or even seed data) so it’s easy to load test users with different roles.

Result: the testing company can say “Log in as Audit Manager; verify these X actions work and Y actions are blocked.”

#### Step 6 – Plan object‑level and tenant‑level checks

- **Goal**: Users should only see data they are allowed to see (by company, BU, assignment, etc.).
- **Action**:
  - For each module (Policy, Risk, Incident, etc.), decide:
    - Do we need per‑tenant filters?
    - Do we need “owner” vs “reviewer” logic?
  - Add filters in the queries (for example: `Incident.objects.filter(organisation=user.organisation)`).
  - Keep RBAC for “can do this type of action?” and use filters for “on which records?”.

Result: RBAC becomes one layer in a more complete security story.

#### Step 7 – Improve logging and auditing

- **Goal**: You can prove that the system is being used correctly.
- **Action**:
  - Turn on key log lines (without flooding the logs).
  - Optionally add an `AuditLog` model that records:
    - user, action, resource, allowed/denied, timestamp.

Result: if something goes wrong, you can trace which user had which permissions and what they tried to do.

---

### 5. Incident module – how RBAC works there today (conceptual)

The **Incident module** in your RBAC behaves as follows:

- In the RBAC table, you have incident‑related flags such as:
  - `view_all_incident` – can view incidents.
  - `create_incident` – can create new incidents.
  - `edit_incident` – can update incident details or status.
  - `assign_incident` – can assign incidents to users.
  - `evaluate_assigned_incident` – can review/approve incidents assigned to them.
  - `escalate_to_risk` – can turn an incident into a risk.
  - `incident_performance_analytics` – can see incident dashboards/KPIs.

- When an Incident API is called (for example: “list all incidents” or “assign an incident”):
  1. RBAC finds the user id from the request.
  2. It loads that user’s RBAC record.
  3. It checks the right flag:
     - Listing incidents → `view_all_incident`.
     - Creating an incident → `create_incident`.
     - Assigning an incident → `assign_incident`.
     - Viewing dashboards → `incident_performance_analytics`.
  4. If the flag is `True`, the user is allowed; if `False`, they get 403 Forbidden.

- In words:
  - **“Incident Viewer”** profile: has `view_all_incident = True`, everything else incident‑related False.
  - **“Incident Manager”** profile: has `view_all_incident`, `create_incident`, `edit_incident`, `assign_incident`, maybe `evaluate_assigned_incident`.
  - **“Risk & Incident Analyst”** profile: has `incident_performance_analytics` and probably some view permissions.

For a tester, this means:
- They can log in as different users (with different RBAC rows).
- They should see:
  - Incident lists, assignment, approval buttons, analytics pages either **visible and working** (if the flag is True)  
  - Or **hidden / blocked with 403** (if the flag is False).

In the next step (after this document), you can tighten the Incident module by:
- Ensuring every incident endpoint in `urls.py` uses the right RBAC decorator or permission class.
- Adding any missing mappings for new incident endpoints to your RBAC utilities.


