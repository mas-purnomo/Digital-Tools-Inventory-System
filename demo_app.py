from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from ui_theme import apply_navigation_styles


TRANSACTION_TYPES = [
    "Pengeluaran ke Proyek Sendiri",
    "Pengeluaran Sewa",
    "Peminjaman",
    "Pengembalian",
    "Pindah Gudang",
    "Kehilangan",
    "Penghapusan",
    "Pembatalan Pengeluaran",
]
OUTGOING_TYPES = [
    "Pengeluaran ke Proyek Sendiri", "Pengeluaran Sewa", "Peminjaman",
]
ACTIVE_OUT_STATUSES = ["Dipakai di Proyek", "Disewa Keluar", "Dipinjam"]
WAREHOUSES = ["Gudang Polonia", "Gudang KA"]
TIMEZONE = ZoneInfo("Asia/Jakarta")


st.set_page_config(
    page_title="Digital Inventory Control - Demo",
    page_icon=":material/inventory_2:",
    layout="wide",
)


def sample_assets():
    return [
        {"Kode Alat": "E-01", "Nama Alat": "Bor Listrik", "Kondisi": "Baik", "Status": "Tersedia", "Lokasi": "Gudang Polonia", "Rak": "A-01", "Proyek/Penyewa": "", "Penanggung Jawab": "", "Tipe/Merk": "Bosch"},
        {"Kode Alat": "E-02", "Nama Alat": "Gerinda Tangan", "Kondisi": "Baik", "Status": "Tersedia", "Lokasi": "Gudang Polonia", "Rak": "A-02", "Proyek/Penyewa": "", "Penanggung Jawab": "", "Tipe/Merk": "Makita"},
        {"Kode Alat": "E-03", "Nama Alat": "Mesin Las", "Kondisi": "Baik", "Status": "Dipakai di Proyek", "Lokasi": "Proyek Contoh A", "Rak": "B-01", "Proyek/Penyewa": "Proyek Contoh A", "Penanggung Jawab": "Petugas Demo", "Tipe/Merk": "Rilon"},
        {"Kode Alat": "E-04", "Nama Alat": "Kompresor", "Kondisi": "Perlu Perawatan", "Status": "Perlu Perawatan", "Lokasi": "Gudang KA", "Rak": "B-02", "Proyek/Penyewa": "", "Penanggung Jawab": "", "Tipe/Merk": "Lakoni"},
        {"Kode Alat": "E-05", "Nama Alat": "Kabel Roll", "Kondisi": "Baik", "Status": "Dipinjam", "Lokasi": "Peminjam Contoh", "Rak": "C-01", "Proyek/Penyewa": "Peminjam Contoh", "Penanggung Jawab": "Petugas Demo", "Tipe/Merk": "Uticon"},
    ]


def sample_transactions():
    events = []
    original_locations = {"E-03": "Gudang KA", "E-05": "Gudang Polonia"}
    for asset in sample_assets():
        events.append({
            "ID Transaksi": f"DEMO-{len(events) + 1:04d}",
            "Tanggal": "2026-01-01 08:00:00",
            "Jenis Transaksi": "Penerimaan",
            "Kode Alat": asset["Kode Alat"],
            "Kondisi Saat Transaksi": asset["Kondisi"],
            "Lokasi Asal": "Penerimaan baru",
            "Lokasi Tujuan": original_locations.get(asset["Kode Alat"], asset["Lokasi"]),
            "Proyek/Penyewa": "",
            "Penanggung Jawab": asset["Penanggung Jawab"],
            "Petugas": "Petugas Demo",
            "Tanggal Rencana Kembali": "",
            "Catatan": "Data contoh demo",
            "Status Persetujuan": "Tidak Perlu",
            "Nama Penerima": "",
            "Telepon/WA Penerima": "",
            "Waktu Persetujuan": "",
        })
    seed_outgoing = [
        ("E-03", "Pengeluaran ke Proyek Sendiri", "Proyek Contoh A"),
        ("E-05", "Peminjaman", "Peminjam Contoh"),
    ]
    for code, transaction_type, destination in seed_outgoing:
        asset = next(item for item in sample_assets() if item["Kode Alat"] == code)
        events.append({
            "ID Transaksi": f"DEMO-{len(events) + 1:04d}",
            "Tanggal": "2026-01-02 08:00:00",
            "Jenis Transaksi": transaction_type,
            "Kode Alat": code,
            "Kondisi Saat Transaksi": "Baik",
            "Lokasi Asal": original_locations.get(asset["Kode Alat"], asset["Lokasi"]),
            "Lokasi Tujuan": destination,
            "Proyek/Penyewa": destination,
            "Penanggung Jawab": "Petugas Demo",
            "Petugas": "Petugas Demo",
            "Tanggal Rencana Kembali": "2026-09-30",
            "Catatan": "Transaksi contoh yang sudah disetujui",
            "Status Persetujuan": "Disetujui",
            "Nama Penerima": "Penerima Demo",
            "Telepon/WA Penerima": "08xxxxxxxxxx",
            "Waktu Persetujuan": "2026-01-02 08:05:00",
        })
    return events


