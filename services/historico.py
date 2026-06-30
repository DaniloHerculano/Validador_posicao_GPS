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
