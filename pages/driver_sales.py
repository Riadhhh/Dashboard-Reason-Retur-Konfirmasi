import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}

# MENENTUKAN ARAH URUTAN
def get_sort_ascending():
    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )
    return sort_order == "Terendah"

def format_number(value):
    return f"{value:,.0f}".replace(",", ".")

def format_currency(value):
    return f"Rp {value:,.0f}".replace(",", ".")

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

# PREPARASI DATA
def prepare_driver_sales_data(df):
    data = df.copy()

    required_numeric = [
        "Kuantiti STK",
        "Kuantiti DO",
        "Kuantiti Alasan",
        "nilai",
    ]

    for column in required_numeric:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            ).fillna(0)

    for column in [
        "Nama Driver",
        "Nama Sales",
    ]:

        if column in data.columns:
            data[column] = (
                data[column]
                .fillna("Tidak Diketahui")
                .astype(str)
                .str.strip()
            )

            data.loc[
                data[column] == "",
                column,
            ] = "Tidak Diketahui"

    return data

# JUMLAH DATA UNIK

def get_top_n(df, column):
    if column not in df.columns:
        return 1

    unique_count = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    return max(1, unique_count)

# DATA BERDASARKAN PARAMETER
def create_parameter_data(
    df,
    column,
    parameter,
):

    if parameter == "Jumlah Transaksi":
        grouped = (
            df.groupby(column)
            .size()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":
        grouped = (
            df.groupby(column)["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Barang Retur"

    else:
        grouped = (
            df.groupby(column)["nilai"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Nominal Retur"

    grouped = grouped[
        grouped[column].notna()
    ].copy()

    grouped[column] = (
        grouped[column]
        .astype(str)
        .str.strip()
    )

    grouped = grouped[
        grouped[column] != ""
    ]

    return grouped, x_title

# GRAFIK DRIVER
def create_driver_chart(
    df,
    top_n,
    parameter,
):

    driver_column = "Nama Driver"

    grouped, x_title = create_parameter_data(
        df,
        driver_column,
        parameter,
    )

    if grouped.empty:
        st.info(
            "Tidak terdapat data driver yang dapat "
            "ditampilkan."
        )
        return

    # Menentukan arah urutan
    ascending = get_sort_ascending()

    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    grouped = (
        grouped
        .sort_values(
            "Jumlah",
            ascending=ascending,
        )
        .head(top_n)
        .sort_values(
            "Jumlah",
            ascending=not ascending,
        )
    )

    title = (
        f"{top_n} Driver {sort_label} Berdasarkan "
        f"{x_title}"
    )

    if parameter == "Nominal Retur":
        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":
        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:
        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    fig = px.bar(
        grouped,
        x="Jumlah",
        y=driver_column,
        orientation="h",
        text="Jumlah",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20),
        ),
        height=max(
            430,
            len(grouped) * 50,
        ),
        margin=dict(
            t=70,
            b=30,
            l=20,
            r=70,
        ),
        xaxis=dict(
            title=x_title,
            separatethousands=True,
        ),
        yaxis=dict(
            title="Nama Driver",
        ),
        showlegend=False,
    )

    if parameter == "Nominal Retur":
        fig.update_xaxes(
            tickprefix="Rp ",
        )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

# GRAFIK SALES
def create_sales_chart(
    df,
    top_n,
    parameter,
):

    sales_column = "Nama Sales"

    grouped, x_title = create_parameter_data(
        df,
        sales_column,
        parameter,
    )

    if grouped.empty:
        st.info(
            "Tidak terdapat data sales yang dapat "
            "ditampilkan."
        )

        return

    # Menentukan arah urutan
    ascending = get_sort_ascending()
    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    grouped = (
        grouped
        .sort_values(
            "Jumlah",
            ascending=ascending,
        )
        .head(top_n)
        .sort_values(
            "Jumlah",
            ascending=not ascending,
        )
    )

    title = (
        f"{top_n} Sales {sort_label} Berdasarkan "
        f"{x_title}"
    )

    if parameter == "Nominal Retur":
        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":
        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:
        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    fig = px.bar(
        grouped,
        x="Jumlah",
        y=sales_column,
        orientation="h",
        text="Jumlah",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20),
        ),
        height=max(
            430,
            len(grouped) * 50,
        ),
        margin=dict(
            t=70,
            b=30,
            l=20,
            r=70,
        ),
        xaxis=dict(
            title=x_title,
            separatethousands=True,
        ),
        yaxis=dict(
            title="Nama Sales",
        ),
        showlegend=False,
    )

    if parameter == "Nominal Retur":
        fig.update_xaxes(
            tickprefix="Rp ",
        )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

# HEATMAP DRIVER DAN SALES
def create_driver_sales_heatmap(
    df,
    parameter,
):

    if df.empty:
        st.info(
            "Tidak terdapat data untuk ditampilkan."
        )
        return

    required_columns = [
        "Nama Driver",
        "Nama Sales",
        "Kuantiti Alasan",
        "nilai",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.warning(
            "Kolom yang diperlukan untuk heatmap "
            "tidak tersedia."
        )

        return

    data = df.copy()

    data["Nama Driver"] = (
        data["Nama Driver"]
        .fillna("Tidak Diketahui")
        .astype(str)
        .str.strip()
    )

    data["Nama Sales"] = (
        data["Nama Sales"]
        .fillna("Tidak Diketahui")
        .astype(str)
        .str.strip()
    )

    data["Kuantiti Alasan"] = pd.to_numeric(
        data["Kuantiti Alasan"],
        errors="coerce",
    ).fillna(0)

    data["nilai"] = pd.to_numeric(
        data["nilai"],
        errors="coerce",
    ).fillna(0)

    data = data[
        (data["Nama Driver"] != "")
        & (data["Nama Sales"] != "")
    ].copy()

    if data.empty:

        st.info(
            "Tidak terdapat kombinasi Driver dan Sales "
            "yang dapat dianalisis."
        )

        return

    # Menentukan nilai berdasarkan parameter
    if parameter == "Jumlah Transaksi":
        pair_df = (
            data.groupby(
                [
                    "Nama Driver",
                    "Nama Sales",
                ]
            )
            .size()
            .reset_index(name="Nilai")
        )

        color_title = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":
        pair_df = (
            data.groupby(
                [
                    "Nama Driver",
                    "Nama Sales",
                ]
            )["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Nilai")
        )

        color_title = "Jumlah Barang Retur"

    else:
        pair_df = (
            data.groupby(
                [
                    "Nama Driver",
                    "Nama Sales",
                ]
            )["nilai"]
            .sum()
            .reset_index(name="Nilai")
        )

        color_title = "Nominal Retur"

    pair_df = pair_df[
        pair_df["Nilai"] > 0
    ].copy()

    if pair_df.empty:
        st.info(
            f"Tidak terdapat {color_title.lower()} "
            "yang bernilai lebih dari 0."
        )

        return

    # Menentukan arah urutan
    ascending = get_sort_ascending()

    # Mengambil 20 kombinasi berdasarkan urutan global
    pair_df = (
        pair_df
        .sort_values(
            "Nilai",
            ascending=ascending,
        )
        .head(20)
        .copy()
    )

    # Urutan Driver
    driver_order = (
        pair_df.groupby("Nama Driver")["Nilai"]
        .sum()
        .sort_values(
            ascending=ascending,
        )
        .index
        .tolist()
    )

    # Urutan Sales
    sales_order = (
        pair_df.groupby("Nama Sales")["Nilai"]
        .sum()
        .sort_values(
            ascending=ascending,
        )
        .index
        .tolist()
    )

    matrix = pair_df.pivot(
        index="Nama Driver",
        columns="Nama Sales",
        values="Nilai",
    )

    matrix = matrix.reindex(
        index=driver_order,
        columns=sales_order,
    )

    z_values = matrix.astype(float).values

    text_values = matrix.map(
        lambda value: (
            f"{value:,.0f}"
            if pd.notna(value)
            else ""
        )
    ).values

    if parameter == "Nominal Retur":
        hover_template = (
            "<b>Driver:</b> %{y}<br>"
            "<b>Sales:</b> %{x}<br>"
            "<b>Nominal Retur:</b> "
            "Rp %{z:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":
        hover_template = (
            "<b>Driver:</b> %{y}<br>"
            "<b>Sales:</b> %{x}<br>"
            "<b>Jumlah Barang Retur:</b> "
            "%{z:,.0f}"
            "<extra></extra>"
        )

    else:
        hover_template = (
            "<b>Driver:</b> %{y}<br>"
            "<b>Sales:</b> %{x}<br>"
            "<b>Jumlah Transaksi:</b> "
            "%{z:,.0f}"
            "<extra></extra>"
        )

    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            colorscale="Blues",
            text=text_values,
            texttemplate="%{text}",
            hoverongaps=False,
            xgap=2,
            ygap=2,
            hovertemplate=hover_template,
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                f"Top 20 Kombinasi Driver dan Sales "
                f"{'Terendah' if ascending else 'Tertinggi'} "
                f"Berdasarkan {color_title}"
            ),
            font=dict(size=20),
        ),
        height=max(
            500,
            len(matrix.index) * 45,
        ),
        xaxis=dict(
            title="Nama Sales",
            side="bottom",
            tickangle=-45,
        ),
        yaxis=dict(
            title="Nama Driver",
        ),
        margin=dict(
            t=75,
            b=130,
            l=120,
            r=30,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# TABEL RINGKASAN
def create_summary_table(
    df,
    column,
    parameter,
):

    grouped, x_title = create_parameter_data(
        df,
        column,
        parameter,
    )

    if grouped.empty:
        return pd.DataFrame()
    total = grouped["Jumlah"].sum()

    if total > 0:
        grouped["Persentase"] = (
            grouped["Jumlah"]
            / total
            * 100
        )

    else:
        grouped["Persentase"] = 0
    ascending = get_sort_ascending()

    grouped = (
        grouped
        .sort_values(
            "Jumlah",
            ascending=ascending,
        )
        .reset_index(drop=True)
    )

    grouped.insert(
        0,
        "Ranking",
        range(
            1,
            len(grouped) + 1,
        ),
    )

    grouped["Persentase"] = (
        grouped["Persentase"]
        .map(
            lambda value:
            f"{value:.2f}%"
        )
    )

    if parameter == "Nominal Retur":
        grouped["Jumlah"] = (
            grouped["Jumlah"]
            .apply(format_currency)
        )

    else:
        grouped["Jumlah"] = (
            grouped["Jumlah"]
            .apply(format_number)
        )

    grouped = grouped.rename(
        columns={
            column: (
                "Nama Driver"
                if column == "Nama Driver"
                else "Nama Sales"
            ),
            "Jumlah": x_title,
            "Persentase": "Persentase",
        }
    )
    return grouped

# HALAMAN DRIVER & SALES
def show_driver_sales(df):
    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan filter "
            "yang dipilih."
        )
        return

    data = prepare_driver_sales_data(
        df
    )

    st.title(
        "Driver & Sales"
    )

    st.caption(
        "Analisis distribusi transaksi, barang retur, "
        "dan nominal retur berdasarkan Driver dan Sales."
    )

    st.divider()

    # PARAMETER ANALISIS
    st.subheader(
        "Parameter Analisis"
    )

    parameter = st.selectbox(
        "Jenis Parameter",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="driver_sales_parameter",
    )

    st.divider()

    # HUBUNGAN DRIVER DAN SALES
    st.subheader(
        "Hubungan Driver dan Sales"
    )

    st.caption(
        "Menampilkan kombinasi Driver dan Sales yang "
        "paling dominan berdasarkan parameter yang dipilih. "
        "Kombinasi yang tidak memiliki data tidak ditampilkan "
        "sebagai nilai 0."
    )

    create_driver_sales_heatmap(
        data,
        parameter,
    )

    st.divider()

    # DISTRIBUSI DRIVER DAN SALES
    st.subheader(
        "Distribusi Driver dan Sales"
    )

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    st.caption(
        f"Menampilkan data berdasarkan urutan "
        f"{sort_order.lower()}."
    )

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    # DISTRIBUSI DRIVER
    with col1:
        st.markdown(
            "#### Distribusi Berdasarkan Driver"
        )

        max_driver = get_top_n(
            data,
            "Nama Driver",
        )

        top_driver = st.slider(
            "Top N Driver",
            min_value=1,
            max_value=20,
            value=min(
                5,
                20,
            ),
            step=1,
            key="driver_sales_top_driver",
        )

        create_driver_chart(
            data,
            top_driver,
            parameter,
        )

    # DISTRIBUSI SALES
    with col2:
        st.markdown(
            "#### Distribusi Berdasarkan Sales"
        )

        max_sales = get_top_n(
            data,
            "Nama Sales",
        )

        top_sales = st.slider(
            "Top N Sales",
            min_value=1,
            max_value=20,
            value=min(
                5,
                20,
            ),
            step=1,
            key="driver_sales_top_sales",
        )

        create_sales_chart(
            data,
            top_sales,
            parameter,
        )

    st.divider()

    # TABEL RINGKASAN
    st.subheader(
        "Ringkasan Driver dan Sales"
    )

    st.caption(
        "Menampilkan seluruh Driver dan Sales yang "
        f"tersedia pada data hasil filter dengan urutan "
        f"{sort_order.lower()}."
    )

    tab_driver, tab_sales = st.tabs(
        [
            "Driver",
            "Sales",
        ]
    )

    # TABEL DRIVER
    with tab_driver:

        driver_table = create_summary_table(
            data,
            "Nama Driver",
            parameter,
        )

        st.dataframe(
            driver_table,
            use_container_width=True,
            hide_index=True,
        )

    # TABEL SALES
    with tab_sales:

        sales_table = create_summary_table(
            data,
            "Nama Sales",
            parameter,
        )

        st.dataframe(
            sales_table,
            use_container_width=True,
            hide_index=True,
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

show_driver_sales(df)