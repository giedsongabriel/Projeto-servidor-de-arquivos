import os
import sys
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega o arquivo .env
load_dotenv()

# Dados do Gmail
GMAIL_USUARIO = os.getenv("GMAIL_USUARIO")
GMAIL_SENHA_APP = os.getenv("GMAIL_SENHA_APP")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")


# Verifica as configurações
if not GMAIL_USUARIO:
    print("ERRO: GMAIL_USUARIO não foi configurado no .env")
    sys.exit(1)

if not GMAIL_SENHA_APP:
    print("ERRO: GMAIL_SENHA_APP não foi configurado no .env")
    sys.exit(1)

if not EMAIL_DESTINO:
    print("ERRO: EMAIL_DESTINO não foi configurado no .env")
    sys.exit(1)


# Recebe o link como argumento
if len(sys.argv) < 2:
    print("ERRO: nenhum link foi informado.")
    print('Uso: python enviar_email.py "https://seu-link.trycloudflare.com"')
    sys.exit(1)

link = sys.argv[1]


# Cria o conteúdo do e-mail
mensagem = MIMEText(
    f"""O servidor de arquivos foi iniciado.

Link para acessar:

{link}

Este e-mail foi enviado automaticamente pelo servidor.
""",
    "plain",
    "utf-8"
)

mensagem["Subject"] = "Servidor de arquivos iniciado"
mensagem["From"] = GMAIL_USUARIO
mensagem["To"] = EMAIL_DESTINO


print("----------------------------------------")
print("Iniciando envio de e-mail...")
print("----------------------------------------")
print("Usuário:", GMAIL_USUARIO)
print("Destino:", EMAIL_DESTINO)
print("Tamanho da senha de app:", len(GMAIL_SENHA_APP))
print("Link:", link)
print("----------------------------------------")


try:
    print("1. Conectando ao servidor SMTP do Gmail...")

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=30
    ) as servidor:

        servidor.set_debuglevel(1)

        print("2. Conexão SMTP estabelecida.")

        print("3. Enviando EHLO...")
        servidor.ehlo()
        print("4. EHLO OK.")

        print("5. Iniciando TLS...")
        servidor.starttls()
        print("6. TLS OK.")

        print("7. Enviando segundo EHLO...")
        servidor.ehlo()
        print("8. Segundo EHLO OK.")

        print("9. Tentando fazer login no Gmail...")
        servidor.login(
            GMAIL_USUARIO,
            GMAIL_SENHA_APP
        )

        print("10. LOGIN OK!")

        print("11. Enviando e-mail...")
        servidor.send_message(mensagem)

        print("12. E-mail enviado com sucesso!")


except smtplib.SMTPAuthenticationError as erro:
    print("----------------------------------------")
    print("ERRO DE AUTENTICAÇÃO DO GMAIL")
    print("----------------------------------------")
    print("O Gmail recusou o usuário ou a senha de app.")
    print("Verifique se GMAIL_SENHA_APP é uma senha de app válida.")
    print()
    print("Detalhes:", erro)
    sys.exit(1)


except smtplib.SMTPServerDisconnected as erro:
    print("----------------------------------------")
    print("ERRO: O Gmail encerrou a conexão.")
    print("----------------------------------------")
    print("Isso aconteceu durante a comunicação SMTP.")
    print()
    print("Detalhes:", erro)
    sys.exit(1)


except smtplib.SMTPException as erro:
    print("----------------------------------------")
    print("ERRO SMTP")
    print("----------------------------------------")
    print("Detalhes:", erro)
    sys.exit(1)


except Exception as erro:
    print("----------------------------------------")
    print("ERRO INESPERADO")
    print("----------------------------------------")
    print("Tipo:", type(erro).__name__)
    print("Detalhes:", erro)
    sys.exit(1)