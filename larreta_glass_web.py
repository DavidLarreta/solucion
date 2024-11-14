import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from streamlit_option_menu import option_menu
import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurar el gestor de cookies
cookies = EncryptedCookieManager(prefix="streamlit_app", password="your_secret_password")

# Asegúrate de llamar a la función de cookies en el inicio de tu aplicación
if not cookies.ready():
    st.stop()

# Definir el alcance y las credenciales de la API de Google Sheets y Google Calendar
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/calendar"]
credentials_path = 'proyeto-larreta-f1a76bfd3fdc.json' 
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
gc = gspread.authorize(credentials)

calendar_credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scope)
calendar_service = build('calendar', 'v3', credentials=calendar_credentials)

# URL de las hojas de cálculo
login_spreadsheet_url = "https://docs.google.com/spreadsheets/d/16xPBOa52sRyq4t1ncxJkXOX8zEBCP3M8_I3fvjj9cU4/edit?gid=0#gid=0"
usuarios_spreadsheet_url = "https://docs.google.com/spreadsheets/d/1o5LngNTa8sWLcOa9HIOxAfDPnK10iWiaH_HwfvTkOZg/edit?gid=0#gid=0"
formulario_spreadsheet_url = "https://docs.google.com/spreadsheets/d/1SdqA3xdm8DdcyA7jweOe2QPirtm61LyAz9tRhSwPM_U/edit?gid=0#gid=0"

login_spreadsheet = gc.open_by_url(login_spreadsheet_url)
usuarios_spreadsheet = gc.open_by_url(usuarios_spreadsheet_url)
formulario_spreadsheet = gc.open_by_url(formulario_spreadsheet_url)

login_worksheet = login_spreadsheet.worksheet("login")  
usuarios_worksheet = usuarios_spreadsheet.worksheet("usuarios")  
formulario_worksheet = formulario_spreadsheet.worksheet("Hoja1")  

def autenticar_usuario(correo, contrasena, es_admin):
    worksheet = login_worksheet if es_admin else usuarios_worksheet
    usuarios = worksheet.get_all_records()
    for usuario in usuarios:
        if usuario['correo'] == correo and str(usuario['Contraseña']) == contrasena:
            return True
    return False

def enviar_correo(sender_email, mensaje, fecha, hora_inicio, hora_fin, nombre):
    receiver_email = "fabriciolarreta_14@hotmail.com"
    gmail_user = "davidlarreta1234@gmail.com"
    gmail_password = "dvpe fumi zrfm ixjy"  

    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = receiver_email
    msg['Subject'] = "Nueva Reserva"

    cuerpo_mensaje = f"Nombre: {nombre}\nCorreo electrónico: {sender_email}\n\nMensaje: {mensaje}\n\nFecha: {fecha}\nHora de inicio: {hora_inicio}\nHora de fin: {hora_fin}"
    msg.attach(MIMEText(cuerpo_mensaje, 'plain'))

    # Enviar el correo
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, receiver_email, text)
        server.quit()
        st.success("Correo electrónico enviado exitosamente.")
    except Exception as e:
        st.error(f"Error al enviar el correo electrónico: {e}")

