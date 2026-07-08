# Using the Ledger App — A Tutorial

This is a walkthrough for people *using* the app day to day — treasurers,
event organizers, and members of a Verein (association). If you're
looking for how the code is built, see `README.md` instead; this guide
only talks about what you see on screen.

---

## 1. The big picture: who owns what

Everything in the app is organized around **account holders**. There
are three kinds, and understanding the difference makes everything
else click into place:

| Kind | What it is | Example |
|---|---|---|
| **Personal** | You. Created automatically the moment you get an account — you never set this up yourself. | "Alice" |
| **Collective** | A Verein, or a sub-group within one. This is where the shared bookkeeping actually happens. | "Musikverein Example e.V." |
| **External party** | A vendor, supplier, or donor — anyone your Verein pays or receives money from, who never logs into the app themselves. | "Getränke Müller GmbH" |

You'll mostly work *inside* one or more collectives. Everywhere you see
a **collective switcher** at the top of a page (accounts, receipts,
categories, events, assets), that's you choosing which Verein's data
you're currently looking at.

---

## 2. Permissions — who can do what

Access is entirely based on **membership**. If you're not a member of
a collective, you simply won't see it — it won't appear in your
collective switcher, and its receipts/accounts/events/assets are
invisible to you.

There are two roles once you *are* a member:

- **Admin** — full access, including managing the collective's
  accounts (adding/editing cash and bank accounts).
- **Member** — can see and work with everything in the collective day
  to day (receipts, categories, events, assets), but doesn't get the
  account-management controls admins get.

A few practical notes:

- Your **personal** account is always just yours — nobody else can see
  it, and you don't need to be "invited" to it.
- **External parties** aren't accounts you log into at all — they only
  exist as a name you can pick when recording who you paid or who paid
  you (the "counterparty" on a receipt).
- If something you expect to see is missing — a collective, a receipt,
  an account — the most common reason is simply that you haven't been
  added as a member yet. Ask whoever administers your Verein's account
  in the app to add you.

---

## 3. Accounts — where the money actually sits

Under **Accounts**, each collective (and your personal profile) can
have any number of:

- **Cash accounts** — a physical till/petty cash box.
- **Bank accounts** — with IBAN/BIC/bank name on file.

Every account shows its **current balance**, computed automatically
from every transaction that's ever touched it — you never enter a
balance directly. Click into any account to see its full transaction
history and running balance over time.

You'll create a new account here whenever your Verein opens a new bank
account or starts a new cash box (e.g. for a specific event).

---

## 4. Receipts — the heart of the app

A **receipt** represents one real-world piece of paper (or digital
invoice): money that came in, went out, or moved internally between
your own accounts. This is where most of your day-to-day time will go.

### Creating a receipt

When you add a receipt, you'll fill in:

- **Direction** — incoming, outgoing, or an internal transfer.
- **Amount** and **date**.
- **Counterparty** — who you paid or received money from.
- **Category** and, optionally, **Event** (see below — this is how
  reporting gets organized).
- **Tax sphere** (*Sphäre*) — for German non-profits, which of the four
  tax categories the receipt falls under (ideeller Bereich,
  Vermögensverwaltung, Zweckbetrieb, wirtschaftlicher
  Geschäftsbetrieb). This matters a lot at tax-filing time.
- **Document status** — whether you actually have the receipt file
  attached yet.

### Attaching the actual document

Every receipt has an upload slot for the physical/digital file. You
have two ways to attach it:

1. **From your computer** — just pick the file directly in the form.
2. **From your phone** — scan the QR code shown in the form with your
   phone's camera. It opens a simple upload page on your phone (no
   login needed), lets you snap a photo or pick a file, and it appears
   back on your computer's screen within a couple of seconds. This is
   the fast way to digitize a paper receipt right when you're handed
   it. Note the QR code / upload link only stays active for a few
   minutes — if it's expired, just reopen the receipt to get a fresh
   one.

### "Open" vs "closed" receipts

A receipt is **closed** once the money it describes has actually been
fully booked as a transaction into your accounts. A receipt can be
**open** (still outstanding) if:

- No transaction has been recorded for it yet, or
- Only part of the amount has been paid/received so far (e.g. a
  deposit was paid, the rest is still owed).

