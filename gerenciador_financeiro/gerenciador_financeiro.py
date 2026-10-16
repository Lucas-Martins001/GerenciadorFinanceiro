
# IMPORTAÇÕES, BANCO DE DADOS E CONFIGURAÇÕES

import sqlite3
from datetime import datetime, date
import customtkinter as ctk
from tkinter import messagebox

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ------------------------- CONFIGURAÇÕES -------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NOME_APP = "Finansee"
BANCO = "finansee.db"

FUNDO = "#0B1120"
PAINEL = "#111A2E"
CARTAO = "#172238"
BORDA = "#25334D"
AZUL = "#5687FF"
VERDE = "#27D6A0"
VERMELHO = "#FF647C"
TEXTO = "#F1F5F9"
TEXTO_SECUNDARIO = "#91A0B8"
ROXO = "#A78BFA"
LARANJA = "#FFB86B"


# ------------------------- BANCO DE DADOS -------------------------

def conectar_banco():
    return sqlite3.connect(BANCO)


def inicializar_banco():
    with conectar_banco() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)


# ------------------------- FUNÇÕES AUXILIARES -------------------------

def formatar_moeda(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def obter_transacoes():
    with conectar_banco() as conn:
        return conn.execute("""
            SELECT id, descricao, valor, tipo, categoria, data
            FROM transacoes
            ORDER BY data DESC, id DESC
        """).fetchall()


def obter_resumo():
    with conectar_banco() as conn:
        receitas = conn.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM transacoes
            WHERE tipo = 'Receita'
        """).fetchone()[0]

        despesas = conn.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM transacoes
            WHERE tipo = 'Despesa'
        """).fetchone()[0]

    return receitas, despesas, receitas - despesas


def criar_botao(pai, texto, comando, cor=AZUL, largura=140):
    return ctk.CTkButton(
        pai,
        text=texto,
        command=comando,
        width=largura,
        height=40,
        corner_radius=10,
        fg_color=cor,
        hover_color=cor,
        text_color="#FFFFFF",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
    )


# ------------------------- APLICAÇÃO PRINCIPAL -------------------------

class GerenciadorFinanceiro(ctk.CTk):

    def __init__(self):
        super().__init__()

        inicializar_banco()

        self.title("Finansee | Gerenciador Financeiro")
        self.geometry("1250x790")
        self.minsize(1000, 650)
        self.configure(fg_color=FUNDO)

        self.transacoes_cache = []
        self.filtro_tipo = "Todos"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.criar_menu_lateral()
        self.criar_area_principal()
        self.atualizar_tudo()

