import spacy
import PyPDF2
import docx2txt 
import os

nlp = spacy.load("en_core_web_sm")

def ingest_documents(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    elif ext in [".docx", ".doc"]:
        text = docx2txt.process(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    return text

def preprocess_text_func(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if not token.is_stop])

def extract_insights(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return {"entities": entities}

def summarize_text_func(text, max_sentences=3):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return " ".join(sentences[:max_sentences])
