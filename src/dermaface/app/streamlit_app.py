"""DermaFace AI — Streamlit demo.

Owner: Ali (UI/UX).

Runnable today: it loads (or falls back to a placeholder), takes a photo, and
shows the prediction + where the Grad-CAM overlay will go. The disclaimer is
shown before and alongside every result — this is a hard requirement
(docs/ethics-and-disclaimer.md).

Run:
    streamlit run src/dermaface/app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script (streamlit run ...) without installing the package.
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

from dermaface.config import load_config  # noqa: E402
from dermaface.inference import predict  # noqa: E402

DISCLAIMER = (
    "**DermaFace AI does not provide medical advice or a diagnosis.** It is an "
    "educational prototype that *estimates* the possible presence and severity of "
    "common skin conditions from a photo. Results can be wrong — especially across "
    "different skin tones, lighting, and image quality. **Always consult a licensed "
    "dermatologist or physician.** Do not use this tool to make treatment decisions."
)


def main() -> None:
    st.set_page_config(page_title="DermaFace AI", page_icon="🩺", layout="centered")
    cfg = load_config()

    st.title("DermaFace AI")
    st.caption("Screening & education — not a diagnosis")
    st.warning(DISCLAIMER)

    if not cfg.model_path.exists():
        st.info(
            "⚙️ Running in **placeholder mode** — no trained model found at "
            f"`{cfg.model_path}`. Predictions below are not real."
        )

    uploaded = st.file_uploader(
        "Upload a clear, well-lit face photo", type=["jpg", "jpeg", "png"]
    )
    consent = st.checkbox(
        "I understand this is an educational tool and not a diagnosis.", value=False
    )

    if uploaded and consent:
        from PIL import Image

        image = Image.open(uploaded).convert("RGB")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Your photo")
            st.image(image, use_container_width=True)

        result = predict(image, cfg)

        with col2:
            st.subheader("Grad-CAM (affected areas)")
            if result.heatmap_overlay is not None:
                st.image(result.heatmap_overlay, use_container_width=True)
            else:
                st.caption("Heatmap appears here once the model + Grad-CAM are wired in.")

        st.divider()
        st.subheader("Estimate")
        if result.placeholder:
            st.error(result.note)
        st.metric("Most likely", result.condition, help="Estimated condition — not a diagnosis")
        st.write(f"**Severity band:** {result.severity}")
        st.write(f"**Confidence:** {result.confidence:.0%}")
        st.bar_chart(result.condition_probs)

        st.divider()
        st.info("👩‍⚕️ For any real concern, please see a dermatologist. " + DISCLAIMER)
    elif uploaded and not consent:
        st.stop()


if __name__ == "__main__":
    main()
