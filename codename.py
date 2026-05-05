from flask import Flask, render_template_string, request, redirect, jsonify
import random
import time

app = Flask(__name__)

# =========================
# CONTROLE
# =========================
versao_sala = 0
espioes_conectados = 0
chat_log = []
ADMIN_SENHA = "712037"

tempo_restante = 0
jogo_ativo = True
turno = None
timer_ativo = False

TEMPO_RETORNO_FINAL = 10
fim_jogo_em = None

espioes = {}
jogadas_jokenpo = {}
espioes_lista = []
jokenpo_pronto = False
resultado_jokenpo = {}

cartas_reveladas = [False] * 25

pontos = {
    "azul": 0,
    "vermelho": 0
}

jogo_encerrado = False
vencedor_jogo = None

limite_palpites = 0
palpites_rodada = 0
palavras_usadas = set()
historico_partidas = []


# =========================
# TEMAS
# =========================
temas = {

    "objetos": [
        "Mesa","Cadeira","Janela","Porta","Espelho","Relógio","Chave","Copo","Livro","Caneta",
        "Telefone","Lâmpada","Faca","Garfo","Colher","Caixa","Bolsa","Mochila","Câmera","Controle"
    ],

    "tecnologia": [
        "Computador","Celular","Internet","Código","Robô","Software","Hardware","Servidor","Banco","Dados",
        "Senha","Rede","Tela","Sistema","Aplicativo","Bug","Download","Upload","Arquivo","Processador"
    ],

    "natureza": [
        "Árvore","Rio","Montanha","Sol","Lua","Estrela","Floresta","Deserto","Mar","Chuva",
        "Vento","Tempestade","Neve","Gelo","Pedra","Areia","Lago","Céu","Nuvem","Raiz"
    ],

    "comida": [
        "Pizza","Hambúrguer","Arroz","Feijão","Chocolate","Café","Leite","Pão","Macarrão","Sorvete",
        "Carne","Frango","Peixe","Salada","Ovo","Queijo","Batata","Doce","Bolo","Suco"
    ],

    "profissoes": [
        "Médico","Professor","Engenheiro","Policial","Advogado","Programador","Designer","Chef","Piloto","Ator",
        "Cantor","Jogador","Motorista","Mecânico","Enfermeiro","Juiz","Bombeiro","Arquiteto","Eletricista","Dentista"
    ],

    "lugares": [
        "Brasil","Paris","Japão","Praia","Escola","Hospital","Aeroporto","Restaurante","Cinema","Estádio",
        "Casa","Prédio","Cidade","Campo","Ilha","Floresta","Biblioteca","Shopping","Rua","Ponte"
    ],

    "transporte": [
        "Carro","Moto","Avião","Navio","Bicicleta","Trem","Ônibus","Helicóptero","Barco","Caminhão",
        "Uber","Táxi","Metrô","Estrada","Rodovia","Garagem","Porto","Pista","Viagem","Passagem"
    ],

    "cultura": [
        "Filme","Série","Música","Arte","Teatro","Livro","Jogo","Dança","Show","Festival",
        "Cinema","Banda","Palco","Tela","História","Câmera","Cena","Diretor","Roteiro","Personagem"
    ],

    "esporte": [
        "Gol","Passe","Chute","Time","Torcida","Copa","Juiz","Camisa","Campo","Bola",
        "Treino","Partida","Final","Liga","Atleta","Corrida","Salto","Vitória","Derrota","Competição"
    ],

    "abstrato": [
        "Tempo","Amor","Guerra","Poder","Vida","Morte","Energia","Força","Velocidade","Ideia",
        "Sorte","Azar","Destino","Verdade","Mentira","Sonho","Medo","Coragem","Liberdade","Controle"
    ],

    "elementos": [
        "Fogo","Água","Terra","Ar","Metal","Madeira","Vidro","Plástico","Luz","Sombra",
        "Calor","Frio","Som","Cor","Escuro","Brilho","Peso","Forma","Tamanho","Volume"
    ]
}

