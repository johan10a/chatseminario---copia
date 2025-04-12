import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import csv
import smtplib
import re
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq

# API festivos Colombia
def es_festivo(fecha_str):
    try:
        año = datetime.strptime(fecha_str, "%Y-%m-%d").year
        response = requests.get(f"https://date.nager.at/api/v3/PublicHolidays/{año}/CO")
        festivos = [f["date"] for f in response.json()]
        return fecha_str in festivos
    except:
        return False

# Configuración correo
CORREO_RECEPTOR = "johanalexischraferrerosa@gmail.com"
CORREO_REMITENTE = "johanalexischraferrerosa@gmail.com"
CLAVE_APP = "dopx appq revn wlny"

# Modelo de IA (Groq)
client = Groq(api_key="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")

# Estados globales
agendando_cita = False
datos_cita = {}
pasos = ["nombre", "fecha", "hora", "sede", "correo"]
indice_paso = 0

# Validaciones
def validar_fecha(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        if fecha.weekday() == 6 or es_festivo(fecha_str):
            return False
        return True
    except:
        return False

def validar_hora(hora_str, fecha_str):
    try:
        hora = datetime.strptime(hora_str, "%H:%M").time()
        dia = datetime.strptime(fecha_str, "%Y-%m-%d").weekday()
        if dia < 5:  # Lunes a viernes
            return datetime.strptime("06:00", "%H:%M").time() <= hora <= datetime.strptime("20:00", "%H:%M").time()
        elif dia == 5:  # Sábado
            return datetime.strptime("06:00", "%H:%M").time() <= hora <= datetime.strptime("17:00", "%H:%M").time()
        return False
    except:
        return False

# IA solo si no es cita
def get_ai_response(query):
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": query}],
        model="llama-3.3-70b-versatile"
    )
    return completion.choices[0].message.content.strip()

# Guardar CSV y enviar
def guardar_y_enviar(datos):
    with open("citas.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datos["nombre"], datos["fecha"], datos["hora"], datos["sede"], datos["correo"]])

    msg = MIMEMultipart()
    msg["From"] = CORREO_REMITENTE
    msg["To"] = datos["correo"]
    msg["Subject"] = "Confirmación de cita médica"
    cuerpo = f"""Hola {datos['nombre']},

Tu cita ha sido agendada exitosamente con los siguientes datos:

🗓 Fecha: {datos['fecha']}
⏰ Hora: {datos['hora']}
📍 Sede: {datos['sede']}

¡Gracias por confiar en el Centro Médico Buena Fé! 🏥😊tu salud es nuestra prioridad.
"""
    msg.attach(MIMEText(cuerpo, "plain"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_REMITENTE, CLAVE_APP)
        server.send_message(msg)

# Procesar entrada
def procesar_entrada(user_input):
    global agendando_cita, indice_paso, datos_cita

    respuesta = ""

    if not agendando_cita:
        if re.search(r"cita|agendar|médic", user_input, re.IGNORECASE):
            agendando_cita = True
            indice_paso = 0
            datos_cita = {}
            respuesta = "Perfecto, ¿cuál es tu nombre?"
        elif re.search(r"sedes?", user_input, re.IGNORECASE):
            respuesta = "Contamos con sedes en Cali y Bogotá."
        elif re.search(r"depresión|ansiedad|triste|estres|soledad", user_input, re.IGNORECASE | re.UNICODE):
            respuesta = get_ai_response(user_input) + "\n\nNo te sientas solo, llama al #106, Si deseas una cita, solo escribe 'quiero una cita' y la agendaremos por ti."
        else:
            respuesta = get_ai_response(user_input)
    else:
        paso = pasos[indice_paso]
        if paso == "nombre":
            datos_cita["nombre"] = user_input
            respuesta = "¿Qué fecha deseas? (Formato: AAAA-MM-DD)"
        elif paso == "fecha":
            if not validar_fecha(user_input):
                respuesta = "Por favor ingresa una fecha válida que no sea domingo ni festivo (AAAA-MM-DD)."
                return respuesta
            datos_cita["fecha"] = user_input
            respuesta = "¿A qué hora deseas la cita? (Formato 24h: HH:MM)"
        elif paso == "hora":
            if not validar_hora(user_input, datos_cita["fecha"]):
                respuesta = "La hora ingresada no está dentro del horario de atención. Intenta otra (L-V 6am-8pm, Sáb 6am-5pm)."
                return respuesta
            datos_cita["hora"] = user_input
            respuesta = "¿En qué ciudad deseas la cita? (Cali o Bogotá)"
        elif paso == "sede":
            if user_input.lower() not in ["cali", "bogota", "bogotá"]:
                respuesta = "Solo tenemos sedes en Cali y Bogotá. Por favor ingresa una ciudad válida."
                return respuesta
            datos_cita["sede"] = user_input.title()
            respuesta = "Finalmente, ¿a qué correo deseas que enviemos la confirmación?"
        elif paso == "correo":
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
                respuesta = "Por favor ingresa un correo válido."
                return respuesta
            datos_cita["correo"] = user_input
            guardar_y_enviar(datos_cita)
            respuesta = "¡Tu cita ha sido agendada y se ha enviado una confirmación a tu correo!"
            agendando_cita = False
            datos_cita = {}
            indice_paso = -1

        indice_paso += 1

    return respuesta

# GUI con Tkinter
def send_message():
    user_input = entry.get()
    chat_box.insert(tk.END, "Tú: " + user_input + "\n")
    entry.delete(0, tk.END)
    respuesta = procesar_entrada(user_input)
    chat_box.insert(tk.END, "Asistente: " + respuesta + "\n\n")

# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Asistente Médico")

chat_box = scrolledtext.ScrolledText(ventana, wrap=tk.WORD)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(ventana, width=80)
entry.pack(padx=10, pady=(0, 10))

boton_enviar = tk.Button(ventana, text="Enviar", command=send_message)
boton_enviar.pack(pady=(0, 10))

chat_box.insert(tk.END, "Asistente: ¡Hola! 👋 Bienvenido al Centro Médico Buena Fé 🏥.\nEstoy aquí para ayudarte. Puedo asistirte con:\n- Agendamiento de citas 📅\n- Información sobre nuestras sedes 📍\n- Soporte en lo que necesites 🤝\n\n¿En qué puedo ayudarte hoy?\n\n")



ventana.mainloop()