def mostrar_reservacion_citas():
    # Título de la aplicación
    st.header("Reservación de Citas")

    # Incrustar el calendario de Google
    st.markdown(
        """
        <iframe src="https://calendar.google.com/calendar/embed?src=davidlarreta1234%40gmail.com&ctz=UTC" style="border: 0" width="600" height="400" frameborder="0" scrolling="no"></iframe>
        """,
        unsafe_allow_html=True,
    )

    # Crear el formulario en Streamlit
    with st.form(key='formulario'):
        nombre = st.text_input("Nombre")
        # Usar el correo del estado de la sesión y deshabilitar el campo
        email = st.text_input("Email", value=st.session_state['usuario'], disabled=True)
        mensaje = st.text_area("Mensaje")
        
        # Obtener la fecha de hoy y calcular el día siguiente
        hoy = datetime.date.today()
        dia_siguiente = hoy + datetime.timedelta(days=1)
        
        # Configurar el campo de fecha para que solo permita seleccionar a partir del día siguiente
        fecha = st.date_input("Fecha de la reserva", min_value=dia_siguiente)
        
        # Definir opciones de tiempo entre 14:00 y 17:00 en intervalos de 10 minutos
        opciones_hora_inicio = [datetime.time(hour, minute) for hour in range(14, 18) for minute in [0, 10, 20, 30, 40, 50]]
        hora_inicio = st.selectbox("Hora de inicio", opciones_hora_inicio, index=0)
        
        duracion = st.slider("Duración (minutos)", min_value=20, max_value=60, step=10, value=20)
        submit_button = st.form_submit_button(label='Enviar')

    # Manejar la lógica de envío del formulario
    if submit_button:
        hora_fin = (datetime.datetime.combine(datetime.date.today(), hora_inicio) + datetime.timedelta(minutes=duracion)).time()

        if hora_inicio < datetime.time(14, 0) or hora_fin > datetime.time(17, 0):
            st.error("Las citas deben ser entre las 14:00 y las 17:00, y la duración debe ser entre 20 y 60 minutos.")
        else:
            reservas = formulario_worksheet.get_all_records()
            nueva_reserva_inicio = f"{fecha} {hora_inicio}"
            nueva_reserva_fin = f"{fecha} {hora_fin}"
            conflicto = False

            for reserva in reservas:
                if 'Fecha' in reserva and 'Hora de inicio' in reserva and 'Hora de fin' in reserva:
                    reserva_inicio = f"{reserva['Fecha']} {reserva['Hora de inicio']}"
                    reserva_fin = f"{reserva['Fecha']} {reserva['Hora de fin']}"
                    if (nueva_reserva_inicio >= reserva_inicio and nueva_reserva_inicio < reserva_fin) or (nueva_reserva_fin > reserva_inicio and nueva_reserva_fin <= reserva_fin):
                        conflicto = True
                        break

            if conflicto:
                st.error("Esta franja horaria ya está reservada. Por favor, elige otra hora.")
            else:
                try:
                    formulario_worksheet.append_row([nombre, email, mensaje, str(fecha), str(hora_inicio), str(hora_fin)])

                    # Crear evento en Google Calendar
                    event = {
                        'summary': 'Cita de {}'.format(nombre),
                        'description': mensaje,
                        'start': {
                            'dateTime': '{}T{}'.format(fecha, hora_inicio),
                            'timeZone': 'UTC',
                        },
                        'end': {
                            'dateTime': '{}T{}'.format(fecha, hora_fin),
                            'timeZone': 'UTC',
                        }
                    }

                    calendar_service.events().insert(calendarId='davidlarreta1234@gmail.com', body=event).execute()

                    enviar_correo(email, mensaje, fecha, hora_inicio, hora_fin, nombre)

                    st.success("Correo enviado exitosamente")
                except Exception as e:
                    st.error(f"Error al enviar los datos a Google Sheets, Google Calendar o correo electrónico: {e}")
                    
def mostrar_presentacion():
    
    # Título de la presentación
    st.header("Empresa Larreta Glass")
    # Contenido de la presentación
    st.subheader("Bienvenidos a Larreta Glass")
    st.write("En Larreta Glass, nuestra misión es innovar continuamente en el campo de la tecnología para ofrecer soluciones que mejoren la vida de las personas.")

    st.subheader("Nuestros Valores")
    st.write("""
    - **Innovación:** Buscamos siempre las ideas más novedosas y creativas.
    - **Calidad:** Nos comprometemos a ofrecer productos y servicios de la más alta calidad.
    - **Integridad:** Actuamos con transparencia y ética en todas nuestras acciones.
    - **Colaboración:** Fomentamos el trabajo en equipo y la colaboración entre nuestros empleados y con nuestros clientes.
    """)

    st.subheader("Nuestros Servicios")
    st.write("""
    - **Instalacion de vidrios:** Creamos aplicaciones personalizadas que se ajustan a las necesidades de nuestros clientes.
    - **Expertos en acero inoxidable:** Ofrecemos asesoramiento experto para ayudar a las empresas a aprovechar al máximo la tecnología.
    - **Soporte Técnico:** Proporcionamos soporte técnico de primer nivel para garantizar que nuestros clientes puedan operar sin interrupciones.
    """)

    st.subheader("Contáctanos")
    st.write("Para más información, visita nuestro sitio web o contáctanos a través de nuestras redes sociales.")

def mostrar_trabajos_realizados():
    # Título de los trabajos realizados
    st.header("Trabajos Realizados")

    # Contenido de los trabajos realizados
    st.write("""
    - Aqui se mostraran los logros de la empresa y los trabajos realizados
    - **2020:** Lanzamos nuestro producto estrella que fue un éxito en ventas.
    - **2019:** Expandimos nuestras operaciones a nivel internacional.
    """)

def mostrar_testimonios():
    # Título del equipo de trabajo
    st.header("Testimonios")

    # Contenido del equipo de trabajo
    st.write("""
    - **CEO:** Juan Pérez
    - **CTO:** María García
    - **COO:** Luis Martínez
    - **CFO:** Ana Rodríguez
    """)