if "demo_assets" not in st.session_state:
    st.session_state.demo_assets = sample_assets()
if "demo_transactions" not in st.session_state:
    st.session_state.demo_transactions = sample_transactions()


st.caption("Developed by : mas_purnomo_st")
st.title("Digital Inventory Control")
st.caption("Sistem Inventaris Alat, Pantau Ketersediaan, Kondisi Alat & Lokasi")
st.info(
    "Mode demo publik: tidak perlu login. Silakan coba fitur menggunakan data contoh; "
    "perubahan hanya tersimpan sementara di sesi browser ini dan tidak mengubah data operasional."
)

apply_navigation_styles()
menu_options = ["Ringkasan", "Daftar alat", "Catat transaksi", "Laporan"]
if "demo_navigation" not in st.session_state:
    st.session_state.demo_navigation = "Ringkasan"

with st.sidebar.container(border=True):
    st.markdown("**Menu**")
    for menu_option in menu_options:
        is_selected = st.session_state.demo_navigation == menu_option
        button_key = f"demo_navigation_{menu_option.casefold().replace(' ', '_')}"
        if st.button(
            menu_option,
            key=button_key,
            type="primary" if is_selected else "secondary",
            width="stretch",
        ):
            st.session_state.demo_navigation = menu_option
            st.rerun()

menu = st.session_state.demo_navigation
if st.sidebar.button("Reset data demo"):
    st.session_state.demo_assets = sample_assets()
    st.session_state.demo_transactions = sample_transactions()
    st.rerun()
st.sidebar.caption("Data demo terpisah untuk setiap sesi pengunjung.")

assets = st.session_state.demo_assets

if menu == "Ringkasan":
    st.badge("RINGKASAN", icon=":material/dashboard:", color="blue")
    st.subheader("Ringkasan alat")
    st.caption("Ikhtisar kondisi inventaris berdasarkan data terbaru.")
    available = sum(asset["Status"] == "Tersedia" for asset in assets)
    in_use = sum(asset["Status"] in ("Dipakai di Proyek", "Dipinjam", "Disewa Keluar") for asset in assets)
    care = sum(asset["Status"] in ("Rusak", "Perlu Perawatan") for asset in assets)
    lost = sum(asset["Status"] == "Hilang" for asset in assets)
    pending = sum(asset["Status"] == "Menunggu Persetujuan" for asset in assets)
    with st.container(horizontal=True):
        st.metric("Total alat", len(assets), border=True)
        st.metric("Tersedia", available, border=True)
        st.metric("Sedang di luar", in_use, border=True)
        st.metric("Rusak / perawatan", care, border=True)
        st.metric("Hilang", lost, border=True)
        st.metric("Menunggu persetujuan", pending, border=True)
    if assets:
        status_counts = pd.Series([asset.get("Status", "Belum diisi") for asset in assets]).value_counts()
        status_summary = pd.DataFrame({"Kategori": status_counts.index, "Jumlah": status_counts.values})
        warehouse_counts = pd.Series([
            asset.get("Lokasi", "Belum diisi") or "Belum diisi" for asset in assets
        ]).value_counts()
        warehouse_summary = pd.DataFrame({"Kategori": warehouse_counts.index, "Jumlah": warehouse_counts.values})
        status_column, warehouse_column = st.columns(2)
        with status_column:
            with st.container(border=True):
                st.markdown("**Alat berdasarkan status**")
                st.bar_chart(
                    status_summary, x="Kategori", y="Jumlah", horizontal=True,
                    alt="Jumlah alat berdasarkan status",
                )
        with warehouse_column:
            with st.container(border=True):
                st.markdown("**Alat berdasarkan gudang**")
                st.bar_chart(
                    warehouse_summary, x="Kategori", y="Jumlah", horizontal=True,
                    alt="Jumlah alat berdasarkan gudang",
                )
    else:
        st.info("Belum ada data alat untuk ditampilkan.")

