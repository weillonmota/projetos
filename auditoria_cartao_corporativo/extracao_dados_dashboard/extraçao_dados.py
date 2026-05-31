import glob
import os
import pandas as pd


def mascarar_nome(nome: str) -> str:
    if pd.isna(nome) or not str(nome).strip():
        return "NÃO IDENTIFICADO"

    nome_str: str = str(nome).strip()
    nome_upper: str = nome_str.upper()

    if (
        nome_upper.startswith("SIGILOSO")
        or "SAQUE" in nome_upper
        or "OPERACIONAL" in nome_upper
    ):
        return nome_str

    partes: list[str] = nome_str.split()
    if len(partes) == 1:
        return partes[0]

    iniciais: str = " ".join([f"{p[0]}." for p in partes[1:] if p])
    return f"{partes[0]} {iniciais}"


def executar_auditoria_pasta(pasta_dados: str, pasta_resultados: str) -> None:
    caminho_padrao: str = os.path.join(pasta_dados, "*.csv")
    arquivos: list[str] = glob.glob(caminho_padrao)

    if not arquivos:
        print(f"Nenhum arquivo CSV encontrado na pasta {pasta_dados}")
        return

    lista_dataframes: list[pd.DataFrame] = []

    for arquivo in arquivos:
        try:
            df: pd.DataFrame = pd.read_csv(
                arquivo, sep=";", encoding="utf-8"
            )
        except UnicodeDecodeError:
            df = pd.read_csv(arquivo, sep=";", encoding="latin1")

        lista_dataframes.append(df)

    df_completo: pd.DataFrame = pd.concat(
        lista_dataframes, ignore_index=True
    )

    df_completo["VALOR_NUM"] = (
        df_completo["VALOR TRANSAÇÃO"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df_completo["DATA_DT"] = pd.to_datetime(
        df_completo["DATA TRANSAÇÃO"], format="%d/%m/%Y", errors="coerce"
    )

    df_completo["ANO_MES"] = (
        df_completo["DATA_DT"].dt.to_period("M").astype(str)
    )

    # =========================================================================
    # HIGIENIZAÇÃO DE SAQUES E DESPESAS OPERACIONAIS/SIGILOSAS
    # =========================================================================
    df_completo["CNPJ OU CPF FAVORECIDO"] = (
        df_completo["CNPJ OU CPF FAVORECIDO"].astype(str).str.strip()
    )

    mask_saque: pd.Series = df_completo["TRANSAÇÃO"].str.contains(
        "SAQUE", case=False, na=False
    )
    df_completo.loc[mask_saque, "NOME FAVORECIDO"] = "SAQUE EM ESPÉCIE"
    df_completo.loc[mask_saque, "CNPJ OU CPF FAVORECIDO"] = "0"

    mask_anomalo: pd.Series = (
        df_completo["NOME FAVORECIDO"]
        .str.upper()
        .isin(["NAO S. A.", "SEM I.", "SIGILOSO"])
        | df_completo["CNPJ OU CPF FAVORECIDO"].str.startswith("-")
    )
    mask_sigilo: pd.Series = mask_anomalo & (~mask_saque)
    df_completo.loc[mask_sigilo, "NOME FAVORECIDO"] = (
        "DESPESA OPERACIONAL / SIGILOSA"
    )
    df_completo.loc[mask_sigilo, "CNPJ OU CPF FAVORECIDO"] = "0"

    print(f"Registros carregados para análise avançada: {len(df_completo)}")

    # =========================================================================
    # PROCESSAMENTO DAS 6 REGRAS DIRETAS (DADOS BRUTOS)
    # =========================================================================

    r1: pd.DataFrame = df_completo[df_completo["VALOR_NUM"] > 3000.00].copy()
    r1["REGRA"] = "R1 - Gasto Diário Elevado"

    df_ordenado: pd.DataFrame = (
        df_completo.dropna(subset=["DATA_DT", "NOME PORTADOR"])
        .sort_values(by=["NOME PORTADOR", "DATA_DT"])
        .copy()
    )
    df_ordenado["SOMA_3DIAS"] = (
        df_ordenado.groupby("NOME PORTADOR")["VALOR_NUM"]
        .rolling(3, min_periods=3)
        .sum()
        .droplevel(0)
    )
    df_ordenado["DIAS_INTERVALO"] = (
        df_ordenado.groupby("NOME PORTADOR")["DATA_DT"].diff(2).dt.days
    )
    r2: pd.DataFrame = df_ordenado[
        (df_ordenado["SOMA_3DIAS"] > 5000.00)
        & (df_ordenado["DIAS_INTERVALO"] <= 2)
    ].copy()
    r2["REGRA"] = "R2 - Suspeita de Fracionamento"

    feriados_fixos: list[str] = [
        "-01-01", "-04-21", "-05-01", "-09-07", "-10-12",
        "-11-02", "-11-15", "-11-20", "-12-25"
    ]
    is_fim_de_semana: pd.Series = df_completo["DATA_DT"].dt.dayofweek.isin([5, 6])
    is_feriado: pd.Series = df_completo["DATA_DT"].dt.strftime("-%m-%d").isin(feriados_fixos)
    r3: pd.DataFrame = df_completo[is_fim_de_semana | is_feriado].copy()
    r3["REGRA"] = "R3 - Uso em Dias Não Úteis"

    r4: pd.DataFrame = df_completo[
        df_completo["TRANSAÇÃO"].str.contains("SAQUE", case=False, na=False)
    ].copy()
    r4["REGRA"] = "R4 - Operação de Saque"

    r5: pd.DataFrame = df_completo[
        df_completo.duplicated(
            subset=["DATA_DT", "VALOR_NUM", "NOME FAVORECIDO"], keep=False
        )
    ].copy()
    r5["REGRA"] = "R5 - Transação Duplicada no Dia"

    df_sigiloso: pd.DataFrame = df_completo[
        df_completo["NOME PORTADOR"].str.upper().str.contains("SIGILOSO", na=False)
    ].copy()
    agro_sigilo: pd.DataFrame = (
        df_sigiloso.groupby(["ANO_MES", "NOME ÓRGÃO"])["VALOR_NUM"]
        .sum()
        .reset_index()
    )
    orgaos_estourados: pd.DataFrame = agro_sigilo[agro_sigilo["VALOR_NUM"] > 10000.00]

    r6: pd.DataFrame = df_completo[
        df_completo["NOME PORTADOR"].str.upper().str.contains("SIGILOSO", na=False)
        & df_completo.set_index(["ANO_MES", "NOME ÓRGÃO"]).index.isin(
            orgaos_estourados.set_index(["ANO_MES", "NOME ÓRGÃO"]).index
        )
    ].copy()
    r6["REGRA"] = "R6 - Despesa Sigilosa Excedente"
    r6["NOME PORTADOR"] = "SIGILOSO - " + r6["NOME ÓRGÃO"]

    df_alertas_todos: pd.DataFrame = pd.concat(
        [r1, r2, r3, r4, r5, r6], ignore_index=True
    )

    os.makedirs(pasta_resultados, exist_ok=True)

    # =========================================================================
    # MÉTRICA DE RISCO 1: SCORE PONDERADO DE FRAUDE POR PORTADOR E MÊS
    # =========================================================================
    analise_portador: pd.DataFrame = (
        df_alertas_todos.groupby(["ANO_MES", "NOME PORTADOR"])
        .agg(
            VALOR_TOTAL_ALERTA=("VALOR_NUM", "sum"),
            REGRAS_VIOLADAS=("REGRA", "nunique"),
            TOTAL_TRANSACOES_SUSPEITAS=("VALOR_NUM", "count")
        )
        .reset_index()
    )

    analise_portador["SCORE_RISCO"] = (
        analise_portador["VALOR_TOTAL_ALERTA"] * analise_portador["REGRAS_VIOLADAS"]
    )

    analise_portador = analise_portador.sort_values(
        by=["ANO_MES", "SCORE_RISCO"], ascending=[True, False]
    )
    top_5_score_mensal: pd.DataFrame = (
        analise_portador.groupby("ANO_MES").head(5).reset_index(drop=True)
    )

    top_5_score_mensal["NOME PORTADOR"] = top_5_score_mensal["NOME PORTADOR"].apply(
        mascarar_nome
    )

    caminho_top5: str = os.path.join(
        pasta_resultados, "airtable_top5_criticidade_mensal.csv"
    )
    top_5_score_mensal.to_csv(
        caminho_top5, sep=";", index=False, encoding="utf-8"
    )

    # =========================================================================
    # MÉTRICA DE RISCO 2: CONCENTRAÇÃO EM FORNECEDOR ÚNICO
    # =========================================================================
    gasto_total_portador: pd.DataFrame = (
        df_completo.groupby(["ANO_MES", "NOME PORTADOR"])["VALOR_NUM"]
        .sum()
        .reset_index(name="GASTO_TOTAL_PORTADOR_MES")
    )

    gasto_por_fornecedor: pd.DataFrame = (
        df_completo.groupby(
            ["ANO_MES", "NOME PORTADOR", "CNPJ OU CPF FAVORECIDO", "NOME FAVORECIDO"]
        )["VALOR_NUM"]
        .sum()
        .reset_index(name="GASTO_FORNECEDOR_MES")
    )

    df_concentracao: pd.DataFrame = pd.merge(
        gasto_por_fornecedor,
        gasto_total_portador,
        on=["ANO_MES", "NOME PORTADOR"]
    )

    df_concentracao["PERC_CONCENTRACAO"] = (
        (df_concentracao["GASTO_FORNECEDOR_MES"] / df_concentracao["GASTO_TOTAL_PORTADOR_MES"]) * 100
    )

    alertas_fornecedor: pd.DataFrame = df_concentracao[
        (df_concentracao["PERC_CONCENTRACAO"] > 75.0)
        & (df_concentracao["GASTO_TOTAL_PORTADOR_MES"] > 1500.0)
    ].copy()

    alertas_fornecedor = alertas_fornecedor.sort_values(
        by=["ANO_MES", "PERC_CONCENTRACAO", "GASTO_FORNECEDOR_MES"],
        ascending=[True, False, False]
    )

    top_concentracao_mensal: pd.DataFrame = (
        alertas_fornecedor.groupby("ANO_MES").head(25).reset_index(drop=True)
    )

    top_concentracao_mensal["NOME PORTADOR"] = top_concentracao_mensal["NOME PORTADOR"].apply(
        mascarar_nome
    )
    top_concentracao_mensal["NOME FAVORECIDO"] = top_concentracao_mensal["NOME FAVORECIDO"].apply(
        mascarar_nome
    )

    caminho_concentracao: str = os.path.join(
        pasta_resultados, "airtable_indicio_direcionamento.csv"
    )
    top_concentracao_mensal.to_csv(
        caminho_concentracao, sep=";", index=False, encoding="utf-8"
    )
    print("Processamento concluído com total sucesso e dados higienizados!")


if __name__ == "__main__":
    executar_auditoria_pasta("dados_brutos", "resultados_auditoria")