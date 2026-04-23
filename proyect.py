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