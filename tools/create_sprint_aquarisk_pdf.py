from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
PDF_PATH = OUT / "Sprint_AquaRisk_6_semanas.pdf"

PURPLE = colors.HexColor("#5B3C88")
PURPLE_DARK = colors.HexColor("#32215A")
TEAL = colors.HexColor("#10A7B8")
GREEN = colors.HexColor("#4CB963")
LAVENDER = colors.HexColor("#EFE8FA")
MINT = colors.HexColor("#E8F8F1")
BLUE_SOFT = colors.HexColor("#EAF7FB")
GRAY = colors.HexColor("#F4F6F8")
INK = colors.HexColor("#182233")
YELLOW = colors.HexColor("#FFF3C4")
RED_SOFT = colors.HexColor("#FBE2E2")
WHITE = colors.white

FONT_REGULAR = "ArialAqua"
FONT_BOLD = "ArialAqua-Bold"
pdfmetrics.registerFont(TTFont(FONT_REGULAR, r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"))


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="AquaTitle",
        fontName=FONT_BOLD,
        fontSize=30,
        leading=34,
        textColor=PURPLE_DARK,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="AquaSubtitle",
        fontName=FONT_REGULAR,
        fontSize=16,
        leading=20,
        textColor=TEAL,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Aqua",
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        textColor=PURPLE_DARK,
        spaceBefore=4,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Aqua",
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=PURPLE,
        spaceBefore=8,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyAqua",
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=12.5,
        textColor=INK,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallAqua",
        fontName=FONT_REGULAR,
        fontSize=7.6,
        leading=9.3,
        textColor=INK,
        spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallBold",
        parent=styles["SmallAqua"],
        fontName=FONT_BOLD,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallWhite",
        parent=styles["SmallAqua"],
        fontName=FONT_BOLD,
        textColor=WHITE,
    )
)
styles.add(
    ParagraphStyle(
        name="TableHead",
        fontName=FONT_BOLD,
        fontSize=7.5,
        leading=8.6,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
)


def p(text, style="BodyAqua"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph(f"• {text}", styles["BodyAqua"])


def callout(title, text, fill=BLUE_SOFT):
    table = Table(
        [[p(f"<b>{title}</b><br/>{text}", "BodyAqua")]],
        colWidths=[9.75 * inch],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BFDDE9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def styled_table(data, widths, header=True, font_size=7.7):
    prepared = []
    for row_index, row in enumerate(data):
        prepared_row = []
        for item in row:
            if hasattr(item, "wrapOn"):
                prepared_row.append(item)
                continue
            style = "TableHead" if row_index == 0 and header else "SmallAqua"
            prepared_row.append(p(str(item).replace("\n", "<br/>"), style))
        prepared.append(prepared_row)

    table = Table(prepared, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DDE6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), PURPLE))
        commands.append(("TEXTCOLOR", (0, 0), (-1, 0), WHITE))
    for row_index in range(1 if header else 0, len(data)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#FBFCFE")))
    table.setStyle(TableStyle(commands))
    return table


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 7.5)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawCentredString(
        landscape(letter)[0] / 2,
        0.28 * inch,
        f"AquaRisk | Cronograma de 6 semanas | Página {doc.page}",
    )
    canvas.restoreState()


def build_pdf():
    OUT.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(letter),
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
    )
    story = []

    story.append(Paragraph("Sprint Contra el Tiempo", styles["AquaTitle"]))
    story.append(
        Paragraph("Plan de trabajo para entregar AquaRisk en 6 semanas", styles["AquaSubtitle"])
    )
    story.append(
        callout(
            "Enfoque del equipo",
            "AquaRisk se plantea como una aplicación web responsiva para monitorear lluvia, ubicación del usuario, zonas de riesgo y alertas preventivas. El reto no es solo programar rápido, sino ordenar dependencias para llegar a una entrega demostrable sin sacrificar pruebas.",
            MINT,
        )
    )
    story.append(Spacer(1, 10))
    meta = [
        [p("Proyecto", "SmallWhite"), "AquaRisk - monitoreo de lluvia e inundación"],
        [p("Periodo", "SmallWhite"), "6 semanas: 20 de julio al 28 de agosto de 2026"],
        [p("Metodología", "SmallWhite"), "Sprint con entregas parciales, revisión semanal y control de alcance"],
        [p("Producto final", "SmallWhite"), "Aplicación funcional, cronograma, pruebas, capacitación y entrega documentada"],
        [p("Líder del equipo", "SmallWhite"), "Osmar Enrique Ramos Reyes"],
    ]
    meta_table = styled_table(meta, [1.9 * inch, 7.85 * inch], header=False)
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PURPLE),
                ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
                ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
            ]
        )
    )
    story.append(meta_table)
    story.append(PageBreak())

    story.append(p("1. Organización del proyecto", "H1Aqua"))
    story.append(
        p(
            "Para no perder tiempo en retrabajo, el equipo decidió ordenar el proyecto desde lo que desbloquea a los demás: primero entender qué debe hacer AquaRisk, después diseñar la experiencia y la base de datos, y de ahí avanzar en paralelo con frontend y backend. Las pruebas se preparan desde antes y se ejecutan con más fuerza cuando la integración ya está estable."
        )
    )
    team = [
        ["Integrante", "Rol principal", "Responsabilidad dentro del sprint"],
        ["Osmar Enrique Ramos Reyes", "Líder de proyecto", "Coordina prioridades, seguimiento semanal, dependencias y comunicación con el cliente."],
        ["Alessandro Bravo Flores", "Frontend", "Construcción de vistas, conexión con mapas, estados de lluvia y flujo móvil."],
        ["Valeria Montes García", "Frontend", "Apoyo en componentes responsivos, permisos de ubicación y visualización del pronóstico."],
        ["Ángel Eduardo Pineda Rodas", "Backend", "Estructura de datos, consumo de servicios, lógica de alertas y conexión con Supabase."],
        ["Diego Iván Morales Cruz", "Backend", "Apoyo en consultas, seguridad de datos, endpoints y revisión de integración."],
        ["Brian Bezares Ávalos", "Diseño UX/UI", "Diseño de interfaz, lectura clara de riesgo, paleta visual y experiencia del usuario."],
        ["Ana Paula Orellana López", "Tester", "Casos de prueba, validación móvil, errores, permisos y revisión final antes de entrega."],
    ]
    story.append(styled_table(team, [2.2 * inch, 1.5 * inch, 6.05 * inch]))
    story.append(Spacer(1, 8))
    story.append(p("Orden lógico, paralelismo y dependencias", "H2Aqua"))
    order = [
        ["#", "Actividad", "Duración", "Responsable", "Depende de", "Puede avanzar al mismo tiempo que"],
        ["1", "Levantamiento de requisitos", "3 días", "Osmar + equipo", "Inicio", "Preparación de tablero y criterios de aceptación"],
        ["2", "Diseño UX/UI", "5 días", "Brian", "Requisitos base", "Diseño de base de datos y contratos de API"],
        ["3", "Diseño de base de datos", "2 días", "Ángel + Diego", "Requisitos base", "UX/UI y definición técnica del backend"],
        ["4", "Desarrollo backend", "10 días", "Ángel + Diego", "Base de datos aprobada", "Frontend con datos de prueba"],
        ["5", "Desarrollo frontend", "9 días", "Alessandro + Valeria", "UX/UI aprobado", "Backend y casos de prueba iniciales"],
        ["6", "Integración", "3 días", "Osmar + front + back", "Módulos principales listos", "Pruebas exploratorias"],
        ["7", "Pruebas", "4 días", "Ana Paula", "Integración funcional", "Correcciones menores y documentación"],
        ["8", "Corrección de errores", "3 días", "Todo el equipo", "Reporte de pruebas", "Capacitación preliminar"],
        ["9", "Capacitación al cliente", "2 días", "Osmar + Ana Paula", "Versión estable", "Cierre, manual breve y entrega final"],
    ]
    story.append(styled_table(order, [0.32 * inch, 1.75 * inch, 0.65 * inch, 1.38 * inch, 1.55 * inch, 4.1 * inch]))
    story.append(Spacer(1, 8))
    story.append(
        callout(
            "Ruta crítica",
            "La cadena que más cuida el equipo es: requisitos -> base de datos -> backend -> integración -> pruebas -> corrección -> capacitación. Frontend avanza en paralelo, pero se vuelve crítico si las pantallas principales no están listas para integrar en la semana 4.",
            BLUE_SOFT,
        )
    )
    story.append(PageBreak())

    story.append(p("2. Priorización con Matriz de Eisenhower", "H1Aqua"))
    story.append(
        p(
            "La matriz se usó para separar lo que realmente protege la fecha de entrega de lo que solo mejora la presentación. En un sprint de 6 semanas, casi todo parece urgente; por eso se prioriza lo que desbloquea trabajo, reduce riesgo o permite probar con usuarios antes del cierre."
        )
    )
    matrix = [
        ["", "Urgente", "No urgente"],
        [
            "Importante",
            "<b>Actividades:</b> levantamiento de requisitos, diseño de base de datos, desarrollo backend, desarrollo frontend, integración, pruebas y corrección de errores.<br/><br/><b>Justificación:</b> si cualquiera de estas actividades falla, el producto no se puede entregar o queda sin validar.",
            "<b>Actividades:</b> diseño UX/UI, documentación breve, capacitación al cliente y criterios de aceptación.<br/><br/><b>Justificación:</b> no siempre bloquean el primer día, pero elevan la calidad y ayudan a que el cliente use AquaRisk sin depender del equipo.",
        ],
        [
            "No importante",
            "<b>Actividades:</b> ajustes menores de presentación, capturas y material de apoyo para exposición.<br/><br/><b>Justificación:</b> tienen fecha cercana, pero no deben quitar tiempo al funcionamiento principal.",
            "<b>Actividades:</b> historial avanzado, perfiles complejos, reportes extensos o mapas decorativos.<br/><br/><b>Justificación:</b> pueden ser buenas ideas para otra versión, pero meterlas ahora pondría en riesgo la entrega.",
        ],
    ]
    matrix_table = styled_table(matrix, [1.15 * inch, 4.3 * inch, 4.3 * inch])
    matrix_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (1, 1), (1, 1), MINT),
                ("BACKGROUND", (2, 1), (2, 1), LAVENDER),
                ("BACKGROUND", (1, 2), (1, 2), YELLOW),
                ("BACKGROUND", (2, 2), (2, 2), GRAY),
            ]
        )
    )
    story.append(matrix_table)
    story.append(Spacer(1, 8))
    story.append(p("Decisiones de priorización", "H2Aqua"))
    decisions = [
        "El alcance mínimo entregable queda formado por ubicación, consulta de clima, lectura de riesgo, mapa, alertas preventivas y pruebas en móvil.",
        "Las mejoras visuales se trabajan solo cuando no afecten backend, integración o pruebas.",
        "La capacitación se prepara desde la semana 5 para no improvisarla al final.",
        "Cualquier función nueva pasa por el líder; si no ayuda a entregar en 6 semanas, se deja para otra versión.",
    ]
    for item in decisions:
        story.append(bullet(item))
    story.append(PageBreak())

    story.append(p("3. Cronograma tipo Gantt", "H1Aqua"))
    story.append(
        p(
            "El cronograma se construyó con semanas laborales de lunes a viernes. La semana 6 se reserva para capacitación, cierre y margen de seguridad, porque AquaRisk depende de datos externos, GPS, notificaciones y validación real en dispositivos."
        )
    )
    gantt = [
        ["Actividad", "Responsable", "Dur.", "Dep.", "Sem. 1\n20-24 jul", "Sem. 2\n27-31 jul", "Sem. 3\n3-7 ago", "Sem. 4\n10-14 ago", "Sem. 5\n17-21 ago", "Sem. 6\n24-28 ago"],
        ["Levantamiento de requisitos", "Osmar + equipo", "3d", "Inicio", p("20-22", "SmallWhite"), "", "", "", "", ""],
        ["Diseño UX/UI", "Brian", "5d", "Req.", p("23-24", "SmallWhite"), p("27-29", "SmallWhite"), "", "", "", ""],
        ["Diseño de base de datos", "Ángel + Diego", "2d", "Req.", p("23-24", "SmallWhite"), "", "", "", "", ""],
        ["Desarrollo backend", "Ángel + Diego", "10d", "BD", "", p("27-31", "SmallWhite"), p("3-7", "SmallWhite"), "", "", ""],
        ["Desarrollo frontend", "Alessandro + Valeria", "9d", "UX", "", p("30-31", "SmallWhite"), p("3-7", "SmallWhite"), p("10-11", "SmallWhite"), "", ""],
        ["Integración", "Osmar + front + back", "3d", "Módulos", "", "", "", p("10-12", "SmallWhite"), "", ""],
        ["Pruebas", "Ana Paula", "4d", "Integr.", "", "", "", p("13-14", "SmallWhite"), p("17-18", "SmallWhite"), ""],
        ["Corrección de errores", "Todo el equipo", "3d", "Pruebas", "", "", "", "", p("19-21", "SmallWhite"), ""],
        ["Capacitación al cliente", "Osmar + Ana Paula", "2d", "Estable", "", "", "", "", "", p("24-25", "SmallWhite")],
        ["Cierre y entrega final", "Osmar + equipo", "3d", "Cap.", "", "", "", "", "", p("26-28", "SmallWhite")],
    ]
    gantt_table = styled_table(
        gantt,
        [1.32 * inch, 1.1 * inch, 0.4 * inch, 0.65 * inch] + [1.02 * inch] * 6,
        font_size=7,
    )
    bar_colors = [TEAL, GREEN, PURPLE, TEAL, GREEN, PURPLE, TEAL, colors.HexColor("#D8527C"), GREEN, PURPLE]
    commands = []
    for row_index in range(1, len(gantt)):
        color = bar_colors[row_index - 1]
        for col_index in range(4, 10):
            if gantt[row_index][col_index]:
                commands.extend(
                    [
                        ("BACKGROUND", (col_index, row_index), (col_index, row_index), color),
                        ("TEXTCOLOR", (col_index, row_index), (col_index, row_index), WHITE),
                        ("FONTNAME", (col_index, row_index), (col_index, row_index), FONT_BOLD),
                        ("ALIGN", (col_index, row_index), (col_index, row_index), "CENTER"),
                    ]
                )
            else:
                commands.append(("BACKGROUND", (col_index, row_index), (col_index, row_index), colors.HexColor("#FAFBFC")))
    gantt_table.setStyle(TableStyle(commands))
    story.append(gantt_table)
    story.append(Spacer(1, 8))
    story.append(
        callout(
            "Lectura del Gantt",
            "Las barras muestran cuándo se trabaja cada actividad. Frontend y backend se empalman porque se integran por módulos; así el equipo detecta fallas antes de la última semana.",
            LAVENDER,
        )
    )
    story.append(PageBreak())

    story.append(p("4. Gestión del tiempo y solución al imprevisto", "H1Aqua"))
    story.append(
        p(
            "Imprevisto trabajado por el equipo: durante la integración, AquaRisk puede presentar diferencias entre el pronóstico y la lluvia real observada, además de comportamientos distintos en permisos de ubicación, notificaciones o capa de radar según el dispositivo. Este imprevisto es creíble porque el proyecto depende de datos externos y permisos del navegador."
        )
    )
    q_rows = [
        ["Pregunta", "Respuesta del equipo"],
        ["¿Qué actividades cambiarían?", "Adelantaríamos integración técnica desde la semana 3, aunque sea con módulos incompletos. También moveríamos pruebas de permisos, GPS y notificaciones a una revisión temprana."],
        ["¿Qué tareas pueden adelantarse?", "Casos de prueba, contrato de datos entre frontend y backend, estructura de Supabase, pantallas base, guía breve para cliente y validación en celular."],
        ["¿Qué tareas deben retrasarse?", "Extras visuales, mapas secundarios, estadísticas históricas y funciones que no sean necesarias para demostrar lluvia, ubicación, zonas de riesgo y alertas."],
        ["¿Cómo evitarían retrasar la entrega?", "Con revisión diaria de 15 minutos, tablero Kanban, responsables visibles, integración por módulos, pruebas desde semana 3, congelamiento de alcance en semana 5 y reserva operativa en semana 6."],
    ]
    story.append(styled_table(q_rows, [2.3 * inch, 7.45 * inch]))
    story.append(Spacer(1, 8))
    story.append(p("Medidas concretas de control", "H2Aqua"))
    controls = [
        ["Medida", "Aplicación"],
        ["Control de alcance", "Desde semana 5 solo se corrigen errores y se ajusta claridad; no se agregan funciones nuevas."],
        ["Revisión técnica", "Backend y frontend validan juntos clima, ubicación y riesgo antes de pruebas formales."],
        ["Pruebas reales", "Ana Paula prueba en móvil, escritorio y navegador con permisos concedidos, bloqueados y restablecidos."],
        ["Comunicación", "Osmar registra acuerdos, bloqueos y cambios para que nadie trabaje sobre suposiciones."],
    ]
    story.append(styled_table(controls, [2.1 * inch, 7.65 * inch]))
    story.append(PageBreak())

    story.append(p("5. Conclusión del equipo", "H1Aqua"))
    story.append(
        p(
            "Como equipo, consideramos que AquaRisk sí puede entregarse en 6 semanas si se cuida el orden de las dependencias y se evita crecer el alcance a mitad del sprint. La clave es no esperar hasta el final para integrar: backend, frontend, diseño y pruebas deben verse como partes conectadas del mismo avance. También aprendimos que una aplicación con clima, GPS y alertas no depende únicamente del código; depende de permisos, datos externos y validación en dispositivos reales. Por eso dejamos una semana final con margen, capacitación y cierre. Nuestra prioridad es entregar una versión funcional, clara para el usuario y defendible ante el cliente, aunque algunas funciones avanzadas queden para una segunda etapa."
        )
    )
    story.append(Spacer(1, 10))
    story.append(p("Referencias", "H1Aqua"))
    refs = [
        "Schwaber, K. y Sutherland, J. (2020). The Scrum Guide. https://scrumguides.org/scrum-guide.html",
        "Project Management Institute. Project schedule management y control de cronogramas. https://www.pmi.org/",
        "Covey, S. R. (1989). The 7 Habits of Highly Effective People. Matriz urgente/importante como apoyo para priorización.",
        "Open-Meteo. Forecast API Documentation. https://open-meteo.com/en/docs",
        "RainViewer. Weather Maps API. https://www.rainviewer.com/api/weather-maps-api.html",
        "MDN Web Docs. Geolocation API y Notifications API. https://developer.mozilla.org/",
        "Supabase. Documentation. https://supabase.com/docs",
    ]
    for ref in refs:
        story.append(bullet(ref))

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