elif menu == "Daftar alat":
    st.badge("DAFTAR ALAT", icon=":material/inventory_2:", color="blue")
    st.subheader("Daftar alat")
    search_column, status_column = st.columns([2, 1])
    with search_column:
        search = st.text_input("Cari kode atau nama alat", type="search")
    status_options = ["Semua"] + sorted({asset["Status"] for asset in assets})
    with status_column:
        selected_status = st.selectbox("Status", status_options)
    visible_assets = [
        asset for asset in assets
        if (selected_status == "Semua" or asset["Status"] == selected_status)
        and (not search.strip() or search.casefold() in asset["Kode Alat"].casefold() or search.casefold() in asset["Nama Alat"].casefold())
    ]
    display_columns = [
        "Kode Alat", "Nama Alat", "Kondisi", "Status", "Lokasi", "Rak",
        "Proyek/Penyewa", "Penanggung Jawab", "Foto Alat URL", "Tipe/Merk",
    ]
    if visible_assets:
        table = pd.DataFrame(visible_assets).reindex(columns=display_columns, fill_value="").style.set_properties(
            subset=["Kode Alat", "Kondisi", "Status"], **{"text-align": "center"}
        ).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#1D4ED8 !important"),
                ("color", "#FFFFFF !important"),
                ("font-weight", "bold"),
            ]},
            {"selector": "th, td", "props": [("border", "1px dashed #8A9AAF")]},
        ])
        st.table(table, hide_index=True)
    else:
        st.info("Tidak ada alat yang cocok dengan pencarian atau filter.")

    with st.expander("Daftarkan alat baru"):
        with st.form("demo_add_asset"):
            used_numbers = [
                int(asset["Kode Alat"].split("-")[-1])
                for asset in assets
                if str(asset.get("Kode Alat", "")).upper().startswith("E-")
                and str(asset["Kode Alat"]).split("-")[-1].isdigit()
            ]
            next_code = f"E-{max(used_numbers, default=0) + 1:02d}"
            st.text_input("Nomor urut / Kode alat", value=next_code, disabled=True)
            st.caption("Kode dibuat otomatis berurutan dan mengikuti format E-01, E-02, dan seterusnya.")
            name = st.text_input("Nama alat")
            brand = st.text_input("Tipe/Merk", placeholder="Contoh: Bosch GSH 500")
            condition = st.selectbox("Kondisi saat diterima", ["Baik", "Rusak", "Perlu Perawatan"])
            location = st.selectbox("Gudang", WAREHOUSES)
            rack = st.text_input("Rak (opsional)")
            responsible = st.text_input("Penanggung jawab (opsional)")
            photo_url = st.text_input("Foto alat URL (opsional)")
            st.text_input("Petugas yang mencatat", value="Pengunjung Demo", disabled=True)
            note = st.text_input("Catatan penerimaan (opsional)")
            submitted = st.form_submit_button("Simpan alat", type="primary")
        if submitted:
            if not name.strip():
                st.error("Nama alat perlu diisi.")
            else:
                assets.append({
                    "Kode Alat": next_code, "Nama Alat": name.strip(),
                    "Kondisi": condition, "Status": "Tersedia" if condition == "Baik" else condition,
                    "Lokasi": location, "Rak": rack.strip(), "Proyek/Penyewa": "",
                    "Penanggung Jawab": responsible.strip(), "Foto Alat URL": photo_url.strip(),
                    "Tipe/Merk": brand.strip(),
                })
                st.session_state.demo_transactions.append({
                    "ID Transaksi": f"DEMO-{len(st.session_state.demo_transactions) + 1:04d}",
                    "Tanggal": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
                    "Jenis Transaksi": "Penerimaan", "Kode Alat": next_code,
                    "Kondisi Saat Transaksi": condition, "Lokasi Asal": "Penerimaan baru",
                    "Lokasi Tujuan": location, "Proyek/Penyewa": "",
                    "Penanggung Jawab": responsible.strip(), "Petugas": "Pengunjung Demo",
                    "Tanggal Rencana Kembali": "", "Catatan": note.strip(),
                    "Status Persetujuan": "Tidak Perlu", "Nama Penerima": "",
                    "Telepon/WA Penerima": "", "Waktu Persetujuan": "",
                })
                st.session_state.demo_assets = assets
                st.success("Alat berhasil dicatat pada sesi demo ini.")
                st.rerun()

    with st.expander("Edit data alat"):
        edit_codes = [asset["Kode Alat"] for asset in assets]
        edit_code = st.selectbox("Pilih kode alat", edit_codes, key="demo_edit_code")
        selected_asset = next(asset for asset in assets if asset["Kode Alat"] == edit_code)
        with st.form("demo_edit_asset"):
            edit_name = st.text_input("Nama alat", value=selected_asset["Nama Alat"])
            edit_rack = st.text_input("Rak", value=selected_asset.get("Rak", ""))
            edit_responsible = st.text_input("Penanggung jawab", value=selected_asset.get("Penanggung Jawab", ""))
            edit_photo_url = st.text_input("Foto alat URL", value=selected_asset.get("Foto Alat URL", ""))
            edit_brand = st.text_input("Tipe/Merk", value=selected_asset.get("Tipe/Merk", ""))
            save_edit = st.form_submit_button("Simpan perubahan")
        if save_edit:
            selected_asset["Nama Alat"] = edit_name.strip() or selected_asset["Nama Alat"]
            selected_asset["Rak"] = edit_rack.strip()
            selected_asset["Penanggung Jawab"] = edit_responsible.strip()
            selected_asset["Foto Alat URL"] = edit_photo_url.strip()
            selected_asset["Tipe/Merk"] = edit_brand.strip()
            st.session_state.demo_assets = assets
            st.success("Perubahan diterapkan pada sesi demo ini.")
            st.rerun()

