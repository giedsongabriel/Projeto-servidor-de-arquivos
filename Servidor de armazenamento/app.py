from flask import Flask, render_template, send_file, abort, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = "chave-doservidor"

PASTA_ARQUIVOS = r"C:\um teste para o servidor"

def caminho_seguro(caminho):
    caminho_completo = os.path.join(PASTA_ARQUIVOS, caminho)
    caminho_real = os.path.realpath(caminho_completo)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)
    if not caminho_real.startswith(raiz_real):
        abort(403)
    return caminho_real

@app.route("/")
@app.route ("/<path:caminho>")
def explorar(caminho=""):

    pasta_atual = os.path.join(PASTA_ARQUIVOS, caminho)

    # Impede acesso fora da pasta principal
    pasta_real = os.path.realpath(pasta_atual)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)

    if not pasta_real.startswith(raiz_real):
        abort(403)

    if not os.path.isdir(pasta_real):
        abort(404)

    itens = []

    for nome in os.listdir(pasta_real):

        caminho_item = os.path.join(pasta_real, nome)

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

    # Pastas primeiro, depois arquivos
    itens.sort(key=lambda x: (x["tipo"] != "pasta", x["nome"].lower()))

    # Caminho anterior
    caminho_pai = os.path.dirname(caminho)

    return render_template(
        "index.html",
        itens=itens,
        caminho=caminho,
        caminho_pai=caminho_pai,

    item_copiado=session.get("item_copiado")
    )


@app.route("/download/<path:caminho>")
def download(caminho):

    arquivo = os.path.join(PASTA_ARQUIVOS, caminho)

    arquivo_real = os.path.realpath(arquivo)
    raiz_real = os.path.realpath(PASTA_ARQUIVOS)

    # Segurança
    if not arquivo_real.startswith(raiz_real):
        abort(403)

    if not os.path.isfile(arquivo_real):
        abort(404)

    return send_file(
        arquivo_real,
        as_attachment=True
    )
@app.route("/upload", methods=["POST"])
def upload():
    caminho = request.form.get("caminho", "").replace("\\", "/").strip("/")

    pasta_destino = os.path.join(PASTA_ARQUIVOS, caminho)

    if not os.path.isdir(pasta_destino):
        abort(404)

    arquivo = request.files.get("arquivo")

    if arquivo is None or arquivo.filename == "":
        return redirect(url_for("explorar", caminho=caminho))

    nome_arquivo = secure_filename(arquivo.filename)

    if not nome_arquivo:
        abort(400)

    destino = os.path.join(pasta_destino, nome_arquivo)

    arquivo.save(destino)

    return redirect(url_for("explorar", caminho=caminho))

@app.route("/mover", methods=["POST"])
def mover():
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

    # Não permite colocar uma pasta dentro dela mesma
    if tipo == "pasta":
        origem_real = os.path.realpath(origem_real)
        destino_real = os.path.realpath(destino_real)

        if destino_real.startswith(origem_real + os.sep):
            abort(400)

    novo_caminho = os.path.join(
        destino_real,
        os.path.basename(origem_real)
    )

    if os.path.exists(novo_caminho):
        abort(409)

    os.rename(origem_real, novo_caminho)

    return "", 204
@app.route("/criar-pasta", methods=["POST"])
def criar_pasta():
    caminho = request.form.get("caminho", "")
    nome = request.form.get("nome", "").strip()

    if not nome:
        abort(400)

    pasta_atual = caminho_seguro(caminho)

    if not os.path.isdir(pasta_atual):
        abort(404)

    nome_seguro = secure_filename(nome)

    if not nome_seguro:
        abort(400)

    nova_pasta = os.path.join(pasta_atual, nome_seguro)

    if os.path.exists(nova_pasta):
        abort(409)

    os.makedirs(nova_pasta)

    return redirect(url_for("explorar", caminho=caminho))

@app.route("/copiar", methods=["POST"])
def copiar ():
    dados = request.get_json()

    item = dados.get("item","")
    tipo = dados.get("tipo", "")

    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)

    session["item_copiado"] = {
        "caminho": item,
        "tipo": tipo
    }
    return "", 204

@app.route("/colar", methods=["POST"])
def colar():

    import shutil

    # Recupera o item que foi copiado
    item_copiado = session.get("item_copiado")

    if not item_copiado:
        abort(400)

    origem = item_copiado.get("caminho", "")
    tipo = item_copiado.get("tipo", "arquivo")

    # Pasta onde o usuário quer colar
    destino = request.form.get("destino", "")

    origem_real = caminho_seguro(origem)
    destino_real = caminho_seguro(destino)

    # Verifica se a origem ainda existe
    if not os.path.exists(origem_real):
        abort(404)

    # Verifica se o destino é uma pasta
    if not os.path.isdir(destino_real):
        abort(404)

    # Impede copiar uma pasta para dentro dela mesma
    if tipo == "pasta":

        origem_real = os.path.realpath(origem_real)
        destino_real = os.path.realpath(destino_real)

        if destino_real == origem_real:
            abort(400)

        if destino_real.startswith(origem_real + os.sep):
            abort(400)

    # Cria o caminho final usando o mesmo nome da origem
    novo_caminho = os.path.join(
        destino_real,
        os.path.basename(origem_real)
    )

    # Não sobrescreve algo que já existe
    if os.path.exists(novo_caminho):
        abort(409)

    # Copia pasta ou arquivo
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

    # IMPORTANTE:
    # NÃO removemos item_copiado da sessão.
    # Assim o usuário pode colar novamente quantas vezes quiser.

    return redirect(
        url_for(
            "explorar",
            caminho=destino
        )
    )

@app.route("/renomear", methods=["POST"])
def renomear ():
    dados = request.get_json()

    item = dados.get("item" , "")
    novo_nome = dados.get ("nome", "").strip()

    if not novo_nome:
        abort(400)
    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)
    pasta = os.path.dirname(item_real)

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

@app.route("/excluir", methods=["POST"])
def excluir_item ():
    import shutil

    dados = request.get_json()

    item = dados.get("item","")
    tipo = dados.get("tipo", "arquivo")

    item_real = caminho_seguro(item)

    if not os.path.exists(item_real):
        abort(404)
    if tipo == "pasta":
        shutil.rmtree(item_real)
    else: 
        os.remove(item_real)
    return "", 204

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )