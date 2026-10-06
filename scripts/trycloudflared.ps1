# =============================================================================
# trycloudflared.ps1
# =============================================================================
# Automatiza a inicialização do servidor de arquivos e a criação de um endereço
# público temporário usando o TryCloudflare (Cloudflare Quick Tunnel).
#
# Fluxo:
#   1. Remove o link antigo.
#   2. Inicia o Flask (app.py).
#   3. Aguarda o Flask iniciar.
#   4. Inicia uma tarefa que, após alguns segundos, verifica o link e chama
#      o script responsável pelo envio do e-mail.
#   5. Inicia o Cloudflare Tunnel.
#   6. Captura a URL *.trycloudflare.com exibida pelo cloudflared.
#   7. Salva a URL em scripts/link.txt.
#
# IMPORTANTE:
# - Este arquivo não deve conter senhas, e-mails ou outros dados secretos.
# - O Python e o cloudflared precisam estar disponíveis no PATH do Windows,
#   ou os caminhos abaixo devem ser ajustados localmente.
# - O arquivo link.txt é gerado automaticamente e não precisa ser versionado.
# =============================================================================


# -----------------------------------------------------------------------------
# CONFIGURAÇÃO
# -----------------------------------------------------------------------------

# Comando usado para executar o Python.
# Se o Python não estiver no PATH, informe aqui o caminho completo para
# python.exe, por exemplo:
#   $python = "C:\Caminho\Para\python.exe"
$python = "python"

# O app.py fica na pasta principal do projeto.
# $PSScriptRoot representa automaticamente a pasta onde este script está.
$raizProjeto = Split-Path -Parent $PSScriptRoot
$app = Join-Path $raizProjeto "app.py"

# Comando do Cloudflare Tunnel.
# Se cloudflared.exe não estiver no PATH, informe o caminho completo.
$cloudflared = "cloudflared"

# Arquivo onde a URL pública temporária será armazenada.
$arquivoLink = Join-Path $PSScriptRoot "link.txt"

# Script Python responsável pelo envio do e-mail.
$scriptEmail = Join-Path $PSScriptRoot "enviar_email.py"


# -----------------------------------------------------------------------------
# VALIDAÇÕES
# -----------------------------------------------------------------------------

# Verifica se o app.py existe antes de iniciar o processo.
if (-not (Test-Path $app)) {
    Write-Error "Não foi encontrado o arquivo app.py em: $app"
    exit 1
}

# Verifica se o script de e-mail existe.
if (-not (Test-Path $scriptEmail)) {
    Write-Error "Não foi encontrado o script enviar_email.py em: $scriptEmail"
    exit 1
}


# -----------------------------------------------------------------------------
# LIMPEZA DO LINK ANTERIOR
# -----------------------------------------------------------------------------

# Remove o link gerado na execução anterior.
# Isso evita que uma URL antiga seja utilizada acidentalmente.
Remove-Item $arquivoLink -ErrorAction SilentlyContinue


# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DO FLASK
# -----------------------------------------------------------------------------

# Inicia o servidor Flask em segundo plano.
Start-Process `
    -FilePath $python `
    -ArgumentList "`"$app`"" `
    -WorkingDirectory $raizProjeto `
    -WindowStyle Hidden


# Aguarda alguns segundos para permitir que o Flask fique disponível
# antes de iniciar o túnel.
Start-Sleep -Seconds 5


# -----------------------------------------------------------------------------
# ENVIO DO LINK POR E-MAIL
# -----------------------------------------------------------------------------

# A tarefa abaixo é executada em segundo plano.
#
# Ela espera 30 segundos antes de verificar o arquivo link.txt.
# Esse tempo permite que o cloudflared tenha oportunidade de gerar a URL.
#
# A lógica original foi mantida: o e-mail só é chamado se o link existir
# e possuir algum conteúdo.
Start-Job -ScriptBlock {

    Start-Sleep -Seconds 30

    # Reutiliza o comando "python" do ambiente.
    $python = "python"

    # Recupera a pasta do script de automação.
    $pastaScripts = $using:PSScriptRoot

    $arquivoLink = Join-Path $pastaScripts "link.txt"
    $scriptEmail = Join-Path $pastaScripts "enviar_email.py"

    # Verifica se o link foi criado pelo processo do Cloudflare.
    if (Test-Path $arquivoLink) {

        $url = (Get-Content $arquivoLink -Raw).Trim()

        # Só executa o envio se uma URL válida tiver sido encontrada.
        if ($url) {

            Start-Process `
                -FilePath $python `
                -ArgumentList "`"$scriptEmail`" `"$url`"" `
                -WindowStyle Hidden
        }
    }

} | Out-Null


# -----------------------------------------------------------------------------
# CLOUDFLARE TUNNEL
# -----------------------------------------------------------------------------

# Inicia o Quick Tunnel apontando para o Flask na porta 5000.
#
# A saída do cloudflared é lida linha por linha para localizar a URL
# temporária no formato:
#
#   https://algum-nome.trycloudflare.com
#
# Quando encontrada, a URL é salva em link.txt.
& $cloudflared tunnel --url http://localhost:5000 2>&1 |
ForEach-Object {

    $linha = $_.ToString()

    # Procura uma URL gerada pelo TryCloudflare.
    if ($linha -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {

        $url = $matches[0]

        # Salva somente a URL no arquivo.
        Set-Content `
            -Path $arquivoLink `
            -Value $url `
            -Encoding UTF8

        Write-Host "URL pública encontrada: $url"
    }
}
