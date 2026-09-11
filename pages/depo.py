import streamlit as st
import pandas as pd
import plotly.express as px


PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
}


# MENENTUKAN ARAH URUTAN

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


# PREPARASI DATA DEPO

def prepare_depo_data(df, depo):

    if depo is None:
        return pd.DataFrame()

    df_depo = df[
        df["Nama Depo"].astype(str) == str(depo)
    ].copy()

    return df_depo


# KPI DEPO

def show_depo_kpis(df_depo):

    jumlah_transaksi = len(df_depo)

    total_stk = df_depo["Kuantiti STK"].sum()
    total_do = df_depo["Kuantiti DO"].sum()
    total_retur = df_depo["Kuantiti Alasan"].sum()
    nilai_retur = df_depo["nilai"].sum()

    persentase_retur = (
        (total_retur / total_stk) * 100
        if total_stk > 0
        else 0
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Jumlah Transaksi",
            format_number(jumlah_transaksi),
        )

    with col2:

        st.metric(
            "Total STK",
            format_number(total_stk),
        )

    with col3:

        st.metric(
            "Total Retur",
            format_number(total_retur),
        )

    with col4:

        st.metric(
            "Persentase Retur",
            f"{persentase_retur:.2f}%",
        )

    with col5:

        st.metric(
            "Nominal Retur",
            format_currency_compact(nilai_retur),
        )


# KOMPOSISI BARANG DO DAN RETUR

def create_quantity_composition(df_depo):

    total_do = df_depo["Kuantiti DO"].sum()
    total_retur = df_depo["Kuantiti Alasan"].sum()

    total_stk = total_do + total_retur

    if total_stk <= 0:

        st.info(
            "Tidak terdapat data DO dan retur "
            "yang dapat divisualisasikan."
        )

        return

    persentase_do = (
        total_do / total_stk
    ) * 100

    persentase_retur = (
        total_retur / total_stk
    ) * 100

    composition_df = pd.DataFrame({
        "Kategori": [
            "Barang DO",
            "Barang Retur",
        ],
        "Jumlah": [
            total_do,
            total_retur,
        ],
    })

    fig = px.pie(
        composition_df,
        names="Kategori",
        values="Jumlah",
        hole=0.55,
    )

    fig.update_traces(
        texttemplate=(
            "%{percent:.2%}<br>"
            "%{value:,.0f} barang"
        ),
        textposition="inside",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Jumlah: %{value:,.0f} barang<br>"
            "Persentase: %{percent:.2%}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title="Komposisi Barang DO dan Retur",
        showlegend=True,
        legend_title_text="Kategori",
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total STK",
            f"{format_number(total_stk)} barang",
        )

    with col2:

        st.metric(
            "Barang DO",
            f"{format_number(total_do)} barang",
            f"{persentase_do:.2f}%",
        )

    with col3:

        st.metric(
            "Barang Retur",
            f"{format_number(total_retur)} barang",
            f"{persentase_retur:.2f}%",
        )


# TREN DEPO

