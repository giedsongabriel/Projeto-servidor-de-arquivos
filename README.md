**📁 Servidor de Arquivos**

Servidor de arquivos desenvolvido em Python + Flask, com interface web para gerenciamento de arquivos e pastas através do navegador.

O projeto foi desenvolvido para facilitar o armazenamento, organização e compartilhamento de arquivos em uma rede, utilizando uma interface semelhante a um explorador de arquivos.

 **Funcionalidades:**

Atualmente, o sistema permite:

-  Navegar entre pastas e subpastas
-  Fazer upload de arquivos
-  Baixar arquivos
-  Criar novas pastas
-  Renomear arquivos e pastas
-  Excluir arquivos e pastas
-  Copiar e colar arquivos
-  Copiar e colar pastas
-  Arrastar arquivos para mover
-  Arrastar pastas através da alça de movimentação
-  Impedir sobrescrita de arquivos durante operações de cópia
-  Impedir que uma pasta seja copiada ou movida para dentro dela mesma
-  Menu de ações para arquivos e pastas

**Tecnologias**

- Python
- Flask
- HTML5
- CSS3
- JavaScript

⚙️ Configuração

O sistema utiliza uma pasta do computador como armazenamento dos arquivos.

No arquivo "app.py", a pasta pode ser definida através da variável:

PASTA_ARQUIVOS = r"C:\um teste para o servidor"

Altere esse caminho para a pasta que deseja disponibilizar através do servidor.

**Como executar**
1. Instale o Python

Certifique-se de que o Python esteja instalado no computador.

2. Instale o Flask

No terminal:

pip install flask

3. Execute o servidor

Dentro da pasta do projeto:

python app.py

O servidor poderá ser acessado pelo navegador através do endereço exibido pelo Flask, normalmente:

http://127.0.0.1:5000

**Objetivo**

O objetivo do projeto é desenvolver uma solução de gerenciamento e compartilhamento de arquivos através de uma interface web, permitindo que usuários possam acessar e administrar arquivos sem precisar utilizar diretamente o sistema de arquivos do computador servidor.

---


Em desenvolvimento 🚧

Novas funcionalidades serão adicionadas conforme o desenvolvimento do projeto.
