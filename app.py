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
# Estados para o carregamento progressivo e listagem
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
    
    for _, row in df.iterrows():
        nome = str(row['Nome'])
        d, m = int(row['Dia']), int(row['Mes'])
        h_id = f"fixo-{nome}-{d}-{m}" 
        
        if h_id not in st.session_state.disabled_holidays:
            for ano in range(ano_inicio, ano_fim + 1):
                h_dict[datetime(ano, m, d).date()] = nome

    for ano in range(ano_inicio, ano_fim + 1):
        p = calcular_pascoa(ano)
        for nome, offset in [("Páscoa", 0), ("Paixão de Cristo", -2), ("Carnaval", -47), ("Corpus Christi", 60)]:
            dt = p + timedelta(days=offset)
            h_id_moveil = f"moveil-{nome}"
            if h_id_moveil not in st.session_state.disabled_holidays:
                h_dict[dt] = nome
            
    for h in st.session_state.custom_holidays:
        h_dict[h["data"]] = h["nome"]
        
    return h_dict

# --- MOTOR DE CÁLCULO ---
def calculate_detail(period, start_date, holiday_dict, dias_folga):
    first_day = start_date
    last_day = start_date + timedelta(days=max(0, period - 1))

    while True:
        prev = first_day - timedelta(days=1)
        if prev.weekday() in dias_folga or prev in holiday_dict:
            first_day = prev
        else:
            break

    while True:
        nxt = last_day + timedelta(days=1)
        if nxt.weekday() in dias_folga or nxt in holiday_dict:
            last_day = nxt
        else:
            break

    total_days = (last_day - first_day).days + 1
    
    feriados_list = [d for d in (first_day + timedelta(n) for n in range(total_days)) if d in holiday_dict]
    feriados = len(feriados_list)
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
    st.header("🔍 Filtros Base")
    d_ini = st.date_input("Início", datetime.now().date())
    d_fim = st.date_input("Fim", datetime.now().date() + timedelta(days=365))
    
    st.subheader("Calendário de Trabalho")
    dias_semana_opcoes = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    mapa_dias = {"Segunda": 0, "Terça": 1, "Quarta": 2, "Quinta": 3, "Sexta": 4, "Sábado": 5, "Domingo": 6}

    dias_uteis_selecionados = st.multiselect(
        "Dias em que você trabalha:",
        options=dias_semana_opcoes,
        default=["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    )
    dias_folga_int = [mapa_dias[d] for d in dias_semana_opcoes if d not in dias_uteis_selecionados]

    # Restrição de dias de início
    st.subheader("Restrição de Início")
    dias_inicio_permitidos = st.multiselect(
        "As férias podem começar em qual dia da semana?",
        options=dias_semana_opcoes,
        default=dias_semana_opcoes,
        help="Filtra a data de início oficial do lote de férias."
    )
    dias_inicio_int = [mapa_dias[d] for d in dias_inicio_permitidos]

    meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    m_sel = st.multiselect("Meses permitidos para início", meses_nomes, default=meses_nomes)

st.title("🏝️ Férias Smart")

# --- CENTRAL DE GERENCIAMENTO ---
with st.expander("📅 Ativar/Desativar Feriados", expanded=False):
    df_source = get_holiday_source()
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Feriados do Calendário")
        for _, row in df_source.iterrows():
            nome, d, m = row['Nome'], row['Dia'], row['Mes']
            h_id = f"fixo-{nome}-{d}-{m}"
            checked = h_id not in st.session_state.disabled_holidays
            if not st.checkbox(f"{nome} ({d}/{m})", value=checked, key=f"cb_{h_id}"):
                st.session_state.disabled_holidays.add(h_id)
            else:
                st.session_state.disabled_holidays.discard(h_id)
        
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

if st.button("🚀 Calcular Possibilidades", type="primary"):
    with st.spinner("Analisando..."):
        all_results_temp = []
        seen_signatures = set() 
        
        for config in configs:
            for p_config in set(itertools.permutations(config)):
                passo = 1 if len(p_config) < 3 else 2 
                for i in range(0, (d_fim - d_ini).days + 1, passo):
                    s_date = d_ini + timedelta(days=i)
                    
                    if meses_nomes[s_date.month - 1] not in m_sel: continue
                    if s_date.weekday() not in dias_inicio_int: continue
                    
                    if total_dias == 0 and s_date not in h_dict and s_date.weekday() not in dias_folga_int:
                        continue

                    comb, curr, valid = [], s_date, True
                    for lote in p_config:
                        det = calculate_detail(lote, curr, h_dict, dias_folga_int)
                        if det["fim_real"] > d_fim: valid = False; break
                        comb.append(det)
                        curr = det["fim_real"] + timedelta(days=2) 
                    
                    if valid:
                        assinatura = tuple((x["inicio_real"], x["fim_real"]) for x in comb)
                        
                        if assinatura not in seen_signatures:
                            seen_signatures.add(assinatura)
                            
                            total_g = sum(x["qtd_total"] for x in comb)
                            efi_m = sum(x["eficiencia"] for x in comb)/len(p_config)
                            total_fer = sum(x["feriados"] for x in comb)
                            total_folgas = sum(x["fds"] for x in comb)
                            data_inicio_real = comb[0]["inicio_real"] 
                            
                            all_results_temp.append({
                                "total": total_g, 
                                "efici": efi_m, 
                                "total_feriados": total_fer,
                                "total_fds": total_folgas,
                                "data_inicio": data_inicio_real,
                                "comb": comb, 
                                "config": "-".join(map(str, p_config))
                            })

        st.session_state.all_results = sorted(all_results_temp, key=lambda x: (x["total"], x["efici"]), reverse=True)
        st.session_state.display_limit = 15

# --- RENDERIZAÇÃO DOS RESULTADOS COM FILTRO/ORDENAÇÃO ---
if st.session_state.all_results is not None:
    st.divider()
    st.subheader("🎯 Refinar Resultados")
    
    mapa_campos = {
        "Total de Dias (Janela Real)": "total",
        "Eficiência Média (%)": "efici",
        "Ordem Cronológica (Data de Início)": "data_inicio",
        "Qtd. de Feriados Alcançados": "total_feriados",
        "Qtd. de FDS/Folgas Alcançados": "total_fds"
    }
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        campo_ord_label = st.selectbox("Ordenar resultados por:", list(mapa_campos.keys()))
        campo_ord = mapa_campos[campo_ord_label]
        
    with f_col2:
        ordem_direcao = st.radio("Ordem:", ["Maior para Menor", "Menor para Maior"])
        reverso = True if ordem_direcao == "Maior para Menor" else False
        
    with f_col3:
        campos_filtro_nomes = {k: v for k, v in mapa_campos.items() if v != "data_inicio"}
        campo_filtro_label = st.selectbox("Filtrar resultados por:", ["Nenhum"] + list(campos_filtro_nomes.keys()))
        
    with f_col4:
        if campo_filtro_label != "Nenhum":
            condicao = st.selectbox("Condição:", ["Maior ou igual a", "Menor ou igual a", "Igual a"])
            valor_filtro = st.number_input("Valor:", value=0.0, step=1.0)
            
    resultados_processados = st.session_state.all_results.copy()
    
    if campo_filtro_label != "Nenhum":
        campo_filtro = mapa_campos[campo_filtro_label]
        if condicao == "Maior ou igual a":
            resultados_processados = [r for r in resultados_processados if r[campo_filtro] >= valor_filtro]
        elif condicao == "Menor ou igual a":
            resultados_processados = [r for r in resultados_processados if r[campo_filtro] <= valor_filtro]
        else:
            resultados_processados = [r for r in resultados_processados if r[campo_filtro] == valor_filtro]
            
    resultados_processados = sorted(
        resultados_processados, 
        key=lambda x: x.get(campo_ord, datetime.min.date() if campo_ord == 'data_inicio' else 0), 
        reverse=reverso
    )

    limite = st.session_state.display_limit
    
    if not resultados_processados:
        st.warning("Nenhuma combinação encontrada para os filtros selecionados.")
    else:
        st.success(f"🎉 Exibindo as {min(limite, len(resultados_processados))} melhores opções dentre {len(resultados_processados)} combinações possíveis!")
        
        for idx, r in enumerate(resultados_processados[:limite]):
            with st.container(border=True):
                dia_semana_inicio = r['comb'][0]['inicio'].strftime('%A')
                dias_trad = {"Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"}
                dia_nome = dias_trad.get(dia_semana_inicio, dia_semana_inicio)
                data_str = r['comb'][0]['inicio'].strftime('%d/%m/%Y')
                
                efi_text = f" | Eficiência: {r['efici']:.0f}%" if r['efici'] != float('inf') else ""
                
                # Título atualizado e completo
                st.subheader(f"Opção #{idx+1} — Divisão: {r['config']} | Início: {dia_nome} ({data_str}) | Total: {r['total']} dias{efi_text}")
                
                st.table(pd.DataFrame([{ 
                    "Lote": f"{p['periodo']}d", 
                    "Início": p["inicio"].strftime("%d/%m/%y"), 
                    "Janela Real": f"{p['inicio_real'].strftime('%d/%m')}—{p['fim_real'].strftime('%d/%m')}", 
                    "Feriados": p["feriados"], 
                    "FDS/Folga": p["fds"], 
                    "Eficiência": f"{p['eficiencia']:.0f}%" if p['eficiencia'] != float('inf') else "Inf%", 
                    "Ganho": f"+{p['qtd_total']}d" 
                } for p in r["comb"]]))
        
        if limite < len(resultados_processados):
            st.write(f"Mostrando {limite} de {len(resultados_processados)} opções filtradas.")
            if st.button("🔽 Carregar mais 15 opções", use_container_width=True):
                st.session_state.display_limit += 15
                st.rerun()