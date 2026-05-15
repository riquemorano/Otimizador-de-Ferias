import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import itertools
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Otimizador de Férias", layout="wide", page_icon="📅")

# Inicialização de estados para persistência
if "custom_holidays" not in st.session_state:
    st.session_state.custom_holidays = []
if "disabled_holidays" not in st.session_state:
    st.session_state.disabled_holidays = set()
# Novos estados para o carregamento progressivo ("Lazy Load" via botão)
if "all_results" not in st.session_state:
    st.session_state.all_results = None
if "display_limit" not in st.session_state:
    st.session_state.display_limit = 15

# --- LÓGICA DE PARTIÇÃO ---
def gerar_todas_particoes(n, max_lotes):
    def particao(n, limite_lotes, min_val=1):
        if limite_lotes == 1:
            yield [n]
            return
        for i in range(min_val, n):
            for p in particao(n - i, limite_lotes - 1, i):
                yield [i] + p
    todas = []
    for i in range(1, max_lotes + 1):
        todas.extend(list(particao(n, i)))
    return todas

# --- DADOS DE FERIADOS ---
def get_holiday_source():
    # Tenta ler do arquivo local, se falhar usa a lista padrão do código original
    if os.path.exists("./data/feriados.csv"):
        try:
            return pd.read_csv("./data/feriados.csv").dropna(how='all')
        except:
            pass
    
    data = {
        "Categoria": ["Feriado"]*9,
        "Nome": ["Ano Novo", "Tiradentes", "Trabalhador", "Independencia", "Aparecida", "Finados", "Republica", "Consciência Negra", "Natal"],
        "Dia": [1, 21, 1, 7, 12, 2, 15, 20, 25],
        "Mes": [1, 4, 5, 9, 10, 11, 11, 11, 12]
    }
    return pd.DataFrame(data)

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

def get_filtered_holidays(ano_inicio, ano_fim):
    df = get_holiday_source()
    h_dict = {}
    
    # 1. Feriados Fixos
    for _, row in df.iterrows():
        nome = str(row['Nome'])
        d, m = int(row['Dia']), int(row['Mes'])
        h_id = f"fixo-{nome}-{d}-{m}" # ID único global para esse feriado
        
        if h_id not in st.session_state.disabled_holidays:
            for ano in range(ano_inicio, ano_fim + 1):
                h_dict[datetime(ano, m, d).date()] = nome

    # 2. Feriados Móveis
    for ano in range(ano_inicio, ano_fim + 1):
        p = calcular_pascoa(ano)
        for nome, offset in [("Páscoa", 0), ("Paixão de Cristo", -2), ("Carnaval", -47), ("Corpus Christi", 60)]:
            dt = p + timedelta(days=offset)
            h_id_moveil = f"moveil-{nome}" # ID por nome para desativar em todos os anos
            if h_id_moveil not in st.session_state.disabled_holidays:
                h_dict[dt] = nome
            
    # 3. Feriados Customizados
    for h in st.session_state.custom_holidays:
        h_dict[h["data"]] = h["nome"]
        
    return h_dict

# --- MOTOR DE CÁLCULO ---
def calculate_detail(period, start_date, holiday_dict, dias_folga):
    # O período de folga começa na data escolhida
    first_day = start_date
    last_day = start_date + timedelta(days=max(0, period - 1))

    # Expansão para trás: se o dia anterior for dia de folga rotineira ou feriado ATIVO
    while True:
        prev = first_day - timedelta(days=1)
        if prev.weekday() in dias_folga or prev in holiday_dict:
            first_day = prev
        else:
            break

    # Expansão para frente: se o dia posterior for dia de folga rotineira ou feriado ATIVO
    while True:
        nxt = last_day + timedelta(days=1)
        if nxt.weekday() in dias_folga or nxt in holiday_dict:
            last_day = nxt
        else:
            break

    total_days = (last_day - first_day).days + 1
    
    # Contagem rigorosa baseada apenas no que está no holiday_dict
    feriados_list = [d for d in (first_day + timedelta(n) for n in range(total_days)) if d in holiday_dict]
    feriados = len(feriados_list)
    # Contagem de folgas rotineiras (FDS ou dias escolhidos)
    fds = sum(1 for d in (first_day + timedelta(n) for n in range(total_days)) if d.weekday() in dias_folga and d not in holiday_dict)
    
    eficiencia = (total_days / period * 100) if period > 0 else float("inf")
    
    return {
        "periodo": period, "inicio": start_date, "inicio_real": first_day,
        "fim_real": last_day, "qtd_total": total_days, "feriados": feriados,
        "fds": fds, "eficiencia": eficiencia
    }