def create_depo_trend(df_depo, parameter):

    if df_depo.empty:

        st.info(
            "Tidak terdapat data untuk ditampilkan."
        )

        return

    trend_df = (
        df_depo
        .dropna(subset=["Tanggal Kirim"])
        .groupby("Tanggal Kirim")
        .agg(
            Jumlah_Transaksi=(
                "Tanggal Kirim",
                "size",
            ),
            Jumlah_Retur=(
                "Kuantiti Alasan",
                "sum",
            ),
            Nominal_Retur=(
                "nilai",
                "sum",
            ),
        )
        .reset_index()
        .sort_values("Tanggal Kirim")
    )

    if parameter == "Jumlah Transaksi":

        y_column = "Jumlah_Transaksi"
        y_title = "Jumlah Transaksi"
        title = "Tren Jumlah Transaksi"

        hover_template = (
            "<b>%{x|%d/%m/%Y}</b><br>"
            "Jumlah Transaksi: %{y:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        y_column = "Jumlah_Retur"
        y_title = "Jumlah Barang Retur"
        title = "Tren Jumlah Barang Retur"

        hover_template = (
            "<b>%{x|%d/%m/%Y}</b><br>"
            "Barang Retur: %{y:,.0f}"
            "<extra></extra>"
        )

    else:

        y_column = "Nominal_Retur"
        y_title = "Nominal Retur"
        title = "Tren Nominal Retur"

        hover_template = (
            "<b>%{x|%d/%m/%Y}</b><br>"
            "Nominal Retur: Rp %{y:,.0f}"
            "<extra></extra>"
        )

    fig = px.line(
        trend_df,
        x="Tanggal Kirim",
        y=y_column,
        markers=True,
    )

    fig.update_traces(
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        xaxis_title="Tanggal Kirim",
        yaxis_title=y_title,
        hovermode="x unified",
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# DISTRIBUSI ALASAN Retur

def create_depo_reason_chart(
    df_depo,
    top_n,
    parameter,
):

    if df_depo.empty:

        st.info(
            "Tidak terdapat data untuk ditampilkan."
        )

        return

    reason_column = "Keterangan Alasan"

    reason_df = df_depo[
        df_depo[reason_column].notna()
        & (
            df_depo[reason_column]
            .astype(str)
            .str.strip()
            != ""
        )
    ].copy()

    if reason_df.empty:

        st.info(
            "Tidak terdapat keterangan alasan "
            "yang dapat ditampilkan."
        )

        return

    # Menentukan arah urutan

    ascending = get_sort_ascending()

    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    if parameter == "Jumlah Transaksi":

        grouped = (
            reason_df
            .groupby(reason_column)
            .size()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Transaksi"

        title = (
            f"{top_n} Alasan {sort_label} Berdasarkan "
            "Jumlah Transaksi"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        grouped = (
            reason_df
            .groupby(reason_column)["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Barang Retur"

        title = (
            f"{top_n} Alasan {sort_label} Berdasarkan "
            "Jumlah Barang Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:

        grouped = (
            reason_df
            .groupby(reason_column)["nilai"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Nominal Retur"

        title = (
            f"{top_n} Alasan {sort_label} Berdasarkan "
            "Nominal Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    # Mengambil data berdasarkan urutan analisis

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

    fig = px.bar(
        grouped,
        x="Jumlah",
        y=reason_column,
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title="Keterangan Alasan",
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# DISTRIBUSI CUSTOMER

def create_depo_customer_chart(
    df_depo,
    top_n,
    parameter,
):

    if df_depo.empty:

        st.info(
            "Tidak terdapat data untuk ditampilkan."
        )

        return

    customer_column = "Nama Customer"

    # Menentukan arah urutan

    ascending = get_sort_ascending()

    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    if parameter == "Jumlah Transaksi":

        grouped = (
            df_depo
            .groupby(customer_column)
            .size()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Transaksi"

        title = (
            f"{top_n} Customer {sort_label} Berdasarkan "
            "Jumlah Transaksi"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        grouped = (
            df_depo
            .groupby(customer_column)["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Barang Retur"

        title = (
            f"{top_n} Customer {sort_label} Berdasarkan "
            "Jumlah Barang Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:

        grouped = (
            df_depo
            .groupby(customer_column)["nilai"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Nominal Retur"

        title = (
            f"{top_n} Customer {sort_label} Berdasarkan "
            "Nominal Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    grouped = grouped.dropna(
        subset=[customer_column]
    )

    # Mengambil data berdasarkan urutan analisis

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

    fig = px.bar(
        grouped,
        x="Jumlah",
        y=customer_column,
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title="Nama Customer",
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# DISTRIBUSI DRIVER

def create_depo_driver_chart(
    df_depo,
    top_n,
    parameter,
):

    if df_depo.empty:

        st.info(
            "Tidak terdapat data untuk ditampilkan."
        )

        return

    driver_column = "Nama Driver"

    # Menentukan arah urutan

    ascending = get_sort_ascending()

    sort_label = (
        "Tertinggi"
        if not ascending
        else "Terendah"
    )

    if parameter == "Jumlah Transaksi":

        grouped = (
            df_depo
            .groupby(driver_column)
            .size()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Transaksi"

        title = (
            f"{top_n} Driver {sort_label} Berdasarkan "
            "Jumlah Transaksi"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Jumlah Transaksi: %{x:,.0f}"
            "<extra></extra>"
        )

    elif parameter == "Jumlah Barang Retur":

        grouped = (
            df_depo
            .groupby(driver_column)["Kuantiti Alasan"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Jumlah Barang Retur"

        title = (
            f"{top_n} Driver {sort_label} Berdasarkan "
            "Jumlah Barang Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Barang Retur: %{x:,.0f}"
            "<extra></extra>"
        )

    else:

        grouped = (
            df_depo
            .groupby(driver_column)["nilai"]
            .sum()
            .reset_index(name="Jumlah")
        )

        x_title = "Nominal Retur"

        title = (
            f"{top_n} Driver {sort_label} Berdasarkan "
            "Nominal Retur"
        )

        hover_template = (
            "<b>%{y}</b><br>"
            "Nominal Retur: Rp %{x:,.0f}"
            "<extra></extra>"
        )

    grouped = grouped.dropna(
        subset=[driver_column]
    )

    # Mengambil data berdasarkan urutan analisis

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

    fig = px.bar(
        grouped,
        x="Jumlah",
        y=driver_column,
        orientation="h",
    )

    fig.update_traces(
        hovertemplate=hover_template,
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title="Nama Driver",
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


# HALAMAN DEPO

def show_depo(df):

    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan filter "
            "yang dipilih."
        )

        return

    depo_values = (
        df["Nama Depo"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    depo_values = sorted(
        value
        for value in depo_values.unique()
        if value != ""
    )

    if not depo_values:

        st.warning(
            "Tidak terdapat data Nama Depo "
            "yang dapat dianalisis."
        )

        return

    st.title("Analisis Depo")

    st.caption(
        "Analisis karakteristik retur berdasarkan depo "
        "yang dipilih."
    )

    selected_depo = st.selectbox(
        "Pilih Depo untuk Dianalisis",
        depo_values,
        key="analisis_depo_select",
    )

    df_depo = prepare_depo_data(
        df,
        selected_depo,
    )

    if df_depo.empty:

        st.warning(
            "Tidak terdapat data untuk depo yang dipilih."
        )

        return

    st.subheader(
        f"Ringkasan Depo: {selected_depo}"
    )

    show_depo_kpis(df_depo)

    st.divider()

    st.subheader(
        "Komposisi Barang DO dan Retur"
    )

    create_quantity_composition(
        df_depo
    )

    st.divider()

    parameter = st.selectbox(
        "Jenis Parameter",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="depo_parameter",
    )

    st.subheader(
        "Tren Retur Berdasarkan Waktu"
    )

    st.caption(
        "Menampilkan perkembangan retur berdasarkan tanggal "
        "pengiriman pada depo yang dipilih."
    )

    create_depo_trend(
        df_depo,
        parameter,
    )

    st.divider()

    st.subheader(
        "Distribusi Retur"
    )

    st.caption(
        "Menampilkan Retur yang paling dominan "
        "berdasarkan parameter yang dipilih."
    )

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:

        st.markdown(
            "#### Distribusi Alasan Retur"
        )

        max_reason = max(
            1,
            df_depo["Keterangan Alasan"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique(),
        )

        top_reason = st.slider(
            "Top N Alasan",
            min_value=1,
            max_value=max_reason,
            value=min(5, max_reason),
            step=1,
            key="depo_top_reason",
        )

        create_depo_reason_chart(
            df_depo,
            top_reason,
            parameter,
        )

    with col2:

        st.markdown(
            "#### Distribusi Retur Berdasarkan Customer"
        )

        max_customer = max(
            1,
            df_depo["Nama Customer"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique(),
        )

        top_customer = st.slider(
            "Top N Customer",
            min_value=1,
            max_value=20,
            value=min(5, 20),
            step=1,
            key="depo_top_customer",
        )

        create_depo_customer_chart(
            df_depo,
            top_customer,
            parameter,
        )

    st.divider()

    st.subheader(
        "Distribusi Retur Berdasarkan Driver"
    )

    st.caption(
        "Menampilkan driver dengan kontribusi terbesar "
        "berdasarkan parameter yang dipilih."
    )

    max_driver = max(
        1,
        df_depo["Nama Driver"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique(),
    )

    top_driver = st.slider(
        "Top N Driver",
        min_value=1,
        max_value=max_driver,
        value=min(5, max_driver),
        step=1,
        key="depo_top_driver",
    )

    create_depo_driver_chart(
        df_depo,
        top_driver,
        parameter,
    )


# MENJALANKAN HALAMAN

if "filtered_df" not in st.session_state:

    st.warning(
        "Data belum tersedia. Silakan upload "
        "file terlebih dahulu."
    )

    st.stop()


df = st.session_state[
    "filtered_df"
]

show_depo(df)