You'll see open/closed status as a badge everywhere receipts are
listed, and — importantly — when you get to tax export time (see
§7), the app will explicitly warn you about any receipts that are
still open for the year you're exporting, so nothing slips through
the cracks.

### Linking a transaction

Once you're ready to record that the money actually moved, open the
receipt and add a **transaction**: which account it came from, which
account it went to, and the amount. This is what actually changes your
account balances — adding a receipt alone does not move any money,
it just records the paperwork. A receipt can have more than one
transaction linked to it (e.g. a deposit now, the balance later).

---

## 5. Categories and Events — how you organize receipts

These two exist purely to help you **group and report on** your
receipts — neither one moves money on its own.

- **Categories** classify *what kind of thing* a receipt was for
  (e.g. "Rent", "Merchandise Sales", "Insurance"). There are two
  separate flavors — receipt categories and event categories — because
  events get their own categorization too (see below).
- **Events** represent a bounded activity with a start and end date —
  a concert, a summer camp, a fundraiser. Every receipt can optionally
  be tagged with the event it belongs to, which is how you answer "did
  this event make or lose money?" at a glance.

Both categories and events have their own **overview page** showing
total income, total expenses, and a chart over time — built entirely
from the receipts tagged with them. Use these liberally; the more
consistently receipts get categorized/tagged, the more useful these
overviews (and your year-end reporting) become.

---

## 6. Assets — tracking things you own, not just money you spent

Not every big purchase is a simple one-time expense for tax purposes.
If your Verein buys something that will be used for years (a laptop, a
PA system, folding tables), tax law usually requires you to spread
its cost over its useful life instead of deducting it all at once.
That's what **Assets** are for.

When you record an asset purchase, you'll choose how it's depreciated:

- **Linear** — the cost is spread evenly over the asset's useful life
  (e.g. a €900 asset over 3 years = €300/year).
- **Immediate write-off (Sofortabschreibung)** — for low-value items
  (GWG, currently ≤€800), the full cost can be deducted right away, no
  spreading needed.
- **Asset pool (Sammelposten)** — a German-specific option: instead of
  tracking several similar low-value items individually, you group
  them into a pool and depreciate the *whole pool* evenly over 5 years,
  regardless of each item's own useful life. Handy if you buy a batch
  of chairs or tablets at once.

Every asset can (optionally) be linked back to the **receipt** that
paid for it — that's the connection between "money left the account"
and "here's the physical thing we bought with it." Each asset, and
each pool, has its own overview page showing the depreciation schedule
year by year: how much is written off this year, how much has
accumulated so far, and what the item is still "worth" on the books
(its book value).

---

## 7. Putting it together: a typical receipt's life

1. You're handed a paper receipt for something the Verein bought.
2. You open **Receipts**, add a new one, fill in amount/date/category/
   event/tax sphere, and scan the QR code with your phone to attach a
   photo of the paper receipt on the spot.
3. If it's a big-ticket item you'll be using for years (not just
   consumed immediately), you also record it under **Assets**, linking
   it back to this same receipt.
4. Once the money actually leaves the account, you add a
   **transaction** on the receipt, picking the paying account. The
   receipt now flips from open to closed, and the account's balance
   updates immediately.
5. Over the year, that receipt contributes to its **category**'s and
   (if tagged) its **event**'s running totals, visible on their
   overview pages.
6. At tax time, someone with access to the export tool runs the year's
   **EÜR export** — every closed, cash-relevant receipt for the year
   becomes a row automatically. If your asset was linearly depreciated
   or pooled, its purchase amount is excluded from that row (it isn't
   deductible all at once) and instead shows up in the separate
   **AVEÜR / AfA export**, spread over the years it's being written
   off. The export screen also flags, up front, any receipts for that
   year that are still open, so they can be chased down before filing.

---

## 8. Quick reference

| I want to... | Go to... |
|---|---|
| See all balances at a glance | Dashboard |
| Add/manage a bank or cash account | Accounts |
| Record money coming in or going out | Receipts |
| Group receipts by topic | Categories |
| Track a specific activity's income/expenses | Events |
| Record a vendor/donor you deal with | External Parties |
| Track a big purchase you'll depreciate over time | Assets |
| Generate a tax-year export | Export (EÜR / AVEÜR) |