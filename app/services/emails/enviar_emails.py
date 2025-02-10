import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.utils.functions import graba_log

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Cc, Bcc, Content

from app.config.db_mallorquina import get_db_connection_mysql, close_connection_mysql
from app.services.auxiliares.sendgrid_service import enviar_email

from app.utils.functions import graba_log, imprime
from app.utils.InfoTransaccion import InfoTransaccion
from app.config.settings import settings
from app.utils.mis_excepciones import MadreException


MAX_OFFSET: int = 400
SALTO: int = 0


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
def proceso(param: InfoTransaccion, servidor: int):
    param.debug="proceso.Inicio"
    enviados = 0
    robinson = 0
    errores = 0
    offset = 0

    param.debug = "get_db_connection_mysql"
    try:
        conn_mysql = get_db_connection_mysql()
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        datos_conexion = obtener_datos_conexion(param, conn_mysql, servidor)
        imprime([datos_conexion], "*")
        if not datos_conexion:
            raise MadreException(param, f"No tenemos datos de conexión del servidor {servidor}", -1)

        while True:
            """ Procesa el envío de todos los emails pendientes """
            emails = obtener_emails_pendientes(param, conn_mysql, servidor, offset)
            if not emails or len(emails) == 0 or offset > MAX_OFFSET:
                break

            offset += SALTO
            for email in emails:
                exito = enviar_email(param, conn_mysql, email, datos_conexion)  #  email["destinatario"], email["asunto"], email["cuerpo"]
                if exito == 0:
                    marcar_email(param, cursor_mysql, email["id"], 'Ok')
                    enviados += 1
                elif exito == 1:
                    marcar_email(param, cursor_mysql, email["id"], 'Robinson')
                    robinson += 1
                else:
                    marcar_email(param, cursor_mysql, email["id"], 'Ko')
                    errores += 1

                conn_mysql.commit()

        return [f'Se hna enviado {enviados} emails, {robinson} no se han enviado por lista Robinson y {errores} han tenido algún tipo de error']

    except Exception as e:
        param.error_sistema()
        graba_log(param, "proceso.Exception", e)
        raise 

    finally:
        close_connection_mysql(conn_mysql, cursor_mysql)


#----------------------------------------------------------------------------------------
# 'P'endiente de enviar;  
# 'E'rror de envío;  
# 'R'eintentar;  
# 'O'K;
# 'L'ista Robinson
#----------------------------------------------------------------------------------------
def marcar_email(param: InfoTransaccion, cursor_mysql, email_id, estado):
    try:
        # 'P'endiente de enviar;  'E'rror de envío;  'R'eintentar;  'O'K; 'L'ista Robinson
        if estado == 'Ok':
            enviado = 'O'   
        elif estado == 'Ko':
            enviado = 'E'
        elif estado == 'Robinson':
            enviado = 'L'   # esto es dejarlo como está o intentar volver a enviar

        query = "UPDATE emails SET enviado = %s WHERE id = %s"
        cursor_mysql.execute(query, (enviado, email_id,))

        

    except Exception as e:
        param.error_sistema()
        graba_log(param, "marcar_email.Exception", e)
        raise 


#----------------------------------------------------------------------------------------
#      Envía un email utilizando SendGrid y los datos del servidor de correo
#----------------------------------------------------------------------------------------
def robinson(param: InfoTransaccion, conn_mysql, lista_emails):

    try:
        if not lista_emails:
            return False
        
        cursor_mysql = conn_mysql.cursor(dictionary=True)

        # Si la lista es pequeña, usar WHERE IN
        if len(lista_emails) <= 500:
            placeholders = ', '.join(['%s'] * len(lista_emails))
            query = f"SELECT email FROM mail_robinson WHERE email IN ({placeholders})"
            cursor_mysql.execute(query, lista_emails)
            emails_en_robinson = {row[0] for row in cursor_mysql.fetchall()}  # Convertimos a set para búsqueda rápida
        else:
            emails_en_robinson = set()
            for email in lista_emails:
                cursor_mysql.execute("SELECT email FROM mail_robinson WHERE email = %s", (email,))
                resultado = cursor_mysql.fetchone()
                if resultado:
                    emails_en_robinson.add(resultado[0])

        # Filtrar la lista original
        emails_filtrados = [email for email in lista_emails if email not in emails_en_robinson]
        
        return emails_filtrados or []

    except Exception as e:
        param.error_sistema()
        graba_log(param, "robinson.Exception", e)
        raise 

    finally:
        cursor_mysql.close()



