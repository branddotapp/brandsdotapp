# App legal/support page templates
Per client app: copy this folder to `/app-legal/<brand>/`, replace every `{{PLACEHOLDER}}`, check with `rg '\{\{' app-legal/<brand>`.
- `support.html` → App Store Support URL / Play contact website
- `delete-account.html` → Google Play Data safety "account deletion URL" (required) and in-app link
- Privacy policy stays on the brand's own site (see appyco-app/docs/PRIVACY_POLICY_APP_ADDENDUM.md for what to add).
Pages are `noindex`. The `_template` folder itself is not linked anywhere.
