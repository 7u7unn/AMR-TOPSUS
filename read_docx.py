import docx

def extract_headings_and_content(filename):
    doc = docx.Document(filename)
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            print(f"[{para.style.name}] {text}")

if __name__ == '__main__':
    extract_headings_and_content(r"d:\MagangUnair26\Topsus - AMR\Preliminary Design Review.docx")
