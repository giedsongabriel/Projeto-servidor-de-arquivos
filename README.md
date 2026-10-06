# Servidor de Arquivos

Servidor de arquivos feito em **Python + Flask** como projeto pessoal e de estudo.

A ideia é transformar um computador em um servidor onde seja possível acessar e organizar arquivos pelo navegador. Além do acesso local, o projeto possui uma automação que cria um endereço público usando o **Cloudflare Tunnel** e envia esse endereço por e-mail.

## Sobre o projeto

Esse projeto foi feito principalmente para estudar e colocar em prática algumas tecnologias que eu estava aprendendo.

Com ele, é possível:

* visualizar arquivos e pastas;
* enviar arquivos;
* baixar arquivos;
* criar pastas;
* renomear arquivos e pastas;
* excluir arquivos e pastas;
* copiar e colar;
* mover arquivos;
* pesquisar arquivos.

A aplicação roda localmente usando Flask e pode ser acessada pelo navegador.

## Tecnologias

* Python
* Flask
* HTML
* CSS
* JavaScript
* PowerShell
* Cloudflare Tunnel
* Gmail SMTP
* NSSM

## Estrutura

```text
servidor-de-arquivos/
│
├── app.py
│
├── templates/
│   └── index.html
│
├── static/
│   └── style.css
│
├── scripts/
│   ├── trycloudflared.ps1
│   ├── enviar_email.py
│   └── link.txt
│
├── arquivos/
│
├── .env
└── .gitignore
```

## Como funciona

A aplicação principal está no `app.py`.

Ele inicia o servidor Flask na porta `5000`:

```text
http://localhost:5000
```

A interface é feita com HTML, CSS e JavaScript e funciona como um pequeno explorador de arquivos.

### Acesso externo

Para acessar o servidor de fora da rede, o projeto utiliza o `cloudflared`.

O script:

```text
scripts/trycloudflared.ps1
```

inicia o Flask e depois executa:

```text
cloudflared tunnel --url http://localhost:5000
```

O Cloudflare gera um endereço temporário parecido com:

```text
https://exemplo.trycloudflare.com
```

O script identifica esse endereço e salva em:

```text
scripts/link.txt
```

### Envio do link por e-mail

Depois que o endereço é encontrado, o `trycloudflared.ps1` chama:

```text
scripts/enviar_email.py
```

O endereço é passado para o script:

```text
python enviar_email.py "https://exemplo.trycloudflare.com"
```

O `enviar_email.py` utiliza o SMTP do Gmail para enviar o endereço para o e-mail configurado.

O fluxo fica basicamente assim:

```text
Windows
   ↓
trycloudflared.ps1
   ↓
app.py
   ↓
Cloudflare Tunnel
   ↓
link.txt
   ↓
enviar_email.py
   ↓
E-mail com o link
```

## Configuração do e-mail

As informações do Gmail ficam em um arquivo `.env`.

Exemplo:

```env
GMAIL_USUARIO=seu_email@gmail.com
GMAIL_SENHA_APP=sua_senha_de_app
EMAIL_DESTINO=destinatario@example.com
```

## Executando

Primeiro, instale as dependências:

```bash
pip install flask python-dotenv
```

Depois execute:

```bash
python app.py
```

Acesse:

```text
http://localhost:5000
```

## Usando o Cloudflare

Para iniciar também o acesso externo:

```powershell
.\scripts\trycloudflared.ps1
```

É necessário ter o `cloudflared` instalado e disponível no sistema.

O script fica responsável por iniciar o servidor, criar o túnel, encontrar a URL e iniciar o envio do e-mail.

## Inicialização automática

No Windows, utilizei o **NSSM** para transformar o `trycloudflared.ps1` em um serviço.

Assim, o processo pode ser iniciado automaticamente junto com o computador:

```text
Windows inicia
      ↓
NSSM
      ↓
trycloudflared.ps1
      ↓
Servidor + Cloudflare + e-mail
```

Essa parte é opcional. Também é possível executar o projeto manualmente.

## Observações

O projeto foi feito para **estudo e uso pessoal**. Não foi pensado inicialmente como uma solução pronta para produção.

Principalmente ao utilizar o Cloudflare Tunnel, é importante ter cuidado com os arquivos que ficam disponíveis, já que o endereço gerado permite acesso ao servidor.

