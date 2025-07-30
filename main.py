import fitz  # PyMuPDF
import re


FONTS = {
    "CenturySchoolbook": "fonts/Century Schoolbook Std Regular.otf",
    "CenturySchoolbook-Bold": "fonts/SCHLBKB.TTF",
}

class PDFProcessor:
    def __init__(self, pdf_path, text):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.target_text = text

    def find_text(self):
        found = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            words = page.get_text("words")
            exact_matches = []

            for w in words:
                x0, y0, x1, y1, word, *_ = w
                cleaned_word = re.sub(r'[^A-Za-z0-9]', '', word)
                if cleaned_word == self.target_text:
                    rect = fitz.Rect(x0, y0, x1, y1)
                    exact_matches.append(rect)

            if exact_matches:
                found.append((page_num, exact_matches))

        return found

    def highlight_text(self):
        found_instances = self.find_text()
        for page_num, instances in found_instances:
            page = self.doc[page_num]
            texts_props = self.text_properties(page)
            for props, inst in zip(texts_props, instances):
                if not props["font"] in FONTS:
                    print(f"Font path not found for {props['font']}\n")
                    continue

                inst[2] -= props["extra_width"]
                highlight = page.add_highlight_annot(inst)
                highlight.update()

    def text_properties(self, page):
        properties = []
        text_dict = page.get_text("dict")
        for block in text_dict["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if self.target_text in span["text"]:
                        words = span["text"].split()
                        for word in words:
                            cleaned_word = re.sub(r'[^A-Za-z0-9]', '', word)
                            if cleaned_word == self.target_text:
                                width = 0
                                if word[:-1] == self.target_text:
                                    if not span["font"] in FONTS:
                                        print(f"Font path not found for {span['font']}\n")
                                        continue
                                    fontObj = fitz.Font(fontname=span["font"], fontfile=FONTS.get(span["font"]))
                                    width = fontObj.text_length(word[-1], fontsize=span["size"])
                                properties.append({
                                    "font_size": span["size"],
                                    "font": span["font"],
                                    "color": span["color"],
                                    "extra_width": width
                                })
        return properties

    def text_color(self, color):
        found_instances = self.find_text()
        for page_num, instances in found_instances:
            page = self.doc[page_num]

            texts_props = self.text_properties(page)
            for props, inst in zip(texts_props, instances):
                if not props["font"] in FONTS:
                    print(f"Font path not found for {props['font']}\n")
                    continue

                inst[2] -= props["extra_width"]
                page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()

                font_path = FONTS.get(props["font"])
                page.insert_text(
                    (inst[0], inst[1] + props["font_size"]),
                    self.target_text,
                    fontsize=props["font_size"],
                    fontfile=font_path,
                    fontname=props["font"],
                    color=color
                )

    def save(self):
        self.doc.save("output.pdf")

text = "PDF"
processor = PDFProcessor("sample.pdf", text)
# processor.highlight_text()
processor.text_color((1, 0, 0))
processor.save()