# =========================
# GERAR JOGO
# =========================
def gerar_jogo():
    global palavras_usadas, historico_partidas

    # 🔥 NÍVEL 2 → escolhe categorias aleatórias
    categorias = random.sample(list(temas.keys()), 3)

    pool = []
    for c in categorias:
        pool += temas[c]

    # mistura todas categorias automaticamente
    lista_total = []
    for lista in temas.values():
        lista_total += lista

    # 🔥 NÍVEL 1 → evita palavras repetidas
    disponiveis = list(set(pool) - palavras_usadas)

    if len(disponiveis) < 25:
        palavras_usadas.clear()
        disponiveis = pool.copy()

    # 🔥 NÍVEL 3 → evita repetir partida igual
    tentativas = 0
    while True:
        palavras = random.sample(disponiveis, 25)

        if palavras not in historico_partidas:
            historico_partidas.append(palavras)
            break

        tentativas += 1
        if tentativas > 10:
            break  # evita loop infinito

    palavras_usadas.update(palavras)

    mapa = (
        (["blue"] * 8) +
        (["red"] * 8) +
        (["neutral"] * 8) +
        (["assassin"])
    )

    random.shuffle(mapa)

    return palavras, mapa

palavras, mapa = gerar_jogo()

def resetar_jogo(forcar_retorno=False):
    global palavras, mapa, chat_log, espioes_conectados
    global cartas_reveladas, pontos, jogo_encerrado, vencedor_jogo
    global turno, tempo_restante, timer_ativo
    global jogadas_jokenpo, espioes_lista, espioes, resultado_jokenpo
    global jogo_ativo, limite_palpites, palpites_rodada, versao_sala
    global fim_jogo_em

    palavras, mapa = gerar_jogo()
    cartas_reveladas = [False] * 25

    chat_log.clear()
    espioes_conectados = 0

    pontos = {
        "azul": 0,
        "vermelho": 0
    }

    jogo_encerrado = False
    vencedor_jogo = None
    turno = None
    tempo_restante = 0
    timer_ativo = False
    jogo_ativo = True
    fim_jogo_em = None

    limite_palpites = 0
    palpites_rodada = 0

    jogadas_jokenpo.clear()
    espioes_lista.clear()
    espioes.clear()
    resultado_jokenpo.clear()

    if forcar_retorno:
        versao_sala += 1

def decidir_vencedor(e1, j1, e2, j2):
    if j1 == j2:
        return None

    regras = {
        "pedra": "tesoura",
        "tesoura": "papel",
        "papel": "pedra"
    }

    return e1 if regras[j1] == j2 else e2

