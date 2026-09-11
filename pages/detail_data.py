import streamlit as st
import pandas as pd


# KONFIGURASI TAMPILAN

DATAFRAME_HEIGHT = 600

DISPLAY_COLUMNS = [
    "Nama Depo",
    "Tanggal Kirim",
    "Nama Driver",
    "Nama Sales",
    "Nama Customer",
    "Category",
    "Keterangan Alasan",
    "Kuantiti STK",
    "Kuantiti DO",
    "Kuantiti Alasan",
    "nilai",
]


# FORMAT ANGKA

def format_number(value):
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value):
    return f"Rp {value:,.0f}".replace(",", ".")


# MENENTUKAN ARAH URUTAN

def get_sort_ascending():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order == "Terendah"


# MENENTUKAN LABEL URUTAN

def get_sort_label():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order


# PREPARASI DATA

def prepare_detail_data(df):

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

    text_columns = [
        "Nama Depo",
        "Nama Driver",
        "Nama Sales",
        "Nama Customer",
        "Category",
        "Keterangan Alasan",
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


# FORMAT DATA UNTUK DITAMPILKAN

def format_detail_table(df):

    data = df.copy()

    if "Tanggal Kirim" in data.columns:

        data["Tanggal Kirim"] = data[
            "Tanggal Kirim"
        ].dt.strftime("%d/%m/%Y")

    numeric_columns = [
        "Kuantiti STK",
        "Kuantiti DO",
        "Kuantiti Alasan",
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = data[column].apply(
                format_number
            )

    if "nilai" in data.columns:

        data["nilai"] = data["nilai"].apply(
            format_currency
        )

    return data


# FILTER TAMBAHAN TABEL DETAIL

def apply_detail_search(data):

    filtered = data.copy()

    st.subheader("Pencarian Data")

    search_column = st.selectbox(
        "Cari berdasarkan",
        [
            "Semua Kolom",
            "Nama Customer",
            "Nama Driver",
            "Nama Sales",
            "Nama Depo",
            "Keterangan Alasan",
        ],
        key="detail_search_column",
    )

    search_keyword = st.text_input(
        "Kata kunci",
        placeholder="Masukkan kata kunci pencarian...",
        key="detail_search_keyword",
    )

    if search_keyword:

        keyword = search_keyword.strip().lower()

        if search_column == "Semua Kolom":

            text_data = filtered.astype(str)

            mask = text_data.apply(
                lambda column: column.str.lower().str.contains(
                    keyword,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)

        else:

            if search_column in filtered.columns:

                mask = (
                    filtered[search_column]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        keyword,
                        na=False,
                        regex=False,
                    )
                )

            else:

                mask = pd.Series(
                    False,
                    index=filtered.index,
                )

        filtered = filtered[mask]

    return filtered


# MENGURUTKAN DATA DETAIL

def sort_detail_data(
    df,
    parameter,
):

    data = df.copy()

    if data.empty:

        return data

    ascending = get_sort_ascending()

    if parameter == "Jumlah Transaksi":

        return data.reset_index(drop=True)

    elif parameter == "Jumlah Barang Retur":

        sort_column = "Kuantiti Alasan"

    else:

        sort_column = "nilai"

    if sort_column in data.columns:

        data = (
            data
            .sort_values(
                sort_column,
                ascending=ascending,
                kind="stable",
            )
            .reset_index(drop=True)
        )

    return data


# TABEL DETAIL DATA

def create_detail_table(df):

    display_df = df.copy()

    available_columns = [
        column
        for column in DISPLAY_COLUMNS
        if column in display_df.columns
    ]

    display_df = display_df[
        available_columns
    ].copy()

    display_df = format_detail_table(
        display_df
    )

    column_config = {}

    if "Nama Depo" in display_df.columns:

        column_config["Nama Depo"] = (
            st.column_config.TextColumn(
                "Nama Depo"
            )
        )

    if "Tanggal Kirim" in display_df.columns:

        column_config["Tanggal Kirim"] = (
            st.column_config.TextColumn(
                "Tanggal Kirim"
            )
        )

    if "Nama Driver" in display_df.columns:

        column_config["Nama Driver"] = (
            st.column_config.TextColumn(
                "Nama Driver"
            )
        )

    if "Nama Sales" in display_df.columns:

        column_config["Nama Sales"] = (
            st.column_config.TextColumn(
                "Nama Sales"
            )
        )

    if "Nama Customer" in display_df.columns:

        column_config["Nama Customer"] = (
            st.column_config.TextColumn(
                "Nama Customer"
            )
        )

    if "Category" in display_df.columns:

        column_config["Category"] = (
            st.column_config.TextColumn(
                "Category"
            )
        )

    if "Keterangan Alasan" in display_df.columns:

        column_config["Keterangan Alasan"] = (
            st.column_config.TextColumn(
                "Keterangan Alasan"
            )
        )

    if "Kuantiti STK" in display_df.columns:

        column_config["Kuantiti STK"] = (
            st.column_config.TextColumn(
                "Kuantiti STK"
            )
        )

    if "Kuantiti DO" in display_df.columns:

        column_config["Kuantiti DO"] = (
            st.column_config.TextColumn(
                "Kuantiti DO"
            )
        )

    if "Kuantiti Alasan" in display_df.columns:

        column_config["Kuantiti Alasan"] = (
            st.column_config.TextColumn(
                "Kuantiti Alasan"
            )
        )

    if "nilai" in display_df.columns:

        column_config["nilai"] = (
            st.column_config.TextColumn(
                "Nilai Retur"
            )
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=DATAFRAME_HEIGHT,
        hide_index=True,
        column_config=column_config,
    )


# HALAMAN DETAIL DATA

def show_detail_data(df):

    st.title("Detail Data")

    st.caption(
        "Menampilkan data transaksi secara detail "
        "berdasarkan hasil filter yang dipilih."
    )

    st.divider()

    if df.empty:

        st.warning(
            "Tidak ada data yang sesuai dengan filter "
            "yang dipilih."
        )

        return

    data = prepare_detail_data(
        df
    )

    # RINGKASAN DATA

    st.subheader("Ringkasan Data")

    total_data = len(data)

    total_stk = (
        data["Kuantiti STK"].sum()
        if "Kuantiti STK" in data.columns
        else 0
    )

    total_do = (
        data["Kuantiti DO"].sum()
        if "Kuantiti DO" in data.columns
        else 0
    )

    total_retur = (
        data["Kuantiti Alasan"].sum()
        if "Kuantiti Alasan" in data.columns
        else 0
    )

    total_nilai = (
        data["nilai"].sum()
        if "nilai" in data.columns
        else 0
    )

    col1, col2, col3, col4, col5 = st.columns(
        5,
        gap="medium",
    )

    with col1:

        st.metric(
            "Jumlah Data",
            format_number(total_data),
        )

    with col2:

        st.metric(
            "Total STK",
            format_number(total_stk),
        )

    with col3:

        st.metric(
            "Total DO",
            format_number(total_do),
        )

    with col4:

        st.metric(
            "Total Retur",
            format_number(total_retur),
        )

    with col5:

        st.metric(
            "Nilai Retur",
            format_currency(total_nilai),
        )

    st.divider()

    # PENCARIAN

    data_search = apply_detail_search(
        data
    )

    st.divider()

    # URUTAN DATA

    st.subheader("Urutan Data")

    parameter = st.selectbox(
        "Urutkan berdasarkan",
        [
            "Jumlah Transaksi",
            "Jumlah Barang Retur",
            "Nominal Retur",
        ],
        key="detail_sort_parameter",
    )

    data_search = sort_detail_data(
        data_search,
        parameter,
    )

    st.divider()

    # INFORMASI HASIL PENCARIAN

    st.subheader("Data Transaksi")

    jumlah_data = len(data_search)

    st.caption(
        f"Menampilkan {format_number(jumlah_data)} "
        f"dari {format_number(total_data)} data."
    )

    if data_search.empty:

        st.info(
            "Tidak ditemukan data berdasarkan "
            "kata kunci pencarian."
        )

        return

    # TABEL

    create_detail_table(
        data_search
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

show_detail_data(
    df
)