def pagina_inicio_sesion():
    st.header("Inicio de Sesión")

    if 'tipo_usuario' not in st.session_state:
        tipo_usuario = st.radio("¿Eres cliente o administrador?", ("Cliente", "Administrador"))
        submit_tipo = st.button("Enviar")

        if submit_tipo:
            st.session_state['tipo_usuario'] = tipo_usuario
            st.experimental_rerun()
    else:
        tipo_usuario = st.session_state['tipo_usuario']

        if tipo_usuario == "Administrador":
            with st.form(key='login_form'):
                correo = st.text_input("Correo electrónico")
                contrasena = st.text_input("Contraseña", type="password")
                submit_button = st.form_submit_button(label='Iniciar Sesión')

            if submit_button:
                if autenticar_usuario(correo, contrasena, es_admin=True):
                    st.session_state['logged_in'] = True
                    st.session_state['usuario'] = correo
                    cookies["logged_in"] = "True"
                    cookies["tipo_usuario"] = tipo_usuario
                    cookies["usuario"] = correo
                    cookies.save()
                    st.success("Inicio de sesión exitoso.")
                    st.experimental_rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")
        else:
            tiene_cuenta = st.radio("¿Tienes cuenta?", ("Sí", "No"))

            if tiene_cuenta == "No":
                with st.form(key='registro_form'):
                    usuario = st.text_input("Nombre de usuario")
                    correo = st.text_input("Correo electrónico")
                    contrasena = st.text_input("Contraseña", type="password")
                    submit_button = st.form_submit_button(label='Registrarse')

                if submit_button:
                    if len(contrasena) < 5:
                        st.error("La contraseña debe tener al menos 5 caracteres.")
                    elif not "@" in correo:
                        st.error("Correo electrónico no válido.")
                    elif not "gmail" or not "hotmail" or not "yahoo" or not "outlook" or not ".com":
                        st.error("Correo electrónico no valido")
                    else:
                        usuarios_worksheet.append_row([usuario, correo, contrasena])
                        st.success("Registro exitoso. Ahora puedes iniciar sesión.")
            else:
                with st.form(key='login_form'):
                    correo = st.text_input("Correo electrónico")
                    contrasena = st.text_input("Contraseña", type="password")
                    submit_button = st.form_submit_button(label='Iniciar Sesión')

                if submit_button:
                    if autenticar_usuario(correo, contrasena, es_admin=False):
                        st.session_state['logged_in'] = True
                        st.session_state['usuario'] = correo
                        cookies["logged_in"] = "True"
                        cookies["tipo_usuario"] = tipo_usuario
                        cookies["usuario"] = correo
                        cookies.save()
                        st.success("Inicio de sesión exitoso.")
                        st.experimental_rerun()
                    else:
                        st.error("Correo o contraseña incorrectos.")

def cerrar_sesion():
    st.session_state['logged_in'] = False
    st.session_state.pop('usuario', None)
    st.session_state.pop('tipo_usuario', None)
    cookies["logged_in"] = "False"
    cookies["tipo_usuario"] = ""
    cookies["usuario"] = ""
    cookies.save()
    st.experimental_rerun()

def cambiar_a_administrador():
    st.session_state['logged_in'] = False
    st.session_state.pop('usuario', None)
    st.session_state.pop('tipo_usuario', None)
    cookies["logged_in"] = "False"
    cookies["tipo_usuario"] = ""
    cookies["usuario"] = ""
    cookies.save()
    st.experimental_rerun()

def mostrar_paginas():
    # Mostrar el icono de perfil según el tipo de usuario con opción para cerrar sesión o cambiar a administrador
    with st.sidebar:
        col1, col2 = st.columns([1, 3])
        if st.session_state['tipo_usuario'] == "Administrador":
            with col1:
                st.image("https://www.w3schools.com/howto/img_avatar.png", width=50)
            with col2:
                if st.button("Cerrar sesión"):
                    cerrar_sesion()
        else:
            with col1:
                st.image("https://www.w3schools.com/howto/img_avatar2.png", width=50)
            with col2:
                if st.button("Cambiar a administrador"):
                    cambiar_a_administrador()

    # Crear el menú de navegación
    with st.sidebar:
        seleccion = option_menu(
            "Menú",
            ["Presentación", "Trabajos realizados", "Testimonios", "Reservación de citas"],
            icons=["house", "trophy", "people", "calendar"],
            menu_icon="cast",
            default_index=0,
        )

    # Mostrar la página seleccionada
    if seleccion == "Reservación de citas":
        mostrar_reservacion_citas()
    elif seleccion == "Trabajos realizados":
        mostrar_trabajos_realizados()
    elif seleccion == "Testimonios":
        mostrar_testimonios()
    else:
        mostrar_presentacion()

# Comprobar si el usuario ha iniciado sesión
if 'logged_in' not in st.session_state:
    if cookies.get("logged_in") == "True":
        st.session_state['logged_in'] = True
        st.session_state['tipo_usuario'] = cookies["tipo_usuario"]
        st.session_state['usuario'] = cookies["usuario"]
    else:
        st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    mostrar_paginas()
else:
    pagina_inicio_sesion()