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

    def guardar_cita(e):
        if nombre.value == "" or medico.value == "" or fecha.value == "" or hora.value == "":
            mensaje.value = "Por favor llena todos los campos"
            mensaje.color = "red"
        else:
            # Guardar datos en la lista
            cita = {
                "nombre": nombre.value,
                "medico": medico.value,
                "fecha": fecha.value,
                "hora": hora.value
            }

            citas.append(cita)

            mensaje.value = "Cita guardada correctamente"
            mensaje.color = "green"

            # Limpiar campos
            nombre.value = ""
            medico.value = ""
            fecha.value = ""
            hora.value = ""

        page.update()