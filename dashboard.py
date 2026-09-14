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
    layout="wide",
    initial_sidebar_state="expanded",
)

# INISIALISASI SESSION STATE
if "filtered_df" not in st.session_state:
    st.session_state["filtered_df"] = pd.DataFrame()

if "customer_composition_df" not in st.session_state:
    st.session_state["customer_composition_df"] = pd.DataFrame()

# DEFINISI HALAMAN
detail_page = st.Page(
    "pages/detail_data.py",
    title="Detail Data",
    url_path="detail-data",
)

overview_page = st.Page(
    "pages/overview.py",
    title="Overview",
    url_path="overview",
)

reason_page = st.Page(
    "pages/gagal_kirim.py",
    title="Alasan Retur",
    url_path="alasan-gagal-kirim",
)

depo_page = st.Page(
    "pages/depo.py",
    title="Analisis Depo",
    url_path="analisis-depo",
)

driver_sales_page = st.Page(
    "pages/driver_sales.py",
    title="Driver & Sales",
    url_path="driver-sales",
)

customer_page = st.Page(
    "pages/customer.py",
    title="Customer",
    url_path="customer",
)

# DEFINISI NAVIGASI APLIKASI
pages = [
    detail_page,
    overview_page,
    reason_page,
    depo_page,
    driver_sales_page,
    customer_page,
]

# NAVIGASI STREAMLIT
pg = st.navigation(
    pages,
    position="hidden",
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
    uploaded_files = st.file_uploader(
        "Upload laporan Retur",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="Upload satu file Excel untuk satu periode bulan.",
    )


# KONDISI BELUM ADA FILE
if not uploaded_files:
    with st.sidebar:

        st.info(
            "Silakan upload file Excel laporan Retur "
            "untuk memulai analisis."
        )

    st.info(
        "Upload file Excel melalui menu Data di sidebar "
        "untuk menampilkan dashboard."
    )

    st.stop()

# MEMBACA DAN MENGGABUNGKAN FILE
data_frames = []
file_errors = []

for uploaded_file in uploaded_files:

    file_df, error_message = read_excel_database(
        uploaded_file
    )

    # CEK KESALAHAN PEMBACAAN FILE
    if error_message:

        file_errors.append(
            f"{uploaded_file.name}: {error_message}"
        )

        continue

    # VALIDASI KOLOM
    is_valid, missing_columns = validate_columns(
        file_df
    )

    if not is_valid:

        file_errors.append(
            f"{uploaded_file.name}: kolom tidak lengkap."
        )

        continue

    # MEMBERSIHKAN DATA
    file_df = clean_data(file_df)

    # MENYIMPAN DATA FILE
    data_frames.append(file_df)

# CEK FILE YANG BERMASALAH
if file_errors:

    for error in file_errors:
        st.error(error)

    st.stop()

# CEK HASIL DATA
if not data_frames:

    st.error(
        "Tidak ada file yang berhasil diproses."
    )

    st.stop()

# MENGGABUNGKAN SEMUA DATA
df = pd.concat(
    data_frames,
    ignore_index=True,
)

# VALIDASI DATA GABUNGAN
validation = validate_data(df)

# VALIDASI DATA
validation = validate_data(df)

# INFORMASI DATA
with st.sidebar:

    st.divider()

    st.subheader("📄 Informasi Data")

    st.write("**File yang diupload:**")

    for uploaded_file in uploaded_files:
        st.write(f"- {uploaded_file.name}")

    jumlah_transaksi = (
        f"{validation['jumlah_baris']:,}"
        .replace(",", ".")
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

# NAVIGASI CUSTOM
with st.sidebar:

    st.divider()

    st.subheader("🧭 Navigasi")

    st.page_link(
        detail_page,
        label="📋 Detail Data",
    )

    st.page_link(
        overview_page,
        label="📊 Overview",
    )

    st.page_link(
        reason_page,
        label="⚠️ Alasan Retur",
    )

    st.page_link(
        depo_page,
        label="🏢 Analisis Depo",
    )

    st.page_link(
        driver_sales_page,
        label="🚚 Driver & Sales",
    )

    st.page_link(
        customer_page,
        label="👥 Customer",
    )


# URUTAN ANALISIS
with st.sidebar:

    st.divider()

    st.subheader("🔽 Urutan Analisis")

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

        valid_dates = (
            filtered["Tanggal Kirim"]
            .dropna()
        )

        if not valid_dates.empty:

            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            selected_period = st.sidebar.date_input(
                "Periode",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            if isinstance(
                selected_period,
                tuple,
            ):

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


    # DATA KOMPOSISI CUSTOMER
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

# MENJALANKAN HALAMAN
pg.run()