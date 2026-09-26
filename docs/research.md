# Research

This note separates public sources from design assumptions. No Newmark internal systems, confidential leases, or invented company statistics are used.

## Verified public sources

1. **Lease abstraction is a known CRE operations problem.** Commercial lease administration includes extracting parties, premises, rent, and critical dates from executed documents. See the Institute of Real Estate Management overview of lease administration responsibilities: [IREM: Lease Administration](https://www.irem.org/).

2. **Document-to-system handoff is a documented bottleneck.** Industry writing on lease abstraction describes manual review as time-intensive and sensitive to omitted dates or options. Example public primer: [Deloitte, "Lease accounting" resources](https://www2.deloitte.com/us/en/pages/audit/articles/lease-accounting.html) discuss the operational burden of capturing lease data after ASC 842 / IFRS 16, without providing Newmark-specific figures.

3. **LLM extraction must be treated as a proposal.** OpenAI and other providers document structured outputs and warn that models can hallucinate. See [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) and [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).

4. **Human-in-the-loop is a standard high-risk pattern.** NIST AI RMF and related responsible-AI guidance recommend human oversight when model errors have operational or financial impact.

5. **Versioned APIs are an integration baseline.** See [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) and common JSON contract versioning practice.

## Design assumptions

These are design assumptions, not measured Newmark facts:

- A reviewer can inspect eight core fields and evidence faster than they can abstract a full legal memo.
- Blocking missing dates or rent is more valuable than extracting every clause in a first slice.
- A short demo should prefer one working workflow over a platform diagram.
- Fixture-mode demos are acceptable when clearly labeled.

## What was not used

- No confidential Newmark data, screenshots, or internal architecture.
- No fabricated accuracy percentages for LLM lease extraction.
- No claim that a live property-management system was integrated.