# MENU LATERAL, CABEÇALHO, CARTÕES E FORMULÁRIO


    def criar_menu_lateral(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=225,
            corner_radius=0,
            fg_color=PAINEL
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="◈  FINANSEE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=AZUL
        ).pack(pady=(30, 5), padx=20, anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text="CONTROLE FINANCEIRO",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXTO_SECUNDARIO
        ).pack(padx=23, anchor="w", pady=(0, 35))

        self.btn_dashboard = ctk.CTkButton(
            self.sidebar,
            text="▦   Visão geral",
            anchor="w",
            height=45,
            corner_radius=10,
            fg_color="#243657",
            hover_color="#243657",
            command=self.ir_dashboard
        )
        self.btn_dashboard.pack(fill="x", padx=14, pady=5)

        self.btn_nova = ctk.CTkButton(
            self.sidebar,
            text="＋   Nova transação",
            anchor="w",
            height=45,
            corner_radius=10,
            fg_color="transparent",
            hover_color=CARTAO,
            command=self.abrir_formulario
        )
        self.btn_nova.pack(fill="x", padx=14, pady=5)

        self.btn_historico = ctk.CTkButton(
            self.sidebar,
            text="◷   Histórico",
            anchor="w",
            height=45,
            corner_radius=10,
            fg_color="transparent",
            hover_color=CARTAO,
            command=self.ir_historico
        )
        self.btn_historico.pack(fill="x", padx=14, pady=5)

        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=BORDA
        ).pack(fill="x", padx=20, pady=25)

        ctk.CTkLabel(
            self.sidebar,
            text="RESUMO",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXTO_SECUNDARIO
        ).pack(padx=23, anchor="w", pady=(0, 10))

        self.sidebar_saldo = ctk.CTkLabel(
            self.sidebar,
            text="R$ 0,00",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=VERDE
        )
        self.sidebar_saldo.pack(padx=20, anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text="Saldo acumulado",
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=12)
        ).pack(padx=20, anchor="w", pady=(3, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="v1.0  •  Finanças pessoais",
            text_color="#64748B",
            font=ctk.CTkFont(size=10)
        ).pack(side="bottom", pady=20)

    def criar_area_principal(self):
        self.main = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=FUNDO
        )
        self.main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        self.header.grid(
            row=0, column=0, sticky="ew",
            padx=30, pady=(25, 18)
        )
        self.header.grid_columnconfigure(0, weight=1)

        self.titulo = ctk.CTkLabel(
            self.header,
            text="Visão geral",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXTO
        )
        self.titulo.grid(row=0, column=0, sticky="w")

        self.subtitulo = ctk.CTkLabel(
            self.header,
            text="Acompanhe sua vida financeira em um só lugar.",
            font=ctk.CTkFont(size=13),
            text_color=TEXTO_SECUNDARIO
        )
        self.subtitulo.grid(row=1, column=0, sticky="w", pady=(5, 0))

        criar_botao(
            self.header,
            "＋  Nova transação",
            self.abrir_formulario,
            cor=AZUL,
            largura=180
        ).grid(row=0, column=1, rowspan=2, padx=(15, 0))

        self.cards_frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        self.cards_frame.grid(
            row=1, column=0, sticky="ew",
            padx=30, pady=(0, 20)
        )

        for coluna in range(3):
            self.cards_frame.grid_columnconfigure(coluna, weight=1)

        self.card_saldo = self.criar_cartao(
            self.cards_frame, "SALDO TOTAL", "R$ 0,00", AZUL, 0
        )
        self.card_receitas = self.criar_cartao(
            self.cards_frame, "RECEITAS", "R$ 0,00", VERDE, 1
        )
        self.card_despesas = self.criar_cartao(
            self.cards_frame, "DESPESAS", "R$ 0,00", VERMELHO, 2
        )

        self.conteudo = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        self.conteudo.grid(
            row=2, column=0, sticky="nsew",
            padx=30, pady=(0, 25)
        )
        self.conteudo.grid_columnconfigure(0, weight=3)
        self.conteudo.grid_columnconfigure(1, weight=2)
        self.conteudo.grid_rowconfigure(0, weight=1)

        self.criar_painel_historico()
        self.criar_painel_grafico()

    def criar_cartao(self, pai, titulo, valor, cor, coluna):
        cartao = ctk.CTkFrame(
            pai,
            fg_color=CARTAO,
            corner_radius=16,
            border_width=1,
            border_color=BORDA
        )
        cartao.grid(
            row=0, column=coluna,
            sticky="ew", padx=(0 if coluna == 0 else 8, 8),
            pady=0
        )

        ctk.CTkLabel(
            cartao,
            text=titulo,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=20, pady=(20, 8))

        indicador = ctk.CTkFrame(
            cartao,
            width=38,
            height=4,
            fg_color=cor,
            corner_radius=5
        )
        indicador.pack(anchor="w", padx=20, pady=(0, 10))

        label_valor = ctk.CTkLabel(
            cartao,
            text=valor,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXTO
        )
        label_valor.pack(anchor="w", padx=20, pady=(0, 22))

        return label_valor

    def criar_painel_historico(self):
        self.painel_lista = ctk.CTkFrame(
            self.conteudo,
            fg_color=PAINEL,
            corner_radius=16,
            border_width=1,
            border_color=BORDA
        )
        self.painel_lista.grid(
            row=0, column=0, sticky="nsew",
            padx=(0, 10)
        )
        self.painel_lista.grid_columnconfigure(0, weight=1)
        self.painel_lista.grid_rowconfigure(2, weight=1)

        topo = ctk.CTkFrame(
            self.painel_lista,
            fg_color="transparent"
        )
        topo.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 10))
        topo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo,
            text="Transações recentes",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXTO
        ).grid(row=0, column=0, sticky="w")

        self.filtro = ctk.CTkOptionMenu(
            topo,
            values=["Todos", "Receita", "Despesa"],
            width=115,
            height=32,
            fg_color=CARTAO,
            button_color=AZUL,
            command=self.aplicar_filtro
        )
        self.filtro.grid(row=0, column=1, sticky="e")

        cabecalho = ctk.CTkFrame(
            self.painel_lista,
            fg_color=CARTAO,
            corner_radius=8
        )
        cabecalho.grid(
            row=1, column=0, sticky="ew",
            padx=15, pady=(0, 8)
        )
        cabecalho.grid_columnconfigure(0, weight=3)
        cabecalho.grid_columnconfigure(1, weight=2)
        cabecalho.grid_columnconfigure(2, weight=2)

        for coluna, texto in enumerate(["DESCRIÇÃO", "DATA", "VALOR"]):
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=TEXTO_SECUNDARIO
            ).grid(
                row=0, column=coluna,
                sticky="w", padx=10, pady=10
            )

        self.lista = ctk.CTkScrollableFrame(
            self.painel_lista,
            fg_color="transparent",
            scrollbar_button_color=BORDA
        )
        self.lista.grid(
            row=2, column=0, sticky="nsew",
            padx=12, pady=(0, 12)
        )

    def criar_painel_grafico(self):
        self.painel_grafico = ctk.CTkFrame(
            self.conteudo,
            fg_color=PAINEL,
            corner_radius=16,
            border_width=1,
            border_color=BORDA
        )
        self.painel_grafico.grid(
            row=0, column=1, sticky="nsew",
            padx=(10, 0)
        )
        self.painel_grafico.grid_columnconfigure(0, weight=1)
        self.painel_grafico.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.painel_grafico,
            text="Receitas x despesas",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXTO
        ).grid(row=0, column=0, sticky="w", padx=20, pady=20)

        self.grafico_frame = ctk.CTkFrame(
            self.painel_grafico,
            fg_color="transparent"
        )
        self.grafico_frame.grid(
            row=1, column=0, sticky="nsew",
            padx=10, pady=(0, 10)
        )