#----------------------------------------------------------------------------------------
#      Envía un email utilizando SendGrid y los datos del servidor de correo
#----------------------------------------------------------------------------------------
def enviar_email(param: InfoTransaccion, conn_mysql, email, datos_conexion):
    destinatario = email["para"]
    asunto = email["asunto"]
    cuerpo = email["cuerpo"]
    
    try:
        # Inicializar el cliente SendGrid con la API Key desde datos_conexion
        sg = sendgrid.SendGridAPIClient(api_key=datos_conexion["password"])

        # Configurar el remitente
        from_email = Email(datos_conexion["de"], datos_conexion["de_nombre"])

        # Configurar destinatarios principales (TO)
        lista = robinson(param, conn_mysql, email["para"])
        to_emails = [To(dest) for dest in lista] if isinstance(lista, list) else [To(lista)]

        # Configurar CC (Con Copia)
        lista = robinson(param, conn_mysql, email.get("cc", []))
        cc_emails = [Cc(dest) for dest in lista] if len(lista)>0 else []

        # Configurar BCC (Con Copia Oculta)
        lista = robinson(param, conn_mysql, email.get("bcc", []))
        bcc_emails = [Cc(dest) for dest in lista] if len(lista)>0 else []

        # Configurar contenido del email
        subject = email["asunto"]
        content = Content("text/html", email["cuerpo"])

        # Construcción del email
        mail = Mail(from_email, to_emails, subject, content)

        # Agregar CC y BCC si existen
        if cc_emails:
            mail.personalizations[0].add_cc(cc_emails)
        if bcc_emails:
            mail.personalizations[0].add_bcc(bcc_emails)

        # Configurar el "Reply-To"
        if "reply_to" in datos_conexion:
            mail.reply_to = Email(datos_conexion["reply_to"])

        # Enviar el email
        response = sg.client.mail.send.post(request_body=mail.get())


        if response.status_code in [200, 202]:
            return 0
        else:
            return -1
    
    except Exception as e:
        param.error_sistema()
        graba_log(param, "enviar_email.Exception", e)
        raise 

    

#----------------------------------------------------------------------------------------
#         Obtiene los emails pendientes de la base de datos
#----------------------------------------------------------------------------------------
def obtener_emails_pendientes(param: InfoTransaccion, conn_mysql, servidor, offset):
    try:
        cursor_mysql = conn_mysql.cursor(dictionary=True)
        
        query = "SELECT * FROM mail_envios WHERE servidor = %s AND estado in ('P', 'R') order by prioridad limit 100 OFFSET %s"
        cursor_mysql.execute(query, (servidor, offset,))
        emails = cursor_mysql.fetchall()
        
        return emails

    except Exception as e:
        param.error_sistema()
        graba_log(param, "obtener_emails_pendientes.Exception", e)
        raise 

    finally:
        cursor_mysql.close()


#----------------------------------------------------------------------------------------
#         Obtiene los datos de CONEXION con el proveedor de servcio de EMAIL
#----------------------------------------------------------------------------------------
def obtener_datos_conexion(param: InfoTransaccion, conn_mysql, servidor):
    try:
        cursor_mysql = conn_mysql.cursor(dictionary=True)
        
        query = "SELECT * FROM mail_servidores WHERE id = %s order by orden_servidor"
        cursor_mysql.execute(query, (servidor,))
        datos = cursor_mysql.fetchone()
        
        return datos

    except Exception as e:
        param.error_sistema()
        graba_log(param, "obtener_datos_conexion.Exception", e)
        raise 

    finally:
        cursor_mysql.close()        
        