elif menu == "Catat transaksi":
    st.badge("CATAT TRANSAKSI", icon=":material/swap_horiz:", color="blue")
    st.subheader("Catat transaksi alat")
    st.caption("Urutan dan aturan transaksi mengikuti aplikasi utama. Semua perubahan hanya berlaku di sesi demo ini.")
    transaction_type = st.selectbox("Jenis transaksi", TRANSACTION_TYPES)

    latest_by_code = {}
    for event in st.session_state.demo_transactions:
        code = event.get("Kode Alat", "")
        if code and (code not in latest_by_code or event.get("Tanggal", "") >= latest_by_code[code].get("Tanggal", "")):
            latest_by_code[code] = event

    if transaction_type in OUTGOING_TYPES or transaction_type == "Pindah Gudang":
        eligible_assets = [asset for asset in assets if asset.get("Status") == "Tersedia"]
    elif transaction_type == "Pengembalian":
        eligible_assets = [asset for asset in assets if asset.get("Status") in ACTIVE_OUT_STATUSES]
    elif transaction_type == "Pembatalan Pengeluaran":
        eligible_assets = [
            asset for asset in assets
            if asset.get("Status") in ACTIVE_OUT_STATUSES
            and latest_by_code.get(asset.get("Kode Alat", ""), {}).get("Jenis Transaksi") in OUTGOING_TYPES
        ]
    else:
        eligible_assets = [asset for asset in assets if asset.get("Status") != "Dihapus"]

    code_options = [asset["Kode Alat"] for asset in eligible_assets if asset.get("Kode Alat")]
    if not code_options:
        st.info("Belum ada alat yang sesuai untuk jenis transaksi ini.")
    else:
        with st.form("demo_transaction_form"):
            code = st.selectbox("Kode alat", code_options)
            selected_asset = next(asset for asset in eligible_assets if asset["Kode Alat"] == code)

            if transaction_type == "Pembatalan Pengeluaran":
                st.info("Pembatalan hanya tersedia untuk pengeluaran terakhir. Status sebelum pengeluaran akan dipulihkan dan dicatat di riwayat demo.")
                condition = ""
            else:
                conditions = ["Baik", "Rusak", "Perlu Perawatan"]
                current_condition = selected_asset.get("Kondisi", "Baik")
                condition = st.selectbox(
                    "Kondisi saat transaksi", conditions,
                    index=conditions.index(current_condition) if current_condition in conditions else 0,
                )

            destination = ""
            rack = ""
            project_or_lender = ""
            responsible = ""
            recipient_phone = ""
            due_date = None

            if transaction_type in OUTGOING_TYPES:
                field_label = {
                    "Pengeluaran ke Proyek Sendiri": "Nama proyek",
                    "Pengeluaran Sewa": "Nama penyewa",
                    "Peminjaman": "Nama peminjam",
                }[transaction_type]
                project_or_lender = st.text_input(field_label)
                responsible = st.text_input("Penanggung jawab / penerima")
                recipient_phone = st.text_input("Telepon / WA penerima")
                due_date = st.date_input(
                    "Tanggal rencana kembali", value=datetime.now(TIMEZONE).date()
                )
            elif transaction_type == "Pengembalian":
                destination = st.selectbox("Gudang tujuan", WAREHOUSES)
                rack = st.text_input("Rak tujuan (opsional)")
                responsible = st.text_input("Penanggung jawab di gudang (opsional)")
            elif transaction_type == "Pindah Gudang":
                destination = st.selectbox("Gudang tujuan", WAREHOUSES)
                rack = st.text_input("Rak tujuan (opsional)")

            st.text_input("Petugas yang mencatat", value="Pengunjung Demo", disabled=True)
            note = st.text_area("Catatan / alasan")
            submitted = st.form_submit_button("Simpan transaksi", type="primary")

        if submitted:
            old_status = selected_asset.get("Status", "")
            old_location = selected_asset.get("Lokasi", "")
            transaction_error = ""
            destination_label = ""
            due_text = ""
            approval_status = "Tidak Perlu"
            transaction_project = project_or_lender.strip() or selected_asset.get("Proyek/Penyewa", "")

            if transaction_type in OUTGOING_TYPES:
                if old_status != "Tersedia":
                    transaction_error = "Alat hanya dapat dikeluarkan jika statusnya Tersedia."
                elif condition != "Baik":
                    transaction_error = "Alat rusak atau perlu perawatan tidak dapat dikeluarkan."
                elif not project_or_lender.strip() or not responsible.strip() or not due_date:
                    transaction_error = "Isi proyek/penyewa/peminjam, penanggung jawab, dan tanggal rencana kembali."
                elif not recipient_phone.strip():
                    transaction_error = "Isi nomor telepon/WA penerima."
                else:
                    selected_asset.update({
                        "Kondisi": condition,
                        "Status": "Menunggu Persetujuan",
                        "Lokasi": project_or_lender.strip(),
                        "Proyek/Penyewa": project_or_lender.strip(),
                        "Penanggung Jawab": responsible.strip(),
                    })
                    destination_label = project_or_lender.strip()
                    due_text = due_date.isoformat()
                    approval_status = "Menunggu Persetujuan"
            elif transaction_type == "Pengembalian":
                if old_status not in ACTIVE_OUT_STATUSES:
                    transaction_error = "Alat ini tidak tercatat sedang dipakai, disewa, atau dipinjam."
                else:
                    selected_asset.update({
                        "Kondisi": condition,
                        "Status": "Tersedia" if condition == "Baik" else condition,
                        "Lokasi": destination,
                        "Rak": rack.strip(),
                        "Proyek/Penyewa": "",
                        "Penanggung Jawab": responsible.strip(),
                    })
                    destination_label = destination
            elif transaction_type == "Pindah Gudang":
                if old_status != "Tersedia":
                    transaction_error = "Perpindahan gudang hanya dapat dicatat untuk alat berstatus Tersedia."
                elif destination not in WAREHOUSES or destination == old_location:
                    transaction_error = "Pilih gudang tujuan yang berbeda dari lokasi saat ini."
                else:
                    selected_asset.update({"Lokasi": destination, "Rak": rack.strip()})
                    destination_label = destination
            elif transaction_type == "Kehilangan":
                if old_status in ("Hilang", "Dihapus"):
                    transaction_error = "Alat ini sudah berstatus hilang atau dihapus."
                elif not note.strip():
                    transaction_error = "Isi catatan kejadian kehilangan."
                else:
                    selected_asset.update({"Status": "Hilang", "Kondisi": condition})
                    destination_label = "Hilang"
            elif transaction_type == "Penghapusan":
                if old_status not in ("Tersedia", "Rusak", "Perlu Perawatan", "Hilang"):
                    transaction_error = "Alat yang masih berada di proyek, disewakan, atau dipinjam tidak dapat dihapus."
                elif not note.strip():
                    transaction_error = "Isi alasan penghapusan."
                else:
                    selected_asset.update({"Status": "Dihapus", "Kondisi": condition})
                    destination_label = "Dihapus"
            else:
                code_events = [event for event in st.session_state.demo_transactions if event.get("Kode Alat") == code]
                if len(code_events) < 2 or code_events[-1].get("Jenis Transaksi") not in OUTGOING_TYPES:
                    transaction_error = "Pembatalan hanya tersedia untuk pengeluaran terakhir alat ini."
                elif not note.strip():
                    transaction_error = "Isi alasan pembatalan."
                else:
                    previous_event = code_events[-2]
                    previous_type = previous_event.get("Jenis Transaksi", "")
                    restored_location = previous_event.get("Lokasi Tujuan", "")
                    if previous_type not in ("Penerimaan", "Pengembalian", "Pindah Gudang"):
                        transaction_error = "Status sebelum pengeluaran tidak dapat dipulihkan otomatis."
                    elif not restored_location:
                        transaction_error = "Lokasi sebelum pengeluaran tidak ditemukan di riwayat demo."
                    else:
                        condition = previous_event.get("Kondisi Saat Transaksi", "Baik")
                        selected_asset.update({
                            "Kondisi": condition,
                            "Status": "Tersedia" if condition == "Baik" else condition,
                            "Lokasi": restored_location,
                            "Proyek/Penyewa": "",
                            "Penanggung Jawab": previous_event.get("Penanggung Jawab", ""),
                        })
                        transaction_project = code_events[-1].get("Proyek/Penyewa", "")
                        responsible = previous_event.get("Penanggung Jawab", "")
                        destination_label = restored_location

            if transaction_error:
                st.error(transaction_error)
            else:
                event = {
                    "ID Transaksi": f"DEMO-{len(st.session_state.demo_transactions) + 1:04d}",
                    "Tanggal": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
                    "Jenis Transaksi": transaction_type,
                    "Kode Alat": code,
                    "Kondisi Saat Transaksi": condition,
                    "Lokasi Asal": old_location,
                    "Lokasi Tujuan": destination_label,
                    "Proyek/Penyewa": transaction_project,
                    "Penanggung Jawab": responsible.strip(),
                    "Petugas": "Pengunjung Demo",
                    "Tanggal Rencana Kembali": due_text,
                    "Catatan": note.strip(),
                    "Status Persetujuan": approval_status,
                    "Nama Penerima": "",
                    "Telepon/WA Penerima": recipient_phone.strip(),
                    "Waktu Persetujuan": "",
                }
                st.session_state.demo_transactions.append(event)
                st.session_state.demo_assets = assets
                st.success(
                    "Transaksi menunggu simulasi persetujuan penerima."
                    if approval_status == "Menunggu Persetujuan"
                    else "Transaksi demo berhasil dicatat."
                )
                st.rerun()

    pending_events = [
        event for event in st.session_state.demo_transactions
        if event.get("Status Persetujuan") == "Menunggu Persetujuan"
    ]
    if pending_events:
        st.markdown("**Persetujuan penerima (simulasi)**")
        for event in pending_events:
            st.write(f"{event['Kode Alat']} · {event['Proyek/Penyewa']} · {event['ID Transaksi']}")
            with st.form(f"demo_approval_{event['ID Transaksi']}"):
                recipient_name = st.text_input(
                    "Nama penerima", value=event.get("Penanggung Jawab", ""),
                    key=f"demo_recipient_{event['ID Transaksi']}",
                )
                recipient_phone = st.text_input(
                    "Telepon / WA", value=event.get("Telepon/WA Penerima", ""),
                    key=f"demo_phone_{event['ID Transaksi']}",
                )
                accepted = st.checkbox(
                    "Saya menyetujui penerimaan alat dan tanggung jawab penggunaannya.",
                    key=f"demo_accept_{event['ID Transaksi']}",
                )
                approved = st.form_submit_button("Simulasikan persetujuan penerima", type="primary")
            if approved:
                if not recipient_name.strip() or not recipient_phone.strip() or not accepted:
                    st.error("Isi nama, telepon/WA, dan centang pernyataan penerimaan.")
                else:
                    asset = next(item for item in assets if item["Kode Alat"] == event["Kode Alat"])
                    final_status = {
                        "Pengeluaran ke Proyek Sendiri": "Dipakai di Proyek",
                        "Pengeluaran Sewa": "Disewa Keluar",
                        "Peminjaman": "Dipinjam",
                    }.get(event["Jenis Transaksi"])
                    if not final_status or asset.get("Status") != "Menunggu Persetujuan":
                        st.error("Status alat sudah berubah; periksa transaksi demo ini.")
                    else:
                        event["Status Persetujuan"] = "Disetujui"
                        event["Nama Penerima"] = recipient_name.strip()
                        event["Penanggung Jawab"] = recipient_name.strip()
                        event["Telepon/WA Penerima"] = recipient_phone.strip()
                        event["Waktu Persetujuan"] = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
                        asset["Status"] = final_status
                        asset["Penanggung Jawab"] = recipient_name.strip()
                        st.session_state.demo_assets = assets
                        st.success("Persetujuan demo tercatat.")
                        st.rerun()

    if st.session_state.demo_transactions:
        st.markdown("**Riwayat transaksi**")
        st.dataframe(st.session_state.demo_transactions, hide_index=True)

