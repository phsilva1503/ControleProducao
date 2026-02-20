from flask import render_template, request, redirect, flash, url_for
from models import *
from datetime import date, datetime
from sqlalchemy import func, case,distinct
from flask import jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

##from models import Componente, Estoque, Movimentacao, Producao, ComponenteProducao


def routes(app):

    # -----------------------
    # Helper: obter ou criar registro de estoque (não faz commit)
    # -----------------------
    def get_or_create_estoque(componente_id):
        estoque = Estoque.query.filter_by(componente_id=componente_id).first()
        if not estoque:
            estoque = Estoque(componente_id=componente_id, quantidade=0)
            db.session.add(estoque)
            db.session.flush()
        return estoque

    # -----------------------
    # Inicializa componentes pré-cadastrados (uma única vez)
    # -----------------------
    def inicializar_componentes():
        componentes_iniciais = ["COMPONENTE"]
        for nome in componentes_iniciais:
            if not Componente.query.filter_by(nome=nome).first():
                novo = Componente(nome=nome, ativo=True)
                db.session.add(novo)
                db.session.flush()
                db.session.add(Estoque(componente_id=novo.id, quantidade=0))
        db.session.commit()

    with app.app_context():
        inicializar_componentes()

    # -----------------------
    # Função auxiliar: recalcular saldos
    # -----------------------
    def atualizar_saldos():
        saldos_query = (
            db.session.query(
                Movimentacao.componente_id,
                func.sum(
                    case(
                        (Movimentacao.tipo == 'entrada', Movimentacao.quantidade),
                        (Movimentacao.tipo == 'saida', -Movimentacao.quantidade),
                        else_=0
                    )
                ).label('saldo')
            )
            .group_by(Movimentacao.componente_id)
            .all()
        )

        for componente_id, saldo in saldos_query:
            estoque = Estoque.query.filter_by(componente_id=componente_id).first()
            if estoque:
                estoque.quantidade = saldo
            else:
                db.session.add(Estoque(componente_id=componente_id, quantidade=saldo))

        db.session.commit()

    # -----------------------
    # Rota inicial
    # -----------------------
    @app.route('/')
    @login_required
    def index():
        return render_template('index-main.html')

    # -----------------------
    # Cadastro de Componentes
    # -----------------------
    @app.route('/cadastro', methods=['GET', 'POST'], endpoint='cadastro_componente')
    def cadastro_componente():
        todos_componentes = Componente.query.all()
        estoques = Estoque.query.all()
        saldos = {e.componente_id: e.quantidade for e in estoques}

        if request.method == 'POST':
            nome = request.form.get('nome')
            if not nome:
                flash("Informe o nome do componente!", "danger")
                return redirect(url_for('cadastro_componente'))

            if Componente.query.filter_by(nome=nome).first():
                flash(f"Componente '{nome}' já existe!", "warning")
                return redirect(url_for('cadastro_componente'))

            novo = Componente(nome=nome, ativo=True)
            db.session.add(novo)
            db.session.flush()
            db.session.add(Estoque(componente_id=novo.id, quantidade=0))
            db.session.commit()

            flash(f"Componente '{nome}' cadastrado com sucesso!", "success")
            return redirect(url_for('cadastro_componente'))

        return render_template('CadastroComponente.html',
                               todos_componentes=todos_componentes,
                               saldos=saldos)

    # -----------------------
    # Ajuste de Estoque
    # -----------------------
    @app.route("/estoque/ajustar/componente/<int:componente_id>", methods=["GET", "POST"])
    def ajustar_estoque(componente_id):
        componente = Componente.query.get_or_404(componente_id)
        estoque = Estoque.query.filter_by(componente_id=componente.id).first()

        if request.method == "POST":
            try:
                quantidade = float(request.form.get("quantidade", 0))
                tipo = request.form.get("tipo")

                if quantidade <= 0 or tipo not in ["entrada", "saida"]:
                    flash("Informe uma quantidade válida e um tipo de ajuste!", "danger")
                    return redirect(url_for("ajustar_estoque", componente_id=componente.id))

                if not estoque:
                    estoque = Estoque(componente_id=componente.id, quantidade=0)
                    db.session.add(estoque)
                    db.session.flush()

                if tipo == "entrada":
                    estoque.quantidade += quantidade
                else:
                    if estoque.quantidade < quantidade:
                        flash("Saldo insuficiente para saída!", "danger")
                        return redirect(url_for("ajustar_estoque", componente_id=componente.id))
                    estoque.quantidade -= quantidade

                mov = Movimentacao(
                    componente_id=componente.id,
                    quantidade=quantidade,
                    tipo=tipo,
                    data=date.today()
                )
                db.session.add(mov)
                db.session.commit()

                flash(f"{quantidade} unidades {'adicionadas' if tipo=='entrada' else 'retiradas'} do estoque de '{componente.nome}'", "success")
                return redirect(url_for("cadastro_componente"))
            except ValueError:
                flash("Quantidade inválida!", "danger")
                return redirect(url_for("ajustar_estoque", componente_id=componente.id))

        return render_template("AjusteEstoque.html", componente=componente, estoque=estoque)

    # -----------------------
    # Visualizar Movimentações
    # -----------------------
    @app.route("/movimentacoes/<int:componente_id>")
    def movimentacoes(componente_id):
        componente = Componente.query.get_or_404(componente_id)
        movimentacoes = Movimentacao.query.filter_by(componente_id=componente.id).order_by(Movimentacao.id.desc()).all()
        return render_template("movimentacoes.html", componente=componente, movimentacoes=movimentacoes)

    # -----------------------
    # Toggle Ativo/Inativo
    # -----------------------
    @app.route('/toggle_componente/<int:componente_id>')
    def toggle_componente(componente_id):
        componente = Componente.query.get_or_404(componente_id)
        componente.ativo = not componente.ativo
        db.session.commit()
        flash(f"Componente '{componente.nome}' agora está {'ativo' if componente.ativo else 'inativo'}.", "info")
        return redirect(url_for('cadastro_componente'))

    # -----------------------
    # Visualizar Estoque
    # -----------------------
    @app.route("/estoque")
    def ver_estoque():
        atualizar_saldos()
        componentes = Componente.query.all()
        estoques = Estoque.query.all()
        saldos = {e.componente_id: e.quantidade for e in estoques}
        return render_template("Estoque.html", componentes=componentes, saldos=saldos)

