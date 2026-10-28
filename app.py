import streamlit as st
import pymupdf
from deep_translator import GoogleTranslator
import io
import tempfile
import os
from pathlib import Path

st.set_page_config(page_title="Polyglot PDF Translator", page_icon="📄", layout="wide")

st.title("📄 Polyglot – Traduttore PDF con preservazione stile")
st.markdown("""
Traduce PDF mantenendo **il più possibile** layout, dimensioni font, grassetto, corsivo e blocchi di codice.

**Limitazione importante**: la riproduzione *esatta* del font originale (soprattutto font proprietari o subset) non è sempre possibile.  
Le traduzioni cambiano lunghezza e set di caratteri. Per risultati più fedeli su documenti scientifici usa anche [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate).
""")

LANGUAGES = {
    "Italiano": "it", "Inglese": "en", "Spagnolo": "es", "Francese": "fr",
    "Tedesco": "de", "Portoghese": "pt", "Russo": "ru", "Cinese (Semplificato)": "zh-CN",
    "Giapponese": "ja", "Coreano": "ko", "Arabo": "ar", "Olandese": "nl",
    "Polacco": "pl", "Turco": "tr", "Svedese": "sv", "Auto-detect": "auto"
}

col1, col2 = st.columns(2)
with col1:
    source_lang_name = st.selectbox("Lingua di origine", list(LANGUAGES.keys()),
                                     index=list(LANGUAGES.keys()).index("Auto-detect"))
    source_lang = LANGUAGES[source_lang_name]
with col2:
    target_lang_name = st.selectbox("Lingua di destinazione",
                                     [k for k in LANGUAGES if k != "Auto-detect"], index=0)
    target_lang = LANGUAGES[target_lang_name]

skip_code = st.checkbox("Preserva blocchi di codice (non tradurre testo monospace)", value=True)

uploaded_file = st.file_uploader("Carica PDF", type=["pdf"])

def is_monospace(span):
    """Detect code-like spans via font flags or name."""
    flags = span.get("flags", 0)
    font = span.get("font", "").lower()
    # bit 3 = monospace in many versions; also check common code fonts
    if flags & (1 << 3):
        return True
    code_fonts = ("courier", "mono", "consolas", "monaco", "dejavu", "source code", "fira code", "jetbrains")
    return any(cf in font for cf in code_fonts)

def span_to_html(span, text):
    """Approximate original style in HTML for insert_htmlbox."""
    size = max(6, min(span.get("size", 10), 28))
    flags = span.get("flags", 0)
    color = span.get("color", 0)
    # Convert sRGB int to hex
    r = (color >> 16) & 255
    g = (color >> 8) & 255
    b = color & 255
    color_css = f"#{r:02x}{g:02x}{b:02x}" if color else "#000000"

    style = f"font-size:{size:.1f}px; color:{color_css}; line-height:1.15; margin:0; padding:0;"
    if flags & (1 << 4):  # bold
        style += " font-weight:bold;"
    if flags & (1 << 1):  # italic
        style += " font-style:italic;"
    if is_monospace(span):
        style += " font-family:monospace, 'Courier New', Consolas;"

    return f'<span style="{style}">{text}</span>'

if uploaded_file and st.button("🚀 Traduci PDF", type="primary", use_container_width=True):
    with st.spinner("Traduzione in corso (può richiedere tempo)..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                input_path = tmp.name

            doc = pymupdf.open(input_path)
            translator = GoogleTranslator(
                source=source_lang if source_lang != "auto" else "auto",
                target=target_lang
            )
            progress = st.progress(0)
            status = st.empty()

            for page_num, page in enumerate(doc):
                status.text(f"Pagina {page_num + 1}/{len(doc)}")
                progress.progress((page_num + 1) / len(doc))

                # Use dict for style info
                data = page.get_text("dict", flags=pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_ACCURATE_BBOXES)
                blocks = data.get("blocks", [])

                for block in blocks:
                    if block.get("type") != 0:  # only text blocks
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if len(text) < 2:
                                continue

                            # Skip pure code blocks if requested
                            if skip_code and is_monospace(span) and len(text) > 5:
                                continue

                            try:
                                translated = translator.translate(text)
                                if not translated or translated.strip() == text:
                                    continue

                                bbox = pymupdf.Rect(span["bbox"])
                                # Cover original
                                page.draw_rect(bbox, color=None, fill=(1, 1, 1))

                                # Insert with approximate style
                                html = span_to_html(span, translated)
                                page.insert_htmlbox(bbox, html)
                            except Exception:
                                continue  # skip problematic spans

            out = io.BytesIO()
            doc.subset_fonts()
            doc.save(out, garbage=4, deflate=True)
            doc.close()
            os.unlink(input_path)

            progress.progress(1.0)
            status.success("Traduzione completata!")

            fname = Path(uploaded_file.name).stem + f"_polyglot_{target_lang}.pdf"
            st.download_button(
                "📥 Scarica PDF tradotto",
                data=out.getvalue(),
                file_name=fname,
                mime="application/pdf",
                use_container_width=True
            )
            st.balloons()

        except Exception as e:
            st.error(f"Errore: {e}")
            st.exception(e)

st.markdown("---")
st.markdown("""
### Deploy su Streamlit Community Cloud
1. Questo repo è già su GitHub.
2. Vai su [share.streamlit.io](https://share.streamlit.io) → New app.
3. Seleziona il repo `sipony/polyglot`, branch `main`, file `app.py`.
4. Deploy.

### Note sullo stile
- Dimensione, colore, grassetto e corsivo vengono approssimati.
- I font esatti del PDF originale non possono essere sempre riusati (limitazione dei PDF).
- I blocchi di codice monospace possono essere lasciati intatti.
- Per layout molto complessi (formule, multi-colonna) i risultati possono variare.
""")
