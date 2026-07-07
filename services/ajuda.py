"""
ajuda.py — Conteúdo da seção "Como usar" exibida na plataforma.
"""
import base64
from pathlib import Path
import streamlit as st
from services.ui import sec

_ASSETS = Path(__file__).parent.parent / "assets"


def _img_b64(nome: str) -> str:
    caminho = _ASSETS / nome
    if caminho.exists():
        return base64.b64encode(caminho.read_bytes()).decode()
    return ""


def _print_passo(nome_arquivo: str, legenda: str, estreito: bool = False):
    """Exibe um print de passo com moldura e legenda.
    estreito=True para imagens verticais/quadradas (limita largura e centraliza)."""
    b64 = _img_b64(nome_arquivo)
    if not b64:
        return
    classe = "print-step print-step-narrow" if estreito else "print-step"
    st.markdown(
        f'<div class="{classe}">'
        f'<img src="data:image/png;base64,{b64}" alt="{legenda}"/>'
        f'<div class="print-cap">{legenda}</div></div>',
        unsafe_allow_html=True)


def render_ajuda():
    sec("Como usar a plataforma")

    st.markdown("""
Plataforma de análise de **testes de rodagem** de rastreadores. Além de comparar a
posição de um rastreador com **GPS ligado** (referência real) contra rastreadores com
**GPS desligado** (posição estimada por antena de celular) — medindo o erro e validando
se a posição caiu dentro do **raio de incerteza** do sistema —, a ferramenta também
analisa, para cada peça:

- **Rede e modem:** tecnologia (2G/3G/4G), operadora e banda/frequência utilizada;
- **Qualidade de GPS:** satélites e índices de precisão (quando o GPS está ligado);
- **Bateria:** nível e consumo ao longo do teste;
- **Movimento:** velocidade e direção;
- **Latência e buffer:** tempo de envio ao servidor, separando a transmissão em tempo
  real dos dados recuperados após perda de sinal.

Você pode usar o modo **Comparativo** (referência × amostras) ou o modo **Individual**
(inspecionar cada peça isoladamente, sem comparar). Também é possível **salvar e reabrir
testes** pelo Histórico e **exportar** um relatório completo em Excel.
""")

    # ── Os arquivos ──
    st.markdown("#### 📑 De onde vêm os dados")
    st.markdown("""
Há **duas maneiras** de fornecer os dados de cada rastreador. O app detecta
automaticamente qual você enviou.
""")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
<div class="help-card" style="border-color:#1f8b4c">
<div class="help-card-tag" style="background:#1f8b4c">RECOMENDADO</div>
<div class="help-card-title">① CSV do Gerenciamento de Firmware</div>
<p>Um <b>único arquivo</b> que já traz <b>tudo</b>: posição (real e estimada), raio de
incerteza, endereço, indicador de posição estimada, rede/operadora/banda, bateria,
latência e status de buffer.</p>
<p>Com ele, <b>não é preciso</b> o portal SSO nem os arquivos XLS/KML.</p>
<p><b>Onde baixar:</b><br>
<a href="http://websites01.positronrt.cloud/firmware/index.php?tipoparametro=diversosplanform" target="_blank">
Portal de Firmware → Diversos → Planilhas de Testes</a></p>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="help-card">
<div class="help-card-tag">ALTERNATIVA</div>
<div class="help-card-title">② XLS + KML do SSO</div>
<p>Caso você tenha acesso apenas ao <b>portal SSO</b>, pode usar o <b>XLS</b> (posição,
endereço, posição estimada, bateria) e o <b>KML</b> (raio de incerteza).</p>
<p><b>Atenção:</b> essa via <b>não traz os dados de rede</b> (2G/3G/4G, operadora,
banda), satélites nem latência — para isso é necessário o CSV. O XLS/KML cobrem
posição e raio, mas não o desempenho de comunicação.</p>
<p><b>Onde baixar:</b><br>
<a href="https://sso.pst.com.br/sso/" target="_blank">Portal SSO / PST</a> (exportar XLS e KML)</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
> **Em resumo:** o **CSV do firmware sozinho já basta** e é o caminho mais simples. O
> **XLS + KML do SSO** é uma alternativa para quem só tem o SSO, mas cobre menos coisas
> (sem rede, sem latência). Também é possível combinar os três arquivos antigos
> (CSV+XLS+KML) — o app une tudo por horário.
""")

    # ── Prints: onde extrair cada arquivo ──
    st.markdown("#### 📸 Onde extrair os arquivos (passo a passo)")

    st.markdown("**① CSV — [Portal de Firmware (Positron)]"
                "(http://websites01.positronrt.cloud/firmware/index.php?tipoparametro=diversosplanform)"
                " — o arquivo que já traz tudo:** "
                "acesse **Upload de arquivo → Diversos → Planilhas de Testes** (1, 2), "
                "escolha o tipo de consulta **\"Consulta carga posições e status\"** (3), "
                "informe o PIN e o período em UTC (4) e clique em **Consultar** (5).")
    _print_passo("config_websites01.png",
                 "Portal de Firmware — geração do CSV completo (Planilhas de Testes)",
                 estreito=True)

    st.markdown("**② XLS e KML — [Portal SSO/PST](https://sso.pst.com.br/sso/) — "
                "via alternativa (posição e raio, sem dados de rede):** "
                "na busca (1), marque **Localização** e "
                "**Posições estimadas** (2, 3), defina data/hora inicial e final e clique "
                "em **Consultar** (4).")
    _print_passo("config_sso.png",
                 "Portal SSO/PST — filtro de consulta (Localização + Posições estimadas)")

    st.markdown("Na aba **Resultado**, use **Exportar XLS** (1) para a posição "
                "e **Exportar KML** (2) para o raio de incerteza.")
    _print_passo("download_xls_kml_sso.png",
                 "Portal SSO/PST — exportação do XLS e do KML")

    # ── Como o app combina as fontes ──
    st.markdown("#### 🔗 Como o app usa cada fonte")
    st.markdown("""
