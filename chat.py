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
esperando_cedula_para_agenda = False
datos_cita = {}
pasos = ["cedula", "nombre", "fecha", "hora", "sede", "correo"]
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
esperando_cedula_para_agenda = False
datos_cita = {}
pasos = ["cedula", "nombre", "fecha", "hora", "sede", "correo"]
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

# IA solo si es una consulta sobre dolor específico
def get_ai_response(query):
    # Aquí no hay respuestas predefinidas, solo se consulta la IA de Groq
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": query}],
        model="llama-3.3-70b-versatile"
    )
    return completion.choices[0].message.content.strip()

# Guardar CSV y enviar
def guardar_y_enviar(datos):
    with open("citas.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datos["cedula"], datos["nombre"], datos["fecha"], datos["hora"], datos["sede"], datos["correo"]])

    msg = MIMEMultipart()
    msg["From"] = CORREO_REMITENTE
    msg["To"] = datos["correo"]
    msg["Subject"] = "Confirmación de cita médica"
    cuerpo = f"""Hola {datos['nombre']},

Tu cita ha sido agendada exitosamente con los siguientes datos:

🗓 Fecha: {datos['fecha']}
⏰ Hora: {datos['hora']}
📍 Sede: {datos['sede']}
🪪 Cédula: {datos['cedula']}

¡Gracias por confiar en nosotros!
"""
    msg.attach(MIMEText(cuerpo, "plain"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_REMITENTE, CLAVE_APP)
        server.send_message(msg)

# Función para mostrar citas por cédula
def mostrar_agenda(cedula):
    try:
        with open("citas.csv", "r") as f:
            reader = csv.reader(f)
            citas = list(reader)
        
        citas_filtradas = [cita for cita in citas if len(cita) > 0 and cita[0] == cedula]
        if citas_filtradas:
            agenda = "📅 Tus citas agendadas:\n\n"
            for cita in citas_filtradas:
                agenda += f"🗓 {cita[2]} ⏰ {cita[3]} 📍 {cita[4]}\n"
            chat_box.insert(tk.END, agenda + "\n")
        else:
            chat_box.insert(tk.END, "❌ No tienes citas agendadas.\n\n")
    except FileNotFoundError:
        chat_box.insert(tk.END, "❌ No se encontró el archivo de citas.\n\n")
# Nuevo estado para el modo conversación con la IA
modo_ia_activo = False
historial_ia = []

# Procesar entrada del usuario
def procesar_entrada(user_input):
    global agendando_cita, indice_paso, datos_cita
    global esperando_cedula_para_agenda, modo_ia_activo, historial_ia

    user_input = user_input.strip()

    if user_input.lower() == "salir":
        if modo_ia_activo:
            modo_ia_activo = False
            historial_ia = []
            return "👋 Saliste del modo de conversación con el asistente médico. ¿En qué más puedo ayudarte?"
        else:
            ventana.destroy()
            return "Saliendo del asistente. ¡Hasta pronto! 👋"

    # Si estamos en conversación activa con IA
    if modo_ia_activo:
        historial_ia.append({"role": "user", "content": user_input})
        completion = client.chat.completions.create(
            messages=historial_ia,
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content.strip()
        historial_ia.append({"role": "assistant", "content": respuesta})
        return respuesta

    if esperando_cedula_para_agenda:
        if not user_input.isdigit() or len(user_input) < 4:
                return "❌ La cédula debe tener mas de 4 dígitosdddd."
        mostrar_agenda(user_input)
        esperando_cedula_para_agenda = False
        return "✅ Esa es tu agenda médica actual."

    if user_input.lower() == "ver mi agenda":
        esperando_cedula_para_agenda = True
        return "Por favor, ingresa tu número de cédula para mostrarte tus citas."

    if agendando_cita:
        paso = pasos[indice_paso]
        if paso == "cedula":
            if not user_input.isdigit() or len(user_input) < 4:
                return "❌ La cédula debe tener mas de 4 dígitos."
            datos_cita["cedula"] = user_input
            respuesta = "¿Cuál es tu nombre completo?"
        elif paso == "nombre":
            datos_cita["nombre"] = user_input
            respuesta = "¿Qué fecha deseas? (AAAA-MM-DD)"
        elif paso == "fecha":
            if not validar_fecha(user_input):
                return "❌ Fecha inválida o no disponible. Intenta otra."
            datos_cita["fecha"] = user_input
            respuesta = "¿A qué hora deseas la cita? (HH:MM)"
        elif paso == "hora":
            if not validar_hora(user_input, datos_cita["fecha"]):
                return "❌ Hora fuera del horario de atención."
            datos_cita["hora"] = user_input
            respuesta = "¿En qué ciudad deseas la cita? (Cali o Bogotá)"
        elif paso == "sede":
            if user_input.lower() not in ["cali", "bogota", "bogotá"]:
                return "Solo tenemos sedes en Cali y Bogotá."
            datos_cita["sede"] = user_input.title()
            respuesta = "¿A qué correo deseas que enviemos la confirmación?"
        elif paso == "correo":
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
                return "❌ Correo inválido."
            datos_cita["correo"] = user_input
            guardar_y_enviar(datos_cita)
            agendando_cita = False
            indice_paso = 0
            datos_cita = {}
            return "✅ ¡Cita agendada y confirmación enviada por correo!"
        indice_paso += 1
        return respuesta

    if re.search(r"agendar|cita", user_input, re.IGNORECASE):
        agendando_cita = True
        indice_paso = 0
        datos_cita = {}
        return "Perfecto, primero, ¿cuál es tu número de cédula?"

    # Activar modo conversación IA si el mensaje empieza con "me duele"
    if user_input.lower().startswith("me duele"):
        partes_cuerpo = ["garganta", "estómago", "cabeza", "pierna", "brazo", "espalda", "cuello", "muñeca", "dedo"]
        if any(parte in user_input.lower() for parte in partes_cuerpo):
            modo_ia_activo = True
            historial_ia = [{"role": "user", "content": user_input}]
            completion = client.chat.completions.create(
                messages=historial_ia,
                model="llama-3.3-70b-versatile"
            )
            respuesta = completion.choices[0].message.content.strip()
            historial_ia.append({"role": "assistant", "content": respuesta})
            return respuesta + "\n\n💬 Puedes seguir preguntando. Escribe 'salir' para volver al asistente principal."
        else:

            return "❌ No se detectó una parte del cuerpo válida. ¿Puedes especificar mejor el dolor?"
        
    if any(palabra in user_input.lower() for palabra in ["desmayo", "descompensación", "colapso"]):
        modo_ia_activo = True
        historial_ia = [{"role": "user", "content": user_input}]
        completion = client.chat.completions.create(
            messages=historial_ia,
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content.strip()
        historial_ia.append({"role": "assistant", "content": respuesta})
        return respuesta + "\n\n💬 Puedes seguir preguntando. Escribe 'salir' para volver al asistente principal."      
      
    if re.search(r"ansiedad|depresión|estres|salud mental|terapia|psicólogo|sentimientos", user_input, re.IGNORECASE): 
        modo_ia_activo = True
        historial_ia = [{
    "role": "system", 
    "content": """
    Eres un asistente de salud mental, responde con empatía y profesionalismo. 
    Recuerda que este servicio es solo una ayuda rápida y no un diagnóstico médico. 
    Al final de cada respuesta, debes incluir este decálogo de responsabilidad:

    1. Este servicio no reemplaza una consulta médica o psicológica profesional.
    2. Las respuestas proporcionadas son para orientación general y no deben tomarse como consejo médico.
    3. Si experimentas una crisis emocional, te recomendamos que busques ayuda inmediata de un profesional de la salud.
    4. El asistente no tiene la capacidad para diagnosticar ni ofrecer tratamientos médicos.
    5. Si necesitas ayuda urgente, por favor, llama a la línea gratuita de salud mental al #106.
    6. Recuerda que cada persona es única, y lo que funciona para algunos puede no ser adecuado para todos.
    7. Este asistente está diseñado para proporcionar información básica y apoyo emocional de forma confidencial.
    8. Si necesitas una cita médica o psicológica, por favor, contacta con un profesional.
    9. El asistente está aquí para acompañarte en momentos difíciles, pero no sustituye la atención de emergencia.
    10. Si alguna respuesta te genera dudas o malestar, no dudes en buscar el consejo de un experto en salud mental.

    Al final de cada respuesta, incluir: "Para ayuda urgente, por favor llama a la línea gratuita de salud mental #106."
    """
}]

        historial_ia.append({"role": "user", "content": user_input})
        completion = client.chat.completions.create(
            messages=historial_ia,
            model="llama-3.3-70b-versatile"
        )
        
        respuesta = completion.choices[0].message.content.strip()
        historial_ia.append({"role": "assistant", "content": respuesta})
        return respuesta + "\n\n💬 Puedes seguir preguntando. Escribe 'salir' para volver al asistente principal." 
    return "❌ Lo siento, no entiendo la consulta. ¿En qué más puedo ayudarte?"

# GUI
ventana = tk.Tk()
ventana.title("Asistente Médico")
chat_box = scrolledtext.ScrolledText(ventana, wrap=tk.WORD)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(ventana, width=80)
entry.pack(padx=10, pady=(0, 10))

# Enviar mensaje
def send_message():
    user_input = entry.get()
    chat_box.insert(tk.END, "Tú: " + user_input + "\n")
    entry.delete(0, tk.END)
    respuesta = procesar_entrada(user_input)
    chat_box.insert(tk.END, "Asistente: " + respuesta + "\n\n")

# Botón para enviar
boton_enviar = tk.Button(ventana, text="Enviar", command=send_message)
boton_enviar.pack(pady=(0, 10))

chat_box.insert(tk.END, "Asistente: ¡Hola! 👋 Bienvenido al Centro Médico Buena Fé 🏥.\nEstoy aquí para ayudarte. Puedes:\n- Agendar una cita 📅\n- Ver tu agenda 🗓 (escribe 'ver mi agenda')\n\n¿En qué puedo ayudarte hoy?\n\n")

ventana.mainloop()
