import streamlit as st


# MENGHITUNG KPI

def calculate_kpis(df):

    total_stk = df["Kuantiti STK"].sum()
    total_do = df["Kuantiti DO"].sum()
    total_retur = df["Kuantiti Alasan"].sum()
    nilai_retur = df["nilai"].sum()

    if total_stk > 0:

        return_percentage = (
            total_retur
            / total_stk
            * 100
        )

    else:

        return_percentage = 0

    return {
        "jumlah_transaksi": len(df),
        "total_stk": total_stk,
        "total_do": total_do,
        "total_retur": total_retur,
        "nilai_retur": nilai_retur,
        "return_percentage": return_percentage,
    }


# MENENTUKAN ARAH URUTAN

def get_sort_ascending():

    sort_order = st.session_state.get(
        "global_sort_order",
        "Tertinggi",
    )

    return sort_order == "Terendah"