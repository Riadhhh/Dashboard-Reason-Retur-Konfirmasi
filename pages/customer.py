import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}

def get_sort_ascending():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order == "Terendah"

# FORMAT ANGKA
def format_number(value):
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value):
    return f"Rp {value:,.0f}".replace(",", ".")


# PREPARASI DATA

def prepare_customer_data(df):

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

    text_columns = [
        "Nama Customer",
        "Nama Driver",
        "Nama Sales",
    ]

    for column in text_columns:

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


# JUMLAH CUSTOMER UNIK

def get_unique_count(df, column):

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


# DATA KONTRIBUSI CUSTOMER

def create_customer_parameter_data(
    df,
    parameter,
):

    customer_column = "Nama Customer"

    if parameter == "Jumlah Transaksi":

        grouped = (
            df.groupby(customer_column)
            .size()
            .reset_index(name="Jumlah")
        )

        parameter_label = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":

        grouped = (
            df.groupby(customer_column)["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Jumlah")
        )

        parameter_label = "Jumlah Barang Retur"

    else:

        grouped = (
            df.groupby(customer_column)["nilai"]
            .sum()
            .reset_index(name="Jumlah")
        )

        parameter_label = "Nominal Retur"

    grouped = grouped[
        grouped[customer_column].notna()
    ].copy()

    grouped[customer_column] = (
        grouped[customer_column]
        .astype(str)
        .str.strip()
    )

    grouped = grouped[
        grouped[customer_column] != ""
    ]

    return grouped, parameter_label


# GRAFIK KONTRIBUSI CUSTOMER