# =========================
# HTML INTEGRADO
# =========================
HTML_JOGO = """ 
<!DOCTYPE html>
<html>
<head>
    <title>Codenames</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>

<body>

<h1>{{ titulo }}</h1>

<input type="hidden" id="nome" value="{{ nome }}">
<input type="hidden" id="papel" value="{{ papel }}">
<input type="hidden" id="meuTime" value="{{ meu_time }}">
<input type="hidden" id="salaVersao" value="{{ sala_versao }}">

<div class="scoreboard">
    <div class="score blue-score">🔵 Azul: <span id="pontosAzul">0</span>/8</div>
    <div class="score red-score">🔴 Vermelho: <span id="pontosVermelho">0</span>/8</div>
</div>

{% if papel == "espiao" %}
<h3 id="meu-time">Você é o espião do time: {{ meu_time.upper() }}</h3>
{% elif papel == "detetive" %}
<h3 id="meu-time">Você é detetive do time: {{ meu_time.upper() }}</h3>
{% endif %}

<div class="container">

    <div>
        <h2>🎯 Tabuleiro</h2>
        <div class="grid">
            {% for i in range(25) %}
            <div class="card-container" onclick="revelarCarta({{i}})">
                <div class="card-inner" id="card-{{i}}">
                    <div class="card-front {% if papel == 'espiao' %}{{ cores[i] }}{% endif %}">
                        {{ palavras[i] }}
                    </div>

                    <div class="card-back {{ cores[i] }}">
                        {{ palavras[i] }}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="chat">
        <h3>📜 Histórico</h3>

        <div id="chat-box" class="chat-box"></div>

        {% if papel == "espiao" %}
        <form onsubmit="enviarMensagem(event)">
            <input id="msgInput" placeholder="Aguardando sua vez..." required disabled>
            <button id="btnEnviar" type="submit" disabled>Enviar</button>
        </form>
        {% else %}
        <p>🔒 Apenas espiões enviam dicas</p>
        {% endif %}
    </div>

</div>

<div style="margin-top: 20px;">
    <h2 id="turno"></h2>
    <h3 id="timer"></h3>
</div>

<script>
let ultimoTurno = null;
let cartaSelecionada = null;
let vitoriaMostrada = false;

function verificarResetGeral() {
    fetch('/status_sala')
        .then(res => res.json())
        .then(data => {
            const minhaVersao = Number(document.getElementById("salaVersao").value);

            if (!data.jogo_ativo || data.versao_sala !== minhaVersao) {
                window.location.href = "/";
            }
        });
}

setInterval(verificarResetGeral, 1000);

function atualizarTempo() {
    fetch('/tempo')
        .then(res => res.json())
        .then(data => {
            if (!data.turno) return;
            
            const grid = document.querySelector(".grid");

            grid.classList.remove("turno-azul", "turno-vermelho");

            if (data.turno === "azul") {
                grid.classList.add("turno-azul");
            } else if (data.turno === "vermelho") {
                grid.classList.add("turno-vermelho");
            }

            if (data.turno !== ultimoTurno) {
                grid.classList.add("animar-turno");

                setTimeout(() => {
                    grid.classList.remove("animar-turno");
                }, 500);

                ultimoTurno = data.turno;
            }

            const timerEl = document.getElementById("timer");
            timerEl.innerText = data.tempo > 0 ? "⏱️ " + data.tempo + "s" : "";

            const turnoEl = document.getElementById("turno");
            turnoEl.innerText = "Turno: " + data.turno;
            turnoEl.style.color = data.turno === "azul" ? "#4facfe" : "#ff6a6a";

            const papel = document.getElementById("papel").value;
            const meuTime = document.getElementById("meuTime").value;
            const inputMsg = document.getElementById("msgInput");
            const btnEnviar = document.getElementById("btnEnviar");

            if (papel === "espiao" && inputMsg && btnEnviar) {
                const minhaVez = meuTime === data.turno;

                inputMsg.disabled = !minhaVez;
                btnEnviar.disabled = !minhaVez;

                inputMsg.placeholder = minhaVez
                    ? "Ex: Futebol 2"
                    : "Aguardando sua vez...";
            }
        });
}

setInterval(atualizarTempo, 1000);

function atualizarChat() {
    fetch('/chat_data')
        .then(res => res.json())
        .then(data => {
            const chatBox = document.getElementById("chat-box");

            const isAtBottom =
                chatBox.scrollHeight - chatBox.scrollTop <= chatBox.clientHeight + 5;

            chatBox.innerHTML = "";

            data.chat.forEach(msg => {
                const p = document.createElement("p");
                p.textContent = msg;
                chatBox.appendChild(p);
            });

            if (isAtBottom) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
}

function atualizarEstadoJogo() {
    fetch('/estado_jogo')
        .then(res => res.json())
        .then(data => {
            document.getElementById("pontosAzul").innerText = data.pontos.azul;
            document.getElementById("pontosVermelho").innerText = data.pontos.vermelho;

            data.cartas_reveladas.forEach((revelada, index) => {
                if (revelada) {
                    const card = document.getElementById("card-" + index);
                    if (card) {
                        card.classList.add("flipped");
                        card.classList.remove("preselected");
                    }
                }
            });

            if (data.jogo_encerrado && data.vencedor) {
                const turnoEl = document.getElementById("turno");

                turnoEl.innerText = "🏆 Vitória do time " + data.vencedor.toUpperCase();
                turnoEl.style.color = data.vencedor === "azul" ? "#4facfe" : "#ff6a6a";

                if (data.retorno_em !== null && data.retorno_em >= 0) {
                    turnoEl.innerText =
                        "🏆 Vitória do time " +
                        data.vencedor.toUpperCase() +
                        " | Voltando em " +
                        data.retorno_em +
                        "s";
                }

                if (!vitoriaMostrada) {
                    vitoriaMostrada = true;
                    setTimeout(() => {
                        alert("🏆 Time " + data.vencedor.toUpperCase() + " venceu!");
                    }, 400);
                }

                if (!data.jogo_ativo) {
                    window.location.href = "/";
                }
            }

            const minhaVersao = Number(document.getElementById("salaVersao").value);
            if (data.versao_sala !== minhaVersao) {
                window.location.href = "/";
            }
        });
}

function revelarCarta(index) {
    const papel = document.getElementById("papel").value;
    const meuTime = document.getElementById("meuTime").value;

    if (papel === "espiao") {
        alert("🕵️ Espiões não podem selecionar cartas.");
        return;
    }

    if (!meuTime) {
        alert("Você precisa estar em um time para jogar.");
        return;
    }

    const card = document.getElementById("card-" + index);

    if (card.classList.contains("flipped")) return;

    if (cartaSelecionada !== index) {
        if (cartaSelecionada !== null) {
            document
                .getElementById("card-" + cartaSelecionada)
                .classList.remove("preselected");
        }

        cartaSelecionada = index;
        card.classList.add("preselected");
        return;
    }

    fetch('/revelar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body:
            'index=' + index +
            '&time=' + encodeURIComponent(meuTime)
    })
    .then(res => res.json())
    .then(data => {
        if (data.erro) {
            alert(data.erro);
            return;
        }

        card.classList.remove("preselected");
        card.classList.add("flipped");

        cartaSelecionada = null;
        atualizarEstadoJogo();
    });
}

function enviarMensagem(e) {
    e.preventDefault();

    const input = document.getElementById("msgInput");
    const nome = document.getElementById("nome").value;

    fetch('/enviar_dica', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body:
            'papel=espiao&mensagem=' +
            encodeURIComponent(input.value) +
            '&nome=' +
            encodeURIComponent(nome)
    });

    input.value = "";
}

setInterval(atualizarChat, 2000);
setInterval(atualizarEstadoJogo, 1000);

atualizarChat();
atualizarEstadoJogo();
</script>

</body>
</html>
"""

