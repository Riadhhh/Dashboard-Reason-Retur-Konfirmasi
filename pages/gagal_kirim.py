import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}


# FUNGSI FORMAT ANGKA

def format_number(value):
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value):
    return f"Rp {value:,.0f}".replace(",", ".")


def format_percentage(value):
    return f"{value:.1f}%"


# FUNGSI MENENTUKAN ARAH URUTAN

def get_sort_ascending():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order == "Terendah"


def get_sort_label():

    return st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )


# FUNGSI MENENTUKAN KOLOM PARAMETER

def get_parameter_column(parameter):

    if parameter == "Jumlah Transaksi":
        return "transaksi"

    if parameter == "Jumlah Barang Retur":
        return "retur"

    return "nominal"


# PREPARASI DATA ALASAN

def prepare_reason_data(df):

    if df.empty:

        return pd.DataFrame(
            columns=[
                "Keterangan Alasan",
                "transaksi",
                "retur",
                "nominal",
                "persentase_transaksi",
                "persentase_retur",
                "persentase_nominal",
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
        data.groupby("Keterangan Alasan")
        .agg(
            transaksi=("Keterangan Alasan", "size"),
            retur=("Kuantiti Alasan", "sum"),
            nominal=("nilai", "sum"),
        )
        .reset_index()
    )

    total_transaksi = reason_df["transaksi"].sum()
    total_retur = reason_df["retur"].sum()
    total_nominal = reason_df["nominal"].sum()

    if total_transaksi > 0:

        reason_df["persentase_transaksi"] = (
            reason_df["transaksi"]
            / total_transaksi
            * 100
        )

    else:

        reason_df["persentase_transaksi"] = 0

    if total_retur > 0:

        reason_df["persentase_retur"] = (
            reason_df["retur"]
            / total_retur
            * 100
        )

    else:

        reason_df["persentase_retur"] = 0

    if total_nominal > 0:

        reason_df["persentase_nominal"] = (
            reason_df["nominal"]
            / total_nominal
            * 100
        )

    else:

        reason_df["persentase_nominal"] = 0

    return reason_df


# KARTU DAN TABEL RINGKASAN

def show_summary_cards(reason_df):

    if reason_df.empty:
        return

    sort_ascending = get_sort_ascending()

    # MENCARI ALASAN BERDASARKAN TRANSAKSI

    top_transaction = (
        reason_df
        .sort_values(
            "transaksi",
            ascending=sort_ascending,
        )
        .iloc[0]
    )

    # MENCARI ALASAN BERDASARKAN RETUR

    top_return = (
        reason_df
        .sort_values(
            "retur",
            ascending=sort_ascending,
        )
        .iloc[0]
    )

    # MENCARI ALASAN BERDASARKAN NOMINAL

    top_nominal = (
        reason_df
        .sort_values(
            "nominal",
            ascending=sort_ascending,
        )
        .iloc[0]
    )

    transaction_label = (
        "Alasan Transaksi Terendah"
        if sort_ascending
        else "Alasan Transaksi Terbanyak"
    )

    return_label = (
        "Alasan Retur Terendah"
        if sort_ascending
        else "Alasan Retur Terbanyak"
    )

    nominal_label = (
        "Alasan Nominal Terendah"
        if sort_ascending
        else "Alasan Nominal Terbesar"
    )

    # KARTU RINGKASAN

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            transaction_label,
            top_transaction[
                "Keterangan Alasan"
            ],
        )

        st.caption(
            f"{format_number(top_transaction['transaksi'])} transaksi "
            f"({format_percentage(top_transaction['persentase_transaksi'])})"
        )

    with col2:

        st.metric(
            return_label,
            top_return[
                "Keterangan Alasan"
            ],
        )

        st.caption(
            f"{format_number(top_return['retur'])} barang "
            f"({format_percentage(top_return['persentase_retur'])})"
        )

    with col3:

        st.metric(
            nominal_label,
            top_nominal[
                "Keterangan Alasan"
            ],
        )

        st.caption(
            f"{format_currency(top_nominal['nominal'])} "
            f"({format_percentage(top_nominal['persentase_nominal'])})"
        )

# GRAFIK BERDASARKAN PARAMETER

def create_parameter_chart(
    reason_df,
    top_n,
    parameter,
):

    ascending = get_sort_ascending()
    sort_label = get_sort_label()

    parameter_column = get_parameter_column(
        parameter
    )

    chart_df = (
        reason_df
        .sort_values(
            parameter_column,
            ascending=ascending,
        )
        .head(top_n)
        .sort_values(
            parameter_column,
            ascending=not ascending,
        )
        .copy()
    )

    if parameter == "Jumlah Transaksi":

        text_template = "%{text:,.0f}"

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}<br>"
            "Persentase: "
            "%{customdata[0]:.1f}%"
            "<extra></extra>"
        )

        custom_data = [
            "persentase_transaksi"
        ]

    elif parameter == "Jumlah Barang Retur":

        text_template = "%{text:,.0f}"

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Barang Retur: %{x:,.0f}<br>"
            "Kontribusi Retur: "
            "%{customdata[0]:.1f}%"
            "<extra></extra>"
        )

        custom_data = [
            "persentase_retur"
        ]

    else:

        text_template = "%{text:,.0f}"

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}<br>"
            "Kontribusi Nominal: "
            "%{customdata[0]:.1f}%"
            "<extra></extra>"
        )

        custom_data = [
            "persentase_nominal"
        ]

    title = (
        f"Top {top_n} Alasan {sort_label} Berdasarkan "
        f"{parameter}"
    )

    fig = px.bar(
        chart_df,
        x=parameter_column,
        y="Keterangan Alasan",
        orientation="h",
        text=parameter_column,
        custom_data=custom_data,
    )

    fig.update_traces(
        texttemplate=text_template,
        textposition="outside",
        cliponaxis=False,
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        height=max(
            400,
            len(chart_df) * 48,
        ),
        margin=dict(
            l=10,
            r=90,
            t=55,
            b=20,
        ),
        xaxis=dict(
            title=parameter,
            separatethousands=True,
        ),
        yaxis=dict(
            title=None,
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# GRAFIK KOMPOSISI ALASAN

def create_reason_donut(
    reason_df,
    top_n,
    parameter,
):

    parameter_column = get_parameter_column(
        parameter
    )

    chart_df = (
        reason_df
        .sort_values(
            parameter_column,
            ascending=False,
        )
        .copy()
    )

    if len(chart_df) > top_n:

        top_df = chart_df.head(top_n).copy()

        other_value = (
            chart_df.iloc[top_n:][
                parameter_column
            ].sum()
        )

        if other_value > 0:

            other_row = pd.DataFrame({
                "Keterangan Alasan": [
                    "Lainnya"
                ],
                parameter_column: [
                    other_value
                ],
            })

            chart_df = pd.concat(
                [
                    top_df[
                        [
                            "Keterangan Alasan",
                            parameter_column,
                        ]
                    ],
                    other_row,
                ],
                ignore_index=True,
            )

        else:

            chart_df = top_df[
                [
                    "Keterangan Alasan",
                    parameter_column,
                ]
            ]

    else:

        chart_df = chart_df[
            [
                "Keterangan Alasan",
                parameter_column,
            ]
        ]

    title = (
        f"Komposisi Alasan Berdasarkan "
        f"{parameter}"
    )

    fig = px.pie(
        chart_df,
        names="Keterangan Alasan",
        values=parameter_column,
        hole=0.55,
    )

    if parameter == "Nominal Retur":

        hover_value = (
            "Nominal Retur: Rp %{value:,.0f}"
        )

    elif parameter == "Jumlah Barang Retur":

        hover_value = (
            "Jumlah Barang Retur: %{value:,.0f}"
        )

    else:

        hover_value = (
            "Jumlah Transaksi: %{value:,.0f}"
        )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"{hover_value}<br>"
            "Persentase: %{percent:.1%}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=title,
        height=450,
        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10,
        ),
        legend=dict(
            orientation="v",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# GRAFIK TREN RETUR

def create_reason_trend(
    df,
    selected_reason,
    parameter,
):

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

    data = data[
        data["Keterangan Alasan"] == selected_reason
    ].copy()

    data = data.dropna(
        subset=["Tanggal Kirim"]
    )

    if data.empty:

        st.info(
            "Tidak terdapat data tanggal untuk "
            "alasan yang dipilih."
        )

        return

    if parameter == "Jumlah Transaksi":

        trend_df = (
            data
            .groupby("Tanggal Kirim")
            .agg(
                nilai_parameter=(
                    "Keterangan Alasan",
                    "size",
                ),
                retur=(
                    "Kuantiti Alasan",
                    "sum",
                ),
            )
            .reset_index()
            .sort_values("Tanggal Kirim")
        )

        y_label = "Jumlah Transaksi"

        hover_label = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":

        trend_df = (
            data
            .groupby("Tanggal Kirim")
            .agg(
                nilai_parameter=(
                    "Kuantiti Alasan",
                    "sum",
                ),
                transaksi=(
                    "Keterangan Alasan",
                    "size",
                ),
            )
            .reset_index()
            .sort_values("Tanggal Kirim")
        )

        y_label = "Jumlah Barang Retur"

        hover_label = "Jumlah Barang Retur"

    else:

        trend_df = (
            data
            .groupby("Tanggal Kirim")
            .agg(
                nilai_parameter=(
                    "nilai",
                    "sum",
                ),
                transaksi=(
                    "Keterangan Alasan",
                    "size",
                ),
            )
            .reset_index()
            .sort_values("Tanggal Kirim")
        )

        y_label = "Nominal Retur"

        hover_label = "Nominal Retur"

    title = (
        f"Tren {parameter} Berdasarkan "
        f"Alasan: {selected_reason}"
    )

    fig = px.line(
        trend_df,
        x="Tanggal Kirim",
        y="nilai_parameter",
        markers=True,
    )

    if parameter == "Nominal Retur":

        hover_template = (
            "<b>%{x|%d %b %Y}</b><br>"
            "Nominal Retur: Rp %{y:,.0f}"
            "<extra></extra>"
        )

    else:

        hover_template = (
            "<b>%{x|%d %b %Y}</b><br>"
            f"{hover_label}: "
            "%{y:,.0f}"
            "<extra></extra>"
        )

    fig.update_traces(
        marker=dict(size=7),
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        height=430,
        margin=dict(
            l=10,
            r=20,
            t=55,
            b=20,
        ),
        xaxis=dict(
            title="Tanggal Kirim",
            tickformat="%d %b",
        ),
        yaxis=dict(
            title=y_label,
            separatethousands=True,
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# MEMBUAT HEATMAP DIMENSI DAN ALASAN

def create_reason_dimension_heatmap(
    df,
    dimension,
    dimension_label,
    parameter,
):

    required_columns = [
        dimension,
        "Keterangan Alasan",
        "nilai",
        "Kuantiti Alasan",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        st.warning(
            "Kolom yang dibutuhkan untuk heatmap "
            "tidak tersedia."
        )

        return

    heatmap_df = df[
        required_columns
    ].copy()

    heatmap_df[dimension] = (
        heatmap_df[dimension]
        .fillna("Tidak Diketahui")
        .astype(str)
    )

    heatmap_df["Keterangan Alasan"] = (
        heatmap_df["Keterangan Alasan"]
        .fillna("Tidak Diketahui")
        .astype(str)
    )

    heatmap_df["nilai"] = pd.to_numeric(
        heatmap_df["nilai"],
        errors="coerce",
    ).fillna(0)

    heatmap_df["Kuantiti Alasan"] = pd.to_numeric(
        heatmap_df["Kuantiti Alasan"],
        errors="coerce",
    ).fillna(0)

    if parameter == "Jumlah Barang Retur":

        metric_column = "Kuantiti Alasan"
        metric_label = "Jumlah Barang Retur"

    elif parameter == "Nominal Retur":

        metric_column = "nilai"
        metric_label = "Nominal Retur"

    else:

        heatmap_df["Jumlah Transaksi"] = 1

        metric_column = "Jumlah Transaksi"
        metric_label = "Jumlah Transaksi"

    ascending = get_sort_ascending()

    dimension_totals = (
        heatmap_df
        .groupby(dimension)[metric_column]
        .sum()
        .sort_values(
            ascending=ascending
        )
        .head(15)
    )

    selected_dimensions = (
        dimension_totals.index.tolist()
    )

    if not selected_dimensions:

        st.info(
            "Tidak terdapat data yang dapat "
            "ditampilkan."
        )

        return

    heatmap_df = heatmap_df[
        heatmap_df[dimension].isin(
            selected_dimensions
        )
    ].copy()

    heatmap_df = (
        heatmap_df
        .groupby(
            [
                dimension,
                "Keterangan Alasan",
            ],
            as_index=False,
        )[metric_column]
        .sum()
        .rename(
            columns={
                metric_column: "Nilai"
            }
        )
    )

    heatmap_df = heatmap_df[
        heatmap_df["Nilai"] > 0
    ].copy()

    if heatmap_df.empty:

        st.info(
            "Tidak terdapat kombinasi data "
            "untuk heatmap."
        )

        return

    reason_order = (
        heatmap_df
        .groupby(
            "Keterangan Alasan"
        )["Nilai"]
        .sum()
        .sort_values(
            ascending=ascending
        )
        .index
        .tolist()
    )

    dimension_order = (
        dimension_totals.index.tolist()
    )

    matrix = heatmap_df.pivot(
        index=dimension,
        columns="Keterangan Alasan",
        values="Nilai",
    )

    matrix = matrix.reindex(
        index=dimension_order,
        columns=reason_order,
    )

    z_values = matrix.astype(float).values

    text_values = matrix.map(
        lambda value:
            format_currency(value)
            if (
                pd.notna(value)
                and parameter == "Nominal Retur"
            )
            else (
                format_number(value)
                if pd.notna(value)
                else ""
            )
    ).values

    sort_label = get_sort_label()

    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            text=text_values,
            texttemplate="%{text}",
            textfont={
                "size": 11
            },
            hoverongaps=False,
            xgap=2,
            ygap=2,
            hovertemplate=(
                f"{dimension_label}: "
                "%{y}<br>"
                "Keterangan Alasan: %{x}<br>"
                f"{metric_label}: "
                "%{z:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=(
            f"Heatmap {dimension_label} dan "
            f"Keterangan Alasan - "
            f"{sort_label}"
        ),
        xaxis_title="Keterangan Alasan",
        yaxis_title=dimension_label,
        height=650,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=150,
        ),
    )

    fig.update_xaxes(
        tickangle=-45
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# HALAMAN ANALISIS Retur

def show_gagal_kirim(df):

    st.title(
        "Alasan Retur"
    )

    st.caption(
        "Analisis alasan Retur berdasarkan "
        "jumlah transaksi, jumlah barang retur, "
        "dan nominal retur."
    )

    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan "
            "filter yang dipilih."
        )

        return

    reason_df = prepare_reason_data(df)

    if reason_df.empty:

        st.warning(
            "Data alasan Retur tidak tersedia."
        )

        return

    max_reason = len(reason_df)

    default_top_n = min(
        8,
        max_reason,
    )

    # PARAMETER ANALISIS

    st.subheader(
        "Parameter Analisis"
    )

    parameter = st.selectbox(
        "Pilih Parameter",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="gagal_kirim_parameter",
    )

    st.divider()

    # Ringkasan

    st.subheader(
        "Ringkasan Alasan"
    )

    show_summary_cards(
        reason_df
    )

    st.divider()

    # Frekuensi dan komposisi

    st.subheader(
        "Frekuensi dan Komposisi Alasan"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.caption(
            f"Alasan berdasarkan {parameter.lower()} "
            f"dari urutan {get_sort_label().lower()}."
        )

        if max_reason > 1:

            top_n_frequency = st.slider(
                "Jumlah alasan",
                min_value=1,
                max_value=max_reason,
                value=default_top_n,
                step=1,
                key="reason_frequency_top_n",
            )

        else:

            top_n_frequency = 1

        create_parameter_chart(
            reason_df,
            top_n_frequency,
            parameter,
        )

    with col2:

        st.caption(
            f"Proporsi alasan berdasarkan "
            f"{parameter.lower()}."
        )

        donut_top_n = min(
            5,
            max_reason,
        )

        create_reason_donut(
            reason_df,
            donut_top_n,
            parameter,
        )

    st.divider()

    # Tren alasan

    st.subheader(
        f"Tren {parameter} Berdasarkan Alasan"
    )

    st.caption(
        f"Pilih satu alasan untuk melihat perkembangan "
        f"{parameter.lower()} pada setiap tanggal."
    )

    available_reasons = (
        reason_df
        .sort_values(
            get_parameter_column(parameter),
            ascending=get_sort_ascending(),
        )[
            "Keterangan Alasan"
        ]
        .tolist()
    )

    selected_reason = st.selectbox(
        "Pilih Alasan Retur",
        available_reasons,
        key="selected_reason",
    )

    create_reason_trend(
        df,
        selected_reason,
        parameter,
    )

    st.divider()

    # Heatmap

    st.subheader(
        "Distribusi Alasan Berdasarkan Dimensi"
    )

    st.caption(
        f"Distribusi {parameter.lower()} berdasarkan "
        "dimensi dan alasan Retur. "
        "Kombinasi tanpa data tidak ditampilkan."
    )

    dimension = st.selectbox(
        "Analisis berdasarkan",
        [
            "Nama Depo",
            "Nama Driver",
            "Nama Sales",
            "Nama Customer",
        ],
        key="reason_heatmap_dimension",
    )

    create_reason_dimension_heatmap(
        df,
        dimension,
        dimension,
        parameter,
    )

    st.divider()

    # DETAIL RINGKASAN

    st.subheader(
        "Detail Ringkasan Alasan"
    )

    st.caption(
        "Rincian seluruh alasan Retur "
        "berdasarkan jumlah transaksi, "
        "barang retur, dan nominal retur."
    )

    show_detail_summary(
        reason_df
    )

# TABEL DETAIL RINGKASAN

def show_detail_summary(reason_df):

    if reason_df.empty:
        return

    table_df = reason_df[
        [
            "Keterangan Alasan",
            "transaksi",
            "retur",
            "nominal",
        ]
    ].copy()

    table_df = table_df.rename(
        columns={
            "Keterangan Alasan": "Alasan",
            "transaksi": "Jumlah Transaksi",
            "retur": "Barang Retur",
            "nominal": "Nominal Retur",
        }
    )

    table_df.insert(
        0,
        "Peringkat",
        range(1, len(table_df) + 1),
    )

    styled_df = (
        table_df.style
        .format(
            {
                "Jumlah Transaksi": "{:,.0f}",
                "Barang Retur": "{:,.0f}",
                "Nominal Retur": "Rp {:,.0f}",
            }
        )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )

# Jalankan halaman

if "filtered_df" in st.session_state:

    show_gagal_kirim(
        st.session_state["filtered_df"]
    )

else:

    st.warning(
        "Data belum tersedia. Silakan upload "
        "file terlebih dahulu."
    )

    st.stop()