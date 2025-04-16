import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import csv
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración correo
CORREO_REMITENTE = "johanalexischraferrerosa@gmail.com"
CLAVE_APP = "dopx appq revn wlny"

# Estados globales
agendando_cita = False
consultando_cita = False
datos_cita = {}
pasos = ["cedula", "nombre", "fecha", "hora", "sede", "correo"]
indice_paso = 0

# Validaciones
def validar_fecha(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        if fecha.weekday() == 6:
            return False
        return True
    except:
        return False

def validar_hora(hora_str, fecha_str):
    try:
        hora = datetime.strptime(hora_str, "%H:%M").time()
        dia = datetime.strptime(fecha_str, "%Y-%m-%d").weekday()
        if dia < 5:
            return datetime.strptime("06:00", "%H:%M").time() <= hora <= datetime.strptime("20:00", "%H:%M").time()
        elif dia == 5:
            return datetime.strptime("06:00", "%H:%M").time() <= hora <= datetime.strptime("17:00", "%H:%M").time()
        return False
    except:
        return False

def enviar_confirmacion(datos, cancelar=False):
    msg = MIMEMultipart()
    msg["From"] = CORREO_REMITENTE
    msg["To"] = datos["correo"]
    msg["Subject"] = "Confirmación de cita médica"

    cuerpo = f"""Hola {datos['nombre']},

Tu cita ha sido agendada exitosamente con los siguientes datos:

🗓 Fecha: {datos['fecha']}
⏰ Hora: {datos['hora']}
📍 Sede: {datos['sede']}
🪪 Documento: {datos['cedula']}

¡Gracias por confiar en el Centro Médico Buena Fé! 🏥😊 Tu salud es nuestra prioridad.
"""
    msg.attach(MIMEText(cuerpo, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_REMITENTE, CLAVE_APP)
        server.send_message(msg)

def buscar_citas_por_cedula(cedula):
    with open("citas.csv", newline="") as f:
        reader = csv.reader(f)
        return [row for row in reader if row[0] == cedula]

def procesar_entrada(user_input):
    global agendando_cita, indice_paso, datos_cita, consultando_cita

    user_input = user_input.strip()
    if user_input.lower() == "salir":
        ventana.destroy()
        return "Saliendo del asistente. ¡Hasta pronto! 👋"

    respuesta = ""

    if agendando_cita:
        paso = pasos[indice_paso]
        if paso == "cedula":
            datos_cita["cedula"] = user_input
            respuesta = "¿Cuál es tu nombre?"
        elif paso == "nombre":
            datos_cita["nombre"] = user_input
            respuesta = "¿Qué fecha deseas? (AAAA-MM-DD)"
        elif paso == "fecha":
            if not validar_fecha(user_input):
                return "Fecha inválida o no disponible. Intenta otra."
            datos_cita["fecha"] = user_input
            respuesta = "¿A qué hora deseas la cita? (HH:MM)"
        elif paso == "hora":
            if not validar_hora(user_input, datos_cita["fecha"]):
                return "Hora fuera del horario de atención."
            datos_cita["hora"] = user_input
            respuesta = "¿En qué ciudad deseas la cita? (Cali o Bogotá)"
        elif paso == "sede":
            if user_input.lower() not in ["cali", "bogota", "bogotá"]:
                return "Solo tenemos sedes en Cali y Bogotá."
            datos_cita["sede"] = user_input.title()
            respuesta = "¿A qué correo deseas que enviemos la confirmación?"
        elif paso == "correo":
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
                return "Correo inválido."
            datos_cita["correo"] = user_input
            guardar_cita_csv(datos_cita)
            enviar_confirmacion(datos_cita)
            respuesta = "¡Cita agendada y confirmación enviada por correo!"
            agendando_cita = False
            datos_cita = {}
            indice_paso = 0
            return respuesta
        indice_paso += 1
        return respuesta

    elif consultando_cita:
        citas = buscar_citas_por_cedula(user_input)
        consultando_cita = False
        if not citas:
            return "No se encontraron citas con esa cédula."
        respuesta = "Tus citas son:\n"
        for idx, cita in enumerate(citas):
            respuesta += f"{idx + 1}. {cita[2]} a las {cita[3]} en {cita[4]}\n"
        return respuesta

    else:
        if re.search(r"agendar|cita", user_input, re.IGNORECASE):
            agendando_cita = True
            indice_paso = 0
            datos_cita = {}
            return "Perfecto, primero ¿cuál es tu número de cédula?"
        elif re.search(r"consultar|ver agenda|mis citas", user_input, re.IGNORECASE):
            consultando_cita = True
            return "Por favor ingresa tu número de cédula para consultar tus citas."
        else:
            return "Lo siento, no te entendí. ¿Cómo puedo ayudarte hoy?"

def guardar_cita_csv(datos):
    with open("citas.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datos["cedula"], datos["nombre"], datos["fecha"], datos["hora"], datos["sede"], datos["correo"]])

# GUI
ventana = tk.Tk()
ventana.title("Asistente Médico")
chat_box = scrolledtext.ScrolledText(ventana, wrap=tk.WORD)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(ventana, width=80)
entry.pack(padx=10, pady=(0, 10))

def send_message():
    user_input = entry.get()
    chat_box.insert(tk.END, "Tú: " + user_input + "\n")
    entry.delete(0, tk.END)
    respuesta = procesar_entrada(user_input)
    chat_box.insert(tk.END, "Asistente: " + respuesta + "\n\n")

boton_enviar = tk.Button(ventana, text="Enviar", command=send_message)
boton_enviar.pack(pady=(0, 10))

chat_box.insert(tk.END, "Asistente: ¡Hola! 👋 Bienvenido al Centro Médico Buena Fé 🏥.\nEstoy aquí para ayudarte. Puedo asistirte con:\n- Agendamiento de citas 📅\n- Consultar tu agenda 🗓\n\n¿En qué puedo ayudarte hoy?\n\n")

ventana.mainloop()