# =========================
# ROTAS
# =========================

@app.route("/")
def home():
    global jogo_ativo

    jogo_ativo = True

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Codenames</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>

<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🎮 Codenames</h2>

        <input id="nomeInput" class="input-ui" placeholder="Digite seu nome">

        <button class="button-ui" onclick="entrar('detetive', 'azul')">
            🔵 Detetive Azul
        </button>

        <br><br>

        <button class="button-ui button-danger" onclick="entrar('detetive', 'vermelho')">
            🔴 Detetive Vermelho
        </button>

        <br><br>

        <button class="button-ui button-alt" onclick="entrar('espiao', '')">
            🕵️ Espião
        </button>
                                  
        <br><br>

        <button class="button-ui button-admin" onclick="window.location.href='/admin'">
            🔒 Admin
        </button>
    </div>
</div>

<script>
function entrar(papel, time) {
    const nome = document.getElementById("nomeInput").value;

    if (!nome) {
        alert("Digite seu nome!");
        return;
    }

    if (papel === "espiao") {
        window.location.href = "/espiao?nome=" + encodeURIComponent(nome);
    } else {
        window.location.href =
            "/jogo?papel=detetive&nome=" +
            encodeURIComponent(nome) +
            "&time=" +
            encodeURIComponent(time);
    }
}
</script>

</body>
</html>
""")

@app.route("/jogo")
def jogo():
    papel = request.args.get("papel", "detetive")
    nome = request.args.get("nome", "Jogador")

    if papel == "espiao":
        meu_time = espioes.get(nome, "")
    else:
        meu_time = request.args.get("time", "")

    return render_template_string(
        HTML_JOGO,
        titulo=f"{nome} ({papel.capitalize()})",
        palavras=palavras,
        cores=mapa,
        mostrar_cores=(papel == "espiao"),
        papel=papel,
        nome=nome,
        meu_time=meu_time,
        sala_versao=versao_sala
    )

@app.route("/espiao")
def espiao():
    global espioes_lista

    nome = request.args.get("nome")

    if not nome:
        return "Nome obrigatório"

    if nome not in espioes_lista and len(espioes_lista) < 2:
        espioes_lista.append(nome)

    return redirect(f"/espera?nome={nome}")

@app.route("/espera")
def espera():
    nome = request.args.get("nome")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2 class="waiting">⏳ Aguardando outro espião...</h2>

        <p>Conectados: {{qtd}} / 2</p>

        <p>A partida começará automaticamente</p>
    </div>
</div>

<script>
const minhaVersao = {{ sala_versao }};

setInterval(() => {
    fetch('/status_espioes')
        .then(res => res.json())
        .then(data => {
            if (data.qtd == 2) {
                window.location.href = "/jokenpo_tela?nome={{nome}}";
            }
        });
}, 1000);

setInterval(() => {
    fetch('/status_sala')
        .then(res => res.json())
        .then(data => {
            if (!data.jogo_ativo || data.versao_sala !== minhaVersao) {
                window.location.href = "/";
            }
        });
}, 1000);
</script>

</body>
</html>
""", qtd=len(espioes_lista), nome=nome, sala_versao=versao_sala)

