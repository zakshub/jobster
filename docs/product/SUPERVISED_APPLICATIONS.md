# Supervised Applications

## Purpose

Jobster can prepare a real application while Zak remains responsible for the
final website Submit action or Gmail Send action.

## Visible browser review

`Fill & review` starts a visible local Chromium session with a private reusable
profile. Jobster follows a clear application link, fills approved answers,
uploads the configured resume, advances through safe intermediate steps, and
stops before final submission.

The session remains open when it encounters:

1. LinkedIn Easy Apply.
2. Login or account creation.
3. Google, Microsoft, or LinkedIn sign-in.
4. Email verification, OTP, or two-factor authentication.
5. CAPTCHA.
6. Unknown required questions.
7. Multiple or ambiguous Apply controls.
8. Assessments, video responses, or unsupported widgets.
9. A final review or Submit control.

After Zak completes the required human step, `Continue filling` resumes the
same session. Existing values are preserved so a manual correction is never
silently overwritten. After Zak submits, `Check submission` records Submitted
only when the website exposes a recognized confirmation.

LinkedIn Easy Apply remains manual. For a normal LinkedIn Apply action that
opens an employer or ATS site, Jobster continues on the external site when the
route is unambiguous.

## Apply by email

Jobster recognizes explicit `mailto:` application instructions. It uses the
recipient stated by the employer, generates a contextual application email
from CareerBrain evidence, attaches the configured approved PDF or DOCX resume,
and saves a Gmail draft. It never guesses a recipient and exposes no Gmail Send
operation.

Gmail setup requires:

1. A Google OAuth client JSON at `private_data/gmail_client_secret.json`.
2. `application.resume_path` pointing to an approved PDF or DOCX.
3. The one-time Gmail connection opened from Jobster.

The OAuth token is saved in `private_data/gmail_token.json`; both files remain
outside Git. The requested OAuth scope is `gmail.compose` because Gmail requires
it for draft creation. Jobster still implements draft creation only.

## Operating boundary

The first release runs on the Windows computer hosting Jobster. VPS remote
browser viewing is a later capability. Only one visible review session runs at
a time to prevent applications or browser identities from being mixed.
