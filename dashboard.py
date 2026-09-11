import streamlit as st
import pandas as pd

from utils.data_processing import (
    read_excel_database,
    validate_columns,
    clean_data,
    validate_data,
    get_data_period,
)

# KONFIGURASI HALAMAN

st.set_page_config(
    page_title="Dashboard Retur",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# INISIALISASI SESSION STATE

if "filtered_df" not in st.session_state:
    st.session_state["filtered_df"] = pd.DataFrame()

# DEFINISI HALAMAN

detail_page = st.Page(
    "pages/detail_data.py",
    title="Detail Data",
    icon="📋",
    url_path="detail-data",
)

overview_page = st.Page(
    "pages/overview.py",
    title="Overview",
    icon="📊",
    url_path="overview",
)

reason_page = st.Page(
    "pages/gagal_kirim.py",
    title="Alasan Retur",
    icon="⚠️",
    url_path="alasan-gagal-kirim",
)

depo_page = st.Page(
    "pages/depo.py",
    title="Analisis Depo",
    icon="🏢",
    url_path="analisis-depo",
)

driver_sales_page = st.Page(
    "pages/driver_sales.py",
    title="Driver & Sales",
    icon="🚚",
    url_path="driver-sales",
)

customer_page = st.Page(
    "pages/customer.py",
    title="Customer",
    icon="👥",
    url_path="customer",
)

# JUDUL DASHBOARD

st.title("Dashboard Retur")

st.caption(
    "Dashboard interaktif untuk memantau dan menganalisis "
    "data laporan Retur."
)


# UPLOAD DATA

with st.sidebar:

    st.header("📂 Data")

    uploaded_file = st.file_uploader(
        "Upload laporan Retur",
        type=["xlsx", "xls"],
        help="Upload satu file Excel untuk satu periode bulan.",
    )

    if uploaded_file is None:

        st.info(
            "Silakan upload file Excel laporan Retur "
            "untuk memulai analisis."
        )

        st.stop()


# NAVIGASI

with st.sidebar:

    st.divider()

    st.subheader("Navigasi")

    st.page_link(
        detail_page,
        label="Detail Data",
        icon="📋",
    )

    st.page_link(
        overview_page,
        label="Overview",
        icon="📊",
    )

    st.page_link(
        reason_page,
        label="Alasan Retur",
        icon="⚠️",
    )

    st.page_link(
        depo_page,
        label="Analisis Depo",
        icon="🏢",
    )

    st.page_link(
        driver_sales_page,
        label="Driver & Sales",
        icon="🚚",
    )

    st.page_link(
        customer_page,
        label="Customer",
        icon="👥",
    )

# MEMBACA FILE

df, error_message = read_excel_database(
    uploaded_file
)

if error_message:

    st.error(error_message)

    st.stop()


# VALIDASI KOLOM

is_valid, missing_columns = validate_columns(df)

if not is_valid:

    st.error(
        "File tidak dapat diproses karena terdapat "
        "kolom yang tidak sesuai."
    )

    st.write("Kolom yang belum ditemukan:")

    for column in missing_columns:
        st.write(f"- {column}")

    st.stop()


# MEMBERSIHKAN DATA

df = clean_data(df)


# VALIDASI DATA

validation = validate_data(df)


with st.sidebar:
    st.divider()
    st.subheader("📄 Informasi Data")

    st.write(f"**Nama File:** {uploaded_file.name}")

    jumlah_transaksi = (
        f"{validation['jumlah_baris']:,}".replace(",", ".")
    )

    st.write(
        f"**Jumlah Transaksi:** {jumlah_transaksi}"
    )

    min_date, max_date = get_data_period(df)

    if min_date is not None and max_date is not None:

        st.write(
            f"**Periode:** "
            f"{min_date.strftime('%d/%m/%Y')} - "
            f"{max_date.strftime('%d/%m/%Y')}"
        )

    st.divider()

    with st.sidebar:
        st.subheader("Urutan Analisis")

        st.radio(
            "Urutan Nilai",
            [
                "Tertinggi",
                "Terendah",
            ],
            index=0,
            key="global_sort_order",
        )

# FUNGSI FILTER GLOBAL

def apply_filters(data):

    filtered = data.copy()

    # FILTER PERIODE

    if "Tanggal Kirim" in filtered.columns:

        valid_dates = filtered["Tanggal Kirim"].dropna()

        if not valid_dates.empty:

            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            selected_period = st.sidebar.date_input(
                "Periode",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            if isinstance(selected_period, tuple):

                if len(selected_period) == 2:

                    start_date, end_date = selected_period

                    filtered = filtered[
                        (
                            filtered["Tanggal Kirim"].dt.date
                            >= start_date
                        )
                        &
                        (
                            filtered["Tanggal Kirim"].dt.date
                            <= end_date
                        )
                    ]

    

    # FILTER DIMENSI SELAIN CUSTOMER

    filter_columns = [
        "Nama Depo",
        "Nama Driver",
        "Nama Sales",
        "Category",
        "Keterangan Alasan",
    ]

    for column in filter_columns:

        if column not in filtered.columns:
            continue

        values = (
            filtered[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        values = sorted(
            value
            for value in values.unique()
            if value != ""
        )

        if not values:
            continue

        selected_value = st.sidebar.multiselect(
            column,
            values,
            key=f"global_filter_{column}",
        )

        if selected_value:

            filtered = filtered[
                filtered[column]
                .astype(str)
                .isin(selected_value)
            ]

    # DATA UNTUK KOMPOSISI CUSTOMER
    # Tidak terpengaruh filter Customer sidebar

    composition_df = filtered.copy()

    # FILTER CUSTOMER

    if "Nama Customer" in filtered.columns:

        values = (
            filtered["Nama Customer"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        values = sorted(
            value
            for value in values.unique()
            if value != ""
        )

        if values:

            selected_customer = st.sidebar.multiselect(
                "Nama Customer",
                values,
                key="global_filter_Nama Customer",
            )

            if selected_customer:

                filtered = filtered[
                    filtered["Nama Customer"]
                    .astype(str)
                    .isin(selected_customer)
                ]

    return filtered, composition_df

# FILTER DATA
filtered_df, composition_df = apply_filters(df)

# SIMPAN HASIL FILTER
st.session_state["filtered_df"] = filtered_df

st.session_state[
    "customer_composition_df"
] = composition_df


# INFORMASI HASIL FILTER

with st.sidebar:

    st.divider()

    jumlah_filter = (
        f"{len(filtered_df):,}"
        .replace(",", ".")
    )

    jumlah_total = (
        f"{len(df):,}"
        .replace(",", ".")
    )

    st.caption(
        f"Menampilkan {jumlah_filter} dari "
        f"{jumlah_total} transaksi."
    )


# NAVIGASI APLIKASI

pg = st.navigation(
    [
        detail_page,
        overview_page,
        reason_page,
        depo_page,
        driver_sales_page,
        customer_page,
    ],
    position="hidden",
)

pg.run()