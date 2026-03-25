import flet as ft

def main(page: ft.Page):
    page.title = "Sistema de Citas Médicas"
    page.padding = 20

    # lista para guardar citas (simula base de datos)
    citas = []

    # mensaje de estado
    mensaje = ft.Text("")

    # datos
    nombre = ft.TextField(label="Nombre del paciente")
    medico = ft.TextField(label="Médico")
    fecha = ft.TextField(label="Fecha (dd/mm/aaaa)")
    hora = ft.TextField(label="Hora (ej: 10:00 AM)")