def create_customer_contribution_chart(
    df,
    top_n,
    parameter,
):

    grouped, parameter_label = (
        create_customer_parameter_data(
            df,
            parameter,
        )
    )

    if grouped.empty:

        st.info(
            "Tidak terdapat data Customer yang "
            "dapat ditampilkan."
        )

        return

    total = grouped["Jumlah"].sum()

    ascending = get_sort_ascending()

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
        .copy()
    )

    if total > 0:

        grouped["Persentase"] = (
            grouped["Jumlah"]
            / total
            * 100
        )

    else:

        grouped["Persentase"] = 0

    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    title = (
        f"{top_n} Customer {sort_label} Berdasarkan "
        f"{parameter_label}"
    )

    if parameter == "Nominal Retur":

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}<br>"
            "Kontribusi: %{customdata[0]:.2f}%"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Barang Retur: %{x:,.0f}<br>"
            "Kontribusi: %{customdata[0]:.2f}%"
            "<extra></extra>"
        )

    else:

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}<br>"
            "Kontribusi: %{customdata[0]:.2f}%"
            "<extra></extra>"
        )

    fig = px.bar(
        grouped,
        x="Jumlah",
        y="Nama Customer",
        orientation="h",
        text="Jumlah",
        custom_data=["Persentase"],
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
            r=90,
        ),
        xaxis=dict(
            title=parameter_label,
            separatethousands=True,
        ),
        yaxis=dict(
            title="Nama Customer",
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


# KOMPOSISI CUSTOMER

def create_customer_composition(
    df,
    selected_customers,
    parameter,
):

    grouped, parameter_label = (
        create_customer_parameter_data(
            df,
            parameter,
        )
    )

    if grouped.empty:

        st.info(
            "Tidak terdapat data Customer "
            "yang dapat dianalisis."
        )

        return

    composition_df = grouped[
        grouped["Nama Customer"].isin(
            selected_customers
        )
    ].copy()

    if composition_df.empty:

        st.info(
            "Pilih minimal satu Customer "
            "untuk menampilkan komposisi."
        )

        return

    composition_df = composition_df.sort_values(
        "Jumlah",
        ascending=get_sort_ascending(),
    )

    fig = px.pie(
        composition_df,
        names="Nama Customer",
        values="Jumlah",
        hole=0.55,
    )

    if parameter == "Nominal Retur":

        hover_template = (
            "<b>%{label}</b><br>"
            "Nominal Retur: Rp %{value:,.0f}<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        hover_template = (
            "<b>%{label}</b><br>"
            "Jumlah Barang Retur: %{value:,.0f}<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        )

    else:

        hover_template = (
            "<b>%{label}</b><br>"
            "Jumlah Transaksi: %{value:,.0f}<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=(
            f"Komposisi Customer Berdasarkan "
            f"{parameter_label}"
        ),
        height=450,
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
        legend_title_text="Customer",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# HEATMAP CUSTOMER DENGAN DRIVER ATAU SALES

def create_customer_relation_heatmap(
    df,
    relation_column,
    parameter,
):

    customer_column = "Nama Customer"

    data = df.copy()

    required_columns = [
        customer_column,
        relation_column,
        "Kuantiti Alasan",
        "nilai",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        st.warning(
            "Kolom yang diperlukan untuk heatmap "
            "tidak tersedia."
        )

        return

    for column in [
        customer_column,
        relation_column,
    ]:

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

    data["Kuantiti Alasan"] = pd.to_numeric(
        data["Kuantiti Alasan"],
        errors="coerce",
    ).fillna(0)

    data["nilai"] = pd.to_numeric(
        data["nilai"],
        errors="coerce",
    ).fillna(0)

    # Menentukan 10 Customer berdasarkan urutan analisis

    ascending = get_sort_ascending()

    if parameter == "Jumlah Transaksi":

        top_customers = (
            data.groupby(customer_column)
            .size()
            .sort_values(
                ascending=ascending,
            )
            .head(10)
            .index
        )

    elif parameter == "Jumlah Barang Retur":

        top_customers = (
            data.groupby(customer_column)["Kuantiti Alasan"]
            .sum()
            .sort_values(
                ascending=ascending,
            )
            .head(10)
            .index
        )

    else:

        top_customers = (
            data.groupby(customer_column)["nilai"]
            .sum()
            .sort_values(
                ascending=ascending,
            )
            .head(10)
            .index
        )

    data = data[
        data[customer_column].isin(top_customers)
    ].copy()

    if data.empty:

        st.info(
            "Tidak terdapat Customer yang dapat "
            "digunakan untuk heatmap."
        )

        return

    # Menghitung hubungan Customer dengan Driver atau Sales

    if parameter == "Jumlah Transaksi":

        grouped = (
            data.groupby(
                [
                    customer_column,
                    relation_column,
                ]
            )
            .size()
            .reset_index(name="Nilai")
        )

        value_label = "Jumlah Transaksi"

    elif parameter == "Jumlah Barang Retur":

        grouped = (
            data.groupby(
                [
                    customer_column,
                    relation_column,
                ]
            )["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Nilai")
        )

        value_label = "Jumlah Barang Retur"

    else:

        grouped = (
            data.groupby(
                [
                    customer_column,
                    relation_column,
                ]
            )["nilai"]
            .sum()
            .reset_index(name="Nilai")
        )

        value_label = "Nominal Retur"

    grouped = grouped[
        grouped["Nilai"] > 0
    ].copy()

    if grouped.empty:

        st.info(
            "Tidak terdapat hubungan Customer dan "
            f"{relation_column} yang dapat dianalisis."
        )

        return

    # Membatasi hubungan menjadi 20 kombinasi berdasarkan urutan analisis

    grouped = (
        grouped
        .sort_values(
            "Nilai",
            ascending=get_sort_ascending(),
        )
        .head(20)
        .copy()
    )

    ascending = get_sort_ascending()

    customer_order = (
        grouped.groupby(customer_column)["Nilai"]
        .sum()
        .sort_values(
            ascending=ascending,
        )
        .index
        .tolist()
    )

    relation_order = (
        grouped.groupby(relation_column)["Nilai"]
        .sum()
        .sort_values(
            ascending=ascending,
        )
        .index
        .tolist()
    )

    matrix = grouped.pivot(
        index=customer_column,
        columns=relation_column,
        values="Nilai",
    )

    matrix = matrix.reindex(
        index=customer_order,
        columns=relation_order,
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
            "<b>Customer:</b> %{y}<br>"
            f"<b>{relation_column}:</b> "
            "%{x}<br>"
            "<b>Nominal Retur:</b> "
            "Rp %{z:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        hover_template = (
            "<b>Customer:</b> %{y}<br>"
            f"<b>{relation_column}:</b> "
            "%{x}<br>"
            "<b>Jumlah Barang Retur:</b> "
            "%{z:,.0f}"
            "<extra></extra>"
        )

    else:

        hover_template = (
            "<b>Customer:</b> %{y}<br>"
            f"<b>{relation_column}:</b> "
            "%{x}<br>"
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
                f"Hubungan Top 10 Customer dan "
                f"{relation_column} Berdasarkan "
                f"{value_label}"
            ),
            font=dict(size=20),
        ),
        height=max(
            500,
            len(matrix.index) * 45,
        ),
        xaxis=dict(
            title=relation_column,
            side="bottom",
            tickangle=-45,
        ),
        yaxis=dict(
            title="Nama Customer",
        ),
        margin=dict(
            t=75,
            b=130,
            l=130,
            r=30,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# TABEL RINGKASAN CUSTOMER

def create_customer_summary_table(
    df,
    parameter,
):

    grouped, parameter_label = (
        create_customer_parameter_data(
            df,
            parameter,
        )
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
            "Jumlah": parameter_label
        }
    )

    return grouped


# HALAMAN CUSTOMER

def show_customer(df):

    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan filter "
            "yang dipilih."
        )

        return

    data = prepare_customer_data(df)

    st.title("Customer")

    st.caption(
        "Analisis kontribusi Customer terhadap transaksi, "
        "barang retur, dan nominal retur."
    )

    st.divider()

    # PARAMETER ANALISIS

    st.subheader("Parameter Analisis")

    parameter = st.selectbox(
        "Jenis Parameter",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="customer_parameter",
    )

    st.divider()

    # KONTRIBUSI CUSTOMER

    st.subheader("Kontribusi Customer")

    st.caption(
        "Menampilkan Customer dengan kontribusi terbesar "
        "berdasarkan parameter yang dipilih."
    )

    max_customer = get_unique_count(
        data,
        "Nama Customer",
    )

    top_customer = st.slider(
        "Top N Customer",
        min_value=1,
        max_value=20,
        value=min(
            10,
            20,
        ),
        step=1,
        key="customer_top_n",
    )

    create_customer_contribution_chart(
        data,
        top_customer,
        parameter,
    )

    st.divider()

    # KOMPOSISI CUSTOMER

    st.subheader("Komposisi Customer")

    st.caption(
        "Pilih Customer yang ingin dibandingkan "
        "dengan maksimal 7 Customer."
    )

    # Menggunakan data khusus komposisi yang tidak terpengaruh
    # oleh filter Customer di sidebar

    composition_source = st.session_state.get(
        "customer_composition_df",
        data,
    )

    composition_source = prepare_customer_data(
        composition_source
    )

    available_customers = sorted(
        composition_source["Nama Customer"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_customers = st.multiselect(
        "Pilih Customer",
        options=available_customers,
        max_selections=7,
        key="customer_composition_selection",
    )

    create_customer_composition(
        composition_source,
        selected_customers,
        parameter,
    )

    st.divider()

    # HUBUNGAN CUSTOMER DAN DRIVER

    st.subheader("Hubungan Customer dan Driver")

    st.caption(
        "Menampilkan hubungan 10 Customer teratas dengan "
        "Driver berdasarkan parameter yang dipilih."
    )

    create_customer_relation_heatmap(
        data,
        "Nama Driver",
        parameter,
    )

    st.divider()

    # HUBUNGAN CUSTOMER DAN SALES

    st.subheader("Hubungan Customer dan Sales")

    st.caption(
        "Menampilkan hubungan 10 Customer teratas dengan "
        "Sales berdasarkan parameter yang dipilih."
    )

    create_customer_relation_heatmap(
        data,
        "Nama Sales",
        parameter,
    )

    st.divider()

    # RINGKASAN CUSTOMER

    st.subheader("Ringkasan Customer")

    st.caption(
        "Menampilkan ranking dan persentase kontribusi "
        "seluruh Customer berdasarkan parameter yang dipilih."
    )

    customer_table = create_customer_summary_table(
        data,
        parameter,
    )

    st.dataframe(
        customer_table,
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

show_customer(df)