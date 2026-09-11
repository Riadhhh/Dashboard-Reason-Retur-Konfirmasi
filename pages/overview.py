import streamlit as st
import pandas as pd
import plotly.express as px


PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}


# FORMAT ANGKA

def format_number(value):
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value):
    return f"Rp {value:,.0f}".replace(",", ".")


def format_percentage(value):
    return f"{value:.2f}%"


def format_currency_compact(value):

    value = float(value)

    if abs(value) >= 1_000_000_000_000:
        return f"Rp {value / 1_000_000_000_000:.2f} triliun"

    if abs(value) >= 1_000_000_000:
        return f"Rp {value / 1_000_000_000:.2f} miliar"

    if abs(value) >= 1_000_000:
        return f"Rp {value / 1_000_000:.2f} juta"

    if abs(value) >= 1_000:
        return f"Rp {value / 1_000:.2f} ribu"

    return f"Rp {value:,.0f}".replace(",", ".")


# MENENTUKAN ARAH URUTAN

def get_sort_ascending():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order == "Terendah"


# PREPARASI DATA

def prepare_overview_data(df):

    data = df.copy()

    numeric_columns = [
        "Kuantiti STK",
        "Kuantiti DO",
        "Kuantiti Alasan",
        "nilai",
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            ).fillna(0)

    if "Tanggal Kirim" in data.columns:

        data["Tanggal Kirim"] = pd.to_datetime(
            data["Tanggal Kirim"],
            errors="coerce",
        )

    return data


# MENGHITUNG KPI

def calculate_overview_kpis(df):

    total_stk = 0
    total_do = 0
    total_retur = 0
    total_nilai = 0

    if "Kuantiti STK" in df.columns:
        total_stk = df["Kuantiti STK"].sum()

    if "Kuantiti DO" in df.columns:
        total_do = df["Kuantiti DO"].sum()

    if "Kuantiti Alasan" in df.columns:
        total_retur = df["Kuantiti Alasan"].sum()

    if "nilai" in df.columns:
        total_nilai = df["nilai"].sum()

    if total_stk > 0:

        persentase_retur = (
            total_retur
            / total_stk
            * 100
        )

    else:

        persentase_retur = 0

    return {
        "total_stk": total_stk,
        "total_do": total_do,
        "total_retur": total_retur,
        "total_nilai": total_nilai,
        "persentase_retur": persentase_retur,
    }


# KPI CARDS

def show_kpi_cards(df):

    kpi = calculate_overview_kpis(df)

    col1, col2, col3, col4, col5 = st.columns(
        5,
        gap="medium",
    )

    with col1:

        st.metric(
            "Total STK",
            format_number(
                kpi["total_stk"]
            ),
        )

    with col2:

        st.metric(
            "Total DO",
            format_number(
                kpi["total_do"]
            ),
        )

    with col3:

        st.metric(
            "Total Retur",
            format_number(
                kpi["total_retur"]
            ),
        )

    with col4:

        st.metric(
            "Persentase Retur",
            format_percentage(
                kpi["persentase_retur"]
            ),
        )

    with col5:

        st.metric(
            "Nominal Retur",
            format_currency(
                kpi["total_nilai"]
            ),
        )


# PREPARASI DATA ALASAN

def prepare_reason_data(df):

    if df.empty:

        return pd.DataFrame(
            columns=[
                "Keterangan Alasan",
                "transaksi",
                "retur",
                "nominal",
            ]
        )

    data = df.copy()

    data["Keterangan Alasan"] = (
        data["Keterangan Alasan"]
        .fillna("Tidak Diketahui")
        .astype(str)
        .str.strip()
    )

    data.loc[
        data["Keterangan Alasan"] == "",
        "Keterangan Alasan",
    ] = "Tidak Diketahui"

    data["Kuantiti Alasan"] = pd.to_numeric(
        data["Kuantiti Alasan"],
        errors="coerce",
    ).fillna(0)

    data["nilai"] = pd.to_numeric(
        data["nilai"],
        errors="coerce",
    ).fillna(0)

    reason_df = (
        data
        .groupby("Keterangan Alasan")
        .agg(
            transaksi=(
                "Keterangan Alasan",
                "size",
            ),
            retur=(
                "Kuantiti Alasan",
                "sum",
            ),
            nominal=(
                "nilai",
                "sum",
            ),
        )
        .reset_index()
    )

    return reason_df


# RINGKASAN ALASAN

