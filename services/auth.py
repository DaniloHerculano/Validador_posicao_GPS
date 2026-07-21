"""
auth.py — Tela de login simples (credenciais fixas) para restringir o acesso.
Padrão visual Stoneridge: logo, vermelho, layout centralizado.
"""
import base64
from pathlib import Path
import streamlit as st

# Credenciais fixas (provisórias)
_USUARIO = "validapst"
_SENHA = "123456"

# Versão corrente do sistema (exibida na tela de login)
VERSAO = "0.11.4"


def _logo_b64() -> str:
    caminho = Path(__file__).parent.parent / "assets" / "stoneridge_logo.png"
    if caminho.exists():
        return base64.b64encode(caminho.read_bytes()).decode()
    return ""


_LOGIN_CSS = """
<style>
/* Esconde sidebar e cabeçalho do Streamlit na tela de login */
section[data-testid="stSidebar"], header[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 3.5rem !important; max-width: 460px !important; }

.login-card{
  background:#ffffff;border:1px solid #dce4ee;border-radius:16px;
  padding:2.4rem 2.2rem;box-shadow:0 18px 50px rgba(44,57,70,.18);
  margin:0 auto;}
.login-logo{text-align:center;margin-bottom:1.4rem;}
.login-logo img{max-height:54px;}
.login-title{font-family:'Barlow Condensed',sans-serif;font-size:1.7rem;font-weight:800;
  color:#2c3946;text-align:center;line-height:1.1;}
.login-sub{font-size:.82rem;color:#6b7f8f;text-align:center;margin-top:.2rem;margin-bottom:1.6rem;}
.login-strip{height:4px;background:linear-gradient(90deg,#2c3946,#dd0933);
  border-radius:3px;margin-bottom:1.6rem;}
.login-sec{text-align:center;font-size:.72rem;color:#6b7f8f;margin-top:1.3rem;}
</style>
"""


def _render_form() -> bool:
    """Desenha o formulário e retorna True se autenticou agora."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    b64 = _logo_b64()
    logo_html = (f'<div class="login-logo"><img src="data:image/png;base64,{b64}"/></div>'
                 if b64 else "")
    st.markdown(
        f'<div class="login-card">{logo_html}'
        f'<div class="login-title">Pósitron Rastreamento</div>'
        f'<div class="login-sub">Testes de Rodagem · Validação e Análise · Stoneridge Brasil</div>'
        f'<div class="login-strip"></div></div>',
        unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        entrar = st.form_submit_button("🔒  Entrar")

    if entrar:
        if usuario.strip() == _USUARIO and senha == _SENHA:
            st.session_state["autenticado"] = True
            return True
        else:
            st.error("Credenciais inválidas. Verifique usuário e senha.")

    st.markdown(f'<div class="login-sec">🔐 Acesso restrito — uso interno Stoneridge'
                f'<br><br>Versão {VERSAO}</div>',
                unsafe_allow_html=True)
    return False


def exigir_login():
    """
    Gate de autenticação. Se não estiver logado, mostra a tela de login e
    interrompe o restante do app. Chame logo no início do app.py.
    """
    if st.session_state.get("autenticado"):
        return
    autenticou = _render_form()
    if autenticou:
        st.rerun()
    st.stop()


def botao_sair():
    """Botão de logout para colocar na sidebar."""
    if st.button("🚪  Sair", key="logout", width='stretch'):
        st.session_state["autenticado"] = False
        st.rerun()
