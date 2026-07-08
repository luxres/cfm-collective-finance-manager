# Ledger — README

`ledger` is a bookkeeping app for organizations that have a "collective"
structure — typically a *Verein* (non-profit association) with several
sub-groups, events, and a mix of cash and bank accounts. It provides
double-entry accounts and transactions, a receipt/document workflow
(including a "scan this QR code with your phone" upload flow), fixed-asset
depreciation tracking, and a German EÜR tax export.

For how the *code* is organized (pages vs. HTMX fragments vs. API,
services layer, naming conventions), see `REFACTOR_NOTES.md`. This
document is about the domain: what the models mean, what the app lets
you do, and who is allowed to do what.

---

## 1. Data model

### 1.1 `AccountHolder` / `AccountHolderMembership`

`AccountHolder` is the central identity concept everything else hangs
off. Every holder has a `holder_type`:

| Type | Meaning | How it's created |
|---|---|---|
| `user` | A single person's personal finances | Auto-created for every new Django user (see [§3](#3-permission-handling)) |
| `collective` | A shared organization/Verein/sub-group | Created manually by an admin |
| `external` | A vendor, donor, or other counterparty that never logs in | Created manually via External Party management |

`AccountHolderMembership` links a Django user to an `AccountHolder`
with a `role` of `admin` or `member`. This is the *only* place
user ↔ organization relationships are recorded — a user's access to
accounts, receipts, categories, events, and assets is always derived
by walking through this table (see [§3](#3-permission-handling)).

- A `user`-type holder is meant to have exactly one membership.
  `clean()` on both `AccountHolder` and `AccountHolderMembership`
  raises a `ValidationError` if a second one is added — but note this
  is only enforced if `full_clean()`/`clean()` actually gets called
  (e.g. via a `ModelForm`); it is **not** a database constraint, so a
  direct `.objects.create()` can still violate it.
- `can_delete` on `AccountHolder` always returns `True` — there is no
  protection today against deleting a holder that still has accounts,
  receipts, or memberships. Deleting one will cascade-delete
  everything that has `on_delete=models.CASCADE` pointed at it
  (finance accounts, memberships, categories, asset pools, assets),
  and will be blocked by `PROTECT` where that's used instead (events,
  receipts, transaction lines that reference the holder's accounts).

### 1.2 `FinanceAccount` / `BankAccountDetails`

A `FinanceAccount` is a cash till or bank account belonging to exactly
one `AccountHolder`. `type` is `cash` or `bank`.

- `balance` is computed on the fly: the sum of all its
  `TransactionLine.amount` values. There is no cached/stored balance.
- `can_delete` is `True` only if the account has never been used in a
  transaction.
- `BankAccountDetails` is a one-to-one extension holding IBAN/BIC/bank
  name/account-holder-name, required (by convention, checked in
  `clean()`) for `bank`-type accounts.

### 1.3 `Transaction` / `TransactionLine`

The actual double-entry ledger. A `Transaction` is a single economic
event (e.g. "paid the caterer"); it has two or more `TransactionLine`
rows, each pointing at a `FinanceAccount` with a signed `amount`. The
lines of a transaction must sum to zero — `Transaction.clean()`
enforces this — which is what makes it double-entry: money leaving one
account (negative line) always equals money arriving in another
(positive line).

A transaction can optionally reference the `Receipt` it documents.
`can_delete` is always `True` (no protection here either — deleting a
transaction removes its lines via `CASCADE` and does not check
anything about the linked receipt's state).

All transaction creation/update goes through
`services/transactions.py` (`create_transfer` / `update_transfer`),
which is the single place that builds the balanced pair of lines — see
`REFACTOR_NOTES.md` for why that used to be duplicated in three places.

### 1.4 `Category`

Categories classify either **receipts** or **events** (the `type`
field picks which) for one `collective`, optionally nested under a
`parent` category of the same kind. `incoming_total` /
`outgoing_total` / `balance_total` are computed by summing the
category's receipts directly (for receipt categories) or by summing
every event's totals underneath it (for event categories).
`can_delete` is blocked if it still has receipts (or events) attached.

### 1.5 `Event`

A bounded activity (`start_date`/`end_date`) belonging to one
`collective`, with a `responsible_holder` (must be a `user`-type
holder — enforced by convention, not by a DB constraint) and an
optional `Category`. Like categories, `incoming_total` /
`outgoing_total` / `balance_total` are computed from its linked
receipts. `can_delete` is blocked while it still has receipts.

### 1.6 `Receipt`

The richest model, representing one paper/digital receipt or invoice:

- `direction`: `in` (money received), `out` (money spent), or
  `intern` (internal transfer between the collective's own accounts).
- `tax_category`: the four German non-profit tax spheres (*ideeller
  Bereich*, *Vermögensverwaltung*, *Zweckbetrieb*,
  *wirtschaftlicher Geschäftsbetrieb*) — used by the EÜR export.
- `document_status`: whether a file is attached, missing, or not
  applicable.
- `address_status`: whether the counterparty's invoice address looks
  correct.
- Links: `collective` (must be a `collective`-type holder),
  `responsible_holder` / `uploaded_by_holder` (must be `user`-type
  holders), `counterparty` (any holder — typically `external`),
  `event`, `category`, and a one-to-one `upload_session` (the file
  upload workflow — see 1.7).

`is_closed` is the key derived state: it walks every `Transaction`
linked to the receipt and checks whether the money that actually moved
through the collective's accounts matches the receipt's stated
`amount` (or, for internal transfers, that all lines stayed inside the
collective and net to zero). In other words: *has this receipt been
fully booked into the ledger yet.* This is what the EÜR export's
"completeness" check is built on.

### 1.7 `UploadSession`

Backs the "scan a QR code with your phone to upload a receipt photo"
flow:

- `token` (a UUID) is the public identifier embedded in the mobile
  upload URL and the QR code — never the numeric primary key.
- `start_timer()` opens a fixed 5-minute upload window by stamping
  `activated_at`; `upload_blocked()` / `can_upload()` gate whether a
  fresh upload is currently accepted, so the link can't be used
  indefinitely after the desktop page that generated the QR code has
  moved on. (Note the window length is hardcoded to 5 minutes in
  `upload_blocked()`, independent of whatever `minutes=` value was
  passed into `start_timer()` — worth reconciling if that parameter is
  ever meant to be configurable.)
- One-to-one with `Receipt` — a session is created up front (e.g. when
  a receipt-add form is opened) and only linked to the receipt once
  the receipt is saved.

### 1.8 `Asset` / `AssetPool` — depreciation (AfA)

Fixed-asset tracking following German tax depreciation rules:

- **`Asset`**: a single purchased item, with `purchase_price`,
  `useful_life` (years), and a `depreciation_method` of `linear`
  (spread evenly over `useful_life`) or `none` (*Sofortabschreibung* —
  fully expensed in the purchase year regardless of `useful_life`).
  `is_gwg` flags assets at or under the €800 *geringwertiges
  Wirtschaftsgut* threshold. `book_value(year)` /
  `accumulated_depreciation(year)` compute the depreciation schedule
  for any given year (defaulting to the current year).
- **`AssetPool`** (*Sammelposten*): a collective depreciation pool.
  Assets assigned to a pool (`asset.asset_pool`) are depreciated
  *together* as a single pool over `depreciation_years` (normally 5) —
  once an asset is in a pool, its own `annual_depreciation` /
  `book_value` all return `0.00`; the pool's `acquisition_cost`,
  `annual_depreciation`, and `remaining_value` take over the
  calculation for the whole group instead. Deleting a pool does not
  delete its assets (`on_delete=models.SET_NULL`) — they simply become
  unpooled and (if their own `depreciation_method`/`useful_life` are
  still set) fall back to individual depreciation.

---

## 2. General functionality

| Area | What it does |
|---|---|
| **Dashboard** | Balance history for the user's personal accounts and every collective they belong to. |
| **Account management** | Create/edit cash and bank accounts per holder (personal or collective); per-account overview with running balance and transaction history. |
| **Receipt management** | Create/edit receipts per collective; attach a document either directly or by scanning a QR code with a phone; link one or more transactions to a receipt; see status (document attached? fully booked/"closed"?) on an overview page. |
| **Category management** | Two tabs — receipt categories and event categories — per collective, each with income/expense/balance totals and an overview page with a chart. |
| **Event management** | Per-collective events with date ranges, a responsible holder, income/expense/balance totals, and an overview page. |
| **External party management** | Vendors, donors, and other counterparties that aren't members of any collective (no login, no membership) — just a name/description for use as a receipt counterparty. |
| **Asset management** | Assets and asset pools per collective, with add/edit/delete and a depreciation-schedule overview for each. |
| **EÜR export** (`exports.py`) | Annual German non-profit cash-flow tax export (Einnahmenüberschussrechnung) for one collective/year: one row per relevant transaction line (internal transfers excluded), plus a completeness report listing which receipts dated in that year aren't fully "closed" yet. |

---

## 3. Permission handling

### 3.1 The model

Access control is entirely membership-based, with no separate
permissions/roles framework — it all comes down to rows in
`AccountHolderMembership`:

- Every Django user automatically gets their own personal `user`-type
  `AccountHolder`, an `admin` membership to it, and a default cash
  `FinanceAccount`, the moment their `User` row is created. This
  happens in `signals.py` (`create_personal_account_holder`, on
  `post_save` of the user model) — there's no manual setup step.
- Access to a `collective`-type holder (and everything scoped to it —
  its accounts, receipts, categories, events, assets) requires a
  membership row linking the user to that holder.
- Only two roles exist: `admin` and `member`. The schema supports
  finer-grained permissions but the app doesn't really use the
  distinction yet — see 3.3.
- `external`-type holders have no memberships at all (they don't log
  in); they're just referenced *by* collectives as receipt
  counterparties.

### 3.2 Where the logic lives

All permission logic is centralized in `services/access.py` rather
than being re-implemented per feature:

| Function | Answers |
|---|---|
| `is_member` / `is_admin` | Does this user have a membership (of that role) in this holder? |
| `get_user_account_holder` | Which `user`-type holder belongs to this Django user? |
| `get_user_collectives` | Which collectives does this user belong to (optionally: as admin only)? |
| `get_accessible_account_holders` | Every holder this user should be able to *see*, e.g. in a dropdown: their memberships, plus **all** `user`-type holders, plus **all** `external`-type holders. |
| `get_manageable_account_holders` | Collectives where this user is an `admin`. |
| `can_access_account_holder(user, holder)` | Gate for viewing a specific object: `True` if the user has *any* membership in that holder, **or** the holder is `user`-type. |
| `can_manage_account_holder(user, holder)` | Gate for admin-only actions: `True` only for an `admin` membership. |

Views call these rather than querying `AccountHolderMembership`
directly — e.g. every `*_overview_page` view (account, category,
event, receipt, asset) does:

```python
if not access.can_access_account_holder(request.user, obj.collective):
    return HttpResponse("Not allowed", status=403)
```

### 3.3 Known gaps — please read before relying on this for real data

This is an honest account of where enforcement is currently thin, not
a description of intended behavior:

1. **`can_access_account_holder` doesn't check *whose* personal holder
   it is.** The `or account_holder.holder_type == AccountHolder.HolderType.USER`
   clause was written to let a user see *their own* personal account —
   but it actually returns `True` for **any** `user`-type holder,
   regardless of which Django user it belongs to. As written, any
   logged-in user who guesses/enumerates another user's personal
   account/receipt/overview URL can view it. This should be tightened
   to also check that the holder *is* `access.get_user_account_holder(user)`
   before this refactor's view-layer split is treated as a finished
   authorization boundary.
2. **Most create/edit/delete endpoints have no permission check at
   all yet.** Throughout `views/partials/`, you'll find
   `# TODO permissions` / `# TODO check permissions` comments on
   things like adding a cash/bank account, adding or deleting a
   category/event/asset/asset pool, and deleting an external party.
   Today these are only gated by Django's `@login_required` (any
   logged-in user) — not by collective membership. The `can_delete`
   business rule on models like `Category`/`Event`/`FinanceAccount`
   prevents *data-integrity* mistakes (deleting something still in
   use), but doesn't prevent an unrelated logged-in user from doing
   it.
3. **`member` vs `admin` is barely used.** Right now the only place
   the distinction actually changes behavior is the accounts
   management page (`can_add` / `can_manage` flags per section, driven
   by `can_manage_account_holder`). Everywhere else, being a `member`
   is functionally equivalent to being an `admin` once you're past the
   `can_access_account_holder` check — e.g. any member can edit any
   receipt/event/category in a collective they belong to today.
4. **`AccountHolder.can_delete` is always `True`** (no check for
   existing accounts, receipts, or memberships) and
   **`Transaction.can_delete`** is likewise always `True` — deleting
   either is only as safe as Django's `on_delete` behavior on the
   models pointing at them.

If tightening this is the next priority, the natural order is:
(1) fix `can_access_account_holder` to check personal-holder ownership,
(2) add real `can_manage_account_holder` checks to the `# TODO`
create/edit/delete endpoints, (3) decide what `member` should
actually be restricted from doing, if anything.