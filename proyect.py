import flet as ft
import sqlite3

DB_NAME = "clinic_system.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT NOT NULL,
            email TEXT
        )
    """)

    estado = ft.Dropdown(
        label="Estado de la cita",
        options=[
            ft.dropdown.Option("Programada"),
            ft.dropdown.Option("Completada"),
            ft.dropdown.Option("Cancelada"),
            ft.dropdown.Option("Perdida")
        ],
        value="Programada"
    )

    # lista visual de citas
    lista_citas = ft.Column()

    def actualizar_lista():
        lista_citas.controls.clear()

        if len(citas) == 0:
            lista_citas.controls.append(
                ft.Text("No hay citas registradas todavía.")
            )
        else:
            for i, cita in enumerate(citas):
                lista_citas.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column([
                                ft.Text(f"Paciente: {cita['nombre']}"),
                                ft.Text(f"Médico: {cita['medico']}"),
                                ft.Text(f"Tipo: {cita['tipo_medico']}"),
                                ft.Text(f"Fecha: {cita['fecha']}"),
                                ft.Text(f"Hora: {cita['hora']}"),
                                ft.Text(f"Estado: {cita['estado']}"),
                            ]),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, idx=i: eliminar_cita(idx)
                            )
                        ]
                    )
                )

        page.update()

    def eliminar_cita(indice):
        citas.pop(indice)
        mensaje.value = "Cita eliminada correctamente"
        mensaje.color = "orange"
        actualizar_lista()

    def guardar_cita(e):
        if (
            nombre.value == "" or
            medico.value == "" or
            fecha.value == "" or
            hora.value == "" or
            tipo_medico.value is None or
            estado.value is None
        ):
            mensaje.value = "Por favor llena todos los campos"
            mensaje.color = "red"

        else:

            # validar que el medico no tenga otra cita a la mima hora
            for c in citas:
                if (
                    c["medico"].lower() == medico.value.lower() and
                    c["fecha"] == fecha.value and
                    c["hora"].lower() == hora.value.lower()
                ):
                    mensaje.value = "Ese médico ya tiene una cita en esa fecha y hora"
                    mensaje.color = "red"
                    page.update()
                    return

            # save datos en la lista
            cita = {
                "nombre": nombre.value,
                "medico": medico.value,
                "tipo_medico": tipo_medico.value,
                "fecha": fecha.value,
                "hora": hora.value,
                "estado": estado.value
            }

            citas.append(cita)

            mensaje.value = "Cita guardada correctamente"
            mensaje.color = "green"

            # limpiar campos
            nombre.value = ""
            medico.value = ""
            fecha.value = ""
            hora.value = ""
            tipo_medico.value = None
            estado.value = "Programada"

        actualizar_lista()
        page.update()

    page.add(
        ft.Text("Sistema de Citas Médicas", size=24, weight="bold"),
        ft.Text("Avance: Registro básico de citas"),
        ft.Divider(),
        nombre,
        medico,
        tipo_medico,
        fecha,
        hora,
        estado,
        ft.ElevatedButton("Guardar cita", on_click=guardar_cita),
        mensaje,
        ft.Divider(),
        ft.Text("Citas registradas"),
        lista_citas
    )

    actualizar_lista()

ft.app(target=main)