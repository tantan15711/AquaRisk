from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
DOCX_PATH = OUT / "Sprint_AquaRisk_6_semanas.docx"

PURPLE = "5B3C88"
PURPLE_DARK = "32215A"
TEAL = "10A7B8"
GREEN = "4CB963"
LAVENDER = "EFE8FA"
MINT = "E8F8F1"
BLUE_SOFT = "EAF7FB"
GRAY = "F4F6F8"
INK = "182233"
WHITE = "FFFFFF"
YELLOW = "FFF3C4"
RED_SOFT = "FBE2E2"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color="D8DDE6", size="6"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=90, start=120, bottom=90, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_text(cell, text, bold=False, color=INK, size=9, align=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    if align:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell)


def style_table(table, header_fill=PURPLE, header_color=WHITE):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            set_cell_border(cell)
            set_cell_margins(cell)
            if row_index == 0:
                set_cell_shading(cell, header_fill)
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor.from_string(header_color)
                        run.bold = True
            else:
                set_cell_shading(cell, WHITE)


def add_heading(doc, text, level=1):
    paragraph = doc.add_heading(text, level=level)
    color = PURPLE_DARK if level == 1 else PURPLE
    for run in paragraph.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor.from_string(color)
        run.bold = True
    paragraph.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    paragraph.paragraph_format.space_after = Pt(5)
    return paragraph


