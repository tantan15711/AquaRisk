from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
DOCX_PATH = OUT / "Sprint_AquaRisk_6_semanas.docx"

BLACK = "111111"
TEXT = "1F2933"
GRAY_HEADER = "D9D9D9"
GRAY_ALT = "FAFAFA"
GRID = "BFBFBF"
BAR_COLORS = {
    "req": "A8DADC",
    "design": "C7E9B0",
    "db": "D8C8F0",
    "dev": "9FD3C7",
    "int": "B8C0E0",
    "test": "F8DFA6",
    "fix": "F2B5B5",
    "close": "CDE7C9",
}


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def border(cell, color=GRID):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def margins(cell, top=80, start=90, bottom=80, end=90):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def cell_text(cell, text, bold=False, size=8.2, align=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    if align:
        paragraph.alignment = align
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(BLACK if bold else TEXT)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    margins(cell)
    border(cell)


def style_table(table, header=True):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            border(cell)
            margins(cell)
            if header and row_index == 0:
                shade(cell, GRAY_HEADER)
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor.from_string(BLACK)
            elif row_index % 2 == 0:
                shade(cell, GRAY_ALT)


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.style = f"Heading {level}"
    paragraph.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.color.rgb = RGBColor.from_string(BLACK)
    run.font.size = Pt(12 if level == 1 else 10.5)
    run.bold = True
    return paragraph


def add_body(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.08
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(TEXT)


def add_bullet(doc, text):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor.from_string(TEXT)


def add_table(doc, rows, widths=None, center_cols=None):
    center_cols = set(center_cols or [])
    table = doc.add_table(rows=1, cols=len(rows[0]))
    for col_index, header in enumerate(rows[0]):
        cell_text(table.rows[0].cells[col_index], header, bold=True, size=7.8, align=WD_ALIGN_PARAGRAPH.CENTER)
    for row_index, row_data in enumerate(rows[1:], start=1):
        row = table.add_row().cells
        for col_index, value in enumerate(row_data):
            align = WD_ALIGN_PARAGRAPH.CENTER if col_index in center_cols else None
            cell_text(row[col_index], value, size=7.6, align=align)
    if widths:
        for col_index, width in enumerate(widths):
            for cell in table.columns[col_index].cells:
                cell.width = Inches(width)
    style_table(table)
    return table


def build_document():
    OUT.mkdir(exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    run = title.add_run("Sprint Contra el Tiempo: Plan de trabajo para AquaRisk")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(15)
    run.font.color.rgb = RGBColor.from_string(BLACK)

    add_heading(doc, "Situación del proyecto", 1)
    add_body(
        doc,
        "La empresa de desarrollo asumió el compromiso de entregar AquaRisk en un plazo máximo de seis semanas. Para efectos del ejercicio, AquaRisk se trabaja como una aplicación móvil/web enfocada en el monitoreo de lluvia, riesgo de inundación, ubicación del usuario y alertas preventivas. Aunque el alcance funcional no es enorme, sí requiere una planeación cuidadosa porque intervienen diseño de interfaz, base de datos, servicios externos, permisos de ubicación, pruebas en dispositivos y capacitación al cliente.",
    )
    add_body(
        doc,
        "El principal reto del equipo es evitar que las actividades se ejecuten de manera aislada. Si backend, frontend, diseño y pruebas avanzan sin coordinación, el proyecto puede llegar a la última semana con pantallas incompletas, errores de integración o funciones difíciles de explicar al usuario.",
    )

    add_heading(doc, "Equipo de trabajo", 2)
    add_table(
        doc,
        [
            ["Rol solicitado", "Integrante", "Responsabilidad principal"],
            ["Líder de Proyecto", "Osmar Enrique Ramos Reyes", "Coordinar alcance, tiempos, prioridades, seguimiento y comunicación con el cliente."],
            ["Programador Frontend", "Alessandro Bravo Flores", "Implementar pantallas principales, mapa, lectura de riesgo y flujo responsivo."],
            ["Programadora Frontend", "Valeria Montes García", "Apoyar componentes visuales, estados de la interfaz y validación en dispositivos."],
            ["Programador Backend", "Ángel Eduardo Pineda Rodas", "Diseñar servicios, lógica de datos, alertas y conexión con Supabase."],
            ["Programador Backend", "Diego Iván Morales Cruz", "Apoyar estructura de base de datos, consultas, seguridad y pruebas de servicios."],
            ["Diseñador UX/UI", "Brian Bezares Ávalos", "Definir experiencia, navegación, jerarquía visual y claridad de la información."],
            ["Tester", "Ana Paula Orellana López", "Diseñar y ejecutar pruebas funcionales, móviles, de permisos y de entrega final."],
        ],
        widths=[1.55, 1.65, 3.45],
    )

    add_heading(doc, "1. Organización de actividades", 1)
    add_body(
        doc,
        "El orden se definió considerando qué actividades desbloquean a las demás. El levantamiento de requisitos va primero porque establece qué se entregará y qué queda fuera. Después se trabajan en paralelo el diseño UX/UI y el diseño de base de datos. Con esas bases, backend y frontend avanzan al mismo tiempo; posteriormente se realiza integración, pruebas, corrección de errores y capacitación.",
    )
    add_table(
        doc,
        [
            ["Orden", "Actividad", "Duración", "Responsable", "Dependencia directa"],
            ["1", "Levantamiento de requisitos", "3 días", "Osmar + equipo", "Inicio del proyecto"],
            ["2", "Diseño UX/UI", "5 días", "Brian", "Requisitos principales definidos"],
            ["3", "Diseño de base de datos", "2 días", "Ángel + Diego", "Requisitos principales definidos"],
            ["4", "Desarrollo backend", "10 días", "Ángel + Diego", "Diseño de base de datos"],
            ["5", "Desarrollo frontend", "9 días", "Alessandro + Valeria", "Diseño UX/UI y criterios de navegación"],
            ["6", "Integración", "3 días", "Osmar + frontend + backend", "Módulos principales"],
            ["7", "Pruebas", "4 días", "Ana Paula", "Integración funcional"],
            ["8", "Corrección de errores", "3 días", "Todo el equipo", "Resultados de pruebas"],
            ["9", "Capacitación al cliente", "2 días", "Osmar + Ana Paula", "Versión estable"],
        ],
        widths=[0.45, 1.45, 0.65, 1.45, 2.1],
        center_cols={0, 2},
    )
    add_heading(doc, "Actividades simultáneas y dependencias", 2)
    for item in [
        "Diseño UX/UI y diseño de base de datos pueden avanzar en paralelo después del levantamiento de requisitos.",
        "Desarrollo frontend y backend se ejecutan al mismo tiempo si existe un acuerdo mínimo sobre datos y pantallas.",
        "Los casos de prueba pueden prepararse durante el desarrollo, aunque su ejecución formal dependa de la integración.",
        "La capacitación puede preparar material desde la semana 5, pero debe cerrarse con una versión estable.",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "2. Priorización con Matriz de Eisenhower", 1)
    add_body(
        doc,
        "La matriz se aplicó para separar lo que protege la fecha de entrega de lo que solo mejora la presentación. La prioridad se asignó según si la actividad desbloquea otra, si afecta la calidad del producto y si puede poner en riesgo la fecha final.",
    )
    add_table(
        doc,
        [
            ["", "Urgente", "No urgente"],
            ["Importante", "Requisitos, base de datos, backend, frontend, integración, pruebas y corrección de errores.", "Diseño UX/UI, capacitación, documentación breve y criterios de aceptación."],
            ["No importante", "Ajustes visuales menores, capturas y material de apoyo para exposición.", "Historial avanzado, perfiles complejos, reportes extensos y mejoras no solicitadas."],
        ],
        widths=[0.95, 2.8, 2.8],
    )
    add_heading(doc, "Justificación de la priorización", 2)
    for item in [
        "Urgente e importante: son actividades que sostienen la entrega; si fallan, no existe una versión confiable.",
        "Importante pero no urgente: aportan calidad y claridad, pero se pueden planear sin bloquear el desarrollo central.",
        "Urgente pero no importante: ayudan a la exposición, pero no deben desplazar tareas críticas.",
        "Ni urgente ni importante: se consideran mejoras futuras para no aumentar retrabajo.",
    ]:
        add_bullet(doc, item)

    doc.add_page_break()
    add_heading(doc, "3. Cronograma de trabajo tipo Gantt", 1)
    add_body(
        doc,
        "El cronograma considera seis semanas laborales, del lunes 20 de julio al viernes 28 de agosto de 2026. Las barras muestran el periodo de trabajo de cada actividad y permiten revisar fechas, responsable, duración y dependencias.",
    )
    gantt_rows = [
        ["Actividad", "Responsable", "Dur.", "Dep.", "S1\n20-24 jul", "S2\n27-31 jul", "S3\n3-7 ago", "S4\n10-14 ago", "S5\n17-21 ago", "S6\n24-28 ago"],
        ["Levantamiento de requisitos", "Osmar + equipo", "3d", "Inicio", "20-22", "", "", "", "", ""],
        ["Diseño UX/UI", "Brian", "5d", "Req.", "23-24", "27-29", "", "", "", ""],
        ["Diseño de base de datos", "Ángel + Diego", "2d", "Req.", "23-24", "", "", "", "", ""],
        ["Desarrollo backend", "Ángel + Diego", "10d", "BD", "", "27-31", "3-7", "", "", ""],
        ["Desarrollo frontend", "Alessandro + Valeria", "9d", "UX/UI", "", "30-31", "3-7", "10-11", "", ""],
        ["Integración", "Osmar + front + back", "3d", "Mód.", "", "", "", "10-12", "", ""],
        ["Pruebas", "Ana Paula", "4d", "Integr.", "", "", "", "13-14", "17-18", ""],
        ["Corrección de errores", "Todo el equipo", "3d", "Pruebas", "", "", "", "", "19-21", ""],
        ["Capacitación al cliente", "Osmar + Ana Paula", "2d", "Estable", "", "", "", "", "", "24-25"],
        ["Cierre y entrega final", "Osmar + equipo", "3d", "Cap.", "", "", "", "", "", "26-28"],
    ]
    gantt = add_table(doc, gantt_rows, widths=[1.05, 0.9, 0.35, 0.5, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55], center_cols={2, 4, 5, 6, 7, 8, 9})
    for row_index, color_key in enumerate(["req", "design", "db", "dev", "dev", "int", "test", "fix", "close", "close"], start=1):
        for col_index in range(4, 10):
            if gantt_rows[row_index][col_index]:
                shade(gantt.rows[row_index].cells[col_index], BAR_COLORS[color_key])
                for paragraph in gantt.rows[row_index].cells[col_index].paragraphs:
                    for run in paragraph.runs:
                        run.bold = True

    add_body(
        doc,
        "Para evitar retrasos, el equipo revisará el avance al cierre de cada semana. Si una tarea crítica se atrasa más de un día, el líder deberá reasignar apoyo temporal antes de que el retraso afecte integración o pruebas.",
    )

    doc.add_page_break()
    add_heading(doc, "4. Gestión del tiempo y solución al imprevisto", 1)
    add_body(
        doc,
        "Problemática asignada para AquaRisk: durante el desarrollo se detecta que la información de lluvia puede variar entre la API meteorológica y lo que el usuario observa en tiempo real. Además, algunos dispositivos pueden pedir permisos de ubicación o notificaciones de forma distinta. Este imprevisto afecta la confiabilidad de la app, por lo que no puede dejarse para el final.",
    )
    add_table(
        doc,
        [
            ["Pregunta", "Respuesta propuesta"],
            ["¿Qué actividades cambiarían?", "Se adelantaría una integración parcial desde la semana 3 para probar datos reales, ubicación y alertas antes de terminar todas las pantallas."],
            ["¿Qué tareas pueden adelantarse?", "Casos de prueba, definición de datos mínimos, estructura de Supabase, permisos de ubicación, mensajes de alerta y validación de API."],
            ["¿Qué tareas deben retrasarse?", "Funciones secundarias, mejoras visuales no esenciales, reportes avanzados e historial de consultas."],
            ["¿Cómo evitarían retrasar la entrega?", "Congelando alcance en la semana 5, haciendo revisiones diarias cortas, registrando bloqueos, integrando por módulos y dejando reserva de tiempo."],
        ],
        widths=[1.6, 4.9],
    )
    add_heading(doc, "Acciones concretas de control", 2)
    for item in [
        "Osmar revisará cada dos días si las tareas críticas están dentro del tiempo planeado.",
        "Backend y frontend acordarán desde la semana 2 el formato de datos.",
        "Ana Paula iniciará pruebas antes de la integración final.",
        "Brian mantendrá el diseño enfocado en claridad de uso.",
        "Las funciones no indispensables se documentarán como mejoras futuras.",
    ]:
        add_bullet(doc, item)

    add_heading(doc, "5. Conclusión del equipo", 1)
    add_body(
        doc,
        "Como equipo, concluimos que AquaRisk puede entregarse en seis semanas siempre que se respete el orden de actividades y se mantenga controlado el alcance. La planeación propuesta permite avanzar en paralelo sin perder de vista las dependencias principales. También ayuda a detectar riesgos antes de la última semana, especialmente en integración, ubicación, datos de lluvia y pruebas en dispositivos. Consideramos que la mejor forma de cumplir es entregar una versión funcional y estable, con interfaz clara y capacitación básica para el cliente, dejando las funciones adicionales para una etapa posterior.",
    )
    add_heading(doc, "Referencias consultadas", 1)
    for ref in [
        "Schwaber, K. y Sutherland, J. (2020). The Scrum Guide.",
        "Project Management Institute. Fundamentos de gestión de cronograma y control de proyectos.",
        "Covey, S. R. (1989). The 7 Habits of Highly Effective People. Matriz urgente/importante.",
        "Open-Meteo. Documentación de Forecast API.",
        "MDN Web Docs. Geolocation API y Notifications API.",
        "Supabase. Documentación de base de datos y servicios backend.",
    ]:
        add_bullet(doc, ref)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("AquaRisk - Plan de trabajo")
    run.font.name = "Arial"
    run.font.size = Pt(8)

    doc.save(DOCX_PATH)
    print(DOCX_PATH)


if __name__ == "__main__":
    build_document()
