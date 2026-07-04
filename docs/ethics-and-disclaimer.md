# Ethics & Disclaimer

## Core stance

DermaFace AI is a **screening and education prototype**, not a medical device and not a diagnostic tool. This framing is a hard constraint on product, UI, and reporting decisions.

## User-facing disclaimer (must appear in the app)

> **DermaFace AI does not provide medical advice or a diagnosis.** It is an educational prototype that estimates the *possible* presence and severity of common skin conditions from a photo. Results can be wrong, especially across different skin tones, lighting, and image quality. **Always consult a licensed dermatologist or physician** for any skin concern. Do not use this tool to make treatment decisions.

## Design commitments

- **Never say "diagnosis."** Use "estimate", "possible", "screening", "for education."
- **Always show uncertainty.** Surface confidence and a clear "see a professional" prompt.
- **Fairness is measured, not assumed.** Report performance stratified by Fitzpatrick skin type; call out gaps honestly in the model card and final report.
- **Consent & privacy.** Photos are processed for the demo only; do not store user images server-side without explicit consent. State this in the UI.
- **No PII in the repo.** No patient-identifying data in commits, issues, screenshots, or the deployed Space.

## Known limitations to document

- Training data skews toward certain skin tones / clinical (not selfie) imagery.
- Severity labels are approximate (see [data-strategy.md](data-strategy.md)).
- Model has not been clinically validated and must not be presented as if it has.

## Responsible-use checklist (before shipping the demo)

- [ ] Disclaimer visible before and alongside any prediction
- [ ] "Consult a professional" prompt present
- [ ] Confidence / uncertainty shown
- [ ] Per-skin-tone performance reported in the model card
- [ ] No user images persisted without consent
- [ ] "Not a diagnosis" language throughout — no clinical claims
