# Policy: PSD2 Payment Services
# ID: policy:psd2
# Last reviewed: 2026-01-22
# Owner: DNB Payments Compliance

## Scope

This policy implements the EU Revised Payment Services Directive (PSD2,
Directive 2015/2366) and the Norwegian Financial Contracts Act provisions
covering payment services.

## Strong customer authentication (SCA)

SCA is required when a customer:

- Accesses their payment account online.
- Initiates an electronic payment transaction.
- Carries out an action through a remote channel that may imply a risk of
  payment fraud or other abuses.

SCA must be based on at least two independent factors from the categories:
**knowledge** (something only the user knows), **possession** (something only
the user holds), and **inherence** (something the user is). Compromise of one
factor must not compromise the others.

### SCA exemptions

Exemptions are available — but not required — for:

- Contactless payments at point of sale up to NOK 400 per transaction (cumulative
  cap of NOK 1,500 or five transactions before SCA is re-applied).
- Trusted beneficiaries added to a customer's whitelist via SCA.
- Recurring transactions of identical amount to the same beneficiary.
- Low-value remote transactions up to EUR 30 (cumulative cap of EUR 100 or
  five transactions).
- Transaction risk analysis (TRA) where DNB's fraud rate stays below
  thresholds defined in RTS.

## Open banking access

DNB exposes regulated APIs to authorized Third Party Providers (TPPs):

- **Account Information Service Providers (AISPs)** — read-only access to
  account data with customer consent.
- **Payment Initiation Service Providers (PISPs)** — initiate credit transfers
  on behalf of the customer.
- **Card-Based Payment Instrument Issuers (CBPIIs)** — funds availability
  confirmation.

TPPs must hold a license from a competent authority and present an eIDAS
qualified certificate. Access is granted without contractual relationship
between DNB and the TPP.

## Liability for unauthorized transactions

For unauthorized payment transactions notified by the customer without undue
delay (and within 13 months at the latest):

- Customer liability is capped at NOK 1,200 unless gross negligence or fraud
  is proven.
- Where DNB does not require SCA when it should have, the customer bears no
  liability except in fraud.
- Refund is processed by end of the next business day, with the account
  restored to the state it would have been in.

## Surcharging

DNB does not surcharge for the use of consumer debit or credit cards. Other
payment instruments may be surcharged where permitted by national law and
disclosed in advance.

## Out of scope

PSD2 does not apply to:

- Cash transactions without intermediary.
- Paper-based payment instruments such as cheques and travelers' cheques.
- Securities transactions (covered by MiFID II).
- Internal transfers between accounts of the same customer at DNB (some SCA
  exemptions still apply).