else:
    st.badge("LAPORAN", icon=":material/analytics:", color="blue")
    st.subheader("Laporan kontrol alat")
    latest_by_code = {}
    for event in st.session_state.demo_transactions:
        code = event.get("Kode Alat", "")
        if code and (code not in latest_by_code or event.get("Tanggal", "") >= latest_by_code[code].get("Tanggal", "")):
            latest_by_code[code] = event

    today = datetime.now(TIMEZONE).date()
    overdue = []
    for asset in assets:
        if asset.get("Status") not in ACTIVE_OUT_STATUSES:
            continue
        due_text = latest_by_code.get(asset.get("Kode Alat", ""), {}).get("Tanggal Rencana Kembali", "")
        try:
            due_date_value = date.fromisoformat(str(due_text)[:10])
        except (ValueError, TypeError):
            continue
        if due_date_value < today:
            overdue.append({**asset, "Tanggal Rencana Kembali": due_text})

    st.markdown("**Terlambat kembali**")
    if overdue:
        st.dataframe(overdue, hide_index=True)
    else:
        st.info("Tidak ada alat yang terlambat kembali.")

    st.markdown("**Rusak atau perlu perawatan**")
    needs_care = [asset for asset in assets if asset.get("Status") in ("Rusak", "Perlu Perawatan")]
    if needs_care:
        st.dataframe(needs_care, hide_index=True)
    else:
        st.info("Tidak ada alat rusak atau perlu perawatan.")

    st.markdown("**Hilang atau dihapus, untuk ditinjau sebagai kebutuhan pengadaan**")
    replacement_review = [asset for asset in assets if asset.get("Status") in ("Hilang", "Dihapus")]
    if replacement_review:
        st.dataframe(replacement_review, hide_index=True)
    else:
        st.info("Tidak ada alat hilang atau dihapus untuk ditinjau.")

st.caption("Waktu transaksi dicatat otomatis. Petugas pada demo tercatat sebagai Pengunjung Demo.")
