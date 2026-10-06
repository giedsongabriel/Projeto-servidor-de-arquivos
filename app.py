from flask import Flask, render_template, send_file, abort, request, redirect, url_for, session
import os
import shutil

from werkzeug.utils import secure_filename


# ---------------------------------------------------------------------------
# Configuração básica da aplicação
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Chave usada pelo Flask para proteger os dados armazenados na sessão.

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)

# Pasta que funciona como a raiz do HD compartilhado.
#
# O caminho pode ser alterado conforme a máquina onde o projeto será executado.
# Também é possível definir a variável de ambiente SHARED_FOLDER.
PASTA_ARQUIVOS = os.environ.get(
    "SHARED_FOLDER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquivos")
)


# ---------------------------------------------------------------------------
# Segurança de caminhos
# ---------------------------------------------------------------------------

def caminho_seguro(caminho):
    """
    Converte um caminho relativo do HD compartilhado em um caminho real.

    A função verifica se o caminho final continua dentro da pasta principal.
    Isso evita que uma requisição tente acessar arquivos fora do diretório
    compartilhado usando caminhos como "../".
    """
    caminho_completo = os.path.join(PASTA_ARQUIVOS, caminho)
    caminho_real = os.path.realpath(caminho_completo)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)

    if not caminho_real.startswith(raiz_real):
        abort(403)

    return caminho_real


# ---------------------------------------------------------------------------
# Navegação pelo HD compartilhado
# ---------------------------------------------------------------------------

@app.route("/")
@app.route("/<path:caminho>")
def explorar(caminho=""):
    """Exibe o conteúdo de uma pasta do HD compartilhado."""

    pasta_atual = os.path.join(PASTA_ARQUIVOS, caminho)

    # Resolve o caminho antes de acessar o sistema de arquivos para impedir
    # que o usuário navegue para fora da pasta compartilhada.
    pasta_real = os.path.realpath(pasta_atual)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)

    if not pasta_real.startswith(raiz_real):
        abort(403)

    if not os.path.isdir(pasta_real):
        abort(404)

    itens = []

    # Percorre os arquivos e pastas existentes no diretório atual.
    for nome in os.listdir(pasta_real):
        caminho_item = os.path.join(pasta_real, nome)

        if os.path.isdir(caminho_item):
            tipo = "pasta"
        else:
            tipo = "arquivo"

        tamanho = 0

        # O tamanho é informado apenas para arquivos.
        if os.path.isfile(caminho_item):
            tamanho = os.path.getsize(caminho_item)

        itens.append({
            "nome": nome,
            "tipo": tipo,
            "tamanho": tamanho
        })

    # Mostra as pastas primeiro e os arquivos depois.
    itens.sort(key=lambda x: (x["tipo"] != "pasta", x["nome"].lower()))

    # Obtém o caminho da pasta anterior para permitir a navegação de volta.
    caminho_pai = os.path.dirname(caminho)

    return render_template(
        "index.html",
        itens=itens,
        caminho=caminho,
        caminho_pai=caminho_pai,
        item_copiado=session.get("item_copiado")
    )


# ---------------------------------------------------------------------------
# Download de arquivos
# ---------------------------------------------------------------------------

@app.route("/download/<path:caminho>")
def download(caminho):
    """Envia um arquivo do HD compartilhado para o navegador."""

    arquivo = os.path.join(PASTA_ARQUIVOS, caminho)

    arquivo_real = os.path.realpath(arquivo)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)

    # Impede que o download acesse arquivos fora da pasta compartilhada.
    if not arquivo_real.startswith(raiz_real):
        abort(403)

    if not os.path.isfile(arquivo_real):
        abort(404)

    return send_file(
        arquivo_real,
        as_attachment=True
    )


