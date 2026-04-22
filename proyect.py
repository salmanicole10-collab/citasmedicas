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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Programada', 'Completada', 'Cancelada', 'Perdida')),
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            UNIQUE (doctor_id, appointment_date, appointment_time)
        )
    """)

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