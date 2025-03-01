# Todo o código foi desenvolvido por Eduardo Isidoro
# a distribuição desta ferramenta não é permitida pelo autor da mesm
# o autor da mesma pode a qualquer momento requerer o diteitos e cobrar a sua utilização
# a ferramenta de testes ainda não tem qualquer tipo de verificação e ou auto update
# mas a mesma pode vir a ter futuramente.
#
# esta versão é ainda uma versão de testes
# ainda tem algumas logicas que não são explicitas para a boa elaboração

# Configurações do camião
TRUCK_DIMS = {
    'length': 13.60,  # metros (comprimento)
    'width': 2.40,    # metros (largura)
    'height': 2.60    # metros (altura)
}
MAX_WEIGHT = 24000       # kg
MAX_STACK_WEIGHT = 300   # kg (peso máximo permitido por pilha)
MAX_STACK_HEIGHT = 3     # número máximo de itens empilhados por pilha

def rect_overlap(r1, r2):
    """Verifica se dois retângulos se sobrepõem (x, y, largura, altura)."""
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if x1 >= x2 + w2 or x2 >= x1 + w1:
        return False
    if y1 >= y2 + h2 or y2 >= y1 + h1:
        return False
    return True

class Carga:
    def __init__(self, doc, comp, larg, alt, peso):
        """
        Representa uma carga ou palete em metros.
        Exemplo Euro-pallet: 1.20 x 0.80 x 0.80
        """
        self.doc = doc.strip()
        self.dims = (comp, larg, alt)  # (comprimento, largura, altura)
        self.peso = peso
        self.volume = comp * larg * alt
        self.empilhavel = peso <= MAX_STACK_WEIGHT
        self.posicionada = False

class Pilha:
    """
    Representa uma pilha (ou grupo de itens empilhados) posicionada no piso do camião.
    A posição (x, y) é o canto inferior esquerdo da base ocupada.
    """
    @staticmethod
    def determine_base(carga):
        comp, larg, alt = carga.dims
        tol = 0.05
        # Se quiser, mantenha ou remova a detecção de paletes padrão:
        if abs(comp - 1.20) < tol and abs(larg - 0.80) < tol and abs(alt - 0.80) < tol:
            return (1.20, 0.80, 0.80)
        elif abs(comp - 1.20) < tol and abs(larg - 1.20) < tol:
            return (1.20, 1.20, alt)
        elif abs(comp - 1.10) < tol and abs(larg - 1.10) < tol:
            return (1.10, 1.10, alt)
        elif abs(comp - 0.80) < tol and abs(larg - 0.80) < tol:
            return (0.80, 0.80, alt)
        else:
            return (comp, larg, alt)
    
    def __init__(self, x, y, base_comp, base_larg, base_alt, carga):
        self.x = x
        self.y = y
        self.base_comp = base_comp
        self.base_larg = base_larg
        self.cargas = [carga]
        self.total_height = base_alt
        self.total_weight = carga.peso
        carga.posicionada = True

    def empilhar(self, carga):
        """Tenta empilhar 'carga' sobre esta pilha."""
        if not carga.empilhavel or len(self.cargas) >= MAX_STACK_HEIGHT:
            return False
        c_comp, c_larg, c_height = Pilha.determine_base(carga)
        # Verifica se a base da nova carga cabe na base fixa da pilha (com rotação)
        if not ((c_comp <= self.base_comp and c_larg <= self.base_larg) or
                (c_comp <= self.base_larg and c_larg <= self.base_comp)):
            return False
        # Verifica altura e peso
        if self.total_height + c_height > TRUCK_DIMS['height']:
            return False
        if self.total_weight + carga.peso > MAX_STACK_WEIGHT:
            return False
        self.cargas.append(carga)
        self.total_height += c_height
        self.total_weight += carga.peso
        carga.posicionada = True
        return True

    def footprint(self):
        return (self.x, self.y, self.base_comp, self.base_larg)

