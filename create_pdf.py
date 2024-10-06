from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

pdf_file = "order_print.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=A4)

styles = getSampleStyleSheet()
style_normal = styles['Normal']
style_normal.fontName = 'Helvetica'
style_title = styles['Title']

content = [
    Paragraph("Документ Перевозки", style_title),
    Spacer(1, 12),
    Paragraph("Номер перевозки: 0006493170", style_normal),
    Paragraph("Номер поставки: 0032692534", style_normal),
    Paragraph("Распечатано: 04.10.21 17:23", style_normal),
    Paragraph("Последние изменения: 04.10.21 15:51", style_normal),
    Spacer(1, 12),
    Paragraph("Резюме перевозки", style_title)
]

summary_data = [
    ["Транспореон-ID", "730220899"],
    ["Отдел планирования", "Rockwool RU"],
    ["Диспетчер", "TP XP Service Account"],
    ["Вес", "3 542,50 kg"],
    ["Объем", "90,00 cbm"],
    ["Транспортное средство", "Грузовик 90 м3"],
    ["Алиас", "YN8464XL"]
]

summary_table = Table(summary_data)
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

content.append(summary_table)
content.append(Spacer(1, 12))

content.append(Paragraph("Цена", style_title))
price_data = [
    ["Предложение", "38 700,00 RUB"],
    ["Крайний срок", "30.09.21 14:36"],
    ["Перевозчик", "ООО \"Евразия\""],
    ["Адрес", "УЛ. ГАГАРИНА, ДОМ 7А, ОФИС 404, Челябинск"],
    ["Телефон", "+79068661989"]
]

price_table = Table(price_data)
price_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

content.append(price_table)
content.append(Spacer(1, 12))

content.append(Paragraph("Комментарий к перевозке:", style_title))
content.append(Paragraph(
    "Freight Instructions: ОБЯЗАТЕЛЬНО НАЛИЧИЕ УСТАНОВЛЕННОГО ПРИЛОЖЕНИЯ Transporeon У ВОДИТЕЛЯ.", style_normal))

doc.build(content)
print(f"PDF создан: {pdf_file}")
