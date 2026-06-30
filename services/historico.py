"""
historico.py — Histórico de relatórios via pasta PÚBLICA do Google Drive (somente leitura).

Modelo (Opção 3): o usuário organiza manualmente, na pasta pública do Drive, uma
subpasta por teste (ex.: "Teste Rota SP BH") contendo os arquivos CSV/XLS/KML.
O app apenas LISTA as subpastas e BAIXA os arquivos — não grava nada.

Requer, em st.secrets:
  [gdrive]
  api_key = "AIza..."           # API Key do Google (restrita à Drive API)
  folder_id = "ID_DA_PASTA_PUBLICA"

A pasta e suas subpastas devem estar com acesso "qualquer pessoa com o link".
"""
import io
import streamlit as st

_MIME_FOLDER = "application/vnd.google-apps.folder"


def disponivel() -> bool:
    """True se há API key e folder_id configurados."""
    try:
        g = st.secrets["gdrive"]
        return bool(g.get("api_key")) and bool(g.get("folder_id"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _servico():
    from googleapiclient.discovery import build
    api_key = st.secrets["gdrive"]["api_key"]
    return build("drive", "v3", developerKey=api_key, cache_discovery=False)


def _folder_id() -> str:
    return st.secrets["gdrive"]["folder_id"]


def listar() -> list:
    """
    Lista as subpastas (cada uma = um teste) dentro da pasta pública.
    Retorna [{nome, pasta_id}], ordenado por nome.
    """
    svc = _servico()
    raiz = _folder_id()
    q = f"'{raiz}' in parents and mimeType = '{_MIME_FOLDER}' and trashed = false"
    res = svc.files().list(
        q=q, fields="files(id,name)", spaces="drive",
        orderBy="name", pageSize=200,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    return [{"nome": f["name"], "pasta_id": f["id"]} for f in res.get("files", [])]


def listar_arquivos(pasta_id: str) -> list:
    """Lista os arquivos (não-pastas) de uma subpasta. Retorna [{nome, id}]."""
    svc = _servico()
    q = f"'{pasta_id}' in parents and trashed = false"
    res = svc.files().list(
        q=q, fields="files(id,name,mimeType)", spaces="drive", pageSize=200,
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    return [{"nome": f["name"], "id": f["id"]}
            for f in res.get("files", [])
            if f["mimeType"] != _MIME_FOLDER]


def baixar_arquivos(pasta_id: str) -> dict:
    """Baixa todos os arquivos de uma subpasta. Retorna {nome: bytes}."""
    svc = _servico()
    arqs = listar_arquivos(pasta_id)
    out = {}
    for a in arqs:
        out[a["nome"]] = _baixar_bytes(svc, a["id"])
    return out


def _baixar_bytes(svc, file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.getvalue()


# ── UI ────────────────────────────────────────────────────────────────────────
def painel_historico(st_mod, expandido=False):
    """
    Renderiza o seletor de histórico (independe de ter arquivos carregados).
    Ao escolher 'Abrir', coloca os bytes em session_state['hist_arquivos'] e
    dá rerun. Pode ser chamado no topo do app, antes do upload.
    """
    st = st_mod
    with st.expander("💾 Abrir um teste salvo no histórico (Google Drive)", expanded=expandido):
        if not disponivel():
            st.info(
                "Esta opção lê os testes de uma **pasta pública do Google Drive**. "
                "Cada subpasta da pasta de histórico é um teste (com CSV/XLS/KML).\n\n"
                "Para ativar, configure em *Settings → Secrets* no Streamlit Cloud:\n"
                "```toml\n[gdrive]\napi_key = \"SUA_API_KEY\"\nfolder_id = \"ID_DA_PASTA\"\n```\n"
                "A pasta e suas subpastas devem estar com acesso "
                "**\"qualquer pessoa com o link\"**.")
            return

        c1, c2 = st.columns([3, 1])
        with c1:
            busca = st.text_input("Pesquisar teste por nome", key="busca_hist",
                                  placeholder="Ex.: SP BH")
        with c2:
            st.write("")
            atualizar = st.button("🔄  Atualizar", key="btn_upd_hist",
                                  use_container_width=True)
        if atualizar or "hist_lista" not in st.session_state:
            try:
                with st.spinner("Lendo pasta do Drive..."):
                    st.session_state["hist_lista"] = listar()
            except Exception as e:
                st.error(f"Falha ao listar a pasta do Drive: {e}")
                st.session_state["hist_lista"] = []
        itens = st.session_state.get("hist_lista", [])
        if busca.strip():
            b = busca.lower()
            itens = [it for it in itens if b in it["nome"].lower()]
        if not itens:
            st.caption("Nenhum teste encontrado na pasta do histórico.")
        for it in itens:
            cI1, cI2 = st.columns([4, 1])
            with cI1:
                st.markdown(f"📁 **{it['nome']}**")
            with cI2:
                if st.button("Abrir", key=f"open_{it['pasta_id']}",
                             use_container_width=True):
                    try:
                        with st.spinner(f"Baixando '{it['nome']}'..."):
                            arqs = baixar_arquivos(it["pasta_id"])
                        if not arqs:
                            st.warning("Esta subpasta não contém arquivos.")
                        else:
                            st.session_state["hist_arquivos"] = arqs
                            st.session_state["hist_label"] = it["nome"]
                            for k in ("resultados", "ref_df", "comparacao", "df_resumo"):
                                st.session_state.pop(k, None)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Falha ao abrir: {e}")
