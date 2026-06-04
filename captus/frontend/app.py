"""
app.py — Frontend (Streamlit) do Captus

Segue o padrão das Aulas 5 e 6:
  - import streamlit as st, import requests, import pandas as pd
  - consome o backend FastAPI via HTTP
  - apresenta os dados em formato organizado e interativo

A URL do backend vem de variável de ambiente (BACKEND_URL). No Docker
Compose, os serviços se comunicam pelo NOME do serviço na rede interna
(ex.: http://backend:8000), conforme item 7.2 do roteiro.
"""

import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Captus CRM", page_icon="🎓", layout="wide")


# --------------------------------------------------------------------------- #
# Funções auxiliares de consumo da API
# --------------------------------------------------------------------------- #
def api_get(rota, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{rota}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Erro ao consultar {rota}: {e}")
        return None


def api_post(rota, payload):
    try:
        r = requests.post(f"{BACKEND_URL}{rota}", json=payload, timeout=5)
        if r.status_code >= 400:
            return False, r.json().get("detail", r.text)
        return True, r.json()
    except requests.RequestException as e:
        return False, str(e)


def api_patch(rota, payload):
    try:
        r = requests.patch(f"{BACKEND_URL}{rota}", json=payload, timeout=5)
        if r.status_code >= 400:
            return False, r.json().get("detail", r.text)
        return True, r.json()
    except requests.RequestException as e:
        return False, str(e)


# --------------------------------------------------------------------------- #
# Cabeçalho + status do banco
# --------------------------------------------------------------------------- #
st.title("🎓 Captus — CRM e Gestão de Turmas")
st.caption("MR Digital · Plataforma de CRM para o setor educacional")

status = api_get("/status")
if status:
    if status["banco_conectado"]:
        st.success(f"Banco conectado · Fonte: {status['fonte_de_dados']} — {status['detalhe']}")
    else:
        st.warning(f"Fonte de dados: {status['fonte_de_dados']} — {status['detalhe']}")

aba_funil, aba_cursos, aba_novo = st.tabs(["📊 Funil de Leads", "📚 Cursos e Turmas", "➕ Novo Lead"])


# --------------------------------------------------------------------------- #
# Aba Funil (REQF01, REQF02)
# --------------------------------------------------------------------------- #
with aba_funil:
    st.subheader("Pipeline de vendas")
    leads = api_get("/leads/") or []
    if leads:
        df = pd.DataFrame(leads)[["id", "nome", "email", "origem", "estagio"]]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("#### Distribuição por estágio")
        dist = df["estagio"].value_counts().rename_axis("estagio").reset_index(name="leads")
        st.bar_chart(dist.set_index("estagio"))

        st.markdown("#### Mover lead no funil (REQF02)")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            opcoes = {f'{l["nome"]} (#{l["id"]})': l["id"] for l in leads}
            escolha = st.selectbox("Lead", list(opcoes.keys()))
        with col2:
            novo_estagio = st.selectbox(
                "Novo estágio",
                ["Novo", "Contatado", "Negociando", "Matriculado", "Perdido"],
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("Mover"):
                ok, resp = api_patch(f"/leads/{opcoes[escolha]}/estagio",
                                     {"estagio": novo_estagio})
                if ok:
                    st.success(f"Lead movido para {novo_estagio}.")
                    st.rerun()
                else:
                    st.error(resp)
    else:
        st.info("Nenhum lead cadastrado.")


# --------------------------------------------------------------------------- #
# Aba Cursos e Turmas (REQF04, REQF05, REQF06)
# --------------------------------------------------------------------------- #
with aba_cursos:
    st.subheader("Oferta educacional")
    cursos = api_get("/cursos/") or []
    turmas = api_get("/turmas/") or []
    nomes_curso = {c["id"]: c["nome"] for c in cursos}

    if turmas:
        linhas = []
        for t in turmas:
            ocupadas = t.get("vagas_ocupadas", 0)
            total = t["vagas_totais"]
            linhas.append({
                "Turma": t["id"],
                "Curso": nomes_curso.get(t["curso_id"], "—"),
                "Início": t["data_inicio"],
                "Vagas": f'{ocupadas}/{total}',
                "Ocupação": f'{(ocupadas / total * 100):.0f}%',
                "Investimento (R$)": t["investimento"],
            })
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

        st.markdown("#### Matricular lead em turma (REQF06 → atualiza vagas REQF05)")
        leads = api_get("/leads/") or []
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            ol = {f'{l["nome"]} (#{l["id"]})': l["id"] for l in leads}
            lead_sel = st.selectbox("Lead", list(ol.keys()), key="mat_lead")
        with col2:
            ot = {f'#{t["id"]} · {nomes_curso.get(t["curso_id"], "")} ({t["data_inicio"]})': t["id"]
                  for t in turmas}
            turma_sel = st.selectbox("Turma", list(ot.keys()), key="mat_turma")
        with col3:
            st.write("")
            st.write("")
            if st.button("Matricular"):
                ok, resp = api_post("/matriculas/",
                                    {"lead_id": ol[lead_sel], "turma_id": ot[turma_sel]})
                if ok:
                    st.success("Matrícula registrada e vaga atualizada automaticamente.")
                    st.rerun()
                else:
                    st.error(resp)
    else:
        st.info("Nenhuma turma cadastrada.")


# --------------------------------------------------------------------------- #
# Aba Novo Lead (REQF01)
# --------------------------------------------------------------------------- #
with aba_novo:
    st.subheader("Cadastrar novo lead")
    nome = st.text_input("Nome")
    email = st.text_input("E-mail")
    telefone = st.text_input("Telefone (opcional)")
    origem = st.selectbox("Origem", ["Instagram", "Site Direto", "WhatsApp", "Indicação"])
    if st.button("Cadastrar lead"):
        if not nome or not email:
            st.warning("Nome e e-mail são obrigatórios.")
        else:
            payload = {"nome": nome, "email": email, "origem": origem}
            if telefone:
                payload["telefone"] = telefone
            ok, resp = api_post("/leads/", payload)
            if ok:
                st.success(f'Lead cadastrado com ID {resp["id"]}.')
            else:
                st.error(resp)
