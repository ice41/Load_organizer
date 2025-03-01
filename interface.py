# Todo o código foi desenvolvido por Eduardo Isidoro
# a distribuição desta ferramenta não é permitida pelo autor da mesm
# o autor da mesma pode a qualquer momento requerer o diteitos e cobrar a sua utilização
# a ferramenta de testes ainda não tem qualquer tipo de verificação e ou auto update
# mas a mesma pode vir a ter futuramente.
#
# esta versão é ainda uma versão de testes
# ainda tem algumas logicas que não são explicitas para a boa elaboração

import tkinter as tk
from tkinter import ttk, messagebox
from logica import GerenciadorCargas, Carga, MAX_WEIGHT

class InterfaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Carga Nacional - Lusocargo v2.5 teste")
        self.geometry("1200x900")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabelframe.Label", font=("Helvetica", 12, "bold"))

        self.gerenciador = GerenciadorCargas()
        self.debug_mode = tk.BooleanVar(value=False)

        self.criar_componentes()
        self.atualizar_status()
        self.monitorar_cargas()

    def criar_componentes(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # Painel de entrada (à esquerda)
        input_frame = ttk.LabelFrame(top_frame, text="Adicionar Carga", padding=15)
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        campos = [
            ("Nº Documento:", "doc"),
            ("Comprimento:", "comp"),
            ("Largura:", "larg"),
            ("Altura:", "alt"),
            ("Peso (kg):", "peso")
        ]
        self.entries = {}
        for row, (label, nome) in enumerate(campos):
            ttk.Label(input_frame, text=label).grid(row=row, column=0, padx=5, pady=2, sticky="e")
            entry = ttk.Entry(input_frame)
            entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
            self.entries[nome] = entry

        # Vincular Enter para mudar de campo, e só no último disparar "Adicionar Carga"
        self.entries['doc'].bind("<Return>", lambda e: self.entries['comp'].focus_set())
        self.entries['comp'].bind("<Return>", lambda e: self.entries['larg'].focus_set())
        self.entries['larg'].bind("<Return>", lambda e: self.entries['alt'].focus_set())
        self.entries['alt'].bind("<Return>", lambda e: self.entries['peso'].focus_set())
        self.entries['peso'].bind("<Return>", lambda e: self.adicionar_carga())

        ttk.Button(input_frame, text="Adicionar Carga", command=self.adicionar_carga).grid(row=6, columnspan=2, pady=10)

        # Modo teste e debug
        self.debug_check = ttk.Checkbutton(input_frame, text="Modo Teste", variable=self.debug_mode,
                                           command=self.toggle_debug)
        self.debug_check.grid(row=7, columnspan=2, pady=5)
        self.debug_container = ttk.Frame(input_frame)
        self.debug_area = tk.Text(self.debug_container, height=15, width=50, wrap="word")
        self.debug_area.pack(fill=tk.X, pady=5)
        self.btn_carregar_lote = ttk.Button(self.debug_container, text="Carregar Lote", command=self.carregar_lote)
        self.btn_carregar_lote.pack(pady=5)

        # Painel de análise (à direita)
        analysis_frame = ttk.LabelFrame(top_frame, text="Análise", padding=15)
        analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        self.stats = {
            'volume': ttk.Label(analysis_frame, text="Volume Total: 0.00 m³"),
            'peso': ttk.Label(analysis_frame, text="Peso Total: 0 kg"),
            'dimensoes': ttk.Label(analysis_frame, text="Espaço Utilizado: 0.00 m (com.) x 0.00 m (larg.) x 0.00 m (alt.)"),
            'stacks': ttk.Label(analysis_frame, text="Pilhas Criadas: 0"),
            'nao_posicionadas': ttk.Label(analysis_frame, text="Cargas Não Posicionadas: 0"),
            'status': ttk.Label(analysis_frame, text="STATUS: Não verificado", foreground="#228822")
        }
        for stat in self.stats.values():
            stat.pack(anchor=tk.W, pady=5)

        # Lista de cargas
        list_frame = ttk.LabelFrame(main_frame, text="Cargas Registadas", padding=15)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.lista = tk.Listbox(list_frame, font=("Consolas", 11), selectbackground="#e0e0ff")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=scroll.set)
        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Menu de contexto para remoção
        self.menu_ctx = tk.Menu(self, tearoff=0)
        self.menu_ctx.add_command(label="Remover", command=lambda: self.remover_selecionado())
        self.lista.bind("<Button-3>", self.mostrar_menu)

        # Rodapé
        footer = ttk.Label(self, text="Criado por Eduardo Isidoro", font=("Helvetica", 8), foreground="gray")
        footer.pack(side=tk.BOTTOM, pady=5)

        # Focar no primeiro campo (Nº Documento)
        self.entries['doc'].focus_set()

    def toggle_debug(self):
        if self.debug_mode.get():
            self.debug_container.grid(row=8, columnspan=2, sticky="ew")
        else:
            self.debug_container.grid_forget()

    def adicionar_carga(self):
        try:
            doc = self.entries['doc'].get()
            comp = float(self.entries['comp'].get())
            larg = float(self.entries['larg'].get())
            alt  = float(self.entries['alt'].get())
            peso = float(self.entries['peso'].get())

            carga = Carga(doc, comp, larg, alt, peso)
            posicionada = self.gerenciador.adicionar_carga(carga)
            status_simbolo = "✓" if posicionada else "✗"
            self.lista.insert(tk.END,
                f"[{status_simbolo}] {carga.doc} | "
                f"{carga.dims[0]:.2f}x{carga.dims[1]:.2f}x{carga.dims[2]:.2f} m "
                f"({carga.volume:.2f} m³) | {carga.peso} kg"
            )
            # Limpar campos e focar novamente no primeiro
            for entry in self.entries.values():
                entry.delete(0, tk.END)
            self.entries['doc'].focus_set()

            self.atualizar_status()

        except ValueError as e:
            messagebox.showerror("Erro", f"Dados inválidos:\n{e}")

    def remover_selecionado(self):
        if selection := self.lista.curselection():
            index = selection[0]
            self.gerenciador.remover_carga(index)
            self.lista.delete(index)
            self.atualizar_status()

    def mostrar_menu(self, event):
        try:
            index = self.lista.nearest(event.y)
            self.lista.selection_clear(0, tk.END)
            self.lista.selection_set(index)
            self.menu_ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_ctx.grab_release()

    def carregar_lote(self):
        dados = self.debug_area.get("1.0", tk.END).strip()
        linhas = dados.splitlines()
        total = len(linhas)
        sucesso = 0
        erros = []
        for i, linha in enumerate(linhas, 1):
            try:
                if not linha.strip():
                    continue
                partes = linha.split(',')
                if len(partes) != 5:
                    raise ValueError("Formato inválido. Use: doc,comp,larg,alt,peso")
                doc, comp, larg, alt, peso = partes
                carga = Carga(doc.strip(), float(comp), float(larg), float(alt), float(peso))
                posicionada = self.gerenciador.adicionar_carga(carga)
                status_simbolo = "✓" if posicionada else "✗"
                self.lista.insert(tk.END,
                    f"[{status_simbolo}] {carga.doc} | "
                    f"{carga.dims[0]:.2f}x{carga.dims[1]:.2f}x{carga.dims[2]:.2f} m "
                    f"({carga.volume:.2f} m³) | {carga.peso} kg"
                )
                sucesso += 1
            except Exception as e:
                erros.append(f"Linha {i}: {str(e)}")

        self.atualizar_status()
        if erros:
            messagebox.showwarning("Resultado do Lote",
                f"Processadas {total} linhas:\n"
                f"Adicionadas: {sucesso}\nErros de formato: {len(erros)}\n\n"
                "Detalhes dos erros:\n" + "\n".join(erros[:20]))
        else:
            messagebox.showinfo("Sucesso", f"Todas as {total} cargas foram registadas!")

    def atualizar_status(self):
        total_volume = sum(c.volume for c in self.gerenciador.cargas)
        total_peso = sum(c.peso for c in self.gerenciador.cargas)
        nao_posicionadas = sum(1 for c in self.gerenciador.cargas if not c.posicionada)

        used_x, used_y = self.gerenciador.get_used_space()
        max_height = self.gerenciador.get_max_height()

        self.stats['volume'].config(text=f"Volume Total: {total_volume:.2f} m³")
        self.stats['peso'].config(text=f"Peso Total: {total_peso:.1f}/{MAX_WEIGHT} kg")
        self.stats['dimensoes'].config(
            text=f"Espaço Utilizado: {used_x:.2f} m (com.) x {used_y:.2f} m (larg.) x {max_height:.2f} m (alt.)"
        )
        self.stats['stacks'].config(text=f"Pilhas Criadas: {len(self.gerenciador.pilhas)}")
        self.stats['nao_posicionadas'].config(text=f"Cargas Não Posicionadas: {nao_posicionadas}")

        status, msg = self.gerenciador.verificar_limites()
        cor = "#228822" if status else "#aa2222"
        self.stats['status'].config(text=f"STATUS: {msg}", foreground=cor)

    def monitorar_cargas(self):
        # Recalcula sempre, em background, para garantir que
        # a cada nova carga as anteriores também possam "rodar" e otimizar espaço
        self.gerenciador.recalcular_empilhamento()
        self.atualizar_status()
        self.after(1000, self.monitorar_cargas)

if __name__ == "__main__":
    app = InterfaceApp()
    app.mainloop()
