"""
historico.py — Histórico de relatórios via Google Drive (conta de serviço).

Permite salvar os arquivos originais (CSV/XLS/KML) de uma análise sob um
Projeto/Rota, e reabrir depois sem precisar dos arquivos em mãos.

Requer, em st.secrets:
  [gdrive]
  folder_id = "ID_DA_PASTA_COMPARTILHADA"
  # credenciais da conta de serviço (JSON), em [gdrive.service_account]
  [gdrive.service_account]
  type = "service_account"
  project_id = "..."
  private_key = "..."
  client_email = "...@...iam.gserviceaccount.com"
  ... (demais campos do JSON)

Sem credenciais, as funções retornam estados que a UI trata com mensagem amigável.
"""
import io
import json
import datetime as _dt
import streamlit as st

_SCOPES = ["https://www.googleapis.com/auth/drive"]
_MIME_FOLDER = "application/vnd.google-apps.folder"


def disponivel() -> bool:
    """True se há credenciais do Drive configuradas em st.secrets."""
    try:
        return "gdrive" in st.secrets and "folder_id" in st.secrets["gdrive"]
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _servico():
    """Cria o cliente do Drive a partir da conta de serviço (cacheado)."""
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    info = dict(st.secrets["gdrive"]["service_account"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _folder_id() -> str:
    return st.secrets["gdrive"]["folder_id"]


def _achar_ou_criar_pasta(svc, nome, pai):
    """Retorna o ID de uma subpasta (cria se não existir)."""
    q = (f"name = '{nome}' and '{pai}' in parents and "
         f"mimeType = '{_MIME_FOLDER}' and trashed = false")
    res = svc.files().list(q=q, fields="files(id,name)", spaces="drive").execute()
    achados = res.get("files", [])
    if achados:
        return achados[0]["id"]
    meta = {"name": nome, "mimeType": _MIME_FOLDER, "parents": [pai]}
    pasta = svc.files().create(body=meta, fields="id").execute()
    return pasta["id"]


def salvar(projeto: str, rota: str, arquivos: dict, meta_extra: dict = None) -> str:
    """
    Salva os arquivos originais sob <pasta_raiz>/<projeto>/<rota>__<timestamp>/.
    arquivos: dict {nome_arquivo: bytes}.
    Retorna o ID da subpasta criada.
    """
    from googleapiclient.http import MediaIoBaseUpload
    svc = _servico()
    raiz = _folder_id()
    proj_id = _achar_ou_criar_pasta(svc, projeto.strip() or "Sem Projeto", raiz)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_rota = f"{(rota.strip() or 'rota')}__{stamp}"
    rota_id = _achar_ou_criar_pasta(svc, nome_rota, proj_id)

    for nome, conteudo in arquivos.items():
        if conteudo is None:
            continue
        media = MediaIoBaseUpload(io.BytesIO(conteudo), mimetype="application/octet-stream",
                                  resumable=False)
        svc.files().create(body={"name": nome, "parents": [rota_id]},
                           media_body=media, fields="id").execute()

    # Grava um manifesto com metadados (projeto, rota, data, arquivos)
    manifesto = {
        "projeto": projeto, "rota": rota,
        "salvo_em": _dt.datetime.now().isoformat(timespec="seconds"),
        "arquivos": list(arquivos.keys()),
    }
    if meta_extra:
        manifesto.update(meta_extra)
    mb = io.BytesIO(json.dumps(manifesto, ensure_ascii=False, indent=2).encode("utf-8"))
    svc.files().create(
        body={"name": "_manifesto.json", "parents": [rota_id]},
        media_body=MediaIoBaseUpload(mb, mimetype="application/json"),
        fields="id").execute()
    return rota_id


def listar() -> list:
    """
    Lista as análises salvas. Retorna lista de dicts:
    {projeto, rota, salvo_em, pasta_id, arquivos:[nomes]}.
    """
    svc = _servico()
    raiz = _folder_id()
    # Projetos (subpastas da raiz)
    q_proj = f"'{raiz}' in parents and mimeType = '{_MIME_FOLDER}' and trashed = false"
    projetos = svc.files().list(q=q_proj, fields="files(id,name)", spaces="drive").execute().get("files", [])
    itens = []
    for proj in projetos:
        q_rota = f"'{proj['id']}' in parents and mimeType = '{_MIME_FOLDER}' and trashed = false"
        rotas = svc.files().list(q=q_rota, fields="files(id,name,createdTime)",
                                 spaces="drive", orderBy="createdTime desc").execute().get("files", [])
        for r in rotas:
            itens.append({
                "projeto": proj["name"], "pasta_id": r["id"],
                "rota_pasta": r["name"], "createdTime": r.get("createdTime", ""),
            })
    return itens


def carregar_manifesto(pasta_id: str) -> dict:
    """Lê o _manifesto.json de uma análise salva (se houver)."""
    svc = _servico()
    q = f"name = '_manifesto.json' and '{pasta_id}' in parents and trashed = false"
    achados = svc.files().list(q=q, fields="files(id)", spaces="drive").execute().get("files", [])
    if not achados:
        return {}
    conteudo = _baixar_bytes(svc, achados[0]["id"])
    try:
        return json.loads(conteudo.decode("utf-8"))
    except Exception:
        return {}


def baixar_arquivos(pasta_id: str) -> dict:
    """Baixa todos os arquivos (exceto manifesto) de uma análise. Retorna {nome: bytes}."""
    svc = _servico()
    q = f"'{pasta_id}' in parents and trashed = false"
    arqs = svc.files().list(q=q, fields="files(id,name,mimeType)", spaces="drive").execute().get("files", [])
    out = {}
    for a in arqs:
        if a["name"] == "_manifesto.json" or a["mimeType"] == _MIME_FOLDER:
            continue
        out[a["name"]] = _baixar_bytes(svc, a["id"])
    return out


def _baixar_bytes(svc, file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    req = svc.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.getvalue()
