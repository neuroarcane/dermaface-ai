"""DermaFace AI — Streamlit demo.

Owner: Ali (UI/UX).

Runnable today: takes a photo, runs a prediction (placeholder until a model is
trained), and renders a Grad-CAM heatmap. The disclaimer is shown before and
alongside every result — a hard requirement (docs/ethics-and-disclaimer.md).

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

# Below this confidence, a real prediction is flagged as unreliable.
# Provisional threshold — Iva/Varsha can tune once real confidences exist.
LOW_CONFIDENCE_THRESHOLD = 0.50


@st.cache_data(show_spinner=False)
def _compute_overlay(image_bytes: bytes):
    """Build the Grad-CAM overlay for an image (cached by raw bytes)."""
    import io

    from PIL import Image

    from dermaface.app.overlay import build_demo_overlay

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return build_demo_overlay(image)


def _load_image(uploaded):
    """Open an uploaded file as RGB, or return None on a bad/corrupt image."""
    import io

    from PIL import Image, UnidentifiedImageError

    try:
        data = uploaded.getvalue()
        return Image.open(io.BytesIO(data)).convert("RGB"), data
    except (UnidentifiedImageError, OSError):
        return None, None


def main() -> None:
    st.set_page_config(page_title="DermaFace AI", page_icon="🩺", layout="centered")
    cfg = load_config()

    st.title("🩺 DermaFace AI")
    st.caption("Screening & education — **not a diagnosis**")
    st.warning(DISCLAIMER)

    if not cfg.model_path.exists():
        st.info(
            "⚙️ **Placeholder mode** — no trained model found at "
            f"`{cfg.model_path.name}`. The condition/severity below are not real "
            "predictions; the Grad-CAM heatmap uses a random-weight model to "
            "demonstrate the interface."
        )

    with st.sidebar:
        st.header("How to use")
        st.markdown(
            "1. Upload a clear, front-facing, well-lit photo.\n"
            "2. Confirm you understand this is educational.\n"
            "3. Review the estimate and heatmap.\n\n"
            "No photos are stored."
        )

    uploaded = st.file_uploader(
        "Upload a clear, well-lit face photo", type=["jpg", "jpeg", "png"]
    )
    consent = st.checkbox(
        "I understand this is an educational tool and not a diagnosis.", value=False
    )

    # --- Edge cases ---------------------------------------------------------
    if uploaded is None:
        st.stop()

    image, image_bytes = _load_image(uploaded)
    if image is None:
        st.error("That file couldn't be read as an image. Please upload a JPG or PNG.")
        st.stop()

    if not consent:
        st.info("Please check the box above to run the estimate.")
        st.stop()

    from dermaface.app.overlay import detect_face

    if not detect_face(image):
        st.warning(
            "⚠️ No face detected. Results on non-face or unclear images are "
            "unreliable — try a clearer, front-facing photo."
        )

    # --- Results ------------------------------------------------------------
    result = predict(image, cfg)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your photo")
        st.image(image, use_container_width=True)
    with col2:
        st.subheader("Grad-CAM")
        if result.placeholder:
            st.caption("⚠️ Illustrative only — random weights, not medically meaningful yet.")
        else:
            st.caption("Regions that most influenced the estimate")
        overlay = result.heatmap_overlay
        if overlay is None:
            try:
                overlay = _compute_overlay(image_bytes)
            except Exception as exc:  # keep the app up if Grad-CAM fails
                st.caption(f"Heatmap unavailable: {exc}")
        if overlay is not None:
            st.image(overlay, use_container_width=True)

    st.divider()
    st.subheader("Estimate")
    if result.placeholder:
        st.error(result.note)
    # In placeholder mode the numbers aren't real — show em-dashes instead of a
    # misleading "clear / 0%" so nobody mistakes it for an actual prediction.
    most_likely = "—" if result.placeholder else result.condition
    severity = "—" if result.placeholder else result.severity
    confidence = "—" if result.placeholder else f"{result.confidence:.0%}"
    c1, c2, c3 = st.columns(3)
    c1.metric("Most likely", most_likely, help="Estimated — not a diagnosis")
    c2.metric("Severity band", severity)
    c3.metric("Confidence", confidence)

    # Low-confidence state: warn when a *real* prediction is below threshold.
    if not result.placeholder and result.confidence < LOW_CONFIDENCE_THRESHOLD:
        st.warning(
            "⚠️ **Low confidence** — this estimate is uncertain and may well be "
            "wrong. Please don't rely on it; see a dermatologist."
        )

    st.bar_chart(result.condition_probs)

    st.divider()
    st.info("👩‍⚕️ For any real concern, please see a dermatologist. " + DISCLAIMER)


if __name__ == "__main__":
    main()
