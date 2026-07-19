from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
PDF_PATH = OUT / "Sprint_AquaRisk_6_semanas.pdf"

FONT_REGULAR = "ArialAqua"
FONT_BOLD = "ArialAqua-Bold"
pdfmetrics.registerFont(TTFont(FONT_REGULAR, r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"))

BLACK = colors.HexColor("#111111")
GRAY_1 = colors.HexColor("#F2F2F2")
GRAY_2 = colors.HexColor("#D9D9D9")
GRAY_3 = colors.HexColor("#E6E6E6")
GRID = colors.HexColor("#BFBFBF")
TEXT = colors.HexColor("#1F2933")
BAR_REQ = colors.HexColor("#A8DADC")
BAR_DESIGN = colors.HexColor("#C7E9B0")
BAR_DB = colors.HexColor("#D8C8F0")
BAR_DEV = colors.HexColor("#9FD3C7")
BAR_INT = colors.HexColor("#B8C0E0")
BAR_TEST = colors.HexColor("#F8DFA6")
BAR_FIX = colors.HexColor("#F2B5B5")
BAR_CLOSE = colors.HexColor("#CDE7C9")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TitleFormal",
        fontName=FONT_BOLD,
        fontSize=15,
        leading=18,
        textColor=BLACK,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Formal",
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=BLACK,
        spaceBefore=10,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Formal",
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=BLACK,
        spaceBefore=8,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyFormal",
        fontName=FONT_REGULAR,
        fontSize=9.2,
        leading=12.2,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallFormal",
        fontName=FONT_REGULAR,
        fontSize=6.7,
        leading=8.2,
        textColor=TEXT,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallCenter",
        parent=styles["SmallFormal"],
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        name="HeadCell",
        fontName=FONT_BOLD,
        fontSize=6.7,
        leading=8,
        textColor=BLACK,
        alignment=TA_CENTER,
    )
)


def p(text, style="BodyFormal"):
    return Paragraph(str(text).replace("\n", "<br/>"), styles[style])


def bullet(text):
    return p(f"• {text}", "BodyFormal")


