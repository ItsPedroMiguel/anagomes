import requests
import streamlit as st

st.set_page_config(page_title="Alterar Preço por SKU", layout="centered")
st.title("Alterar Preço por SKU")

WC_URL = st.secrets.get("WC_URL", "").rstrip("/")
WC_KEY = st.secrets.get("WC_CONSUMER_KEY", "")
WC_SECRET = st.secrets.get("WC_CONSUMER_SECRET", "")

if not (WC_URL and WC_KEY and WC_SECRET):
    st.error("Faltam credenciais. Define WC_URL, WC_CONSUMER_KEY e WC_CONSUMER_SECRET em .streamlit/secrets.toml")
    st.stop()

API_BASE = f"{WC_URL}/wp-json/wc/v3"

session = requests.Session()
session.auth = (WC_KEY, WC_SECRET)
session.headers.update({"Content-Type": "application/json"})


def wc_get_product_by_sku(sku: str):
    url = f"{API_BASE}/products"
    r = session.get(url, params={"sku": sku, "per_page": 1}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else None


def wc_update_product_price(product_id: int, new_price: float):
    url = f"{API_BASE}/products/{product_id}"
    payload = {"regular_price": f"{new_price:.2f}"}
    r = session.put(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


sku = st.text_input("SKU do produto").strip()

col1, col2 = st.columns(2)
with col1:
    btn_search = st.button("Procurar produto", use_container_width=True)
with col2:
    st.caption("")

if "produto" not in st.session_state:
    st.session_state["produto"] = None

if btn_search and sku:
    try:
        produto = wc_get_product_by_sku(sku)
        if not produto:
            st.session_state["produto"] = None
            st.error("SKU não encontrado.")
        else:
            st.session_state["produto"] = produto
            st.success("Produto encontrado.")
    except requests.HTTPError as e:
        st.session_state["produto"] = None
        st.error(f"Erro HTTP ao consultar WooCommerce: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        st.session_state["produto"] = None
        st.error(f"Erro inesperado: {e}")

produto = st.session_state["produto"]

if produto:
    st.divider()

    product_id = produto.get("id")
    nome = produto.get("name", "-")
    preco_atual = produto.get("regular_price") or produto.get("price") or "—"
    status = produto.get("status", "-")
    permalink = produto.get("permalink", "")

    # ✅ IMAGEM DO PRODUTO (primeira imagem)
    images = produto.get("images", [])
    if images and images[0].get("src"):
        st.image(images[0]["src"], caption=nome, use_container_width=True)
    else:
        st.info("Este produto não tem imagem definida.")

    st.write(f"**Nome:** {nome}")
    st.write(f"**Preço atual:** {preco_atual} €")
    st.write(f"**Status:** {status}")

    st.divider()

    novo_preco = st.number_input(
        "Novo preço (€)",
        min_value=0.0,
        step=0.5,
        format="%.2f",
        value=float(preco_atual) if str(preco_atual).replace(".", "", 1).isdigit() else 0.0
    )

    colA, colB = st.columns(2)
    with colA:
        atualizar = st.button("Atualizar preço", type="primary", use_container_width=True)
    with colB:
        st.warning("Confirma bem o valor antes de atualizar.")

    if atualizar:
        try:
            atualizado = wc_update_product_price(product_id, float(novo_preco))
            st.success("Preço atualizado com sucesso.")
            st.session_state["produto"] = atualizado
            st.write(f"**Novo preço guardado:** {atualizado.get('regular_price', '—')} €")
        except requests.HTTPError as e:
            st.error(f"Erro HTTP ao atualizar: {e.response.status_code} — {e.response.text}")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
else:
    if sku:
        st.info("Clica em **Procurar produto** para carregar os dados.")