# CADASTRO, VALIDAÇÃO, EDIÇÃO E EXCLUSÃO DE TRANSAÇÕES


    def abrir_formulario(self, transacao=None):
        janela = ctk.CTkToplevel(self)
        janela.title(
            "Editar transação" if transacao else "Nova transação"
        )
        janela.geometry("440x570")
        janela.resizable(False, False)
        janela.configure(fg_color=FUNDO)
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text="Editar transação" if transacao else "Nova transação",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXTO
        ).pack(anchor="w", padx=28, pady=(25, 5))

        ctk.CTkLabel(
            janela,
            text="Preencha os dados da movimentação financeira.",
            font=ctk.CTkFont(size=12),
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=28, pady=(0, 22))

        formulario = ctk.CTkFrame(
            janela,
            fg_color="transparent"
        )
        formulario.pack(fill="both", expand=True, padx=28)

        ctk.CTkLabel(
            formulario,
            text="Descrição",
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 6))

        campo_descricao = ctk.CTkEntry(
            formulario,
            placeholder_text="Ex.: Salário, aluguel, mercado...",
            height=42,
            corner_radius=10
        )
        campo_descricao.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            formulario,
            text="Valor (R$)",
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 6))

        campo_valor = ctk.CTkEntry(
            formulario,
            placeholder_text="0,00",
            height=42,
            corner_radius=10
        )
        campo_valor.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            formulario,
            text="Tipo de movimentação",
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 6))

        campo_tipo = ctk.CTkOptionMenu(
            formulario,
            values=["Receita", "Despesa"],
            height=40,
            corner_radius=10,
            fg_color=CARTAO,
            button_color=AZUL,
            command=lambda _: atualizar_categorias()
        )
        campo_tipo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            formulario,
            text="Categoria",
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 6))

        campo_categoria = ctk.CTkOptionMenu(
            formulario,
            values=["Salário"],
            height=40,
            corner_radius=10,
            fg_color=CARTAO,
            button_color=AZUL
        )
        campo_categoria.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            formulario,
            text="Data (DD/MM/AAAA)",
            text_color=TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 6))

        campo_data = ctk.CTkEntry(
            formulario,
            height=40,
            corner_radius=10
        )
        campo_data.pack(fill="x", pady=(0, 20))
        campo_data.insert(0, date.today().strftime("%d/%m/%Y"))

        categorias_receita = [
            "Salário", "Freelance", "Investimentos",
            "Vendas", "Presente", "Outros"
        ]

        categorias_despesa = [
            "Moradia", "Alimentação", "Transporte",
            "Saúde", "Educação", "Lazer",
            "Contas", "Compras", "Assinaturas", "Outros"
        ]

        def atualizar_categorias():
            tipo = campo_tipo.get()
            categorias = (
                categorias_receita
                if tipo == "Receita"
                else categorias_despesa
            )
            categoria_atual = campo_categoria.get()

            campo_categoria.configure(values=categorias)

            if categoria_atual not in categorias:
                campo_categoria.set(categorias[0])

        def converter_valor(texto):
            texto = texto.strip().replace("R$", "").replace(" ", "")

            if not texto:
                raise ValueError("Informe o valor da transação.")

            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")

            valor = float(texto)

            if valor <= 0:
                raise ValueError("O valor precisa ser maior que zero.")

            return valor

        if transacao:
            trans_id, descricao, valor, tipo, categoria, data_iso = transacao

            campo_descricao.insert(0, descricao)
            campo_valor.insert(0, f"{valor:.2f}".replace(".", ","))
            campo_tipo.set(tipo)
            atualizar_categorias()
            campo_categoria.set(categoria)

            data_obj = datetime.strptime(data_iso, "%Y-%m-%d")
            campo_data.delete(0, "end")
            campo_data.insert(0, data_obj.strftime("%d/%m/%Y"))

        else:
            trans_id = None
            campo_tipo.set("Receita")
            atualizar_categorias()

        def salvar():
            descricao = campo_descricao.get().strip()
            tipo = campo_tipo.get()
            categoria = campo_categoria.get()
            data_texto = campo_data.get().strip()

            if not descricao:
                messagebox.showwarning(
                    "Campo obrigatório",
                    "Informe a descrição da transação.",
                    parent=janela
                )
                return

            try:
                valor = converter_valor(campo_valor.get())
                data_iso = datetime.strptime(
                    data_texto, "%d/%m/%Y"
                ).strftime("%Y-%m-%d")

            except ValueError as erro:
                messagebox.showerror(
                    "Dados inválidos",
                    str(erro) if str(erro) else "Confira o valor e a data.",
                    parent=janela
                )
                return

            try:
                with conectar_banco() as conn:
                    if trans_id is None:
                        conn.execute("""
                            INSERT INTO transacoes
                            (descricao, valor, tipo, categoria, data)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            descricao, valor, tipo, categoria, data_iso
                        ))
                    else:
                        conn.execute("""
                            UPDATE transacoes
                            SET descricao = ?, valor = ?, tipo = ?,
                                categoria = ?, data = ?
                            WHERE id = ?
                        """, (
                            descricao, valor, tipo, categoria,
                            data_iso, trans_id
                        ))

                janela.destroy()
                self.atualizar_tudo()

            except sqlite3.Error as erro:
                messagebox.showerror(
                    "Erro no banco de dados",
                    f"Não foi possível salvar a transação.\n{erro}",
                    parent=janela
                )

        criar_botao(
            janela,
            "Salvar transação",
            salvar,
            cor=AZUL,
            largura=200
        ).pack(pady=(0, 25))

    def editar_transacao(self, trans_id):
        with conectar_banco() as conn:
            transacao = conn.execute("""
                SELECT id, descricao, valor, tipo, categoria, data
                FROM transacoes
                WHERE id = ?
            """, (trans_id,)).fetchone()

        if transacao:
            self.abrir_formulario(transacao)

    def excluir_transacao(self, trans_id):
        confirmar = messagebox.askyesno(
            "Excluir transação",
            "Tem certeza de que deseja excluir esta transação?\n"
            "Essa ação não poderá ser desfeita."
        )

        if not confirmar:
            return

        try:
            with conectar_banco() as conn:
                conn.execute(
                    "DELETE FROM transacoes WHERE id = ?",
                    (trans_id,)
                )

            self.atualizar_tudo()

        except sqlite3.Error as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível excluir a transação.\n{erro}"
            )

    def aplicar_filtro(self, escolha):
        self.filtro_tipo = escolha
        self.atualizar_lista()

    def ir_dashboard(self):
        self.titulo.configure(text="Visão geral")
        self.subtitulo.configure(
            text="Acompanhe sua vida financeira em um só lugar."
        )
        self.filtro.set("Todos")
        self.filtro_tipo = "Todos"
        self.atualizar_tudo()

    def ir_historico(self):
        self.titulo.configure(text="Histórico financeiro")
        self.subtitulo.configure(
            text="Consulte, edite e organize suas movimentações."
        )
        self.atualizar_tudo()


# ATUALIZAÇÃO DA INTERFACE, GRÁFICO E EXECUÇÃO DO PROGRAMA


    def atualizar_tudo(self):
        self.atualizar_resumo()
        self.atualizar_lista()
        self.atualizar_grafico()

    def atualizar_resumo(self):
        receitas, despesas, saldo = obter_resumo()

        self.card_saldo.configure(
            text=formatar_moeda(saldo),
            text_color=VERDE if saldo >= 0 else VERMELHO
        )

        self.card_receitas.configure(
            text=formatar_moeda(receitas),
            text_color=VERDE
        )

        self.card_despesas.configure(
            text=formatar_moeda(despesas),
            text_color=VERMELHO
        )

        self.sidebar_saldo.configure(
            text=formatar_moeda(saldo),
            text_color=VERDE if saldo >= 0 else VERMELHO
        )

    def atualizar_lista(self):
        for widget in self.lista.winfo_children():
            widget.destroy()

        transacoes = obter_transacoes()

        if self.filtro_tipo != "Todos":
            transacoes = [
                t for t in transacoes
                if t[3] == self.filtro_tipo
            ]

        self.transacoes_cache = transacoes

        if not transacoes:
            ctk.CTkLabel(
                self.lista,
                text="Nenhuma transação encontrada.\n"
                     "Clique em '+ Nova transação' para começar.",
                font=ctk.CTkFont(size=13),
                text_color=TEXTO_SECUNDARIO,
                justify="center"
            ).pack(pady=50)
            return

        for transacao in transacoes:
            trans_id, descricao, valor, tipo, categoria, data_iso = transacao

            linha = ctk.CTkFrame(
                self.lista,
                fg_color=CARTAO,
                corner_radius=10
            )
            linha.pack(fill="x", pady=4, padx=2)

            linha.grid_columnconfigure(0, weight=3)
            linha.grid_columnconfigure(1, weight=2)
            linha.grid_columnconfigure(2, weight=2)

            info = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )
            info.grid(
                row=0, column=0,
                sticky="ew", padx=10, pady=10
            )

            cor_tipo = VERDE if tipo == "Receita" else VERMELHO
            sinal = "+" if tipo == "Receita" else "-"

            ctk.CTkLabel(
                info,
                text=descricao,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXTO,
                anchor="w",
                wraplength=160
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=categoria,
                font=ctk.CTkFont(size=10),
                text_color=TEXTO_SECUNDARIO,
                anchor="w"
            ).pack(anchor="w", pady=(3, 0))

            data_formatada = datetime.strptime(
                data_iso, "%Y-%m-%d"
            ).strftime("%d/%m/%Y")

            ctk.CTkLabel(
                linha,
                text=data_formatada,
                font=ctk.CTkFont(size=11),
                text_color=TEXTO_SECUNDARIO
            ).grid(
                row=0, column=1,
                sticky="w", padx=5
            )

            ctk.CTkLabel(
                linha,
                text=f"{sinal} {formatar_moeda(valor)}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=cor_tipo
            ).grid(
                row=0, column=2,
                sticky="w", padx=5
            )

            acoes = ctk.CTkFrame(
                self.lista,
                fg_color="transparent"
            )
            acoes.pack(fill="x", padx=5, pady=(0, 5))

            ctk.CTkButton(
                acoes,
                text="✎ Editar",
                width=75,
                height=25,
                corner_radius=7,
                fg_color="#243657",
                hover_color="#30466B",
                font=ctk.CTkFont(size=10),
                command=lambda tid=trans_id: self.editar_transacao(tid)
            ).pack(side="right", padx=(4, 0))

            ctk.CTkButton(
                acoes,
                text="✕ Excluir",
                width=75,
                height=25,
                corner_radius=7,
                fg_color="#492633",
                hover_color="#703243",
                font=ctk.CTkFont(size=10),
                command=lambda tid=trans_id: self.excluir_transacao(tid)
            ).pack(side="right", padx=4)

    def atualizar_grafico(self):
        for widget in self.grafico_frame.winfo_children():
            widget.destroy()

        receitas, despesas, _ = obter_resumo()

        figura = Figure(
            figsize=(4.0, 3.8),
            dpi=100,
            facecolor=PAINEL
        )

        eixo = figura.add_subplot(111)
        eixo.set_facecolor(PAINEL)

        valores = [receitas, despesas]
        cores = [VERDE, VERMELHO]
        nomes = ["Receitas", "Despesas"]

        if receitas == 0 and despesas == 0:
            eixo.text(
                0.5, 0.5,
                "Sem movimentações financeiras",
                color=TEXTO_SECUNDARIO,
                ha="center",
                va="center",
                fontsize=10,
                transform=eixo.transAxes
            )
            eixo.set_xticks([])
            eixo.set_yticks([])
        else:
            barras = eixo.bar(
                nomes,
                valores,
                color=cores,
                width=0.48,
                zorder=3
            )

            maior_valor = max(valores) or 1
            eixo.set_ylim(0, maior_valor * 1.25)

            for barra, valor in zip(barras, valores):
                eixo.text(
                    barra.get_x() + barra.get_width() / 2,
                    barra.get_height() + maior_valor * 0.035,
                    formatar_moeda(valor),
                    color=TEXTO,
                    ha="center",
                    va="bottom",
                    fontsize=8
                )

            eixo.tick_params(
                axis="x",
                colors=TEXTO_SECUNDARIO,
                labelsize=9
            )
            eixo.tick_params(
                axis="y",
                colors=TEXTO_SECUNDARIO,
                labelsize=8
            )

            eixo.yaxis.grid(
                True,
                color=BORDA,
                linestyle="--",
                linewidth=0.6,
                zorder=0
            )

            for lado in ["top", "right", "left", "bottom"]:
                eixo.spines[lado].set_visible(False)

        figura.tight_layout(pad=2)

        canvas = FigureCanvasTkAgg(
            figura,
            master=self.grafico_frame
        )
        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )


# ========================= INICIAR APLICAÇÃO =========================

if __name__ == "__main__":
    app = GerenciadorFinanceiro()
    app.mainloop()