def table(data, widths, header=True, center_cols=None):
    rows = []
    center_cols = set(center_cols or [])
    for row_index, row in enumerate(data):
        out = []
        for col_index, value in enumerate(row):
            if hasattr(value, "wrapOn"):
                out.append(value)
            else:
                style = "HeadCell" if header and row_index == 0 else (
                    "SmallCenter" if col_index in center_cols else "SmallFormal"
                )
                out.append(p(value, style))
        rows.append(out)

    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), GRAY_2))
    for i in range(1 if header else 0, len(rows)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAFA")))
    t.setStyle(TableStyle(commands))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(letter[0] / 2, 0.35 * inch, f"AquaRisk - Plan de trabajo | Página {doc.page}")
    canvas.restoreState()


def build_pdf():
    OUT.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    story = []

    story.append(p("Sprint Contra el Tiempo: Plan de trabajo para AquaRisk", "TitleFormal"))
    story.append(p("Situación del proyecto", "H1Formal"))
    story.append(
        p(
            "La empresa de desarrollo asumió el compromiso de entregar AquaRisk en un plazo máximo de seis semanas. Para efectos del ejercicio, AquaRisk se trabaja como una aplicación móvil/web enfocada en el monitoreo de lluvia, riesgo de inundación, ubicación del usuario y alertas preventivas. Aunque el alcance funcional no es enorme, sí requiere una planeación cuidadosa porque intervienen diseño de interfaz, base de datos, servicios externos, permisos de ubicación, pruebas en dispositivos y capacitación al cliente."
        )
    )
    story.append(
        p(
            "El principal reto del equipo es evitar que las actividades se ejecuten de manera aislada. Si backend, frontend, diseño y pruebas avanzan sin coordinación, el proyecto puede llegar a la última semana con pantallas incompletas, errores de integración o funciones difíciles de explicar al usuario. Por eso se propone una secuencia lógica con tareas paralelas, dependencias claras y revisiones semanales."
        )
    )
    story.append(p("Equipo de trabajo", "H2Formal"))
    team = [
        ["Rol solicitado", "Integrante", "Responsabilidad principal"],
        ["Líder de Proyecto", "Osmar Enrique Ramos Reyes", "Coordinar alcance, tiempos, prioridades, seguimiento y comunicación con el cliente."],
        ["Programador Frontend", "Alessandro Bravo Flores", "Implementar pantallas principales, mapa, lectura de riesgo y flujo responsivo."],
        ["Programadora Frontend", "Valeria Montes García", "Apoyar componentes visuales, estados de la interfaz y validación en dispositivos."],
        ["Programador Backend", "Ángel Eduardo Pineda Rodas", "Diseñar servicios, lógica de datos, alertas y conexión con Supabase."],
        ["Programador Backend", "Diego Iván Morales Cruz", "Apoyar estructura de base de datos, consultas, seguridad y pruebas de servicios."],
        ["Diseñador UX/UI", "Brian Bezares Ávalos", "Definir experiencia, navegación, jerarquía visual y claridad de la información."],
        ["Tester", "Ana Paula Orellana López", "Diseñar y ejecutar pruebas funcionales, móviles, de permisos y de entrega final."],
    ]
    story.append(table(team, [1.3 * inch, 1.55 * inch, 3.2 * inch]))

    story.append(p("1. Organización de actividades", "H1Formal"))
    story.append(
        p(
            "El orden se definió considerando qué actividades desbloquean a las demás. El levantamiento de requisitos va primero porque establece qué se entregará y qué queda fuera. Después se trabajan en paralelo el diseño UX/UI y el diseño de base de datos, ya que ambos parten de los requisitos pero atienden frentes distintos. Con esas bases, backend y frontend pueden avanzar al mismo tiempo; posteriormente se realiza la integración, pruebas, corrección de errores y capacitación."
        )
    )
    activities = [
        ["Orden", "Actividad", "Duración", "Responsable", "Dependencia directa"],
        ["1", "Levantamiento de requisitos", "3 días", "Osmar + equipo", "Inicio del proyecto"],
        ["2", "Diseño UX/UI", "5 días", "Brian", "Requisitos principales definidos"],
        ["3", "Diseño de base de datos", "2 días", "Ángel + Diego", "Requisitos principales definidos"],
        ["4", "Desarrollo backend", "10 días", "Ángel + Diego", "Diseño de base de datos"],
        ["5", "Desarrollo frontend", "9 días", "Alessandro + Valeria", "Diseño UX/UI y criterios de navegación"],
        ["6", "Integración", "3 días", "Osmar + frontend + backend", "Módulos principales de backend y frontend"],
        ["7", "Pruebas", "4 días", "Ana Paula", "Integración funcional"],
        ["8", "Corrección de errores", "3 días", "Todo el equipo", "Resultados de pruebas"],
        ["9", "Capacitación al cliente", "2 días", "Osmar + Ana Paula", "Versión estable"],
    ]
    story.append(table(activities, [0.45 * inch, 1.45 * inch, 0.62 * inch, 1.45 * inch, 2.08 * inch], center_cols={0, 2}))

    story.append(p("Actividades que pueden realizarse al mismo tiempo", "H2Formal"))
    for item in [
        "Diseño UX/UI y diseño de base de datos pueden avanzar en paralelo después del levantamiento de requisitos.",
        "Desarrollo frontend y desarrollo backend se ejecutan al mismo tiempo, siempre que exista un acuerdo mínimo sobre datos, pantallas y flujos.",
        "Los casos de prueba pueden prepararse durante el desarrollo, aunque su ejecución formal dependa de la integración.",
        "La capacitación puede preparar su material desde la semana 5, pero debe cerrarse hasta tener una versión estable.",
    ]:
        story.append(bullet(item))
    story.append(p("Dependencias clave", "H2Formal"))
    story.append(
        p(
            "La dependencia más delicada es la integración entre backend y frontend. Si los servicios no entregan datos en el formato acordado, la interfaz puede funcionar de manera incompleta. Por eso el equipo debe definir desde temprano qué datos usará AquaRisk para clima, mapa, zonas de riesgo, ubicación y alertas."
        )
    )

    story.append(p("2. Priorización con Matriz de Eisenhower", "H1Formal"))
    story.append(
        p(
            "La matriz se aplicó para decidir qué actividades deben recibir atención inmediata y cuáles se pueden controlar sin distraer al equipo. En un proyecto de seis semanas, casi todo parece urgente; sin embargo, no todo tiene el mismo impacto sobre la entrega. La prioridad se asignó con base en tres criterios: si la actividad desbloquea otra, si afecta la calidad del producto y si puede poner en riesgo la fecha final."
        )
    )
    matrix = [
        ["", "Urgente", "No urgente"],
        [
            "Importante",
            "Levantamiento de requisitos, diseño de base de datos, desarrollo backend, desarrollo frontend, integración, pruebas y corrección de errores.",
            "Diseño UX/UI, preparación de capacitación, documentación breve y criterios de aceptación.",
        ],
        [
            "No importante",
            "Ajustes visuales menores, capturas para exposición y detalles que no afectan el funcionamiento principal.",
            "Funciones fuera de alcance: historial avanzado, perfiles complejos, reportes extensos y mejoras no solicitadas para esta entrega.",
        ],
    ]
    story.append(table(matrix, [0.9 * inch, 2.55 * inch, 2.6 * inch]))
    story.append(p("Justificación de la priorización", "H2Formal"))
    justifications = [
        "Urgente e importante: se colocan aquí las actividades que sostienen la entrega. Sin requisitos claros no hay alcance; sin base de datos y backend no hay datos; sin frontend no hay producto visible; sin integración y pruebas no existe una versión confiable.",
        "Importante pero no urgente: el diseño UX/UI y la capacitación son importantes porque ayudan a que AquaRisk sea entendible, pero se pueden planear con más margen si no bloquean el desarrollo central.",
        "Urgente pero no importante: los materiales de exposición o ajustes de apariencia pueden tener fecha cercana, pero no deben desplazar tareas críticas.",
        "Ni urgente ni importante: las funciones adicionales se consideran fuera del alcance de seis semanas. Incluirlas sería una decisión riesgosa porque aumentaría retrabajo y pruebas.",
    ]
    for item in justifications:
        story.append(bullet(item))

    story.append(PageBreak())
    story.append(p("3. Cronograma de trabajo tipo Gantt", "H1Formal"))
    story.append(
        p(
            "El cronograma considera seis semanas laborales, del lunes 20 de julio al viernes 28 de agosto de 2026. Las barras muestran el periodo de trabajo de cada actividad. La planeación conserva una semana final para capacitación, cierre y margen de seguridad, porque AquaRisk depende de permisos del navegador, datos externos y pruebas en dispositivos reales."
        )
    )
    gantt = [
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
    gantt_table = table(
        gantt,
        [0.96 * inch, 0.82 * inch, 0.32 * inch, 0.46 * inch, 0.58 * inch, 0.58 * inch, 0.58 * inch, 0.58 * inch, 0.58 * inch, 0.58 * inch],
        center_cols={2, 4, 5, 6, 7, 8, 9},
    )
    bar_colors = [BAR_REQ, BAR_DESIGN, BAR_DB, BAR_DEV, BAR_DEV, BAR_INT, BAR_TEST, BAR_FIX, BAR_CLOSE, BAR_CLOSE]
    commands = []
    for row_index in range(1, len(gantt)):
        for col_index in range(4, 10):
            if gantt[row_index][col_index]:
                commands.extend([
                    ("BACKGROUND", (col_index, row_index), (col_index, row_index), bar_colors[row_index - 1]),
                    ("FONTNAME", (col_index, row_index), (col_index, row_index), FONT_BOLD),
                ])
    gantt_table.setStyle(TableStyle(commands))
    story.append(gantt_table)
    story.append(Spacer(1, 6))
    story.append(
        p(
            "Para evitar retrasos, el equipo revisará el avance al cierre de cada semana. Si una tarea crítica se atrasa más de un día, el líder deberá reasignar apoyo temporal antes de que el retraso afecte integración o pruebas."
        )
    )

    story.append(PageBreak())
    story.append(p("4. Gestión del tiempo y solución al imprevisto", "H1Formal"))
    story.append(
        p(
            "Problemática asignada para AquaRisk: durante el desarrollo se detecta que la información de lluvia puede variar entre la API meteorológica y lo que el usuario observa en tiempo real. Además, algunos dispositivos pueden pedir permisos de ubicación o notificaciones de forma distinta. Este imprevisto afecta directamente la confiabilidad de la app, por lo que no se puede dejar para el final."
        )
    )
    impact = [
        ["Pregunta", "Respuesta propuesta"],
        ["¿Qué actividades cambiarían?", "Se adelantaría una integración parcial desde la semana 3 para probar datos reales, ubicación y alertas antes de terminar todas las pantallas. También se moverían las pruebas móviles a una etapa más temprana."],
        ["¿Qué tareas pueden adelantarse?", "Casos de prueba, definición de datos mínimos, estructura de Supabase, permisos de ubicación, mensajes de alerta, validación de API y preparación del manual breve para cliente."],
        ["¿Qué tareas deben retrasarse?", "Funciones secundarias, mejoras visuales no esenciales, reportes avanzados e historial de consultas. Estas tareas no se eliminan como idea, pero se posponen para no comprometer la entrega."],
        ["¿Cómo evitarían retrasar la entrega?", "Congelando alcance al iniciar la semana 5, trabajando con revisiones diarias cortas, registrando bloqueos, integrando por módulos y dejando una reserva de tiempo para correcciones críticas."],
    ]
    story.append(table(impact, [1.6 * inch, 4.45 * inch]))
    story.append(p("Acciones concretas de control", "H2Formal"))
    actions = [
        "Osmar revisará cada dos días si las tareas críticas están dentro del tiempo planeado.",
        "Backend y frontend acordarán desde la semana 2 el formato de datos para evitar cambios tardíos.",
        "Ana Paula iniciará una lista de pruebas antes de la integración final, incluyendo permisos, ubicación, mapa y alertas.",
        "Brian mantendrá el diseño enfocado en claridad de uso; no se agregarán elementos visuales que no ayuden a entender el riesgo.",
        "Si una función no es indispensable para demostrar AquaRisk, se documentará como mejora futura.",
    ]
    for item in actions:
        story.append(bullet(item))

    story.append(p("5. Conclusión del equipo", "H1Formal"))
    story.append(
        p(
            "Como equipo, concluimos que AquaRisk puede entregarse en seis semanas siempre que se respete el orden de actividades y se mantenga controlado el alcance. La planeación propuesta permite avanzar en paralelo sin perder de vista las dependencias principales. También ayuda a detectar riesgos antes de la última semana, especialmente en integración, ubicación, datos de lluvia y pruebas en dispositivos. Consideramos que la mejor forma de cumplir es entregar una versión funcional y estable, con interfaz clara y capacitación básica para el cliente, dejando las funciones adicionales para una etapa posterior."
        )
    )
    story.append(p("Referencias consultadas", "H1Formal"))
    for ref in [
        "Schwaber, K. y Sutherland, J. (2020). The Scrum Guide.",
        "Project Management Institute. Fundamentos de gestión de cronograma y control de proyectos.",
        "Covey, S. R. (1989). The 7 Habits of Highly Effective People. Matriz urgente/importante.",
        "Open-Meteo. Documentación de Forecast API.",
        "MDN Web Docs. Geolocation API y Notifications API.",
        "Supabase. Documentación de base de datos y servicios backend.",
    ]:
        story.append(bullet(ref))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