class GerenciadorCargas:
    def __init__(self):
        self.cargas = []
        self.pilhas = []
        self.candidate_positions = [(0, 0)]  # onde podemos criar novas pilhas

    def adicionar_carga(self, carga):
        # Adiciona a carga à lista e recalcula tudo do zero,
        # assim reorienta e reposiciona as anteriores, se necessário.
        self.cargas.append(carga)
        self.recalcular_empilhamento()
        return carga.posicionada

    def remover_carga(self, index):
        if 0 <= index < len(self.cargas):
            del self.cargas[index]
        self.recalcular_empilhamento()

    def tentar_posicionar_nova_pilha(self, carga):
        comp, larg, alt = Pilha.determine_base(carga)
        # Duas orientações possíveis no piso:
        orientacoes = [
            (comp, larg),  # normal
            (larg, comp)   # girado 90°
        ]
        for pos in self.candidate_positions[:]:
            x, y = pos

            # Ver quais orientações cabem
            opcoes_viaveis = []
            for (oc, ol) in orientacoes:
                # Testa se cabe dentro do caminhão
                if x + oc <= TRUCK_DIMS['length'] and y + ol <= TRUCK_DIMS['width']:
                    # Testa sobreposição
                    new_rect = (x, y, oc, ol)
                    overlap_found = any(rect_overlap(new_rect, pilha.footprint()) for pilha in self.pilhas)
                    if not overlap_found:
                        opcoes_viaveis.append((oc, ol))

            # Se não coube em nenhuma orientação, continua
            if not opcoes_viaveis:
                continue

            # Escolhe a orientação que minimiza (x + oc), para ocupar menos comprimento
            opcoes_viaveis.sort(key=lambda o: x + o[0])
            best_comp, best_larg = opcoes_viaveis[0]

            # Criar a pilha com essa orientação
            nova_pilha = Pilha(x, y, best_comp, best_larg, alt, carga)
            self.pilhas.append(nova_pilha)
            self.candidate_positions.remove(pos)

            # Gerar novas posições.
            # Primeiro tentamos ocupar mais largura (y + best_larg),
            # depois avançamos no comprimento (x + best_comp).
            new_candidate = (x, y + best_larg)
            if (new_candidate not in self.candidate_positions
                    and new_candidate[1] < TRUCK_DIMS['width']):
                self.candidate_positions.append(new_candidate)

            new_candidate = (x + best_comp, y)
            if (new_candidate not in self.candidate_positions
                    and new_candidate[0] < TRUCK_DIMS['length']):
                self.candidate_positions.append(new_candidate)

            return True
        return False

    def recalcular_empilhamento(self):
        # Limpa todas as pilhas e refaz o layout do zero
        self.pilhas = []
        self.candidate_positions = [(0, 0)]
        for c in self.cargas:
            c.posicionada = False

        # Recoloca cada carga, permitindo que até as antigas mudem de posição/orientação
        for c in self.cargas:
            placed = False
            # Tentar empilhar em pilhas existentes
            for pilha in self.pilhas:
                if pilha.empilhar(c):
                    placed = True
                    break
            # Se não coube em nenhuma pilha, criar nova
            if not placed:
                self.tentar_posicionar_nova_pilha(c)

    def get_used_space(self):
        max_x = max((p.x + p.base_comp for p in self.pilhas), default=0.0)
        max_y = max((p.y + p.base_larg for p in self.pilhas), default=0.0)
        return max_x, max_y

    def get_max_height(self):
        return max((p.total_height for p in self.pilhas), default=0.0)

    def verificar_limites(self):
        status = True
        mensagens = []
        total_peso = sum(c.peso for c in self.cargas)
        total_volume = sum(c.volume for c in self.cargas)

        if total_peso > MAX_WEIGHT:
            status = False
            mensagens.append(f"PESO EXCEDIDO: {total_peso:.1f}/{MAX_WEIGHT} kg")

        # Verifica volume total
        if total_volume > (TRUCK_DIMS['length'] * TRUCK_DIMS['width'] * TRUCK_DIMS['height']):
            status = False
            mensagens.append(f"VOLUME TOTAL EXCEDIDO: {total_volume:.1f} m³")

        used_x, used_y = self.get_used_space()
        if used_x > TRUCK_DIMS['length']:
            status = False
            mensagens.append(f"COMPRIMENTO OCUPADO: {used_x:.2f} m")
        if used_y > TRUCK_DIMS['width']:
            status = False
            mensagens.append(f"LARGURA OCUPADA: {used_y:.2f} m")

        nao_posicionadas = sum(1 for c in self.cargas if not c.posicionada)
        if nao_posicionadas > 0:
            status = False
            mensagens.append(f"CARGAS NÃO POSICIONADAS: {nao_posicionadas}")

        return status, "\n".join(mensagens) if mensagens else "DENTRO DOS LIMITES"
