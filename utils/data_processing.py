import pandas as pd

REQUIRED_COLUMNS = [
    "Region",
    "Id Depo",
    "Nama Depo",
    "Tanggal Kirim",
    "szfdjrid",
    "szdriverid",
    "Nama Driver",
    "Department",
    "szfdoid",
    "szfsoid",
    "szcustid",
    "Nama Customer",
    "Category",
    "szsalesid",
    "Nama Sales",
    "szproductid",
    "szcompuomid",
    "sznickname",
    "Kuantiti STK",
    "Kuantiti DO",
    "Kuantiti Alasan",
    "Id Alasan",
    "Keterangan Alasan",
    "nilai",
    "Kategori Gagal Kirim",
]

NUMERIC_COLUMNS = [
    "Kuantiti STK",
    "Kuantiti DO",
    "Kuantiti Alasan",
    "nilai",
]

TEXT_COLUMNS = [
    "Region",
    "Id Depo",
    "Nama Depo",
    "szfdjrid",
    "szdriverid",
    "Nama Driver",
    "Department",
    "szfdoid",
    "szfsoid",
    "szcustid",
    "Nama Customer",
    "Category",
    "szsalesid",
    "Nama Sales",
    "szproductid",
    "szcompuomid",
    "sznickname",
    "Id Alasan",
    "Keterangan Alasan",
    "Kategori Gagal Kirim",
]

# MEMBACA FILE EXCEL
def read_excel_database(uploaded_file):
    """
    Membaca file Excel dan mengambil sheet 'Database'.

    Returns:
        df: DataFrame hasil pembacaan
        error: pesan error jika terjadi kesalahan
    """

    try:
        # Membaca nama-nama sheet terlebih dahulu
        excel_file = pd.ExcelFile(uploaded_file)

        if "Database" not in excel_file.sheet_names:
            return None, (
                "Sheet 'Database' tidak ditemukan. "
                f"Sheet yang tersedia: {', '.join(excel_file.sheet_names)}"
            )

        # Membaca sheet Database
        df = pd.read_excel(
            uploaded_file,
            sheet_name="Database"
        )

        return df, None

    except Exception as e:
        return None, f"Gagal membaca file Excel: {str(e)}"

# VALIDASI KOLOM
def validate_columns(df):
    """
    Memeriksa apakah seluruh kolom wajib tersedia.
    """

    actual_columns = df.columns.tolist()

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in actual_columns
    ]

    if missing_columns:
        return False, missing_columns

    return True, []

# CLEANING DATA
def clean_data(df):
    """
    Membersihkan dan menyesuaikan tipe data.
    """

    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()

    if "Tanggal Kirim" in df.columns:
        df["Tanggal Kirim"] = pd.to_datetime(
            df["Tanggal Kirim"],
            errors="coerce"
        )

    for column in NUMERIC_COLUMNS:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    for column in TEXT_COLUMNS:

        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    return df

# VALIDASI DATA 
def validate_data(df):
    """
    Memberikan informasi mengenai kondisi data.
    """

    validation = {}

    # Jumlah baris
    validation["jumlah_baris"] = len(df)

    # Jumlah kolom
    validation["jumlah_kolom"] = len(df.columns)

    # Jumlah tanggal kosong
    if "Tanggal Kirim" in df.columns:
        validation["tanggal_kosong"] = int(
            df["Tanggal Kirim"].isna().sum()
        )
    else:
        validation["tanggal_kosong"] = 0

    # Jumlah STK kosong
    if "Kuantiti STK" in df.columns:
        validation["stk_kosong"] = int(
            df["Kuantiti STK"].isna().sum()
        )
    else:
        validation["stk_kosong"] = 0

    # Jumlah DO kosong
    if "Kuantiti DO" in df.columns:
        validation["do_kosong"] = int(
            df["Kuantiti DO"].isna().sum()
        )
    else:
        validation["do_kosong"] = 0

    # Jumlah alasan kosong
    if "Kuantiti Alasan" in df.columns:
        validation["alasan_kosong"] = int(
            df["Kuantiti Alasan"].isna().sum()
        )
    else:
        validation["alasan_kosong"] = 0

    # Jumlah nilai kosong
    if "nilai" in df.columns:
        validation["nilai_kosong"] = int(
            df["nilai"].isna().sum()
        )
    else:
        validation["nilai_kosong"] = 0

    return validation

# PERIODE DATA
def get_data_period(df):
    """
    Mengambil tanggal minimum dan maksimum dari Tanggal Kirim.
    """

    if "Tanggal Kirim" not in df.columns:
        return None, None

    valid_dates = df["Tanggal Kirim"].dropna()

    if valid_dates.empty:
        return None, None

    min_date = valid_dates.min()
    max_date = valid_dates.max()

    return min_date, max_date