def add_body(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.08
    run = paragraph.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor.from_string(INK)
    return paragraph


def add_callout(doc, title, text, fill=BLUE_SOFT):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.columns[0].width = Inches(9.0)
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_border(cell, color="BFDDE9")
    set_cell_margins(cell, top=130, bottom=130, start=180, end=180)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(2)
    title_run = paragraph.add_run(title)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor.from_string(PURPLE_DARK)
    title_run.font.size = Pt(10.5)
    paragraph.add_run("\n")
    body_run = paragraph.add_run(text)
    body_run.font.size = Pt(10)
    body_run.font.color.rgb = RGBColor.from_string(INK)
    return table


def add_page_break(doc):
    doc.add_page_break()


def build_document():
    OUT.mkdir(exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11)
    section.page_height = Inches(8.5)
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)
    styles["Normal"].font.color.rgb = RGBColor.from_string(INK)

    # Cover
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(4)
    run = title.add_run("Sprint Contra el Tiempo")
    run.bold = True
    run.font.size = Pt(30)
    run.font.color.rgb = RGBColor.from_string(PURPLE_DARK)

    subtitle = doc.add_paragraph()
    subtitle_run = subtitle.add_run(
        "Plan de trabajo para entregar AquaRisk en 6 semanas"
    )
    subtitle_run.font.size = Pt(17)
    subtitle_run.font.color.rgb = RGBColor.from_string(TEAL)
    subtitle.paragraph_format.space_after = Pt(12)

    add_callout(
        doc,
        "Enfoque del equipo",
        "AquaRisk se plantea como una aplicación web responsiva para monitorear lluvia, ubicación del usuario, zonas de riesgo y alertas preventivas. El reto no es solo programar rápido, sino ordenar las dependencias para llegar a una entrega demostrable sin sacrificar pruebas.",
        fill=MINT,
    )

    meta = doc.add_table(rows=5, cols=2)
    widths = [Inches(2.3), Inches(6.7)]
    for column_index, width in enumerate(widths):
        for cell in meta.columns[column_index].cells:
            cell.width = width
    rows = [
        ("Proyecto", "AquaRisk - monitoreo de lluvia e inundación"),
        ("Periodo", "6 semanas: 20 de julio al 28 de agosto de 2026"),
        ("Metodología de trabajo", "Sprint con entregas parciales, revisión semanal y control de alcance"),
        ("Producto final", "Aplicación funcional, cronograma, pruebas, capacitación y entrega documentada"),
        ("Líder del equipo", "Osmar Enrique Ramos Reyes"),
    ]
    for row, (label, value) in zip(meta.rows, rows):
        set_cell_text(row.cells[0], label, bold=True, color=WHITE)
        set_cell_shading(row.cells[0], PURPLE)
        set_cell_text(row.cells[1], value)
    for row in meta.rows:
        for cell in row.cells:
            set_cell_border(cell, color="D6CAE8")

    add_page_break(doc)

    add_heading(doc, "1. Organización del proyecto", 1)
    add_body(
        doc,
        "Para no perder tiempo en retrabajo, el equipo decidió ordenar el proyecto desde lo que desbloquea a los demás: primero entender qué debe hacer AquaRisk, después diseñar la experiencia y la base de datos, y de ahí avanzar en paralelo con frontend y backend. Las pruebas no se dejan hasta el último día; se preparan desde antes y se ejecutan con más fuerza cuando la integración ya está estable.",
    )

    team = doc.add_table(rows=1, cols=3)
    headers = ["Integrante", "Rol principal", "Responsabilidad dentro del sprint"]
    for cell, text in zip(team.rows[0].cells, headers):
        set_cell_text(cell, text, bold=True, color=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, PURPLE)
    team_rows = [
        ("Osmar Enrique Ramos Reyes", "Líder de proyecto", "Coordina prioridades, seguimiento semanal, dependencias y comunicación con el cliente."),
        ("Alessandro Bravo Flores", "Frontend", "Construcción de vistas, conexión con mapas, estados de lluvia y flujo móvil."),
        ("Valeria Montes García", "Frontend", "Apoyo en componentes responsivos, permisos de ubicación y visualización del pronóstico."),
        ("Ángel Eduardo Pineda Rodas", "Backend", "Estructura de datos, consumo de servicios, lógica de alertas y conexión con Supabase."),
        ("Diego Iván Morales Cruz", "Backend", "Apoyo en consultas, seguridad de datos, endpoints y revisión de integración."),
        ("Brian Bezares Ávalos", "Diseño UX/UI", "Diseño de interfaz, lectura clara de riesgo, paleta visual y experiencia del usuario."),
        ("Ana Paula Orellana López", "Tester", "Casos de prueba, validación móvil, errores, permisos y revisión final antes de entrega."),
    ]
    for item in team_rows:
        row = team.add_row().cells
        for cell, text in zip(row, item):
            set_cell_text(cell, text, size=8.7)
    style_table(team)

    add_heading(doc, "Orden lógico, paralelismo y dependencias", 2)
    order = doc.add_table(rows=1, cols=6)
    order_headers = [
        "#",
        "Actividad",
        "Duración",
        "Responsable",
        "Depende de",
        "Puede avanzar al mismo tiempo que",
    ]
    for cell, text in zip(order.rows[0].cells, order_headers):
        set_cell_text(cell, text, bold=True, color=WHITE, size=8.8, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, PURPLE)
    order_rows = [
        ("1", "Levantamiento de requisitos", "3 días", "Osmar + equipo", "Inicio del proyecto", "Preparación de tablero y criterios de aceptación"),
        ("2", "Diseño UX/UI", "5 días", "Brian", "Requisitos base", "Diseño de base de datos y contratos de API"),
        ("3", "Diseño de base de datos", "2 días", "Ángel + Diego", "Requisitos base", "UX/UI y definición técnica del backend"),
        ("4", "Desarrollo backend", "10 días", "Ángel + Diego", "Base de datos aprobada", "Frontend con datos de prueba"),
        ("5", "Desarrollo frontend", "9 días", "Alessandro + Valeria", "UX/UI aprobado", "Backend y casos de prueba iniciales"),
        ("6", "Integración", "3 días", "Osmar + front + back", "Módulos principales listos", "Pruebas exploratorias"),
        ("7", "Pruebas", "4 días", "Ana Paula", "Integración funcional", "Correcciones menores y documentación"),
        ("8", "Corrección de errores", "3 días", "Todo el equipo", "Reporte de pruebas", "Capacitación preliminar"),
        ("9", "Capacitación al cliente", "2 días", "Osmar + Ana Paula", "Versión estable", "Cierre, manual breve y entrega final"),
    ]
    for item in order_rows:
        row = order.add_row().cells
        for cell, text in zip(row, item):
            set_cell_text(cell, text, size=8.2)
    style_table(order)

    add_callout(
        doc,
        "Ruta crítica",
        "La cadena que más cuida el equipo es: requisitos -> base de datos -> backend -> integración -> pruebas -> corrección -> capacitación. Frontend avanza en paralelo, pero se vuelve crítico si las pantallas principales no están listas para integrar en la semana 4.",
        fill=BLUE_SOFT,
    )

    add_page_break(doc)

    add_heading(doc, "2. Priorización con Matriz de Eisenhower", 1)
    add_body(
        doc,
        "La matriz se usó para separar lo que realmente protege la fecha de entrega de lo que solo mejora la presentación. En un sprint de 6 semanas, casi todo parece urgente; por eso la decisión fue priorizar aquello que desbloquea trabajo, reduce riesgo o permite probar con usuarios antes del cierre.",
    )

    matrix = doc.add_table(rows=3, cols=3)
    matrix_data = [
        ("", "Urgente", "No urgente"),
        (
            "Importante",
            "Levantamiento de requisitos, diseño de base de datos, desarrollo backend, desarrollo frontend, integración, pruebas y corrección de errores.\n\nJustificación: si cualquiera de estas actividades falla, el producto no se puede entregar o queda sin validar.",
            "Diseño UX/UI, documentación breve, capacitación al cliente y criterios de aceptación.\n\nJustificación: no siempre bloquean el primer día, pero elevan la calidad, evitan confusiones y ayudan a que el cliente use AquaRisk sin depender del equipo.",
        ),
        (
            "No importante",
            "Ajustes menores de presentación, preparación de capturas y material de apoyo para exposición.\n\nJustificación: tienen fecha cercana y conviene terminarlos, pero no deben quitar tiempo al funcionamiento principal.",
            "Funciones extra fuera del alcance: historial avanzado, perfiles de usuario complejos, reportes extensos o mapas decorativos.\n\nJustificación: pueden ser buenas ideas para otra versión, pero meterlas ahora pondría en riesgo la entrega.",
        ),
    ]
    for row_index, row in enumerate(matrix.rows):
        for col_index, cell in enumerate(row.cells):
            text = matrix_data[row_index][col_index]
            set_cell_text(cell, text, bold=(row_index == 0 or col_index == 0), size=8.7)
            if row_index == 0 or col_index == 0:
                set_cell_shading(cell, PURPLE)
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = RGBColor.from_string(WHITE)
            elif row_index == 1 and col_index == 1:
                set_cell_shading(cell, MINT)
            elif row_index == 1 and col_index == 2:
                set_cell_shading(cell, LAVENDER)
            elif row_index == 2 and col_index == 1:
                set_cell_shading(cell, YELLOW)
            else:
                set_cell_shading(cell, GRAY)
            set_cell_border(cell, color="D8DDE6")
    matrix.alignment = WD_TABLE_ALIGNMENT.CENTER

    add_heading(doc, "Decisiones de priorización", 2)
    decisions = [
        "El alcance mínimo entregable queda formado por ubicación, consulta de clima, lectura de riesgo, mapa, alertas preventivas y pruebas en móvil.",
        "Las mejoras visuales se trabajan solo cuando no afecten el avance del backend, integración o pruebas.",
        "La capacitación se prepara desde la semana 5 para que no se vuelva una tarea improvisada al final.",
        "Cualquier función nueva debe pasar por el líder del proyecto; si no ayuda a la entrega de 6 semanas, se deja para una segunda versión.",
    ]
    for text in decisions:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(text)
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor.from_string(INK)

    add_page_break(doc)

    add_heading(doc, "3. Cronograma tipo Gantt", 1)
    add_body(
        doc,
        "El cronograma se construyó con semanas laborales de lunes a viernes. La semana 6 se reserva para capacitación, cierre y margen de seguridad, porque en un proyecto con datos externos, GPS y notificaciones siempre puede aparecer algún ajuste final.",
    )

    gantt = doc.add_table(rows=1, cols=10)
    gantt_headers = [
        "Actividad",
        "Responsable",
        "Duración",
        "Dependencia",
        "Sem. 1\n20-24 jul",
        "Sem. 2\n27-31 jul",
        "Sem. 3\n3-7 ago",
        "Sem. 4\n10-14 ago",
        "Sem. 5\n17-21 ago",
        "Sem. 6\n24-28 ago",
    ]
    for cell, text in zip(gantt.rows[0].cells, gantt_headers):
        set_cell_text(cell, text, bold=True, color=WHITE, size=7.8, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, PURPLE)
    gantt_rows = [
        ("Levantamiento de requisitos", "Osmar + equipo", "3 días", "Inicio", ["20-22", "", "", "", "", ""]),
        ("Diseño UX/UI", "Brian", "5 días", "Requisitos", ["23-24", "27-29", "", "", "", ""]),
        ("Diseño de base de datos", "Ángel + Diego", "2 días", "Requisitos", ["23-24", "", "", "", "", ""]),
        ("Desarrollo backend", "Ángel + Diego", "10 días", "BD", ["", "27-31", "3-7", "", "", ""]),
        ("Desarrollo frontend", "Alessandro + Valeria", "9 días", "UX/UI", ["", "30-31", "3-7", "10-11", "", ""]),
        ("Integración", "Osmar + front + back", "3 días", "Módulos base", ["", "", "", "10-12", "", ""]),
        ("Pruebas", "Ana Paula", "4 días", "Integración", ["", "", "", "13-14", "17-18", ""]),
        ("Corrección de errores", "Todo el equipo", "3 días", "Pruebas", ["", "", "", "", "19-21", ""]),
        ("Capacitación al cliente", "Osmar + Ana Paula", "2 días", "Versión estable", ["", "", "", "", "", "24-25"]),
        ("Cierre y entrega final", "Osmar + equipo", "3 días", "Capacitación", ["", "", "", "", "", "26-28"]),
    ]
    palette = [TEAL, GREEN, PURPLE, TEAL, GREEN, PURPLE, TEAL, "D8527C", GREEN, PURPLE]
    for index, item in enumerate(gantt_rows):
        row = gantt.add_row().cells
        base = item[:4]
        weeks = item[4]
        for cell, text in zip(row[:4], base):
            set_cell_text(cell, text, size=7.5)
            set_cell_shading(cell, WHITE)
        for week_cell, text in zip(row[4:], weeks):
            if text:
                set_cell_text(week_cell, text, bold=True, color=WHITE, size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
                set_cell_shading(week_cell, palette[index])
            else:
                set_cell_text(week_cell, "", size=7.5)
                set_cell_shading(week_cell, "FAFBFC")
        for cell in row:
            set_cell_border(cell, color="D8DDE6")
    style_table(gantt)

    add_callout(
        doc,
        "Lectura del Gantt",
        "Las barras muestran cuándo se trabaja cada actividad. Las tareas de frontend y backend se empalman porque no tiene sentido esperar a que una termine por completo; se integran por módulos para detectar fallas antes de la última semana.",
        fill=LAVENDER,
    )

    add_page_break(doc)

    add_heading(doc, "4. Gestión del tiempo y solución al imprevisto", 1)
    add_body(
        doc,
        "Imprevisto trabajado por el equipo: durante la integración, AquaRisk puede presentar diferencias entre el pronóstico y la lluvia real observada, además de comportamientos distintos en permisos de ubicación, notificaciones o capa de radar según el dispositivo. Este imprevisto es creíble porque el proyecto depende de datos externos y de permisos del navegador.",
    )

    questions = doc.add_table(rows=1, cols=2)
    for cell, text in zip(questions.rows[0].cells, ["Pregunta", "Respuesta del equipo"]):
        set_cell_text(cell, text, bold=True, color=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, PURPLE)
    q_rows = [
        (
            "¿Qué actividades cambiarían?",
            "Adelantaríamos integración técnica desde la semana 3, aunque sea con módulos incompletos. También moveríamos las pruebas de permisos, GPS y notificaciones a una revisión temprana para no descubrir fallas en la semana final.",
        ),
        (
            "¿Qué tareas pueden adelantarse?",
            "Casos de prueba, contrato de datos entre frontend y backend, estructura de Supabase, pantallas base, guía breve para cliente y validación en celular. Todo eso puede avanzar sin esperar a tener el sistema completo.",
        ),
        (
            "¿Qué tareas deben retrasarse?",
            "Extras visuales, mapas secundarios, estadísticas históricas y funciones que no sean necesarias para demostrar lluvia, ubicación, zonas de riesgo y alertas. Es mejor entregar una versión clara que una versión grande pero inestable.",
        ),
        (
            "¿Cómo evitarían retrasar la entrega?",
            "Con revisión diaria de 15 minutos, tablero Kanban, responsables visibles, integración por módulos, pruebas desde la semana 3, congelamiento de alcance al iniciar la semana 5 y una reserva operativa en la semana 6.",
        ),
    ]
    for question, answer in q_rows:
        row = questions.add_row().cells
        set_cell_text(row[0], question, bold=True, size=8.8)
        set_cell_shading(row[0], MINT)
        set_cell_text(row[1], answer, size=8.8)
    style_table(questions)

    add_heading(doc, "Medidas concretas de control", 2)
    controls = [
        ("Control de alcance", "A partir de la semana 5 solo se corrigen errores y se ajusta claridad; no se agregan funciones nuevas."),
        ("Revisión técnica", "Backend y frontend validan juntos los datos de clima, ubicación y riesgo antes de pasar a pruebas formales."),
        ("Pruebas reales", "Ana Paula prueba en móvil, escritorio y navegador con permisos concedidos, bloqueados y restablecidos."),
        ("Comunicación", "Osmar registra acuerdos, bloqueos y cambios para que el equipo no trabaje sobre suposiciones."),
    ]
    control_table = doc.add_table(rows=1, cols=2)
    for cell, text in zip(control_table.rows[0].cells, ["Medida", "Aplicación"]):
        set_cell_text(cell, text, bold=True, color=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, PURPLE)
    for label, value in controls:
        row = control_table.add_row().cells
        set_cell_text(row[0], label, bold=True, size=9)
        set_cell_shading(row[0], BLUE_SOFT)
        set_cell_text(row[1], value, size=9)
    style_table(control_table)

    add_page_break(doc)

    add_heading(doc, "5. Conclusión del equipo", 1)
    add_body(
        doc,
        "Como equipo, consideramos que AquaRisk sí puede entregarse en 6 semanas si se cuida el orden de las dependencias y se evita crecer el alcance a mitad del sprint. La clave es no esperar hasta el final para integrar: backend, frontend, diseño y pruebas deben verse como partes conectadas del mismo avance. También aprendimos que una aplicación con clima, GPS y alertas no depende únicamente del código; depende de permisos, datos externos y validación en dispositivos reales. Por eso dejamos una semana final con margen, capacitación y cierre. Nuestra prioridad es entregar una versión funcional, clara para el usuario y defendible ante el cliente, aunque algunas funciones avanzadas queden para una segunda etapa.",
    )

    add_heading(doc, "Referencias", 1)
    refs = [
        "Schwaber, K. y Sutherland, J. (2020). The Scrum Guide. https://scrumguides.org/scrum-guide.html",
        "Project Management Institute. Project schedule management y control de cronogramas. https://www.pmi.org/",
        "Covey, S. R. (1989). The 7 Habits of Highly Effective People. Matriz urgente/importante como apoyo para priorización.",
        "Open-Meteo. Forecast API Documentation. https://open-meteo.com/en/docs",
        "RainViewer. Weather Maps API. https://www.rainviewer.com/api/weather-maps-api.html",
        "MDN Web Docs. Geolocation API y Notifications API. https://developer.mozilla.org/",
        "Supabase. Documentation. https://supabase.com/docs",
    ]
    for reference in refs:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(reference)
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor.from_string(INK)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("AquaRisk | Cronograma de 6 semanas | Entrega académica")
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor.from_string("6B7280")

    doc.save(DOCX_PATH)
    return DOCX_PATH


if __name__ == "__main__":
    path = build_document()
    print(path)
