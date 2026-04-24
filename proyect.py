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

    cur.execute("""
        CREATE VIEW IF NOT EXISTS appointment_summary AS
        SELECT
            a.id,
            p.full_name AS patient_name,
            d.full_name AS doctor_name,
            d.specialty AS specialty,
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
    
def main(page: ft.Page):
    page.title = "Sistema de Citas Médicas"
    page.padding = 15
    page.window_width = 1200
    page.window_height = 750
    page.scroll = ft.ScrollMode.AUTO

    init_db()

    content_area = ft.Container(expand=True)
    status_text = ft.Text("Sistema listo", color=ft.Colors.GREEN)

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
                ORDER BY appointment_date, appointment_time
            """, (
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
                        ft.Text(
                            title,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK
                        ),
                        ft.Text(
                            str(value),
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                width=220,
                height=120,
                padding=15,
                border_radius=12,
                bgcolor=ft.Colors.BLUE_50
            )
        
        return ft.Column(
            [
                ft.Text("Dashboard", size=26, weight=ft.FontWeight.BOLD),
                ft.Text("Resumen general del sistema"),
                ft.ResponsiveRow(
                    [
                        ft.Container(card("Pacientes", counts["patients"]), col={"sm": 6, "md": 4, "lg": 2}),
                        ft.Container(card("Doctores", counts["doctors"]), col={"sm": 6, "md": 4, "lg": 2}),
                        ft.Container(card("Citas", counts["appointments"]), col={"sm": 6, "md": 4, "lg": 2}),
                        ft.Container(card("Programadas", counts["scheduled"]), col={"sm": 6, "md": 4, "lg": 2}),
                        ft.Container(card("Completadas", counts["completed"]), col={"sm": 6, "md": 4, "lg": 2}),
                        ft.Container(card("Canceladas", counts["canceled"]), col={"sm": 6, "md": 4, "lg": 2}),
                    ]
                )
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO
        )

    def patients_view():
        full_name = ft.TextField(label="Nombre completo", width=300)
        age = ft.TextField(label="Edad", width=150)
        phone = ft.TextField(label="Teléfono", width=200)
        email = ft.TextField(label="Email", width=250)
        search = ft.TextField(label="Buscar paciente", width=300)
        patient_table = ft.Column()

        def load_patients(filter_text=""):
            patient_table.controls.clear()
            rows = get_patients()

            if filter_text.strip():
                rows = [r for r in rows if filter_text.lower() in r["full_name"].lower()]

            if not rows:
                patient_table.controls.append(ft.Text("No hay pacientes registrados"))
            else:
                for row in rows:
                    patient_table.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(f"ID: {row['id']}", width=60),
                                    ft.Text(row["full_name"], width=250),
                                    ft.Text(f"Edad: {row['age']}", width=100),
                                    ft.Text(row["phone"], width=160),
                                    ft.Text(row["email"] or "", width=220),
                                ]
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=8
                        )
                    )
            page.update()

        def save_patient(e):
            if not full_name.value or not age.value or not phone.value:
                show_message("Completa nombre, edad y teléfono del paciente", ft.Colors.RED)
                return

            try:
                age_value = int(age.value)
                if age_value <= 0:
                    show_message("La edad debe se mayor que 0", ft.Colors.RED)
                    return
            except ValueError:
                show_message("La edad debe ser numérica", ft.Colors.RED)
                return

            conn = get_connection()
            conn.execute("""
                INSERT INTO patients (full_name, age, phone, email)
                VALUES (?, ?, ?, ?)
            """, (full_name.value, age_value, phone.value, email.value))
            conn.commit()
            conn.close()

            full_name.value = ""
            age.value = ""
            phone.value = ""
            email.value = ""

            load_patients()
            show_message("Paciente guardado coraectamente", ft.Colors.GREEN)

        load_patients()

        return ft.Column(
            [
                ft.Text("Patients", size=26, weight=ft.FontWeight.BOLD),
                ft.Row([full_name, age, phone, email], wrap=True),
                ft.ElevatedButton("Guardar paciente", on_click=save_patient),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_patients(search.value)),
                        ft.ElevatedButton("Mostrar todos", on_click=lambda e: load_patients())
                    ]
                ),
                patient_table
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def doctors_view():
        full_name = ft.TextField(label="Nombre del doctor", width=300)
        specialty = ft.Dropdown(
            label="Especialidad",
            width=220,
            options=[
                ft.dropdown.Option("General"),
                ft.dropdown.Option("Pediatra"),
                ft.dropdown.Option("Cardiólogo"),
                ft.dropdown.Option("Dermatólogo"),
                ft.dropdown.Option("Ginecólogo"),
                ft.dropdown.Option("Odontólogo")
            ]
        )
        phone = ft.TextField(label="Teléfono", width=200)
        search = ft.TextField(label="Buscar doctor", width=300)
        doctor_table = ft.Column()

        def load_doctors(filter_text=""):
            doctor_table.controls.clear()
            rows = get_doctors()

            if filter_text.strip():
                rows = [
                    r for r in rows
                    if filter_text.lower() in r["full_name"].lower()
                    or filter_text.lower() in r["specialty"].lower()
                ]

            if not rows:
                doctor_table.controls.append(ft.Text("No hay doctores registrados"))
            else:
                for row in rows:
                    doctor_table.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(f"ID: {row['id']}", width=60),
                                    ft.Text(row["full_name"], width=260),
                                    ft.Text(row["specialty"], width=180),
                                    ft.Text(row["phone"], width=180),
                                ]
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=8
                        )
                    )
            page.update()

        def save_doctor(e):
            if not full_name.value or not specialty.value or not phone.value:
                show_message("Completa todos los campos del doctor", ft.Colors.RED)
                return

            conn = get_connection()
            conn.execute("""
                INSERT INTO doctors (full_name, specialty, phone)
                VALUES (?, ?, ?)
            """, (full_name.value, specialty.value, phone.value))
            conn.commit()
            conn.close()

            full_name.value = ""
            specialty.value = None
            phone.value = ""

            load_doctors()
            show_message("Doctor guardado correctamente", ft.Colors.GREEN)

        load_doctors()

        return ft.Column(
            [
                ft.Text("Doctors", size=26, weight=ft.FontWeight.BOLD),
                ft.Row([full_name, specialty, phone], wrap=True),
                ft.ElevatedButton("Guardar doctor", on_click=save_doctor),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_doctors(search.value)),
                        ft.ElevatedButton("Mostrar todos", on_click=lambda e: load_doctors())
                    ]
                ),
                doctor_table
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def appointments_view():
        patient_dropdown = ft.Dropdown(label="Paciente", width=280)
        doctor_dropdown = ft.Dropdown(label="Doctor", width=280)
        appointment_date = ft.TextField(label="Fecha (YYYY-MM-DD)", width=180)
        appointment_time = ft.TextField(label="Hora (HH:MM)", width=150)
        status = ft.Dropdown(
            label="Estado",
            width=180,
            options=[
                ft.dropdown.Option("Programada"),
                ft.dropdown.Option("Completada"),
                ft.dropdown.Option("Cancelada"),
                ft.dropdown.Option("Perdida")
            ],
            value="Programada"
        )

        notes = ft.TextField(label="Notas", multiline=True, min_lines=2, max_lines=3, width=350)
        search = ft.TextField(label="Buscar cita", width=300)
        appointment_table = ft.Column()

        def load_dropdowns():
            patient_dropdown.options = [
                ft.dropdown.Option(key=str(p["id"]), text=p["full_name"])
                for p in get_patients()
            ]
            doctor_dropdown.options = [
                ft.dropdown.Option(key=str(d["id"]), text=f"{d['full_name']} - {d['specialty']}")
                for d in get_doctors()
            ]
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
                            content=ft.Column(
                                [
                                    ft.Text(f"Cita #{row['id']}", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Paciente: {row['patient_name']}"),
                                    ft.Text(f"Doctor: {row['doctor_name']}"),
                                    ft.Text(f"Especialidad: {row['specialty']}"),
                                    ft.Text(f"Fecha: {row['appointment_date']}"),
                                    ft.Text(f"Hora: {row['appointment_time']}"),
                                    ft.Text(f"Estado: {row['status']}"),
                                    ft.Text(f"Notas: {row['notes'] or ''}"),
                                ]
                            ),
                            padding=12,
                            border=ft.border.all(1, ft.Colors.BLACK12),
                            border_radius=10
                        )
                    )
            page.update()


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

            conn = get_connection()
            try:
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
                conn.commit()

                patient_dropdown.value = None
                doctor_dropdown.value = None
                appointment_date.value = ""
                appointment_time.value = ""
                status.value = "Programada"
                notes.value = ""

                load_appointments()
                show_message("Cita guardada correctamente", ft.Colors.GREEN)

            except sqlite3.IntegrityError:
                show_message("Ese doctor ya tiene una cita en esa fecha y hora", ft.Colors.RED)
            except Exception as ex:
                show_message(f"Error al guardar cita: {ex}", ft.Colors.RED)
            finally:
                conn.close()

        load_dropdowns()
        load_appointments()
        
        
        return ft.Column(
            [
                ft.Text("Appointments", size=26, weight=ft.FontWeight.BOLD),
                ft.Row([patient_dropdown, doctor_dropdown], wrap=True),
                ft.Row([appointment_date, appointment_time, status], wrap=True),
                notes,
                ft.ElevatedButton("Guardar cita", on_click=save_appointment),
                ft.Divider(),
                ft.Row(
                    [
                        search,
                        ft.ElevatedButton("Buscar", on_click=lambda e: load_appointments(search.value)),
                        ft.ElevatedButton("Mostrar todas", on_click=lambda e: load_appointments())
                    ]
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
                ft.Text("Reporte: Citas por estado", size=20, weight=ft.FontWeight.BOLD)
            )
            for row in rows:
                report_content.controls.append(ft.Text(f"{row['status']}: {row['total']}"))
            page.update()

        def report_by_doctor(e=None):
            report_content.controls.clear()
            conn = get_connection()
            rows = conn.execute("""
                SELECT d.full_name AS doctor_name, d.specialty, COUNT(a.id) AS total
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id
                GROUP BY d.id, d.full_name, d.specialty
                ORDER BY total DESC, doctor_name
            """).fetchall()
            conn.close()

            report_content.controls.append(
                ft.Text("Reporte: Citas por doctor", size=20, weight=ft.FontWeight.BOLD)
            )
            for row in rows:
                report_content.controls.append(
                    ft.Text(f"{row['doctor_name']} ({row['specialty']}): {row['total']}")
                )
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
                ft.Text("Reporte con CASE", size=20, weight=ft.FontWeight.BOLD)
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
                ft.Text("Reports", size=26, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.ElevatedButton("Citas por estado", on_click=report_by_status),
                        ft.ElevatedButton("Citas por doctor", on_click=report_by_doctor),
                        ft.ElevatedButton("Reporte con CASE", on_click=report_case),
                    ],
                    wrap=True
                ),
                ft.Divider(),
                report_content
            ],
            scroll=ft.ScrollMode.AUTO
        )