@app.route("/status_espioes")
def status_espioes():
    return {"qtd": len(espioes_lista)}

@app.route("/jokenpo_tela")
def jokenpo_tela():
    nome = request.args.get("nome")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🎲 Pedra, Papel ou Tesoura</h2>

        <p>Escolha sua jogada</p>
                                          
        <br><br>

        <button class="button-ui" onclick="jogar('pedra')">✊🏻 Pedra</button>
                                          
        <br><br>
        
        <button class="button-ui button-alt" onclick="jogar('papel')">🖐🏻 Papel</button>
                                          
        <br><br>
        
        <button class="button-ui button-danger" onclick="jogar('tesoura')">✌🏻 Tesoura</button>
    </div>
</div>

<script>
const minhaVersao = {{ sala_versao }};

function jogar(escolha) {
    fetch('/jokenpo', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'nome={{nome}}&escolha=' + escolha
    });

    alert("Escolha enviada!");
}

setInterval(() => {
    fetch('/status_jokenpo')
        .then(res => res.json())
        .then(data => {
            if (data.pronto) {
                window.location.href = "/resultado_jokenpo?nome={{nome}}";
            }
        });
}, 1000);

setInterval(() => {
    fetch('/status_sala')
        .then(res => res.json())
        .then(data => {
            if (!data.jogo_ativo || data.versao_sala !== minhaVersao) {
                window.location.href = "/";
            }
        });
}, 1000);
</script>

</body>
</html>
""", nome=nome, sala_versao=versao_sala)

@app.route("/status_jokenpo")
def status_jokenpo():
    return {"pronto": len(jogadas_jokenpo) == 2}

@app.route("/jokenpo", methods=["POST"])
def jokenpo():
    global jogadas_jokenpo, turno, espioes

    nome = request.form.get("nome")
    escolha = request.form.get("escolha")

    jogadas_jokenpo[nome] = escolha

    if len(jogadas_jokenpo) == 2:
        nomes = list(jogadas_jokenpo.keys())
        e1, e2 = nomes[0], nomes[1]

        j1 = jogadas_jokenpo[e1]
        j2 = jogadas_jokenpo[e2]

        vencedor = decidir_vencedor(e1, j1, e2, j2)

        if vencedor is None:
            jogadas_jokenpo.clear()
            chat_log.append(f"🎲 {e1} ({j1}) vs {e2} ({j2}) → Empate! Joguem novamente.")
            return ("", 204)

        if vencedor == e1:
            turno = "azul"
            espioes[e1] = "azul"
            espioes[e2] = "vermelho"
        else:
            turno = "azul"
            espioes[e2] = "azul"
            espioes[e1] = "vermelho"

        resultado_jokenpo["vencedor"] = vencedor
        resultado_jokenpo["jogadas"] = {
            e1: j1,
            e2: j2
        }

        chat_log.append(f"🎲 {e1} ({j1}) vs {e2} ({j2})")
        chat_log.append(f"🏁 {vencedor} começa!")

    return ("", 204)

@app.route("/resultado_jokenpo")
def resultado():
    nome = request.args.get("nome")

    vencedor = resultado_jokenpo.get("vencedor")
    jogadas = resultado_jokenpo.get("jogadas", {})

    if len(jogadas) < 2:
        return redirect(f"/jokenpo_tela?nome={nome}")

    nomes = list(jogadas.keys())
    valores = list(jogadas.values())

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🎲 Resultado do Jokenpô</h2>

        <p>{{n1}} jogou: {{j1}}</p>
        <p>{{n2}} jogou: {{j2}}</p>

        <h3>
            {% if nome == vencedor %}
                🎉 Você começa!
            {% else %}
                😬 Você não começa
            {% endif %}
        </h3>

        <button class="button-ui" onclick="irJogo()">Ir para o jogo</button>
    </div>
</div>

<script>
const minhaVersao = {{ sala_versao }};

function irJogo() {
    window.location.href = "/jogo?papel=espiao&nome={{nome}}";
}

setInterval(() => {
    fetch('/status_sala')
        .then(res => res.json())
        .then(data => {
            if (!data.jogo_ativo || data.versao_sala !== minhaVersao) {
                window.location.href = "/";
            }
        });
}, 1000);
</script>

</body>
</html>
""",
    nome=nome,
    vencedor=vencedor,
    n1=nomes[0],
    n2=nomes[1],
    j1=valores[0],
    j2=valores[1],
    sala_versao=versao_sala
    )

