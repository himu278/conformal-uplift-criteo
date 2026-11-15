# Methods note

## Setting

Units *i* = 1, …, *n* have features *X*, a randomized assignment *T* ∈ {0, 1} with
P(*T* = 1) = *e* independent of *X*, and binary potential outcomes *Y*(0), *Y*(1).
We observe *Y* = *Y*(*T*). The individual treatment effect (ITE) is
*D* = *Y*(1) − *Y*(0) ∈ {−1, 0, 1}.

## Conformal sets for potential outcomes

Fit a model p̂ₜ(*x*) ≈ P(*Y* = 1 | *X* = *x*, *T* = *t*) on a training split. On a
calibration split, take the units with *T* = *t* and compute the score
*s*(*x*, *y*) = 1 − p̂ₜ(*y* | *x*), i.e. p̂ₜ(*x*) if *y* = 0 and 1 − p̂ₜ(*x*) if *y* = 1.
Let *q* be the ⌈(*m* + 1)(1 − β)⌉-th smallest of the *m* scores. The set
Cₜ(*x*) = {*y* : *s*(*x*, *y*) ≤ *q*} satisfies P(*Y*(*t*) ∈ Cₜ(*X*)) ≥ 1 − β for a new
unit from the same population. This holds because, under randomization, the calibration units
in arm *t* and a new unit's (*X*, *Y*(*t*)) are exchangeable. No propensity weighting is
needed because *e* does not depend on *x* (Lei & Candès, 2021).

## ITE sets

With β = α/2 in each arm, define C(*x*) = {*y*₁ − *y*₀ : *y*₁ ∈ C₁(*x*), *y*₀ ∈ C₀(*x*)}.
By the union bound, P(*D* ∈ C(*X*)) ≥ 1 − α **for every joint law of (*Y*(0), *Y*(1))**.
This matters because that joint law is not identified from experimental data.

## Why the sets are rarely informative for rare outcomes

If P(*Y*(*t*) = 1 | *x*) is small for both arms, the shortest valid set for each potential
outcome is {0}, so C(*x*) = {0}. That set covers *D* whenever *D* = 0, which is true for most
users. It is valid but carries no information about who benefits. To certify a benefit
(C(*x*) = {1}) the model would need to be confident that *Y*(1) = 1 **and** *Y*(0) = 0 for the
same user, which a rare binary outcome almost never allows. When the outcome is common, the
sets widen to {−1, 0, 1} instead. The simulation quantifies both regimes.

## Couplings used in the simulation

For marginals μ₀(*x*), μ₁(*x*) and a uniform *U*:

- comonotone: *Y*(*t*) = 1{*U* < μₜ}
- independent: separate uniforms
- countermonotone: *Y*(0) = 1{*U* < μ₀}, *Y*(1) = 1{1 − *U* < μ₁}

All three give the same distribution of observed data.

## Ranking evaluation

For the top fraction φ by predicted uplift, V(φ) = φ · (Ȳ_{T=1, top φ} − Ȳ_{T=0, top φ}).
Random targeting gives φ · ATE. The AUUC gain is ∫₀¹ (V(φ) − φ · ATE) dφ, estimated on a
held-out test set. Confidence intervals come from a Poisson bootstrap: each unit gets an
independent Poisson(1) weight, so the sort order never changes.

## Assignment vs. exposure

Controls are never exposed. The intention-to-treat effect is the difference in means by
`treatment`. Under the exclusion restriction (assignment affects the outcome only through
exposure), the effect of exposure among compliers is ITT / P(exposed | treated). Comparing
exposed treated users directly with controls is biased, because exposure depends on auction
outcomes that are related to the user.
