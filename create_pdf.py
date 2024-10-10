from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

pdf_file = "flex_layout.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=A4)

styles = getSampleStyleSheet()
style_normal = styles['Normal']
style_normal.fontName = 'DejaVu'

content = []

table_data = [
    [Paragraph("Левый элемент", style_normal),
     Paragraph("Правый элемент", style_normal)]
]

table = Table(table_data)
table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))

content.append(table)
doc.build(content)

print(f"PDF создан: {pdf_file}")