def show_reason_summary(df):

    reason_df = prepare_reason_data(df)

    if reason_df.empty:

        st.info(
            "Data alasan Retur tidak tersedia."
        )

        return

    st.subheader(
        "Analisis Alasan Retur"
    )

    st.caption(
        "Menampilkan ringkasan alasan Retur "
        "berdasarkan parameter dan urutan nilai yang dipilih."
    )

    col1 = st.columns(1)[0]

    with col1:

        parameter = st.selectbox(
            "Parameter Analisis",
            [
                "Jumlah Transaksi",
                "Jumlah Barang Retur",
                "Nominal Retur",
            ],
            key="overview_reason_parameter",
        )

    if parameter == "Jumlah Transaksi":

        metric_column = "transaksi"

    elif parameter == "Jumlah Barang Retur":

        metric_column = "retur"

    else:

        metric_column = "nominal"

    ascending = get_sort_ascending()

    ranked_df = (
        reason_df
        .sort_values(
            metric_column,
            ascending=ascending,
        )
        .reset_index(drop=True)
    )

    ranked_df.insert(
        0,
        "Peringkat",
        range(
            1,
            len(ranked_df) + 1,
        ),
    )

    # RINGKASAN UTAMA

    first_row = ranked_df.iloc[0]

    if parameter == "Jumlah Transaksi":

        nilai_utama = format_number(
            first_row["transaksi"]
        )

        persentase = (
            first_row["transaksi"]
            / reason_df["transaksi"].sum()
            * 100
        )

        label_nilai = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":

        nilai_utama = format_number(
            first_row["retur"]
        )

        persentase = (
            first_row["retur"]
            / reason_df["retur"].sum()
            * 100
        )

        label_nilai = "Barang Retur"

    else:

        nilai_utama = format_currency(
            first_row["nominal"]
        )

        persentase = (
            first_row["nominal"]
            / reason_df["nominal"].sum()
            * 100
        )

        label_nilai = "Nominal Retur"

    label_urutan = (
        "Terendah"
        if ascending
        else "Tertinggi"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            f"Alasan {label_urutan}",
            first_row["Keterangan Alasan"],
        )

    with col2:

        st.metric(
            label_nilai,
            nilai_utama,
        )

    with col3:

        st.metric(
            "Kontribusi",
            format_percentage(
                persentase
            ),
        )

    st.divider()


# PERBANDINGAN DEPO

def prepare_depo_comparison_data(df):

    if df.empty or "Nama Depo" not in df.columns:

        return pd.DataFrame()

    data = df.copy()

    data["Nama Depo"] = (
        data["Nama Depo"]
        .fillna("Tidak Diketahui")
        .astype(str)
        .str.strip()
    )

    data.loc[
        data["Nama Depo"] == "",
        "Nama Depo",
    ] = "Tidak Diketahui"

    data["Kuantiti Alasan"] = pd.to_numeric(
        data["Kuantiti Alasan"],
        errors="coerce",
    ).fillna(0)

    data["nilai"] = pd.to_numeric(
        data["nilai"],
        errors="coerce",
    ).fillna(0)

    depo_df = (
        data
        .groupby("Nama Depo")
        .agg(
            transaksi=(
                "Nama Depo",
                "size",
            ),
            retur=(
                "Kuantiti Alasan",
                "sum",
            ),
            nominal=(
                "nilai",
                "sum",
            ),
        )
        .reset_index()
    )

    return depo_df


# BAR CHART PERBANDINGAN DEPO