**Se você usa o CSV do firmware:** ele já contém tudo, então o app lê um arquivo só e
pronto — posição, raio, rede, bateria, latência e buffer saem todos dele.

**Se você usa o XLS + KML do SSO:** o app pega a posição e o endereço do **XLS** e o
raio de incerteza do **KML**. Nesse caso, as abas que dependem de dados de comunicação
(Rede, Latência) ficam vazias, porque o SSO não fornece essas informações — elas só
existem no CSV.

**Se você combina os três arquivos antigos (CSV+XLS+KML):** o app une tudo pelo
horário mais próximo — posição e bateria do XLS, dados técnicos do CSV, raio do KML.

Em qualquer caso, o app mostra o que for possível com o que você forneceu.
""")

    # ── O KML e o raio ──
    st.markdown("#### 🎯 O KML e o raio do sistema")
    st.markdown("""
O **KML** (extraído do portal SSO/PST, no mesmo local do XLS) contém, para cada
posição estimada, o **raio de incerteza** que o próprio sistema calcula — no arquivo
aparece como, por exemplo, `Raio: 3012.0` (em metros; o app converte para km).

Esse raio representa a área onde o sistema afirma que o rastreador deveria estar.
A aba **Raio do Sistema** verifica, no mesmo horário já analisado, se a posição real
(da referência) caiu **dentro desse raio** — informando o percentual de acerto do
próprio sistema. É uma forma de validar o sistema de geolocalização atual.

> Sem o KML, todas as demais análises continuam funcionando; apenas a validação
> contra o raio do sistema fica indisponível.
""")

    # ── Exemplo de nomes ──
    st.markdown("#### 📁 Como nomear os arquivos")
    st.markdown("""
**Usando o CSV do firmware:** basta um arquivo por rastreador. O nome é livre, mas
ajuda identificar o equipamento — ex.: `RI720_623639301_com_fallback.csv`.

**Usando XLS + KML (ou os três arquivos):** os arquivos do **mesmo** rastreador devem
ter o **mesmo nome**, mudando só a extensão, para o app agrupá-los. Exemplo:
""")
    st.code(
        "RI130_623721833_teste.csv   ← dados técnicos (rede, latência...)\n"
        "RI130_623721833_teste.xls   ← posição e endereço (SSO)\n"
        "RI130_623721833_teste.kml   ← raio de incerteza (SSO)",
        language="text")
    st.markdown("Não é obrigatório ter todos — o app usa o que você fornecer.")

    # ── Passo a passo ──
    st.markdown("#### 🚀 Passo a passo")
    st.markdown("""
1. **Baixe os dados** de cada rastreador. O mais simples é o **CSV do Gerenciamento de
   Firmware**, que já traz tudo. (Alternativamente, XLS + KML do SSO.)
2. **Suba os arquivos** na seção *Importar Arquivos* — ou abra um teste salvo no
   **Histórico**.
3. **Escolha o modo**: *Comparativo* (referência × amostras) ou *Individual*
   (inspecionar cada peça isoladamente).
4. No modo comparativo, **escolha a referência** (rastreador com GPS ligado,
   normalmente o RI130) e marque quais comparar.
5. **Ajuste na barra lateral** a tolerância de horário e os raios de precisão
   (1 / 3 / 5 km, editáveis).
6. Clique em **Iniciar Análise** e navegue pelas abas.
7. Na aba **Dados & Export**, baixe o Excel com tabelas e gráficos.
""")

    # ── Modos de análise ──
    st.markdown("#### 🔀 Dois modos de análise")
    st.markdown("""
Ao carregar os arquivos, escolha o modo:

