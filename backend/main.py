from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pymupdf
from deep_translator import GoogleTranslator
import io
import tempfile
import os
from pathlib import Path

app = FastAPI(title="Polyglot PDF Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_monospace(span):
    flags = span.get("flags", 0)
    font = span.get("font", "").lower()
    if flags & (1 << 3):
        return True
    code_fonts = ("courier", "mono", "consolas", "monaco", "dejavu", "source code", "fira code", "jetbrains")
    return any(cf in font for cf in code_fonts)

def span_to_html(span, text):
    size = max(6, min(span.get("size", 10), 28))
    flags = span.get("flags", 0)
    color = span.get("color", 0)
    r = (color >> 16) & 255
    g = (color >> 8) & 255
    b = color & 255
    color_css = f"#{r:02x}{g:02x}{b:02x}" if color else "#000000"

    style = f"font-size:{size:.1f}px; color:{color_css}; line-height:1.15; margin:0; padding:0;"
    if flags & (1 << 4):
        style += " font-weight:bold;"
    if flags & (1 << 1):
        style += " font-style:italic;"
    if is_monospace(span):
        style += " font-family:monospace, 'Courier New', Consolas;"

    return f'<span style="{style}">{text}</span>'

@app.post("/translate")
async def translate_pdf(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("it"),
    skip_code: bool = Form(True)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            input_path = tmp.name

        doc = pymupdf.open(input_path)
        translator = GoogleTranslator(
            source=source_lang if source_lang != "auto" else "auto",
            target=target_lang
        )

        for page in doc:
            data = page.get_text("dict", flags=pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_ACCURATE_BBOXES)
            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if len(text) < 2:
                            continue
                        if skip_code and is_monospace(span) and len(text) > 5:
                            continue
                        try:
                            translated = translator.translate(text)
                            if not translated or translated.strip() == text:
                                continue
                            bbox = pymupdf.Rect(span["bbox"])
                            page.draw_rect(bbox, color=None, fill=(1, 1, 1))
                            html = span_to_html(span, translated)
                            page.insert_htmlbox(bbox, html)
                        except Exception:
                            continue

        out = io.BytesIO()
        doc.subset_fonts()
        doc.save(out, garbage=4, deflate=True)
        doc.close()
        os.unlink(input_path)
        out.seek(0)

        filename = Path(file.filename).stem + f"_polyglot_{target_lang}.pdf"
        return StreamingResponse(
            out,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
