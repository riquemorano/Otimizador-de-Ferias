import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import itertools

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Otimizador de Férias", layout="wide", page_icon="📅")

if "custom_holidays" not in st.session_state:
    st.session_state.custom_holidays = []


def gerar_todas_particoes(n, max_lotes):
    """Gera todas as combinações de somas que resultam em N, limitado ao número de lotes."""

    def particao(n, limite_lotes, min_val=1):
        if limite_lotes == 1:
            yield [n]
            return
        for i in range(min_val, n):
            for p in particao(n - i, limite_lotes - 1, i):
                yield [i] + p

    todas = []
    for i in range(1, max_lotes + 1):
        # Usamos set para evitar permutações duplicadas e depois convertemos para listas
        # Ex: [10, 20] e [20, 10] são testados via busca de data, então pegamos a base
        res = list(particao(n, i))
        todas.extend(res)
    return todas


# --- CONSTANTES ---
CSV_ANUAL = """Categoria,Nome,Dia,Mes
Feriado,Ano Novo,1,1
Feriado,Aniversário de Sao Paulo,25,1
Feriado,Tiradentes,21,4
Feriado,Dia do Trabalhador,1,5
Feriado,Revolucao Constitucionalista,9,7
Feriado,Independencia do Brasil,7,9
Feriado,Nossa Senhora Aparecida,12,10
Feriado,Finados,2,11
Feriado,Proclamacao da Republica,15,11
Feriado,Dia da Consiencia Negra,20,11
Feriado,Natal,25,12"""


# --- UTILITÁRIOS DE DATA ---
def calcular_pascoa(ano):
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(ano, mes, dia).date()


def get_all_holidays(ano_inicio, ano_fim):
    h_list = []
    for line in CSV_ANUAL.split("\n")[1:]:
        cat, nome, d, m = line.split(",")
        for ano in range(ano_inicio, ano_fim + 1):
            dt = datetime(ano, int(m), int(d)).date()
            h_list.append({"nome": nome, "data": dt, "tipo": "Padrão"})
    for ano in range(ano_inicio, ano_fim + 1):
        p = calcular_pascoa(ano)
        moveis = [
            ("Páscoa", 0),
            ("Paixão de Cristo", -2),
            ("Carnaval", -47),
            ("Corpus Christi", 60),
        ]
        for nome, offset in moveis:
            dt = p + timedelta(days=offset)
            h_list.append({"nome": nome, "data": dt, "tipo": "Padrão"})
    for h in st.session_state.custom_holidays:
        h_list.append({"nome": h["nome"], "data": h["data"], "tipo": "Criado"})
    return h_list


def calculate_detail(period, start_date, holiday_dict):
    first_day = start_date
    if period > 0:
        if start_date.weekday() == 0:
            first_day -= timedelta(days=2)
        elif start_date.weekday() == 6:
            first_day -= timedelta(days=1)
    last_day_vacation = start_date + timedelta(days=max(0, period - 1))
    last_day = last_day_vacation
    if period > 0:
        if last_day_vacation.weekday() == 4:
            last_day += timedelta(days=2)
        elif last_day_vacation.weekday() == 5:
            last_day += timedelta(days=1)
    while (first_day - timedelta(days=1)) in holiday_dict:
        first_day -= timedelta(days=1)
    while (last_day + timedelta(days=1)) in holiday_dict:
        last_day += timedelta(days=1)
    total_days = (last_day - first_day).days + 1
    feriados, fds = 0, 0
    curr = first_day
    while curr <= last_day:
        if curr in holiday_dict:
            feriados += 1
        elif curr.weekday() >= 5:
            fds += 1
        curr += timedelta(days=1)
    eficiencia = (total_days / period * 100) if period > 0 else float("inf")
    return {
        "periodo": period,
        "inicio": start_date,
        "inicio_real": first_day,
        "fim_real": last_day,
        "qtd_total": total_days,
        "feriados": feriados,
        "fds": fds,
        "eficiencia": eficiencia,
    }


# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    total_dias = st.number_input("Dias totais de férias", value=30, min_value=0)
    modo_busca = st.radio(
        "Modo de Divisão",
        ["Manual (Eu defino os lotes)", "Automático (Explodir Combinações)"],
    )

    if modo_busca == "Manual (Eu defino os lotes)":
        num_lotes = st.slider("Quantidade de Lotes", 1, 5, 2)
        lotes_input = [
            st.number_input(f"Dias no Lote {i+1}", 0, 30, total_dias // num_lotes)
            for i in range(num_lotes)
        ]
        if sum(lotes_input) != total_dias:
            st.error(f"Soma incorreta ({sum(lotes_input)}/{total_dias}).")
            st.stop()
        configuracoes_para_testar = [lotes_input]
    else:
        max_l = st.select_slider(
            "Máximo de Lotes para testar", options=[1, 2, 3, 4, 5], value=2
        )
        configuracoes_para_testar = gerar_todas_particoes(total_dias, max_l)
        st.info(
            f"Testando {len(configuracoes_para_testar)} divisões matemáticas possíveis."
        )

    st.divider()
    st.header("🔍 Filtros")
    data_inicio_filtro = st.date_input("A partir de:", datetime.now().date())
    data_fim_filtro = st.date_input("Até:", datetime.now().date() + timedelta(days=365))
    meses_nomes = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    meses_selecionados = st.multiselect(
        "Meses permitidos:", meses_nomes, default=meses_nomes
    )

# --- ÁREA PRINCIPAL ---
st.title("🏝️ Férias Smart 3.0")

all_h = get_all_holidays(2026, 2027)
h_dict = {h["data"]: h["nome"] for h in all_h}

# --- BUSCA ---
all_results = []
diff_dias = (data_fim_filtro - data_inicio_filtro).days

if st.button("🚀 Calcular Todas as Possibilidades"):
    with st.spinner(
        "Isso pode demorar um pouco. Processando milhares de combinações..."
    ):
        for config in configuracoes_para_testar:
            # Testamos também a inversão da configuração (ex: 1-29 e 29-1)
            permutacoes = set(itertools.permutations(config))
            for p_config in permutacoes:
                for i in range(diff_dias + 1):
                    s_date = data_inicio_filtro + timedelta(days=i)
                    if meses_nomes[s_date.month - 1] not in meses_selecionados:
                        continue

                    comb, curr, valid = [], s_date, True
                    for lote in p_config:
                        det = calculate_detail(lote, curr, h_dict)
                        if det["fim_real"] > data_fim_filtro:
                            valid = False
                            break
                        comb.append(det)
                        # Intervalo mínimo de 1 dia entre lotes para não fundir as férias
                        curr = det["fim_real"] + timedelta(days=2)

                    if valid:
                        total_ganho = sum(x["qtd_total"] for x in comb)
                        eficiencia_media = sum(x["eficiencia"] for x in comb) / len(
                            p_config
                        )
                        all_results.append(
                            {
                                "total": total_ganho,
                                "efici": eficiencia_media,
                                "comb": comb,
                                "config_str": "-".join(map(str, p_config)),
                            }
                        )

    top = sorted(all_results, key=lambda x: (x["total"], x["efici"]), reverse=True)[:20]

    if not top:
        st.warning("Nenhuma combinação encontrada.")
    else:
        st.success(f"🏆 Melhor divisão encontrada: **{top[0]['config_str']}**")
        for idx, r in enumerate(top):
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                col_a.subheader(f"Opção #{idx+1} — Divisão: {r['config_str']}")
                col_b.metric("Ganho Total", f"{r['total']} dias")

                df_res = pd.DataFrame(
                    [
                        {
                            "Lote": f"{p['periodo']}d",
                            "Início": p["inicio"].strftime("%d de %b de %Y"),
                            "Janela Real": f"{p['inicio_real'].strftime('%d de %b de %Y')} — {p['fim_real'].strftime('%d de %b de %Y')}",
                            "Feriados": p["feriados"],
                            "FDS": p["fds"],
                            "Eficiência": (
                                f"{p['eficiencia']:.0f}%"
                                if p["eficiencia"] != float("inf")
                                else "Infinity%"
                            ),
                            "Ganho": f"+{p['qtd_total']}d",
                        }
                        for p in r["comb"]
                    ]
                )
                st.table(df_res)
else:
    st.info(
        "Ajuste as configurações na lateral e clique no botão acima para iniciar a busca exaustiva."
    )