# --- INTERFACE ---
with st.sidebar:
    st.header("⚙️ Configurações")
    total_dias = st.number_input("Dias totais de férias", value=30, min_value=0)
    modo = st.radio("Divisão", ["Manual", "Automático"])
    if modo == "Manual":
        n_lotes = st.slider("Lotes", 1, 5, 2)
        lotes = [st.number_input(f"Lote {i+1}", 0, 30, total_dias//n_lotes) for i in range(n_lotes)]
        if sum(lotes) != total_dias: st.error("Soma incorreta!"); st.stop()
        configs = [lotes]
    else:
        max_l = st.select_slider("Máximo de Lotes", options=[1, 2, 3], value=2)
        configs = gerar_todas_particoes(total_dias, max_l)
    
    st.divider()
    st.header("🔍 Filtros")
    d_ini = st.date_input("Início", datetime.now().date())
    d_fim = st.date_input("Fim", datetime.now().date() + timedelta(days=365))
    
    # Novo seletor de dias úteis
    st.subheader("Dias Úteis da Semana")
    dias_semana_opcoes = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dias_uteis_selecionados = st.multiselect(
        "Selecione os dias em que você trabalha:",
        options=dias_semana_opcoes,
        default=["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    )
    
    # Mapeamento do nome do dia para o índice do weekday() no Python (0 = Segunda ... 6 = Domingo)
    mapa_dias = {"Segunda": 0, "Terça": 1, "Quarta": 2, "Quinta": 3, "Sexta": 4, "Sábado": 5, "Domingo": 6}
    # Descobre os dias de folga (o inverso do que o usuário selecionou)
    dias_folga_int = [mapa_dias[d] for d in dias_semana_opcoes if d not in dias_uteis_selecionados]

    meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    m_sel = st.multiselect("Meses permitidos para início", meses_nomes, default=meses_nomes)

st.title("🏝️ Férias Smart")

# --- CENTRAL DE GERENCIAMENTO ---
with st.expander("📅 Ativar/Desativar Feriados", expanded=False):
    df_source = get_holiday_source()
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Feriados do Calendário")
        # Feriados Fixos
        for _, row in df_source.iterrows():
            nome, d, m = row['Nome'], row['Dia'], row['Mes']
            h_id = f"fixo-{nome}-{d}-{m}"
            checked = h_id not in st.session_state.disabled_holidays
            if not st.checkbox(f"{nome} ({d}/{m})", value=checked, key=f"cb_{h_id}"):
                st.session_state.disabled_holidays.add(h_id)
            else:
                st.session_state.disabled_holidays.discard(h_id)
        
        # Feriados Móveis
        for m_nome in ["Carnaval", "Paixão de Cristo", "Corpus Christi"]:
            h_id_m = f"moveil-{m_nome}"
            checked_m = h_id_m not in st.session_state.disabled_holidays
            if not st.checkbox(f"{m_nome} (Móvel)", value=checked_m, key=f"cb_{h_id_m}"):
                st.session_state.disabled_holidays.add(h_id_m)
            else:
                st.session_state.disabled_holidays.discard(h_id_m)

    with c2:
        st.subheader("Customizados")
        n_c = st.text_input("Nome")
        d_c = st.date_input("Data", key="add_c")
        if st.button("Adicionar"):
            st.session_state.custom_holidays.append({"nome": n_c, "data": d_c})
            st.rerun()
        for idx, h in enumerate(st.session_state.custom_holidays):
            ct, cd = st.columns([4, 1])
            ct.write(f"📌 {h['nome']} - {h['data'].strftime('%d/%m')}")
            if cd.button("🗑️", key=f"del_{idx}"):
                st.session_state.custom_holidays.pop(idx); st.rerun()

# --- PROCESSAMENTO ---
h_dict = get_filtered_holidays(d_ini.year, d_fim.year)

if st.button("🚀 Calcular Possibilidades"):
    with st.spinner("Analisando..."):
        all_results_temp = []
        for config in configs:
            for p_config in set(itertools.permutations(config)):
                # Redução de amostragem para evitar lentidão extrema no modo Automático
                passo = 1 if len(p_config) < 3 else 3 
                for i in range(0, (d_fim - d_ini).days + 1, passo):
                    s_date = d_ini + timedelta(days=i)
                    if meses_nomes[s_date.month - 1] not in m_sel: continue
                    
                    # No modo 0 dias, só faz sentido se a data for feriado ou colada em um
                    if total_dias == 0 and s_date not in h_dict and s_date.weekday() not in dias_folga_int:
                        continue

                    comb, curr, valid = [], s_date, True
                    for lote in p_config:
                        det = calculate_detail(lote, curr, h_dict, dias_folga_int)
                        if det["fim_real"] > d_fim: valid = False; break
                        comb.append(det)
                        curr = det["fim_real"] + timedelta(days=2) # Intervalo mínimo
                    
                    if valid:
                        total_g = sum(x["qtd_total"] for x in comb)
                        efi_m = sum(x["eficiencia"] for x in comb)/len(p_config)
                        all_results_temp.append({
                            "total": total_g, "efici": efi_m, "comb": comb, 
                            "config": "-".join(map(str, p_config))
                        })

        # Salva todos os resultados ordenados no Session State e reseta o limite visual
        st.session_state.all_results = sorted(all_results_temp, key=lambda x: (x["total"], x["efici"]), reverse=True)
        st.session_state.display_limit = 15

# --- RENDERIZAÇÃO DOS RESULTADOS ---
# Como a renderização está fora do 'if st.button', ela sobrevive a recarregamentos de página (ao clicar em "Carregar mais")
if st.session_state.all_results is not None:
    resultados = st.session_state.all_results
    limite = st.session_state.display_limit
    
    if not resultados:
        st.warning("Nenhuma combinação encontrada.")
    else:
        st.success(f"🎉 Foram encontradas {len(resultados)} combinações possíveis! Exibindo ordenado da melhor para a pior.")
        
        # Exibe apenas a quantidade definida no 'limite'
        for idx, r in enumerate(resultados[:limite]):
            with st.container(border=True):
                st.subheader(f"Opção #{idx+1} — Divisão: {r['config']} | Total: {r['total']} dias")
                st.table(pd.DataFrame([{ 
                    "Lote": f"{p['periodo']}d", 
                    "Início": p["inicio"].strftime("%d/%m/%y"), 
                    "Janela Real": f"{p['inicio_real'].strftime('%d/%m')}—{p['fim_real'].strftime('%d/%m')}", 
                    "Feriados": p["feriados"], 
                    "FDS/Folga": p["fds"], 
                    "Eficiência": f"{p['eficiencia']:.0f}%" if p['eficiencia'] != float('inf') else "Inf%", 
                    "Ganho": f"+{p['qtd_total']}d" 
                } for p in r["comb"]]))
        
        # Botão para expandir a lista
        if limite < len(resultados):
            st.write(f"Mostrando {limite} de {len(resultados)} opções.")
            if st.button("🔽 Carregar mais 15 opções", use_container_width=True):
                st.session_state.display_limit += 15
                st.rerun()