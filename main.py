import flet as ft
import sqlite3
from datetime import datetime, timedelta

# ---------- CONFIGURACIÓN ----------
TRABAJADORES = ["Adrian", "Roynel", "Reinaldo", "Leandro"]
TIPOS_AUSENCIA = ["-", "Enfermedad", "Personal", "Vacaciones", "Permiso", "Injustificada", "Otra"]
HORA_OFICIAL = "08:00"

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect("asistencia.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            trabajador TEXT NOT NULL,
            hora_entrada TEXT,
            hora_salida TEXT,
            tarde TEXT,
            min_tarde INTEGER,
            ausente TEXT,
            tipo_ausencia TEXT,
            descripcion TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_registro(datos):
    conn = sqlite3.connect("asistencia.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO registros
        (fecha, trabajador, hora_entrada, hora_salida, tarde, min_tarde, ausente, tipo_ausencia, descripcion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, datos)
    conn.commit()
    conn.close()

def obtener_registros():
    conn = sqlite3.connect("asistencia.db")
    c = conn.cursor()
    c.execute("SELECT * FROM registros ORDER BY fecha DESC, id DESC")
    filas = c.fetchall()
    conn.close()
    return filas

def eliminar_registro(id_reg):
    conn = sqlite3.connect("asistencia.db")
    c = conn.cursor()
    c.execute("DELETE FROM registros WHERE id = ?", (id_reg,))
    conn.commit()
    conn.close()

def existe_registro(fecha_iso, trabajador):
    conn = sqlite3.connect("asistencia.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM registros WHERE fecha = ? AND trabajador = ?", (fecha_iso, trabajador))
    cantidad = c.fetchone()[0]
    conn.close()
    return cantidad > 0

def calcular_tarde(hora_entrada):
    if not hora_entrada or hora_entrada == "-":
        return "-", 0
    try:
        h, m = map(int, hora_entrada.split(":"))
        hof, mof = map(int, HORA_OFICIAL.split(":"))
        diff = (h * 60 + m) - (hof * 60 + mof)
        if diff > 0:
            return "Sí", diff
        return "No", 0
    except:
        return "-", 0

# ---------- INTERFAZ GRÁFICA ----------
def main(page: ft.Page):
    page.title = "Control de Asistencia"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    init_db()

    # Variables de estado
    fecha_seleccionada = datetime.now().strftime("%Y-%m-%d")
    hora_entrada_sel = "08:00"
    hora_salida_sel = "16:00"

    # ----- COMPONENTES DE LA PANTALLA REGISTRAR -----
    txt_fecha = ft.Text(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", size=16, weight=ft.FontWeight.BOLD)
    
    def cambiar_fecha(e):
        nonlocal fecha_seleccionada
        if e.control.value:
            fecha_seleccionada = e.control.value.strftime("%Y-%m-%d")
            txt_fecha.value = f"Fecha: {e.control.value.strftime('%d/%m/%Y')}"
            page.update()

    date_picker = ft.DatePicker(
        first_date=datetime(2023, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=cambiar_fecha
    )
    page.overlay.append(date_picker)
    
    btn_fecha = ft.Button("Seleccionar Fecha", icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: date_picker.pick_date())

    combo_trabajador = ft.Dropdown(
        label="Trabajador",
        options=[ft.dropdown.Option(t) for t in TRABAJADORES],
        width=300
    )

    def sel_entrada(e):
        nonlocal hora_entrada_sel
        hora_entrada_sel = e.control.value

    def sel_salida(e):
        nonlocal hora_salida_sel
        hora_salida_sel = e.control.value

    picker_entrada = ft.TimePicker(on_change=sel_entrada, help_text="Hora Entrada")
    picker_salida = ft.TimePicker(on_change=sel_salida, help_text="Hora Salida")
    page.overlay.extend([picker_entrada, picker_salida])

    btn_entrada = ft.Button("Hora Entrada (08:00)", icon=ft.Icons.LOGIN, on_click=lambda _: picker_entrada.pick_time())
    btn_salida = ft.Button("Hora Salida (16:00)", icon=ft.Icons.LOGOUT, on_click=lambda _: picker_salida.pick_time())

    combo_tipo = ft.Dropdown(
        label="Tipo de Ausencia",
        options=[ft.dropdown.Option(ta) for ta in TIPOS_AUSENCIA],
        value="-",
        width=300
    )

    txt_desc = ft.TextField(label="Descripción (Opcional)", width=300)
    chk_ausente = ft.Checkbox(label="Marcar como AUSENTE", value=False)

    def guardar_click(e):
        trabajador = combo_trabajador.value
        if not trabajador:
            page.snack_bar = ft.SnackBar(ft.Text("Selecciona un trabajador"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        if existe_registro(fecha_seleccionada, trabajador):
            page.snack_bar = ft.SnackBar(ft.Text(f"{trabajador} ya tiene registro este día"), bgcolor=ft.Colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        if chk_ausente.value:
            entrada, salida, tarde, min_t, ausente = "-", "-", "-", 0, "Sí"
            tipo = combo_tipo.value if combo_tipo.value != "-" else "Injustificada"
            desc = txt_desc.value or "-"
        else:
            entrada = hora_entrada_sel
            salida = hora_salida_sel
            tarde, min_t = calcular_tarde(entrada)
            ausente = "No"
            tipo = combo_tipo.value
            desc = txt_desc.value or "-"

        guardar_registro((fecha_seleccionada, trabajador, entrada, salida, tarde, min_t, ausente, tipo, desc))
        
        page.snack_bar = ft.SnackBar(ft.Text("✅ Registro guardado"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        
        combo_trabajador.value = None
        txt_desc.value = ""
        chk_ausente.value = False
        page.update()

    def todos_presentes_click(e):
        ya_existen = [t for t in TRABAJADORES if existe_registro(fecha_seleccionada, t)]
        por_registrar = [t for t in TRABAJADORES if t not in ya_existen]

        if not por_registrar:
            page.snack_bar = ft.SnackBar(ft.Text("Todos ya tienen registro hoy"), bgcolor=ft.Colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        tarde, min_t = calcular_tarde(hora_entrada_sel)
        for trabajador in por_registrar:
            guardar_registro((fecha_seleccionada, trabajador, hora_entrada_sel, hora_salida_sel, tarde, min_t, "No", "-", "-"))

        page.snack_bar = ft.SnackBar(ft.Text(f"✅ {len(por_registrar)} asistencias guardadas"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    btn_guardar = ft.Button("Guardar Registro", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=guardar_click, width=300)
    btn_todos = ft.Button("✅ Todos Presentes", icon=ft.Icons.GROUP, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE, on_click=todos_presentes_click, width=300)

    view_registrar = ft.Column([
        ft.Text("Nuevo Registro", size=24, weight=ft.FontWeight.BOLD),
        txt_fecha,
        btn_fecha,
        ft.Divider(),
        combo_trabajador,
        ft.Row([btn_entrada, btn_salida], alignment=ft.MainAxisAlignment.CENTER),
        combo_tipo,
        txt_desc,
        chk_ausente,
        ft.Divider(),
        btn_guardar,
        btn_todos
    ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


    # ----- COMPONENTES DE LA PANTALLA VER REGISTROS -----
    lista_registros = ft.ListView(expand=1, spacing=10, padding=20)

    def cargar_registros():
        lista_registros.controls.clear()
        regs = obtener_registros()
        for r in regs:
            fecha_disp = datetime.strptime(r[1], "%Y-%m-%d").strftime("%d/%m/%Y")
            texto = f"{fecha_disp} | {r[2]} | E:{r[3]} S:{r[4]}"
            color = ft.Colors.RED if r[7] == "Sí" else ft.Colors.BLACK
            
            def borrar_click(e, id_reg=r[0]):
                eliminar_registro(id_reg)
                cargar_registros()
                page.update()

            lista_registros.controls.append(
                ft.ListTile(
                    title=ft.Text(texto, color=color, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"Tarde: {r[5]} ({r[6]} min) - {r[8]}"),
                    trailing=ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=borrar_click)
                )
            )
        page.update()

    view_registros = ft.Column([
        ft.Text("Registros Recientes", size=24, weight=ft.FontWeight.BOLD),
        ft.Button("Recargar Lista", icon=ft.Icons.REFRESH, on_click=lambda _: cargar_registros()),
        lista_registros
    ], expand=True)


    # ----- COMPONENTES DE LA PANTALLA REPORTES -----
    texto_reporte = ft.Text("Los reportes se generan aquí", size=14)
    
    def generar_reporte(mensual=False):
        hoy = datetime.now()
        if mensual:
            primero = hoy.replace(day=1)
            desde = primero.strftime("%Y-%m-%d")
            hasta = hoy.strftime("%Y-%m-%d")
            titulo = f"REPORTE MENSUAL ({primero.strftime('%d/%m')} - {hoy.strftime('%d/%m')})"
        else:
            lunes = hoy - timedelta(days=hoy.weekday())
            desde = lunes.strftime("%Y-%m-%d")
            hasta = hoy.strftime("%Y-%m-%d")
            titulo = f"REPORTE SEMANAL ({lunes.strftime('%d/%m')} - {hoy.strftime('%d/%m')})"

        conn = sqlite3.connect("asistencia.db")
        c = conn.cursor()
        c.execute("SELECT * FROM registros WHERE fecha BETWEEN ? AND ?", (desde, hasta))
        regs = c.fetchall()
        conn.close()

        resumen = {}
        for r in regs:
            t = r[2]
            resumen.setdefault(t, {"asist": 0, "aus": 0, "tarde": 0, "min": 0})
            if r[7] == "Sí":
                resumen[t]["aus"] += 1
            else:
                resumen[t]["asist"] += 1
                if r[5] == "Sí":
                    resumen[t]["tarde"] += 1
                    resumen[t]["min"] += r[6] or 0

        texto = f"{titulo}\n\n"
        for t in TRABAJADORES:
            d = resumen.get(t, {"asist": 0, "aus": 0, "tarde": 0, "min": 0})
            total = d["asist"] + d["aus"]
            porc = (d["asist"] / total * 100) if total > 0 else 0
            texto += f"👤 {t}:\n"
            texto += f"   Asistencias: {d['asist']} | Faltas: {d['aus']}\n"
            texto += f"   Tardanzas: {d['tarde']} ({d['min']} min)\n"
            texto += f"   Asistencia: {porc:.0f}%\n\n"
        
        texto_reporte.value = texto
        page.update()

    view_reportes = ft.Column([
        ft.Text("Reportes de Asistencia", size=24, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.Button("Semanal", icon=ft.Icons.DATE_RANGE, on_click=lambda _: generar_reporte(False)),
            ft.Button("Mensual", icon=ft.Icons.CALENDAR_VIEW_MONTH, on_click=lambda _: generar_reporte(True))
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        ft.Container(content=texto_reporte, padding=10, bgcolor=ft.Colors.GREY_100, border_radius=10)
    ], scroll=ft.ScrollMode.AUTO)


    # ----- NAVEGACIÓN INFERIOR -----
    def cambiar_pestana(e):
        index = e.control.selected_index
        if index == 0:
            contenido.content = view_registrar
        elif index == 1:
            cargar_registros()
            contenido.content = view_registros
        elif index == 2:
            contenido.content = view_reportes
        page.update()

    barra_navegacion = ft.NavigationBar(
        selected_index=0,
        on_change=cambiar_pestana,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.EDIT, label="Registrar"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Registros"),
            ft.NavigationBarDestination(icon=ft.Icons.ASSESSMENT, label="Reportes"),
        ]
    )

    contenido = ft.Container(content=view_registrar, expand=True)
    page.add(contenido, barra_navegacion)

# Ejecutar la app
if __name__ == "__main__":
    ft.run(main)