- **Comparativo** — compara um rastreador de **referência** (GPS ligado) contra as
  amostras estimadas, medindo a precisão da posição. É o modo para validar posicionamento.
- **Individual** — inspeciona **cada peça isoladamente** (consumo de bateria, rede e
  operadora, banda, qualidade de GPS, movimento, latência), **sem** precisar de
  referência nem comparação. Útil quando você quer só analisar uma peça — por exemplo,
  ver a bateria ou a rede que ela usou.
""")

    # ── O que cada aba mostra ──
    st.markdown("#### 📊 O que cada aba mostra")
    st.markdown("""
| Aba | Conteúdo | Precisa de |
|-----|----------|------------|
| **Visão Geral** | Resumo comparativo e erro médio | XLS (posição) |
| **Mapa** | Pontos no mapa + linhas de erro + calor | XLS (posição) |
| **Precisão GPS** | Erro em km, % por raio, endereços de maior erro | XLS (posição) |
| **Raio do Sistema** | % de pontos dentro do raio que o sistema informa | KML + XLS |
| **Rede & Operadora** | 2G/3G/4G, operadora, banda/frequência, UDP/SMS | CSV (técnico) |
| **Qualidade GPS** | Satélites, DOP, altitude | CSV (técnico) |
| **Movimento** | Velocidade, direção, sensor | CSV + XLS |
| **Bateria** | Nível e consumo | XLS ou CSV |
| **Latência** | Tempo módulo→servidor, buffer | CSV (técnico) |
| **Histórico** | Abrir testes salvos no Google Drive | — |
""")

    # ── Como o erro é medido ──
    st.markdown("#### 📐 Como o erro é medido")
    st.markdown("""
A distância entre o ponto estimado e o real é a **distância geodésica** (linha reta
sobre a curvatura da Terra, modelo WGS-84 — o mesmo do GPS). O app pareia cada ponto
estimado com o ponto real de **horário mais próximo** (dentro da tolerância) e mede
essa distância em km.

> **Atenção:** se os equipamentos estavam em movimento, parte do erro pode ser o
> deslocamento real do veículo entre os dois horários, não falha da estimativa. A
> coluna `dif_seg` nos dados sincronizados mostra essa defasagem de tempo.
""")

    # ── Histórico ──
    st.markdown("#### 💾 Histórico de testes (Google Drive)")
    st.markdown("""
Para evitar que cada pessoa precise enviar os arquivos de novo, é possível **abrir um
teste já salvo** numa pasta do Google Drive. O seletor fica no topo da página, na
seção *Importar Arquivos* → **"Abrir um teste salvo no histórico"**.

Como está organizado: dentro da pasta de histórico, **cada subpasta é um teste** (com
seus arquivos CSV / XLS / KML). Para abrir, basta selecionar o teste na lista e clicar
em **Abrir** — o app baixa os arquivos e roda a análise automaticamente.

Para **adicionar** um novo teste ao histórico, crie uma subpasta no Drive (ex.:
*Cliente X_Rota SP-BH_10.06-15.06*) e coloque nela os arquivos daquele teste. Na
próxima vez que abrir o seletor (ou clicar em *Atualizar*), o novo teste aparece para
toda a equipe.
""")

    st.caption("Stoneridge Brasil · Teste de Rodagem")


HELP_CSS = """
<style>
.help-card{background:#ffffff;border:1px solid #dce4ee;border-top:3px solid #dd0933;
  border-radius:10px;padding:1.1rem 1.3rem;height:100%;box-shadow:0 1px 3px rgba(44,57,70,.05);}
.help-card-tag{display:inline-block;background:#dd0933;color:#fff;font-family:'Barlow Condensed',sans-serif;
  font-weight:700;font-size:.72rem;letter-spacing:.1em;padding:2px 10px;border-radius:5px;margin-bottom:.5rem;}
.help-card-title{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:1.25rem;
  color:#2c3946;margin-bottom:.5rem;}
.help-card p{font-size:.86rem;color:#3a4a57;margin:.4rem 0;}
.help-card a{color:#dd0933;font-weight:600;text-decoration:none;}
.help-card a:hover{text-decoration:underline;}
.print-step{margin:.6rem 0 1.2rem 0;border:1px solid #dce4ee;border-radius:10px;
  overflow:hidden;background:#fff;box-shadow:0 1px 3px rgba(44,57,70,.06);}
.print-step img{width:100%;display:block;border-bottom:1px solid #eef2f7;}
.print-step-narrow img{max-width:380px;width:100%;margin:0 auto;border-bottom:none;}
.print-step-narrow{text-align:center;}
.print-step-narrow .print-cap{border-top:1px solid #eef2f7;text-align:left;}
.print-cap{font-size:.74rem;color:#6b7f8f;padding:.5rem .8rem;background:#f9fafb;}
</style>
"""