# ---------------------------------------------------------------------------
# Upload de arquivos
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    """Recebe um arquivo enviado pelo navegador e salva na pasta atual."""

    caminho = request.form.get(
        "caminho",
        ""
    ).replace("\\", "/").strip("/")

    pasta_destino = os.path.join(PASTA_ARQUIVOS, caminho)

    if not os.path.isdir(pasta_destino):
        abort(404)

    arquivo = request.files.get("arquivo")

    # Se nenhum arquivo foi selecionado, retorna para a pasta atual.
    if arquivo is None or arquivo.filename == "":
        return redirect(url_for("explorar", caminho=caminho))

    # Remove caracteres potencialmente perigosos do nome enviado.
    nome_arquivo = secure_filename(arquivo.filename)

    if not nome_arquivo:
        abort(400)

    destino = os.path.join(pasta_destino, nome_arquivo)

    arquivo.save(destino)

    return redirect(url_for("explorar", caminho=caminho))


# ---------------------------------------------------------------------------
# Mover arquivos e pastas
# ---------------------------------------------------------------------------

@app.route("/mover", methods=["POST"])
def mover():
    """Move um arquivo ou uma pasta para outro diretório."""

    dados = request.get_json()

    item = dados.get("item", "")
    destino = dados.get("destino", "")
    tipo = dados.get("tipo", "arquivo")

    origem_real = caminho_seguro(item)
    destino_real = caminho_seguro(destino)

    if not os.path.exists(origem_real):
        abort(404)

    if not os.path.isdir(destino_real):
        abort(404)

    # Uma pasta não pode ser movida para dentro dela mesma.
    if tipo == "pasta":
        origem_real = os.path.realpath(origem_real)
        destino_real = os.path.realpath(destino_real)

        if destino_real.startswith(origem_real + os.sep):
            abort(400)

    novo_caminho = os.path.join(
        destino_real,
        os.path.basename(origem_real)
    )

    # Evita substituir um arquivo ou pasta que já exista no destino.
    if os.path.exists(novo_caminho):
        abort(409)

    os.rename(origem_real, novo_caminho)

    return "", 204


# ---------------------------------------------------------------------------
# Criação de pastas
# ---------------------------------------------------------------------------

@app.route("/criar-pasta", methods=["POST"])
def criar_pasta():
    """Cria uma nova pasta dentro do diretório atualmente aberto."""

    caminho = request.form.get("caminho", "")
    nome = request.form.get("nome", "").strip()

    if not nome:
        abort(400)

    pasta_atual = caminho_seguro(caminho)

    if not os.path.isdir(pasta_atual):
        abort(404)

    # Garante que o nome da pasta seja seguro para o sistema de arquivos.
    nome_seguro = secure_filename(nome)

    if not nome_seguro:
        abort(400)

    nova_pasta = os.path.join(pasta_atual, nome_seguro)

    if os.path.exists(nova_pasta):
        abort(409)

    os.makedirs(nova_pasta)

    return redirect(url_for("explorar", caminho=caminho))


# ---------------------------------------------------------------------------
# Copiar e colar
# ---------------------------------------------------------------------------

@app.route("/copiar", methods=["POST"])
def copiar():
    """Armazena na sessão o arquivo ou pasta selecionado para cópia."""

    dados = request.get_json()

    item = dados.get("item", "")
    tipo = dados.get("tipo", "")

    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)

    # Apenas o caminho e o tipo são armazenados na sessão.
    # O conteúdo do arquivo continua no disco.
    session["item_copiado"] = {
        "caminho": item,
        "tipo": tipo
    }

    return "", 204


@app.route("/colar", methods=["POST"])
def colar():
    """Copia o item selecionado anteriormente para uma nova pasta."""

    # O shutil é usado para copiar arquivos e diretórios.
    item_copiado = session.get("item_copiado")

    if not item_copiado:
        abort(400)

    origem = item_copiado.get("caminho", "")
    tipo = item_copiado.get("tipo", "arquivo")

    # Pasta onde o usuário deseja colar o item.
    destino = request.form.get("destino", "")

    origem_real = caminho_seguro(origem)
    destino_real = caminho_seguro(destino)

    if not os.path.exists(origem_real):
        abort(404)

    if not os.path.isdir(destino_real):
        abort(404)

    # Impede copiar uma pasta para dentro dela mesma ou para um de seus
    # próprios subdiretórios.
    if tipo == "pasta":
        origem_real = os.path.realpath(origem_real)
        destino_real = os.path.realpath(destino_real)

        if destino_real == origem_real:
            abort(400)

        if destino_real.startswith(origem_real + os.sep):
            abort(400)

    # O item mantém o mesmo nome no destino.
    novo_caminho = os.path.join(
        destino_real,
        os.path.basename(origem_real)
    )

    # Não sobrescreve itens existentes.
    if os.path.exists(novo_caminho):
        abort(409)

    if tipo == "pasta":
        shutil.copytree(
            origem_real,
            novo_caminho
        )
    else:
        shutil.copy2(
            origem_real,
            novo_caminho
        )

    # O item permanece armazenado na sessão para que possa ser colado
    # novamente em outro diretório.
    return redirect(
        url_for(
            "explorar",
            caminho=destino
        )
    )