@app.route("/enviar_dica", methods=["POST"])
def enviar_dica():
    global tempo_restante, timer_ativo, limite_palpites, palpites_rodada

    papel = request.form.get("papel")
    mensagem = request.form.get("mensagem")
    nome = request.form.get("nome")

    if papel != "espiao":
        return "🚫 Apenas espiões podem enviar dicas!"

    if nome not in espioes:
        return "🚫 Você não está autorizado"

    if espioes.get(nome) != turno:
        return "🚫 Não é seu turno!"

    if mensagem and nome:
        chat_log.append(f"🕵️ {nome}: {mensagem}")

        partes = mensagem.strip().split()
        numero = partes[-1] if partes else "0"

        if numero.isdigit():
            limite_palpites = int(numero)
        else:
            limite_palpites = 1

        palpites_rodada = 0
        tempo_restante = 120
        timer_ativo = True

    return ("", 204)

@app.route("/chat_data")
def chat_data():
    return jsonify({"chat": chat_log})

@app.route("/estado_jogo")
def estado_jogo():
    global jogo_ativo

    retorno_em = None

    if jogo_encerrado and fim_jogo_em:
        restante = TEMPO_RETORNO_FINAL - int(time.time() - fim_jogo_em)
        retorno_em = max(0, restante)

        if retorno_em <= 0:
            resetar_jogo(forcar_retorno=True)
            jogo_ativo = False

    return jsonify({
        "pontos": pontos,
        "turno": turno,
        "jogo_encerrado": jogo_encerrado,
        "vencedor": vencedor_jogo,
        "cartas_reveladas": cartas_reveladas,
        "cores": mapa,
        "limite_palpites": limite_palpites,
        "palpites_rodada": palpites_rodada,
        "retorno_em": retorno_em,
        "jogo_ativo": jogo_ativo,
        "versao_sala": versao_sala
    })

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        senha = request.form.get("senha")

        if senha == ADMIN_SENHA:
            return redirect(f"/admin_painel?senha={senha}")

        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🔒 Admin</h2>

        <p style="color:red;">Senha incorreta</p>

        <form method="post">
            <input class="input-ui" type="password" name="senha" placeholder="Senha">
            <button class="button-ui">Entrar</button>
        </form>
    </div>
</div>

</body>
</html>
""")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🔒 Admin</h2>

        <form method="post">
            <input class="input-ui" type="password" name="senha" placeholder="Senha">
            <button class="button-ui">Entrar</button>
        </form>
    </div>
</div>

</body>
</html>
""")

@app.route("/admin_painel")
def admin_painel():
    senha = request.args.get("senha")

    if senha != ADMIN_SENHA:
        return redirect("/admin")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>

<div class="page-center">
    <div class="card-ui">
        <h2>🎮 Painel Admin</h2>

        <p>Espiões: {{espioes}}</p>
        <p>Mensagens: {{chat}}</p>
                                          
        <br><br>

        <button class="button-ui" onclick="acao('reset')">🔄 Reset</button>
        
        <br><br>
        
        <button class="button-ui button-alt" onclick="acao('tempo')">⏱️ Timer</button>
                                          
        <br><br>
        
        <button class="button-ui button-danger" onclick="acao('inicio')">🏠 Reset Geral</button>
    </div>
</div>

<script>
function acao(tipo) {
    fetch('/admin_acao', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'tipo=' + tipo + '&senha={{senha}}'
    }).then(() => {
        alert("Ação executada!");
    });
}
</script>

