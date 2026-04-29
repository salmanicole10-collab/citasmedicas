import flet as ft
import sqlite3
import re
from datetime import datetime

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
            phone TEXT NOT NULL,
            exequatur TEXT
        )
    """)

    columns = cur.execute("PRAGMA table_info(doctors)").fetchall()
    column_names = [col["name"] for col in columns]

    if "exequatur" not in column_names:
        cur.execute("ALTER TABLE doctors ADD COLUMN exequatur TEXT")

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

    cur.execute("DROP VIEW IF EXISTS appointment_summary")

    cur.execute("""
        CREATE VIEW appointment_summary AS
        SELECT
            a.id,
            p.full_name AS patient_name,
            d.full_name AS doctor_name,
            d.specialty AS specialty,
            d.exequatur AS exequatur,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.notes
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
    """)

    conn.commit()
    conn.close()
    
def valid_email(email):
    if email.strip() == "":
        return True
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


def valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_time(time_text):
    try:
        datetime.strptime(time_text, "%H:%M")
        return True
    except ValueError:
        return False


def main(page: ft.Page):
    page.title = "Sistema de Citas Médicas"
    page.padding = 15
    page.window.width = 1500
    page.window.height = 900
    page.window.center()
    page.scroll = ft.ScrollMode.AUTO

    init_db()

    content_area = ft.Container(expand=True)
    status_text = ft.Text("Sistema listo", color=ft.Colors.GREEN)

    only_numbers = ft.NumbersOnlyInputFilter()
    date_filter = ft.InputFilter(allow=True, regex_string=r"^[0-9-]*$")
    time_filter = ft.InputFilter(allow=True, regex_string=r"^[0-9:]*$")

    def show_message(text, color=ft.Colors.BLUE):
        status_text.value = text
        status_text.color = color
        page.update()

    def get_patients():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM patients ORDER BY full_name").fetchall()
        conn.close()
        return rows

    def get_doctors():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM doctors ORDER BY full_name").fetchall()
        conn.close()
        return rows

    def get_appointments(search_text=""):
        conn = get_connection()

        if search_text.strip():
            rows = conn.execute("""
                SELECT * FROM appointment_summary
                WHERE patient_name LIKE ?
                   OR doctor_name LIKE ?
                   OR specialty LIKE ?
                   OR appointment_date LIKE ?
                   OR status LIKE ?
                   OR exequatur LIKE ?
                ORDER BY appointment_date, appointment_time
            """, (
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%"
            )).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM appointment_summary
                ORDER BY appointment_date, appointment_time
            """).fetchall()

        conn.close()
        return rows

    def get_counts():
        conn = get_connection()
        cur = conn.cursor()

        total_patients = cur.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        total_doctors = cur.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
        total_appointments = cur.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        scheduled = cur.execute("SELECT COUNT(*) FROM appointments WHERE status='Programada'").fetchone()[0]
        completed = cur.execute("SELECT COUNT(*) FROM appointments WHERE status='Completada'").fetchone()[0]
        canceled = cur.execute("SELECT COUNT(*) FROM appointments WHERE status='Cancelada'").fetchone()[0]

        conn.close()

        return {
            "patients": total_patients,
            "doctors": total_doctors,
            "appointments": total_appointments,
            "scheduled": scheduled,
            "completed": completed,
            "canceled": canceled
        }

    def dashboard_view():
        counts = get_counts()

        def card(title, value):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                        ft.Text(str(value), size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                width=190,
                height=120,
                padding=15,
                border_radius=12,
                bgcolor=ft.Colors.BLUE_50
            )

        return ft.Column(
            [
                ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Resumen general del sistema"),
                ft.Row(
                    [
                        card("Pacientes", counts["patients"]),
                        card("Doctores", counts["doctors"]),
                        card("Citas", counts["appointments"]),
                        card("Programadas", counts["scheduled"]),
                        card("Completadas", counts["completed"]),
                        card("Canceladas", counts["canceled"]),
                    ],
                    wrap=True,
                    spacing=12,
                    run_spacing=12
                )
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO
        )


    def patients_view():
        selected_id = {"value": None}

        full_name = ft.TextField(label="Nombre completo", width=300)
        age = ft.TextField(label="Edad", width=120, input_filter=only_numbers)
        phone = ft.TextField(label="Teléfono", width=200, input_filter=only_numbers)
        email = ft.TextField(label="Email", width=250)
        search = ft.TextField(label="Buscar paciente", width=300)

        patient_table = ft.Column()
        save_button = ft.ElevatedButton("Guardar paciente")

        def clear_form(e=None):
            selected_id["value"] = None
            full_name.value = ""
            age.value = ""
            phone.value = ""
            email.value = ""
            save_button.text = "Guardar paciente"
            page.update()

        def load_patients(filter_text=""):
            patient_table.controls.clear()
            rows = get_patients()

            if filter_text.strip():
                rows = [
                    r for r in rows
                    if filter_text.lower() in r["full_name"].lower()
                    or filter_text.lower() in r["phone"].lower()
                    or filter_text.lower() in (r["email"] or "").lower()
                ]

            if not rows:
                patient_table.controls.append(ft.Text("No hay pacientes registrados"))
            else:
                for row in rows:
                    patient_table.controls.append(
                        ft.Container(
                            padding=10,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=8,
                            content=ft.Row(
                                [
                                    ft.Text(f"ID: {row['id']}", width=60),
                                    ft.Text(row["full_name"], width=220),
                                    ft.Text(f"Edad: {row['age']}", width=90),
                                    ft.Text(row["phone"], width=150),
                                    ft.Text(row["email"] or "", width=220),
                                    ft.ElevatedButton("Editar", on_click=lambda e, r=row: edit_patient(r)),
                                    ft.ElevatedButton(
                                        "Eliminar",
                                        bgcolor=ft.Colors.RED_100,
                                        on_click=lambda e, pid=row["id"]: delete_patient(pid)
                                    ),
                                ],
                                wrap=True
                            )
                        )
                    )

            page.update()

        def edit_patient(row):
            selected_id["value"] = row["id"]
            full_name.value = row["full_name"]
            age.value = str(row["age"])
            phone.value = row["phone"]
            email.value = row["email"] or ""
            save_button.text = "Actualizar paciente"
            show_message("Editando paciente seleccionado", ft.Colors.BLUE)

        def delete_patient(patient_id):
            conn = get_connection()
            conn.execute("DELETE FROM appointments WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            conn.close()

            load_patients()
            show_message("Paciente y sus citas eliminados correctamente", ft.Colors.ORANGE)

        def save_patient(e):
            if not full_name.value or not age.value or not phone.value:
                show_message("Completa nombre, edad y teléfono del paciente", ft.Colors.RED)
                return

            if not age.value.isdigit():
                show_message("La edad solo puede contener números", ft.Colors.RED)
                return

            if not phone.value.isdigit():
                show_message("El teléfono solo puede contener números", ft.Colors.RED)
                return

            age_value = int(age.value)

            if age_value <= 0 or age_value > 120:
                show_message("La edad debe estar entre 1 y 120", ft.Colors.RED)
                return

            if len(phone.value) < 7:
                show_message("El teléfono debe tener al menos 7 números", ft.Colors.RED)
                return

            if not valid_email(email.value):
                show_message("El email no tiene un formato válido", ft.Colors.RED)
                return

            conn = get_connection()

            if selected_id["value"] is None:
                conn.execute("""
                    INSERT INTO patients (full_name, age, phone, email)
                    VALUES (?, ?, ?, ?)
                """, (full_name.value, age_value, phone.value, email.value))
                message = "Paciente guardado correctamente"
            else:
                conn.execute("""
                    UPDATE patients
                    SET full_name = ?, age = ?, phone = ?, email = ?
                    WHERE id = ?
                """, (full_name.value, age_value, phone.value, email.value, selected_id["value"]))
                message = "Paciente actualizado correctamente"

            conn.commit()
            conn.close()

            clear_form()
            load_patients()
            show_message(message, ft.Colors.GREEN)

        save_button.on_click = save_patient
        load_patients()

        return ft.Column(
            [
                ft.Text("Patients", size=28, weight=ft.FontWeight.BOLD),
                ft.Row([full_name, age, phone, email], wrap=True),
                ft.Row([save_button, ft.ElevatedButton("Limpiar", on_click=clear_form)]),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_patients(search.value)),
                        ft.ElevatedButton("Mostrar todos", on_click=lambda e: load_patients()),
                    ],
                    wrap=True
                ),
                patient_table
            ],
            scroll=ft.ScrollMode.AUTO
        )


    def doctors_view():
        selected_id = {"value": None}

        full_name = ft.TextField(label="Nombre del doctor", width=280)
        specialty = ft.Dropdown(
            label="Especialidad",
            width=220,
            options=[
                ft.dropdown.Option("General"),
                ft.dropdown.Option("Pediatra"),
                ft.dropdown.Option("Cardiólogo"),
                ft.dropdown.Option("Dermatólogo"),
                ft.dropdown.Option("Ginecólogo"),
                ft.dropdown.Option("Odontólogo"),
            ]
        )
        phone = ft.TextField(label="Teléfono", width=180, input_filter=only_numbers)
        exequatur = ft.TextField(label="Exequátur", width=180, input_filter=only_numbers)
        search = ft.TextField(label="Buscar doctor", width=300)

        doctor_table = ft.Column()
        save_button = ft.ElevatedButton("Guardar doctor")

        def clear_form(e=None):
            selected_id["value"] = None
            full_name.value = ""
            specialty.value = None
            phone.value = ""
            exequatur.value = ""
            save_button.text = "Guardar doctor"
            page.update()

        def load_doctors(filter_text=""):
            doctor_table.controls.clear()
            rows = get_doctors()

            if filter_text.strip():
                rows = [
                    r for r in rows
                    if filter_text.lower() in r["full_name"].lower()
                    or filter_text.lower() in r["specialty"].lower()
                    or filter_text.lower() in (r["exequatur"] or "").lower()
                    or filter_text.lower() in r["phone"].lower()
                ]

            if not rows:
                doctor_table.controls.append(ft.Text("No hay doctores registrados"))
            else:
                for row in rows:
                    doctor_table.controls.append(
                        ft.Container(
                            padding=10,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=8,
                            content=ft.Row(
                                [
                                    ft.Text(f"ID: {row['id']}", width=60),
                                    ft.Text(row["full_name"], width=210),
                                    ft.Text(row["specialty"], width=150),
                                    ft.Text(row["phone"], width=130),
                                    ft.Text(f"Exequátur: {row['exequatur'] or ''}", width=180),
                                    ft.ElevatedButton("Editar", on_click=lambda e, r=row: edit_doctor(r)),
                                    ft.ElevatedButton(
                                        "Eliminar",
                                        bgcolor=ft.Colors.RED_100,
                                        on_click=lambda e, did=row["id"]: delete_doctor(did)
                                    ),
                                ],
                                wrap=True
                            )
                        )
                    )

            page.update()

        def edit_doctor(row):
            selected_id["value"] = row["id"]
            full_name.value = row["full_name"]
            specialty.value = row["specialty"]
            phone.value = row["phone"]
            exequatur.value = row["exequatur"] or ""
            save_button.text = "Actualizar doctor"
            show_message("Editando doctor seleccionado", ft.Colors.BLUE)

        def delete_doctor(doctor_id):
            conn = get_connection()
            conn.execute("DELETE FROM appointments WHERE doctor_id = ?", (doctor_id,))
            conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
            conn.commit()
            conn.close()

            load_doctors()
            show_message("Doctor y sus citas eliminados correctamente", ft.Colors.ORANGE)

        def save_doctor(e):
            if not full_name.value or not specialty.value or not phone.value or not exequatur.value:
                show_message("Completa nombre, especialidad, teléfono y exequátur", ft.Colors.RED)
                return

            if not phone.value.isdigit():
                show_message("El teléfono solo puede contener números", ft.Colors.RED)
                return

            if not exequatur.value.isdigit():
                show_message("El exequátur solo puede contener números", ft.Colors.RED)
                return

            if len(phone.value) < 7:
                show_message("El teléfono debe tener al menos 7 números", ft.Colors.RED)
                return

            if len(exequatur.value) < 3:
                show_message("El exequátur debe tener al menos 3 números", ft.Colors.RED)
                return

            conn = get_connection()

            if selected_id["value"] is None:
                conn.execute("""
                    INSERT INTO doctors (full_name, specialty, phone, exequatur)
                    VALUES (?, ?, ?, ?)
                """, (full_name.value, specialty.value, phone.value, exequatur.value))
                message = "Doctor guardado correctamente"
            else:
                conn.execute("""
                    UPDATE doctors
                    SET full_name = ?, specialty = ?, phone = ?, exequatur = ?
                    WHERE id = ?
                """, (full_name.value, specialty.value, phone.value, exequatur.value, selected_id["value"]))
                message = "Doctor actualizado correctamente"

            conn.commit()
            conn.close()

            clear_form()
            load_doctors()
            show_message(message, ft.Colors.GREEN)

        save_button.on_click = save_doctor
        load_doctors()

        return ft.Column(
            [
                ft.Text("Doctors", size=28, weight=ft.FontWeight.BOLD),
                ft.Row([full_name, specialty, phone, exequatur], wrap=True),
                ft.Row([save_button, ft.ElevatedButton("Limpiar", on_click=clear_form)]),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_doctors(search.value)),
                        ft.ElevatedButton("Mostrar todos", on_click=lambda e: load_doctors()),
                    ],
                    wrap=True
                ),
                doctor_table
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def appointments_view():
        selected_id = {"value": None}

        patient_dropdown = ft.Dropdown(label="Paciente", width=280)
        doctor_dropdown = ft.Dropdown(label="Doctor", width=340)

        appointment_date = ft.TextField(
            label="Fecha (YYYY-MM-DD)",
            width=180,
            input_filter=date_filter
        )

        appointment_time = ft.TextField(
            label="Hora (HH:MM)",
            width=150,
            input_filter=time_filter
        )

        status = ft.Dropdown(
            label="Estado",
            width=180,
            options=[
                ft.dropdown.Option("Programada"),
                ft.dropdown.Option("Completada"),
                ft.dropdown.Option("Cancelada"),
                ft.dropdown.Option("Perdida"),
            ],
            value="Programada"
        )

        notes = ft.TextField(label="Notas", multiline=True, min_lines=2, max_lines=3, width=420)
        search = ft.TextField(label="Buscar cita", width=300)

        appointment_table = ft.Column()
        save_button = ft.ElevatedButton("Guardar cita")

        def load_dropdowns():
            patient_dropdown.options = [
                ft.dropdown.Option(key=str(p["id"]), text=p["full_name"])
                for p in get_patients()
            ]

            doctor_dropdown.options = [
                ft.dropdown.Option(
                    key=str(d["id"]),
                    text=f"{d['full_name']} - {d['specialty']} - Exeq. {d['exequatur'] or 'N/A'}"
                )
                for d in get_doctors()
            ]

            page.update()

        def clear_form(e=None):
            selected_id["value"] = None
            patient_dropdown.value = None
            doctor_dropdown.value = None
            appointment_date.value = ""
            appointment_time.value = ""
            status.value = "Programada"
            notes.value = ""
            save_button.text = "Guardar cita"
            page.update()

        def load_appointments(filter_text=""):
            appointment_table.controls.clear()
            rows = get_appointments(filter_text)

            if not rows:
                appointment_table.controls.append(ft.Text("No hay citas registradas"))
            else:
                for row in rows:
                    appointment_table.controls.append(
                        ft.Container(
                            padding=12,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=10,
                            content=ft.Column(
                                [
                                    ft.Text(f"Cita #{row['id']}", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Paciente: {row['patient_name']}"),
                                    ft.Text(f"Doctor: {row['doctor_name']}"),
                                    ft.Text(f"Especialidad: {row['specialty']}"),
                                    ft.Text(f"Exequátur: {row['exequatur'] or ''}"),
                                    ft.Text(f"Fecha: {row['appointment_date']}"),
                                    ft.Text(f"Hora: {row['appointment_time']}"),
                                    ft.Text(f"Estado: {row['status']}"),
                                    ft.Text(f"Notas: {row['notes'] or ''}"),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton("Editar", on_click=lambda e, r=row: edit_appointment(r)),
                                            ft.ElevatedButton(
                                                "Eliminar",
                                                bgcolor=ft.Colors.RED_100,
                                                on_click=lambda e, aid=row["id"]: delete_appointment(aid)
                                            ),
                                        ]
                                    )
                                ]
                            )
                        )
                    )

            page.update()

        def edit_appointment(row):
            conn = get_connection()
            appointment = conn.execute(
                "SELECT * FROM appointments WHERE id = ?",
                (row["id"],)
            ).fetchone()
            conn.close()

            if appointment is None:
                show_message("No se encontró la cita", ft.Colors.RED)
                return

            selected_id["value"] = appointment["id"]
            patient_dropdown.value = str(appointment["patient_id"])
            doctor_dropdown.value = str(appointment["doctor_id"])
            appointment_date.value = appointment["appointment_date"]
            appointment_time.value = appointment["appointment_time"]
            status.value = appointment["status"]
            notes.value = appointment["notes"] or ""
            save_button.text = "Actualizar cita"
            show_message("Editando cita seleccionada", ft.Colors.BLUE)

        def delete_appointment(appointment_id):
            conn = get_connection()
            conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            conn.commit()
            conn.close()

            load_appointments()
            show_message("Cita eliminada correctamente", ft.Colors.ORANGE)

        def save_appointment(e):
            if (
                not patient_dropdown.value or
                not doctor_dropdown.value or
                not appointment_date.value or
                not appointment_time.value or
                not status.value
            ):
                show_message("Completa todos los campos obligatorios de la cita", ft.Colors.RED)
                return

            if not valid_date(appointment_date.value):
                show_message("La fecha debe tener formato YYYY-MM-DD", ft.Colors.RED)
                return

            if not valid_time(appointment_time.value):
                show_message("La hora debe tener formato HH:MM", ft.Colors.RED)
                return

            conn = get_connection()

            try:
                if selected_id["value"] is None:
                    conn.execute("""
                        INSERT INTO appointments (
                            patient_id, doctor_id, appointment_date, appointment_time, status, notes
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        int(patient_dropdown.value),
                        int(doctor_dropdown.value),
                        appointment_date.value,
                        appointment_time.value,
                        status.value,
                        notes.value
                    ))
                    message = "Cita guardada correctamente"
                else:
                    conn.execute("""
                        UPDATE appointments
                        SET patient_id = ?, doctor_id = ?, appointment_date = ?,
                            appointment_time = ?, status = ?, notes = ?
                        WHERE id = ?
                    """, (
                        int(patient_dropdown.value),
                        int(doctor_dropdown.value),
                        appointment_date.value,
                        appointment_time.value,
                        status.value,
                        notes.value,
                        selected_id["value"]
                    ))
                    message = "Cita actualizada correctamente"

                conn.commit()
                clear_form()
                load_appointments()
                show_message(message, ft.Colors.GREEN)

            except sqlite3.IntegrityError:
                show_message("Ese doctor ya tiene una cita en esa fecha y hora", ft.Colors.RED)
            except Exception as ex:
                show_message(f"Error al guardar cita: {ex}", ft.Colors.RED)
            finally:
                conn.close()

        save_button.on_click = save_appointment
        load_dropdowns()
        load_appointments()

        return ft.Column(
            [
                ft.Text("Appointments", size=28, weight=ft.FontWeight.BOLD),
                ft.Row([patient_dropdown, doctor_dropdown], wrap=True),
                ft.Row([appointment_date, appointment_time, status], wrap=True),
                notes,
                ft.Row([save_button, ft.ElevatedButton("Limpiar", on_click=clear_form)]),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_appointments(search.value)),
                        ft.ElevatedButton("Mostrar todas", on_click=lambda e: load_appointments()),
                    ],
                    wrap=True
                ),
                appointment_table
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def reports_view():
        report_content = ft.Column()

        def report_by_status(e=None):
            report_content.controls.clear()

            conn = get_connection()
            rows = conn.execute("""
                SELECT status, COUNT(*) AS total
                FROM appointments
                GROUP BY status
                ORDER BY total DESC
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte: Citas por estado", size=22, weight=ft.FontWeight.BOLD)
            )

            for row in rows:
                report_content.controls.append(ft.Text(f"{row['status']}: {row['total']}"))

            page.update()

        def report_by_doctor(e=None):
            report_content.controls.clear()

            conn = get_connection()
            rows = conn.execute("""
                SELECT d.full_name AS doctor_name, d.specialty, d.exequatur, COUNT(a.id) AS total
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id
                GROUP BY d.id, d.full_name, d.specialty, d.exequatur
                ORDER BY total DESC, doctor_name
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte: Citas por doctor", size=22, weight=ft.FontWeight.BOLD)
            )

            for row in rows:
                report_content.controls.append(
                    ft.Text(
                        f"{row['doctor_name']} | {row['specialty']} | "
                        f"Exeq. {row['exequatur'] or ''}: {row['total']} citas"
                    )
                )

            page.update()

        def report_by_date(e=None):
            report_content.controls.clear()

            conn = get_connection()
            rows = conn.execute("""
                SELECT appointment_date, COUNT(*) AS total
                FROM appointments
                GROUP BY appointment_date
                ORDER BY appointment_date
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte: Citas por fecha", size=22, weight=ft.FontWeight.BOLD)
            )

            for row in rows:
                report_content.controls.append(ft.Text(f"{row['appointment_date']}: {row['total']} citas"))

            page.update()

        def report_by_specialty(e=None):
            report_content.controls.clear()

            conn = get_connection()
            rows = conn.execute("""
                SELECT specialty, COUNT(*) AS total
                FROM appointment_summary
                GROUP BY specialty
                ORDER BY total DESC
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte: Citas por especialidad", size=22, weight=ft.FontWeight.BOLD)
            )

            for row in rows:
                report_content.controls.append(ft.Text(f"{row['specialty']}: {row['total']} citas"))

            page.update()

        def report_case(e=None):
            report_content.controls.clear()

            conn = get_connection()
            rows = conn.execute("""
                SELECT
                    patient_name,
                    doctor_name,
                    appointment_date,
                    appointment_time,
                    status,
                    CASE
                        WHEN appointment_date = date('now') THEN 'Hoy'
                        WHEN appointment_date > date('now') THEN 'Próxima'
                        WHEN status = 'Completada' THEN 'Finalizada'
                        WHEN status = 'Cancelada' THEN 'Cancelada'
                        ELSE 'Pasada'
                    END AS category
                FROM appointment_summary
                ORDER BY appointment_date, appointment_time
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte con CASE", size=22, weight=ft.FontWeight.BOLD)
            )

            for row in rows:
                report_content.controls.append(
                    ft.Text(
                        f"{row['appointment_date']} {row['appointment_time']} | "
                        f"{row['patient_name']} | {row['doctor_name']} | "
                        f"{row['status']} | {row['category']}"
                    )
                )

            page.update()

        return ft.Column(
            [
                ft.Text("Reports", size=28, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.ElevatedButton("Citas por estado", on_click=report_by_status),
                        ft.ElevatedButton("Citas por doctor", on_click=report_by_doctor),
                        ft.ElevatedButton("Citas por fecha", on_click=report_by_date),
                        ft.ElevatedButton("Citas por especialidad", on_click=report_by_specialty),
                        ft.ElevatedButton("Reporte con CASE", on_click=report_case),
                    ],
                    wrap=True
                ),
                ft.Divider(),
                report_content
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def open_dashboard(e=None):
        content_area.content = dashboard_view()
        page.update()

    def open_patients(e=None):
        content_area.content = patients_view()
        page.update()

    def open_doctors(e=None):
        content_area.content = doctors_view()
        page.update()

    def open_appointments(e=None):
        content_area.content = appointments_view()
        page.update()

    def open_reports(e=None):
        content_area.content = reports_view()
        page.update()

    sidebar = ft.Container(
        width=220,
        padding=10,
        bgcolor=ft.Colors.BLUE_GREY_50,
        border_radius=10,
        content=ft.Column(
            [
                ft.Text("Menú", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Divider(),
                ft.ElevatedButton("Dashboard", width=190, on_click=open_dashboard),
                ft.ElevatedButton("Patients", width=190, on_click=open_patients),
                ft.ElevatedButton("Doctors", width=190, on_click=open_doctors),
                ft.ElevatedButton("Appointments", width=190, on_click=open_appointments),
                ft.ElevatedButton("Reports", width=190, on_click=open_reports),
                ft.Divider(),
                status_text
            ],
            spacing=10
        )
    )

    content_area.content = dashboard_view()

    page.add(
        ft.Row(
            [
                sidebar,
                ft.VerticalDivider(width=1),
                ft.Container(content=content_area, expand=True, padding=15)
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    )


ft.run(main)