# ---------------------------------------------------------------------------
# Renomear arquivos e pastas
# ---------------------------------------------------------------------------

@app.route("/renomear", methods=["POST"])
def renomear():
    """Altera o nome de um arquivo ou pasta."""

    dados = request.get_json()

    item = dados.get("item", "")
    novo_nome = dados.get("nome", "").strip()

    if not novo_nome:
        abort(400)

    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)

    pasta = os.path.dirname(item_real)

    # Sanitiza o novo nome antes de utilizá-lo no sistema de arquivos.
    novo_nome_seguro = secure_filename(novo_nome)

    if not novo_nome_seguro:
        abort(400)

    novo_caminho = os.path.join(pasta, novo_nome_seguro)

    if os.path.exists(novo_caminho):
        abort(409)

    os.rename(
        item_real,
        novo_caminho
    )

    return "", 204


# ---------------------------------------------------------------------------
# Exclusão de arquivos e pastas
# ---------------------------------------------------------------------------

@app.route("/excluir", methods=["POST"])
def excluir_item():
    """Exclui um arquivo ou uma pasta do HD compartilhado."""

    dados = request.get_json()

    item = dados.get("item", "")
    tipo = dados.get("tipo", "arquivo")

    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)

    if tipo == "pasta":
        # Remove a pasta e todo o seu conteúdo.
        shutil.rmtree(item_real)
    else:
        os.remove(item_real)

    return "", 204


# ---------------------------------------------------------------------------
# Pesquisa
# ---------------------------------------------------------------------------

@app.route("/pesquisar")
def pesquisar():
    """Pesquisa arquivos e pastas pelo nome dentro do diretório atual."""

    termo = request.args.get("q", "").strip()
    caminho = request.args.get("caminho", "").strip("/")

    pasta_atual = caminho_seguro(caminho)

    if not os.path.isdir(pasta_atual):
        abort(404)

    itens = []

    for nome in os.listdir(pasta_atual):

        # A pesquisa não diferencia letras maiúsculas e minúsculas.
        if termo.lower() not in nome.lower():
            continue

        caminho_item = os.path.join(
            pasta_atual,
            nome
        )

        if os.path.isdir(caminho_item):
            tipo = "pasta"
        else:
            tipo = "arquivo"

        tamanho = 0

        if os.path.isfile(caminho_item):
            tamanho = os.path.getsize(caminho_item)

        itens.append({
            "nome": nome,
            "tipo": tipo,
            "tamanho": tamanho
        })

    # Mantém o mesmo padrão da navegação: pastas primeiro.
    itens.sort(
        key=lambda x: (
            x["tipo"] != "pasta",
            x["nome"].lower()
        )
    )

    caminho_pai = os.path.dirname(caminho)

    return render_template(
        "index.html",
        itens=itens,
        caminho=caminho,
        caminho_pai=caminho_pai,
        item_copiado=session.get("item_copiado"),
        termo_pesquisa=termo
    )


# ---------------------------------------------------------------------------
# Inicialização da aplicação
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 0.0.0.0 permite que o servidor seja acessado por outros dispositivos
    # da rede local e também facilita o encaminhamento pelo Cloudflare Tunnel.
    #
    # Em produção, recomenda-se utilizar um servidor WSGI apropriado em vez
    # do servidor de desenvolvimento do Flask.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