</body>
</html>
""", espioes=len(espioes_lista), chat=len(chat_log), senha=senha)

@app.route("/admin_acao", methods=["POST"])
def admin_acao():
    global tempo_restante, jogo_ativo

    senha = request.form.get("senha")
    tipo = request.form.get("tipo")

    if senha != ADMIN_SENHA:
        return "🚫 Acesso negado"

    if tipo == "reset":
        resetar_jogo()

    elif tipo == "inicio":
        resetar_jogo(forcar_retorno=True)
        jogo_ativo = False

    elif tipo == "tempo":
        tempo_restante = 30

    return ("", 204)

@app.route("/revelar", methods=["POST"])
def revelar():
    global cartas_reveladas, turno, pontos
    global jogo_encerrado, vencedor_jogo, timer_ativo, tempo_restante
    global palpites_rodada, limite_palpites, fim_jogo_em

    if jogo_encerrado:
        return jsonify({
            "erro": "O jogo já foi encerrado.",
            "jogo_encerrado": True,
            "vencedor": vencedor_jogo
        })

    index = int(request.form.get("index"))
    time_jogador = request.form.get("time")

    if not turno:
        return jsonify({"erro": "O turno ainda não foi definido."})

    if time_jogador != turno:
        return jsonify({"erro": "Não é o turno do seu time."})

    if cartas_reveladas[index]:
        return jsonify({"erro": "Essa carta já foi revelada."})

    cartas_reveladas[index] = True
    cor = mapa[index]
    palavra = palavras[index]

    if cor == "assassin":
        jogo_encerrado = True
        fim_jogo_em = time.time()
        vencedor_jogo = "vermelho" if turno == "azul" else "azul"
        timer_ativo = False
        tempo_restante = 0

        chat_log.append(f"💀 {palavra} era a carta assassina!")
        chat_log.append(f"🏆 Time {vencedor_jogo.upper()} venceu!")

    elif cor == "blue":
        pontos["azul"] += 1
        chat_log.append(f"🔵 Carta azul revelada: {palavra}")

        if pontos["azul"] >= 8:
            jogo_encerrado = True
            fim_jogo_em = time.time()
            vencedor_jogo = "azul"
            timer_ativo = False
            tempo_restante = 0
            chat_log.append("🏆 Time AZUL encontrou todas as cartas e venceu!")

        elif turno == "azul":
            palpites_rodada += 1

            if limite_palpites > 0 and palpites_rodada >= limite_palpites:
                turno = "vermelho"
                timer_ativo = False
                tempo_restante = 0
                chat_log.append("✅ Limite da dica atingido! Agora é turno do time VERMELHO")
        else:
            turno = "vermelho"
            timer_ativo = False
            tempo_restante = 0
            chat_log.append("❌ Carta do outro time! Agora é turno do time VERMELHO")

    elif cor == "red":
        pontos["vermelho"] += 1
        chat_log.append(f"🔴 Carta vermelha revelada: {palavra}")

        if pontos["vermelho"] >= 8:
            jogo_encerrado = True
            fim_jogo_em = time.time()
            vencedor_jogo = "vermelho"
            timer_ativo = False
            tempo_restante = 0
            chat_log.append("🏆 Time VERMELHO encontrou todas as cartas e venceu!")

        elif turno == "vermelho":
            palpites_rodada += 1

            if limite_palpites > 0 and palpites_rodada >= limite_palpites:
                turno = "azul"
                timer_ativo = False
                tempo_restante = 0
                chat_log.append("✅ Limite da dica atingido! Agora é turno do time AZUL")
        else:
            turno = "azul"
            timer_ativo = False
            tempo_restante = 0
            chat_log.append("❌ Carta do outro time! Agora é turno do time AZUL")

    elif cor == "neutral":
        timer_ativo = False
        tempo_restante = 0
        turno = "vermelho" if turno == "azul" else "azul"

        chat_log.append(f"⚪ Carta neutra revelada: {palavra}")
        chat_log.append(f"Agora é turno do time {turno.upper()}")

    return jsonify({
        "ok": True,
        "index": index,
        "cor": cor,
        "pontos": pontos,
        "turno": turno,
        "jogo_encerrado": jogo_encerrado,
        "vencedor": vencedor_jogo
    })

@app.route("/tempo")
def tempo():
    global tempo_restante, timer_ativo, turno

    if jogo_encerrado:
        return {
            "tempo": 0,
            "turno": turno,
            "ativo": False
        }

    if timer_ativo and tempo_restante > 0:
        tempo_restante -= 1

    elif tempo_restante == 0 and timer_ativo:
        timer_ativo = False
        turno = "vermelho" if turno == "azul" else "azul"
        chat_log.append(f"⏱️ Tempo esgotado! Agora é turno do time {turno}")

    return {
        "tempo": tempo_restante,
        "turno": turno,
        "ativo": timer_ativo
    }

@app.route("/status_sala")
def status_sala():
    return jsonify({
        "jogo_ativo": jogo_ativo,
        "versao_sala": versao_sala
    })

# =========================
# RODAR
# =========================
if __name__ == "__main__":
    app.run(debug=True)