def create_depo_comparison_bar(
    depo_df,
    parameter,
):

    if depo_df.empty:

        st.info(
            "Data depo tidak tersedia."
        )

        return

    ascending = get_sort_ascending()

    if parameter == "Jumlah Transaksi":

        metric_column = "transaksi"
        x_title = "Jumlah Transaksi"

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        metric_column = "retur"
        x_title = "Jumlah Barang Retur"

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:

        metric_column = "nominal"
        x_title = "Nominal Retur"

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    chart_df = (
        depo_df
        .sort_values(
            metric_column,
            ascending=ascending,
        )
        .copy()
    )

    fig = px.bar(
        chart_df,
        x=metric_column,
        y="Nama Depo",
        orientation="h",
        text=metric_column,
    )

    if parameter == "Nominal Retur":

        fig.update_traces(
            texttemplate="Rp %{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=hover_template,
        )

    else:

        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=hover_template,
        )

    sort_label = (
        "Terendah"
        if ascending
        else "Tertinggi"
    )

    fig.update_layout(
        title=dict(
            text=f"Perbandingan Depo Berdasarkan "
            f"{parameter}",
            font=dict(size=20),
        ),
        height=450,
        margin=dict(
            t=70,
            b=50,
            l=30,
            r=30,
        ),
        xaxis=dict(
            title=x_title,
            separatethousands=True,
        ),
        yaxis=dict(
            title="Nama Depo",
            categoryorder="array",
            categoryarray=chart_df["Nama Depo"].tolist(),
            autorange="reversed",
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# DONAT PERSENTASE KONTRIBUSI DEPO

def create_depo_comparison_donut(
    depo_df,
    parameter,
):

    if depo_df.empty:

        st.info(
            "Data depo tidak tersedia."
        )

        return

    if parameter == "Jumlah Transaksi":

        metric_column = "transaksi"
        label_metric = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":

        metric_column = "retur"
        label_metric = "Jumlah Barang Retur"

    else:

        metric_column = "nominal"
        label_metric = "Nominal Retur"

    donut_df = depo_df[
        [
            "Nama Depo",
            metric_column,
        ]
    ].copy()

    total_value = donut_df[
        metric_column
    ].sum()

    if total_value <= 0:

        st.info(
            "Tidak terdapat nilai yang dapat "
            "digunakan untuk menghitung persentase."
        )

        return

    donut_df["Persentase"] = (
        donut_df[metric_column]
        / total_value
        * 100
    )

    ascending = get_sort_ascending()

    donut_df = donut_df.sort_values(
        metric_column,
        ascending=ascending,
    )

    fig = px.pie(
        donut_df,
        names="Nama Depo",
        values=metric_column,
        hole=0.55,
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"{label_metric}: "
            "%{value:,.0f}<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=dict(
            text=f"Persentase Kontribusi Depo",
            font=dict(size=20),
        ),
        height=450,
        margin=dict(
            t=70,
            b=20,
            l=20,
            r=20,
        ),
        legend=dict(
            title="Nama Depo",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# PERBANDINGAN SETIAP DEPO

def show_depo_comparison(df):

    depo_df = prepare_depo_comparison_data(
        df
    )

    if depo_df.empty:

        return

    st.subheader(
        "Perbandingan Setiap Depo"
    )

    st.caption(
        "Membandingkan kontribusi setiap depo berdasarkan "
        "parameter yang dipilih."
    )

    parameter = st.selectbox(
        "Parameter Perbandingan",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="overview_depo_parameter",
    )

    st.divider()

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:

        create_depo_comparison_bar(
            depo_df,
            parameter,
        )

    with col2:

        create_depo_comparison_donut(
            depo_df,
            parameter,
        )

    st.divider()


# RINGKASAN KONDISI DATA

def create_overall_status_chart(df):

    kpi = calculate_overview_kpis(df)

    summary_df = pd.DataFrame({
        "Status": [
            "STK",
            "DO",
            "Retur",
        ],
        "Jumlah": [
            kpi["total_stk"],
            kpi["total_do"],
            kpi["total_retur"],
        ],
    })

    fig = px.bar(
        summary_df,
        x="Status",
        y="Jumlah",
        text="Jumlah",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Jumlah: %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=dict(
            text="Ringkasan Jumlah Pengiriman",
            font=dict(size=20),
        ),
        height=420,
        margin=dict(
            t=70,
            b=40,
            l=50,
            r=30,
        ),
        xaxis=dict(
            title="Status",
        ),
        yaxis=dict(
            title="Jumlah",
            separatethousands=True,
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# TREN DATA

def create_overview_trend_chart(df):

    required_columns = [
        "Tanggal Kirim",
        "Kuantiti STK",
        "Kuantiti DO",
        "Kuantiti Alasan",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        st.warning(
            "Kolom yang diperlukan untuk grafik "
            "tren tidak tersedia."
        )

        return

    trend_df = df[
        required_columns
    ].dropna(
        subset=["Tanggal Kirim"]
    ).copy()

    if trend_df.empty:

        st.info(
            "Tidak terdapat data tanggal yang dapat "
            "digunakan untuk grafik tren."
        )

        return

    trend_df = (
        trend_df
        .groupby("Tanggal Kirim")
        [
            [
                "Kuantiti STK",
                "Kuantiti DO",
                "Kuantiti Alasan",
            ]
        ]
        .sum()
        .reset_index()
        .sort_values("Tanggal Kirim")
    )

    trend_long = trend_df.melt(
        id_vars="Tanggal Kirim",
        value_vars=[
            "Kuantiti STK",
            "Kuantiti DO",
            "Kuantiti Alasan",
        ],
        var_name="Kategori",
        value_name="Jumlah",
    )

    trend_long["Kategori"] = trend_long[
        "Kategori"
    ].replace({
        "Kuantiti STK": "STK",
        "Kuantiti DO": "DO",
        "Kuantiti Alasan": "Retur",
    })

    fig = px.line(
        trend_long,
        x="Tanggal Kirim",
        y="Jumlah",
        color="Kategori",
        markers=True,
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Tanggal: %{x|%d/%m/%Y}<br>"
            "Jumlah: %{y:,.0f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=dict(
            text="Tren Pengiriman dan Retur",
            font=dict(size=20),
        ),
        height=450,
        margin=dict(
            t=70,
            b=50,
            l=50,
            r=30,
        ),
        xaxis=dict(
            title="Tanggal Kirim",
        ),
        yaxis=dict(
            title="Jumlah",
            separatethousands=True,
        ),
        legend=dict(
            title="Kategori",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# RASIO PENGIRIMAN

def create_delivery_ratio_chart(df):

    kpi = calculate_overview_kpis(df)

    total_stk = kpi["total_stk"]
    total_do = kpi["total_do"]
    total_retur = kpi["total_retur"]

    if total_stk <= 0:

        st.info(
            "Tidak dapat menghitung komposisi karena "
            "Total STK bernilai 0."
        )

        return

    ratio_df = pd.DataFrame({
        "Kategori": [
            "DO Berhasil",
            "Retur",
        ],
        "Jumlah": [
            total_do,
            total_retur,
        ],
    })

    fig = px.pie(
        ratio_df,
        names="Kategori",
        values="Jumlah",
        hole=0.55,
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Jumlah: %{value:,.0f}<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=dict(
            text="Komposisi Hasil Pengiriman",
            font=dict(size=20),
        ),
        height=420,
        margin=dict(
            t=70,
            b=20,
            l=20,
            r=20,
        ),
        legend_title_text="Kategori",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# RINGKASAN PERIODE

def show_period_summary(df):

    if "Tanggal Kirim" not in df.columns:

        return

    valid_dates = df[
        "Tanggal Kirim"
    ].dropna()

    if valid_dates.empty:

        return

    min_date = valid_dates.min()
    max_date = valid_dates.max()

    jumlah_hari = (
        max_date.date()
        - min_date.date()
    ).days + 1

    kpi = calculate_overview_kpis(df)

    if kpi["total_stk"] > 0:

        do_percentage = (
            kpi["total_do"]
            / kpi["total_stk"]
            * 100
        )

        retur_percentage = (
            kpi["total_retur"]
            / kpi["total_stk"]
            * 100
        )

    else:

        do_percentage = 0
        retur_percentage = 0

    st.markdown(
        f"""
        **Periode Data:** {min_date.strftime('%d/%m/%Y')}
        - {max_date.strftime('%d/%m/%Y')}

        **Durasi Periode:** {jumlah_hari} hari

        **Tingkat Pengiriman Berhasil:** {do_percentage:.2f}%

        **Tingkat Retur:** {retur_percentage:.2f}%
        """
    )


# HALAMAN OVERVIEW

def show_overview(df):

    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan filter "
            "yang dipilih."
        )

        return

    data = prepare_overview_data(df)

    st.title(
        "Overview"
    )

    st.caption(
        "Ringkasan kondisi keseluruhan data Retur "
        "berdasarkan periode dan filter yang dipilih."
    )

    st.divider()

    # KPI UTAMA

    st.subheader(
        "Ringkasan Utama"
    )

    show_kpi_cards(
        data
    )

    st.divider()

    # INFORMASI PERIODE

    st.subheader(
        "Informasi Periode"
    )

    show_period_summary(
        data
    )

    st.divider()

    # PERBANDINGAN DEPO

    show_depo_comparison(
        data
    )

    # ANALISIS ALASAN RETUR

    show_reason_summary(
        data
    )

    # TREN

    st.subheader(
        "Tren Pengiriman"
    )

    st.caption(
        "Menampilkan perubahan jumlah STK, DO, dan retur "
        "berdasarkan tanggal kirim."
    )

    create_overview_trend_chart(
        data
    )

    st.divider()

    # RINGKASAN HASIL PENGIRIMAN

    st.subheader(
        "Ringkasan Hasil Pengiriman"
    )

    st.caption(
        "Membandingkan jumlah barang yang tercatat pada "
        "STK, DO, dan retur secara keseluruhan."
    )

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:

        create_overall_status_chart(
            data
        )

    with col2:

        create_delivery_ratio_chart(
            data
        )


# JALANKAN HALAMAN

if "filtered_df" not in st.session_state:

    st.warning(
        "Data belum tersedia. Silakan upload "
        "file terlebih dahulu."
    )

    st.stop()


df = st.session_state[
    "filtered_df"
]

show_overview(
    df
)