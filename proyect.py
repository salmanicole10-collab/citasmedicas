import flet as ft

def main(page: ft.Page):
    page.title = "Sistema de Citas Médicas"
    page.padding = 20

    # lista pa guardar citas 
    citas = []

    # mensaje de estado
    mensaje = ft.Text("")

    # datos
    nombre = ft.TextField(label="Nombre del paciente")
    medico = ft.TextField(label="Médico")
    fecha = ft.TextField(label="Fecha (dd/mm/aaaa)")
    hora = ft.TextField(label="Hora (ej: 10:00 AM)")

    tipo_medico = ft.Dropdown(
        label="Tipo de médico",
        options=[
            ft.dropdown.Option("General"),
            ft.dropdown.Option("Pediatra"),
            ft.dropdown.Option("Cardiólogo"),
            ft.dropdown.Option("Dermatólogo"),
            ft.dropdown.Option("Ginecólogo"),
            ft.dropdown.Option("Odontólogo")
        ]
    )

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


    def guardar_cita(e):
        if nombre.value == "" or medico.value == "" or fecha.value == "" or hora.value == "":
            mensaje.value = "Por favor llena todos los campos"
            mensaje.color = "red"
        else:
            # save datos en la lista
            cita = {
                "nombre": nombre.value,
                "medico": medico.value,
                "fecha": fecha.value,
                "hora": hora.value
            }

            citas.append(cita)

            mensaje.value = "Cita guardada correctamente"
            mensaje.color = "green"

            # limpiar campos
            nombre.value = ""
            medico.value = ""
            fecha.value = ""
            hora.value = ""

        page.update()

    page.add(
        ft.Text("Sistema de Citas Médicas", size=24, weight="bold"),
        ft.Text("Avance: Registro básico de citas"),
        ft.Divider(),
        nombre,
        medico,
        fecha,
        hora,
        ft.ElevatedButton("Guardar cita", on_click=guardar_cita),
        mensaje
    )

ft.app(target=main)