# -----------------------
# Controle de Produção
# -----------------------

    # -----------------------
    # Controle de Produção
    # -----------------------
    @app.route('/controle-producao')
    @login_required
    def controle_producao():
        ##producoes = Producao.query.all()
        producoes = Producao.query.order_by(Producao.id.desc()).all()
        componentes = Componente.query.filter_by(ativo=True).all()
        fichas = FichaTecnica.query.all()
        hoje = date.today().strftime('%Y-%m-%d')
        todos_componentes = Componente.query.all()
        tipos_espuma = TipoEspuma.query.all()

        # 👇 CRIE A VARIÁVEL SALDOS AQUI:
        estoques = Estoque.query.all()
        saldos = {e.componente_id: e.quantidade for e in estoques}

        return render_template('controle_producao.html',
                               producoes=producoes,
                               componentes=componentes,
                               hoje=hoje,
                               todos_componentes=todos_componentes,
                               saldos=saldos,
                               fichas=fichas,
                               tipos_espuma=tipos_espuma
                        
        )
    
# -----------------------
# Cadastro de Produção
    @app.route("/cadastro_producao", methods=["GET"], endpoint="mostrar_cadastro_producao")
    def mostrar_cadastro_producao():
        producoes = Producao.query.all()
        todos_componentes = Componente.query.all()
        componentes = Componente.query.filter_by(ativo=True).all()
        hoje = date.today().strftime("%Y-%m-%d")
        fichas = FichaTecnica.query.all()
        
        tipos_espuma = (
        TipoEspuma.query
        .join(FichaTecnica, FichaTecnica.tipo_espuma_id == TipoEspuma.id)
        .distinct()
        .all()
                        )

        
        #  CRIE A VARIÁVEL SALDOS AQUI:
        estoques = Estoque.query.all()
        saldos = {e.componente_id: e.quantidade for e in estoques}

        return redirect(url_for(
            "controle_producao",
            producoes=producoes,
            componentes=componentes,
            todos_componentes=todos_componentes,
            hoje=hoje,
            saldos=saldos,
            fichas=fichas,
            tipos_espuma=tipos_espuma
        ))

    # Rota POST: processa o formulário
    @app.route("/cadastro_producao", methods=["POST"], endpoint="cadastro_producao")
    def cadastro_producao():
        try:
            producao_id = request.form['producao_id']
            data_producao = request.form.get('data_producao') or date.today().strftime('%Y-%m-%d')
            tipo_espuma_id = int(request.form['tipo_espuma'])
            cor = request.form['cor']
            altura = float(request.form.get('altura', 0))
            conformidade = request.form['conformidade']
            observacoes = request.form.get('observacoes', '')
            ficha = FichaTecnica.query.filter_by(tipo_espuma_id=tipo_espuma_id).first()
            if not ficha:
                flash("Nenhuma ficha técnica encontrada para este tipo de espuma!", "danger")
                return redirect(url_for("mostrar_cadastro_producao"))



            data_producao = datetime.strptime(data_producao, "%Y-%m-%d").date()

            # Evita duplicidade de número de bloco
            if Producao.query.filter_by(producao_id=producao_id).first():
                flash(f"Número de bloco '{producao_id}' já cadastrado!", "danger")
                return redirect(url_for("mostrar_cadastro_producao"))


            # Cria o registro da produção
            nova_producao = Producao(
                producao_id=producao_id,
                data_producao=data_producao,
                tipo_espuma=ficha.tipo_espuma.nome,
                cor=cor,
                altura=altura,
                conformidade=conformidade,
                observacoes=observacoes,
                usuario_id=current_user.id
            )
            db.session.add(nova_producao)
            db.session.flush()  # Pega o ID antes do commit

            # 🔹 Pega apenas os componentes da ficha técnica selecionada
            # pega apenas componentes da ficha técnica
            componentes_ficha = [fc.componente for fc in ficha.componentes]

            for componente in componentes_ficha:
                campo_nome = f"componente_{componente.id}"
                quantidade = float(request.form.get(campo_nome, 0))

                if quantidade > 0:
                    estoque = Estoque.query.filter_by(componente_id=componente.id).first()
                    if not estoque or estoque.quantidade < quantidade:
                        db.session.rollback()
                        flash(f"Saldo insuficiente do componente '{componente.nome}'", "danger")
                        return redirect(url_for("mostrar_cadastro_producao"))

                    # Registra o uso do componente
                    cp = ComponenteProducao(
                        producao_id=nova_producao.id,
                        componente_id=componente.id,
                        quantidade_usada=quantidade
                    )
                    db.session.add(cp)

                    # Atualiza o estoque e cria a movimentação
                    estoque.quantidade -= quantidade
                    db.session.add(Movimentacao(
                        componente_id=componente.id,
                        data=datetime.now(),
                        tipo='saida',
                        quantidade=quantidade,
                        producao_id=nova_producao.id
                    ))

            db.session.commit()
            flash("Produção cadastrada com sucesso!", "success")
            return redirect(url_for("mostrar_cadastro_producao"))

        except (KeyError, ValueError) as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar produção: {str(e)}", "danger")
            return redirect(url_for("mostrar_cadastro_producao"))
        


    @app.route("/componentes_por_tipo/<int:tipo_id>")
    def componentes_por_tipo(tipo_id):
        # encontra a ficha técnica relacionada ao tipo de espuma selecionado
        ficha = FichaTecnica.query.filter_by(tipo_espuma_id=tipo_id).first()

        # assumimos que sempre existe ficha (você disse que só seleciona itens válidos)
        componentes = [
                {
                "id": fc.componente.id,
                "nome": fc.componente.nome
            }
            for fc in ficha.componentes
        ]

        return jsonify(componentes)

    # -----------------------
    # Visualizar Componentes de uma Produção
    # -----------------------
    @app.route('/ComponentesProducao/<int:producao_id>')
    def ver_componentes_producao(producao_id):
        producao = Producao.query.get_or_404(producao_id)
        componentes = ComponenteProducao.query.filter_by(producao_id=producao_id).all()

        ficha = (
            FichaTecnica.query
            .join(TipoEspuma)
            .filter(TipoEspuma.nome == producao.tipo_espuma)
            .first()
        )

        tipo_espuma_nome = ficha.tipo_espuma.nome if ficha else "N/A"
        tipo_espuma_id   = ficha.tipo_espuma.id if ficha else "N/A"

        return render_template(
            'ComponentesProducao.html',
            producao=producao,
            componentes=componentes,
            tipo_espuma=tipo_espuma_nome,
            tipo_espuma_id=tipo_espuma_id
        )

    
    # -----------------------
    # Fichas Técnicas
    # -----------------------
    
  
    @app.route('/ficha-tecnica', methods=['GET'], endpoint='mostrar_ficha_tecnica')
    def mostrar_ficha_tecnica():
        fichas = FichaTecnica.query.all()
        componentes = Componente.query.filter_by(ativo=True).all()
        tipo_espuma = TipoEspuma.query.all()  # 🔹 Busca os tipos de espuma do banco
        return redirect(url_for(
            'controle_producao',
            componentes=componentes,
            fichas=fichas,
            tipos_espuma=tipo_espuma
        ))

    # POST → processa o cadastro e volta para a mesma página
    @app.route('/ficha-tecnica', methods=['GET', 'POST'], endpoint='cadastrar_ficha_tecnica')
    def cadastrar_ficha_tecnica():
        componentes = Componente.query.filter_by(ativo=True).all()
        tipos_espuma = TipoEspuma.query.all()

        # ---------------------
        #       POST
        # ---------------------
        if request.method == 'POST':
            tipo_espuma_id = request.form.get('tipo_espuma_id')
            descricao = request.form.get('descricao', '')

            if not tipo_espuma_id:
                flash("Informe o tipo de espuma!", "danger")
                return redirect(url_for('cadastrar_ficha_tecnica'))

            tipo_espuma_id_int = int(tipo_espuma_id)

            if FichaTecnica.query.filter_by(tipo_espuma_id=tipo_espuma_id_int).first():
                flash("Já existe uma ficha técnica para este tipo de espuma!", "warning")
                return redirect(url_for('cadastrar_ficha_tecnica'))

            ficha = FichaTecnica(tipo_espuma_id=tipo_espuma_id_int, descricao=descricao)
            db.session.add(ficha)
            db.session.flush()

            # ✅ Aqui pegamos todos os componentes selecionados
            componentes_selecionados = request.form.getlist('componentes_ids')
            for componente_id in componentes_selecionados:
                db.session.add(
                    FichaTecnicaComponente(
                        ficha_tecnica_id=ficha.id,
                        componente_id=int(componente_id)
                    )
                )

            db.session.commit()
            flash(f"Ficha técnica '{TipoEspuma.query.get(tipo_espuma_id_int).nome}' criada com sucesso!", "success")
            return redirect(url_for('mostrar_ficha_tecnica'))

        # ---------------------
        #       GET
        # ---------------------
        return render_template(
            "ficha_tecnica/cadastrar.html",
            componentes=componentes,
            tipos_espuma=tipos_espuma
        )

        

    @app.route('/ficha-tecnica/editar/<int:ficha_id>', methods=['GET', 'POST'], endpoint='editar_ficha_tecnica')
    def editar_ficha_tecnica(ficha_id):
            ficha = FichaTecnica.query.get_or_404(ficha_id)
            componentes = Componente.query.filter_by(ativo=True).all()
            tipos_espuma = TipoEspuma.query.all()

            if request.method == 'POST':
                # Valores enviados pelo formulário
                tipo_espuma_id = request.form.get('tipo_espuma_id')
                descricao = request.form.get('descricao', '')

                try:
                    tipo_espuma_id_int = int(tipo_espuma_id)
                except ValueError:
                    flash("Valor inválido para tipo de espuma!", "danger")
                    return redirect(url_for('editar_ficha_tecnica', ficha_id=ficha.id))

                # Atualiza campos principais
                ficha.tipo_espuma_id = int(tipo_espuma_id)
                ficha.descricao = descricao

                # Remove relações antigas e recria conforme seleção do formulário
                FichaTecnicaComponente.query.filter_by(ficha_tecnica_id=ficha.id).delete()
                for componente in componentes:
                    if request.form.get(f'componente_{componente.id}'):
                        rel = FichaTecnicaComponente(
                            ficha_tecnica_id=ficha.id,
                            componente_id=componente.id
                        )
                        db.session.add(rel)

                db.session.commit()
                tipo_nome = TipoEspuma.query.get(ficha.tipo_espuma_id).nome if ficha.tipo_espuma_id else ''
                flash(f"Ficha técnica '{tipo_nome}' atualizada com sucesso!", "success")
                return redirect(url_for('mostrar_ficha_tecnica'))

            # GET -> prepara dados para o formulário (ids dos componentes já vinculados)
            ficha_componentes_ids = [c.componente_id for c in ficha.componentes]

            return render_template(
                'editarFichaTecnica.html',
                ficha=ficha,
                componentes=componentes,
                tipos_espuma=tipos_espuma,
                componentes_marcados=ficha_componentes_ids
            )

    @app.route('/tipo-espuma', methods=['GET', 'POST'], endpoint='cadastrar_tipo_espuma')
    def cadastrar_tipo_espuma():
            if request.method == 'POST':
                nome = request.form.get('nome', '').strip()
                if not nome:
                    flash("Informe o nome da espuma!", "danger")
                    ##return redirect(url_for('cadastrar_tipo_espuma'))
                    return render_template('CadastroTipoEspuma.html', espumas=TipoEspuma.query.order_by(TipoEspuma.nome).all()) 
                    

                if TipoEspuma.query.filter_by(nome=nome).first():
                    flash("Este tipo de espuma já está cadastrado!", "warning")
                   ##return redirect(url_for('cadastrar_tipo_espuma'))
                    return render_template('CadastroTipoEspuma.html', espumas=TipoEspuma.query.order_by(TipoEspuma.nome).all())

                nova = TipoEspuma(nome=nome)
                db.session.add(nova)
                db.session.commit()
                flash(f"Tipo de espuma '{nome}' cadastrado com sucesso!", "success")
                ##return redirect(url_for('cadastrar_tipo_espuma'))
                return render_template('CadastroTipoEspuma.html', espumas=TipoEspuma.query.order_by(TipoEspuma.nome).all())

            espumas = TipoEspuma.query.order_by(TipoEspuma.nome).all()
            return render_template('CadastroTipoEspuma.html', espumas=espumas)
    
    # -----------------------
    # Rota AJAX: AQUI GERA UM JSON COM OS COMPOENTES DA FIICHA E MANDA PARA O FRONT 
    @app.route('/get_componentes_ficha/<int:tipo_espuma_id>')
    def get_componentes_ficha(tipo_espuma_id):
        ficha = FichaTecnica.query.filter_by(tipo_espuma_id=tipo_espuma_id).first()
        if not ficha:
            return {"componentes": []}
        
        componentes_ids = [rel.componente_id for rel in ficha.componentes]
        componentes = Componente.query.filter(Componente.id.in_(componentes_ids)).all()

        return {
            "componentes": [
                {"id": c.id, "nome": c.nome}
                for c in componentes
            ]
        }
    
    @app.route('/tipo-espuma/<int:id>/editar', methods=['POST'], endpoint='editar_tipo_espuma')
    def editar_tipo_espuma(id):
        nova_nome = request.form.get('novo_nome', '').strip()

        if not nova_nome:
            flash("Informe o novo nome da espuma!", "danger")
            espumas = TipoEspuma.query.order_by(TipoEspuma.nome).all()
            return render_template('CadastroTipoEspuma.html', espumas=espumas)

        # Verifica duplicidade
        if TipoEspuma.query.filter(TipoEspuma.nome == nova_nome, TipoEspuma.id != id).first():
            flash("Já existe um tipo de espuma com esse nome!", "warning")
            espumas = TipoEspuma.query.order_by(TipoEspuma.nome).all()
            return render_template('CadastroTipoEspuma.html', espumas=espumas)

        espuma = TipoEspuma.query.get_or_404(id)
        espuma.nome = nova_nome
        db.session.commit()
        flash(f"Tipo de espuma atualizado para '{nova_nome}' com sucesso!", "success")

        espumas = TipoEspuma.query.order_by(TipoEspuma.nome).all()
        return render_template('CadastroTipoEspuma.html', espumas=espumas)
    

    #--------------------
    #rota de login
    #------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            senha = request.form.get('senha')

            usuario = Usuario.query.filter_by(email=email, ativo=True).first()

            if usuario and usuario.check_senha(senha):
                login_user(usuario)
                return redirect(url_for('index'))
            else:
                flash("Usuário ou senha inválidos", "danger")
                return render_template("login.html")

        return render_template("login.html")

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash("Logout realizado com sucesso!", "info")
        return redirect(url_for('login'))

    # -----------------------
    # Cadastro de Usuário
    # -----------------------
    @app.route('/cadastro_usuario', methods=['GET', 'POST'], endpoint='cadastro_usuario')
    def cadastro_usuario():

        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip().lower()
            senha = request.form.get('senha', '').strip()
            confirmar_senha = request.form.get('confirmar_senha', '').strip()

            # 1. Campos obrigatórios
            if not nome or not email or not senha or not confirmar_senha:
                flash("Preencha todos os campos!", "danger")
                return render_template(
                    'cadastroUsuario.html',
                    nome=nome,
                    email=email
                )

            # 2. Domínio do e-mail
            if not email.endswith('@bonsono.com.br'):
                flash("Cadastro permitido apenas para e-mails @bonsono.com.br", "danger")
                return render_template(
                    'cadastroUsuario.html',
                    nome=nome,
                    email=email
                )

            # 3. Senhas
            if senha != confirmar_senha:
                flash("As senhas não conferem!", "danger")
                return render_template(
                    'cadastroUsuario.html',
                    nome=nome,
                    email=email
                )

            # 4. E-mail já existente
            if Usuario.query.filter_by(email=email).first():
                flash("Este e-mail já está cadastrado!", "warning")
                return render_template(
                    'cadastroUsuario.html',
                    nome=nome,
                    email=email
                )

            # 5. Criação do usuário
            novo_usuario = Usuario(nome=nome, email=email)
            novo_usuario.set_senha(senha)

            db.session.add(novo_usuario)
            db.session.commit()

            flash("Usuário cadastrado com sucesso!", "success")
            return render_template('login.html')

        # GET
        return render_template('cadastroUsuario.html')
    
    #----------------------------
    #QUERY DE USUARIOS CADASTRADOS
    #----------------------------
    @app.route('/usuarios')
    @login_required
    def listar_usuarios():
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        return render_template('Usuarios.html', usuarios=usuarios)

    @app.route('/usuarios/status/<int:id>', methods=['POST'])
    @login_required
    def alterar_status_usuario(id):
        usuario = Usuario.query.get_or_404(id)
        usuario.ativo = not usuario.ativo  # alterna entre True e False
        db.session.commit()
        flash(f"Status do usuário {usuario.nome} alterado com sucesso!", "success")
        return redirect(url_for('listar_usuarios'))
    
    @app.route('/usuario/<int:id>/senha', methods=['POST'])
    @login_required
    def alterar_senha_usuario(id):
        usuario = Usuario.query.get_or_404(id)
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')

        if nova_senha != confirma_senha:
            flash('As senhas não conferem!', 'danger')
            return redirect(url_for('listar_usuarios'))

        usuario.set_senha(nova_senha)
        db.session.commit()
        flash(f'Senha de {usuario.nome} alterada com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))





    # -----------------------
    # Páginas estáticas
    # -----------------------
    @app.route('/laudo-tecnico')
    def laudo_tecnico():
        return render_template('laudo-tecnico.html')

    @app.route('/lean-six-sigma')
    def lean_six_sigma():
        return render_template('lean.html')

    @app.route('/analise_preditiva')
    def analise_preditiva():
        return render_template('analise_preditiva.html')

    @app.route('/dashboard')
    def dashboard():
         # Pega todas as produções, do mais recente para o mais antigo
        producoes = Producao.query.order_by(Producao.id.desc()).all()
    
    # Também pode pegar componentes ativos, se quiser mostrar info extra
        componentes = Componente.query.filter_by(ativo=True).all()
    
    # Passa os dados para o template
        return render_template(
        'dashboard.html',
        producoes=producoes,
        componentes=componentes
        )
        return render_template('dashboard.html')

    @app.route('/relatorios')
    def relatorios():
        return render_template('relatorios.html')
    



