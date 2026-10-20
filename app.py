from datetime import date, datetime
from html import escape
from io import BytesIO
from pathlib import Path
import re
import secrets
from urllib.parse import quote
from uuid import uuid4
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import streamlit as st
from ui_theme import apply_navigation_styles


SPREADSHEET_ID = "13G_BqeqNGswSmEUq8JpRwTnGlmj-PsSoupQZM8G2jCE"
CREDENTIALS_FILE = Path(__file__).parent / ".streamlit" / "service_account.json"
TIMEZONE = ZoneInfo("Asia/Jakarta")

ASSET_HEADERS = [
    "Kode Alat",
    "Nama Alat",
    "Kondisi",
    "Status",
    "Lokasi",
    "Rak",
    "Proyek/Penyewa",
    "Penanggung Jawab",
    "Foto Alat URL",
    "Tipe/Merk",
]
TRANSACTION_HEADERS = [
    "ID Transaksi",
    "Tanggal",
    "Jenis Transaksi",
    "Kode Alat",
    "Kondisi Saat Transaksi",
    "Lokasi Asal",
    "Lokasi Tujuan",
    "Proyek/Penyewa",
    "Penanggung Jawab",
    "Petugas",
    "Tanggal Rencana Kembali",
    "Catatan",
    "Status Persetujuan",
    "Nama Penerima",
    "Telepon/WA Penerima",
    "Waktu Persetujuan",
    "Token Persetujuan",
    "Pernyataan Persetujuan",
]
CONSENT_STATEMENT = "Saya menyatakan telah menerima alat sesuai daftar dan bertanggung jawab atas penggunaannya."
CONDITIONS = ["Baik", "Rusak", "Perlu Perawatan"]
WAREHOUSE_LABELS = {"Gudang-1": "Gudang Polonia", "Gudang-2": "Gudang KA"}
WAREHOUSES = list(WAREHOUSE_LABELS.values())
ACTIVE_OUT_STATUSES = ["Dipakai di Proyek", "Disewa Keluar", "Dipinjam"]
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
TRANSACTION_LABELS = {
    "Pengeluaran ke Proyek": "Pengeluaran ke Proyek Sendiri",
    "Pembatalan pengeluaran (latihan)": "Pembatalan Pengeluaran",
    "Pembatalan Pengeluaran (latihan)": "Pembatalan Pengeluaran",
}
OUTGOING_TYPES = ["Pengeluaran ke Proyek Sendiri", "Pengeluaran ke Proyek", "Pengeluaran Sewa", "Peminjaman"]


st.set_page_config(
    page_title="Digital Inventory Control",
    page_icon=":material/inventory_2:",
    layout="wide",
)


def authenticate_user():
    if "auth" not in st.secrets:
        st.error("Login Google belum dikonfigurasi untuk aplikasi ini.")
        st.info("Developer perlu mengatur OAuth Google dan daftar akun pada Secrets Streamlit sebelum aplikasi dapat digunakan.")
        st.stop()

    if not st.user.is_logged_in:
        st.title("Digital Inventory Control")
        st.write("Silakan masuk dengan akun Google yang telah diizinkan.")
        st.button("Masuk dengan Google", on_click=st.login, type="primary")
        st.stop()

    email = str(st.user.get("email", "")).strip().casefold()
    access = st.secrets.get("app_access", {})
    developer_email = str(access.get("developer_email", "")).strip().casefold()
    officer_emails = {
        str(item).strip().casefold()
        for item in access.get("officer_emails", [])
        if str(item).strip()
    }

    if email and email == developer_email:
        role = "Developer"
    elif email and email in officer_emails:
        role = "Petugas Gudang"
    else:
        st.error("Akun Google ini belum diberi akses. Hubungi Developer aplikasi.")
        st.button("Keluar", on_click=st.logout)
        st.stop()

    st.sidebar.caption(f"Masuk sebagai: {st.user.get('name', email)}")
    st.sidebar.caption(f"Peran: {role}")
    st.sidebar.button("Keluar", on_click=st.logout)
    return role, str(st.user.get("name", email)).strip() or email


approval_token = st.query_params.get("persetujuan", "")
if approval_token:
    user_role = "Penerima"
    authenticated_user_name = ""
else:
    user_role, authenticated_user_name = authenticate_user()


def display_location(value):
    return WAREHOUSE_LABELS.get(value, value)


@st.cache_resource
def connect_spreadsheet():
    if CREDENTIALS_FILE.exists():
        client = gspread.service_account(filename=str(CREDENTIALS_FILE))
    else:
        service_account = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(dict(service_account))
    return client.open_by_key(SPREADSHEET_ID)


def read_records(worksheet, expected_headers):
    values = worksheet.get_all_values()
    if not values:
        return []

    headers = values[0]
    if headers[: len(expected_headers)] != expected_headers:
        raise ValueError(
            f"Judul kolom tab {worksheet.title} belum sesuai. "
            "Periksa baris pertama Google Sheet."
        )

    records = []
    for row in values[1:]:
        padded = row + [""] * max(0, len(expected_headers) - len(row))
        record = dict(zip(expected_headers, padded[: len(expected_headers)]))
        if expected_headers == ASSET_HEADERS:
            record["Lokasi"] = display_location(record.get("Lokasi", ""))
        elif expected_headers == TRANSACTION_HEADERS:
            record["Jenis Transaksi"] = TRANSACTION_LABELS.get(
                record.get("Jenis Transaksi", ""), record.get("Jenis Transaksi", "")
            )
            for field in ("Lokasi Asal", "Lokasi Tujuan"):
                record[field] = display_location(record.get(field, ""))
        if expected_headers == TRANSACTION_HEADERS:
            token = transaction_token_from_row(padded)
            if token and not record.get("Token Persetujuan"):
                record["Waktu Persetujuan"] = ""
                record["Token Persetujuan"] = token
        if any(str(value).strip() for value in record.values()):
            records.append(record)
    return records


def transaction_token_from_row(row):
    padded = row + [""] * max(0, len(TRANSACTION_HEADERS) - len(row))
    token = padded[16]
    if (
        not token
        and padded[12] == "Menunggu Persetujuan"
        and re.fullmatch(r"[A-Za-z0-9_-]{20,}", padded[15])
    ):
        # Legacy rows placed the token in Waktu Persetujuan instead of Token Persetujuan.
        return padded[15]
    return token


def make_cell_data(values):
    return [
        {"userEnteredValue": {"stringValue": str(value or "")}}
        for value in values
    ]


def append_cells_request(sheet_id, values):
    return {
        "appendCells": {
            "sheetId": sheet_id,
            "rows": [{"values": make_cell_data(values)}],
            "fields": "userEnteredValue",
        }
    }


def update_asset_and_append_transaction(
    spreadsheet, asset_sheet, transaction_sheet, row_number, asset_values, transaction_values
):
    requests = [
        {
            "updateCells": {
                "range": {
                    "sheetId": asset_sheet.id,
                    "startRowIndex": row_number - 1,
                    "endRowIndex": row_number,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(ASSET_HEADERS),
                },
                "rows": [{"values": make_cell_data(asset_values)}],
                "fields": "userEnteredValue",
            }
        },
        append_cells_request(transaction_sheet.id, transaction_values),
    ]
    spreadsheet.batch_update({"requests": requests})


def append_new_asset_and_transaction(
    spreadsheet, asset_sheet, transaction_sheet, asset_values, transaction_values
):
    spreadsheet.batch_update(
        {
            "requests": [
                append_cells_request(asset_sheet.id, asset_values),
                append_cells_request(transaction_sheet.id, transaction_values),
            ]
        }
    )


def add_missing_transaction_columns(spreadsheet, transaction_sheet):
    headers = transaction_sheet.row_values(1)
    legacy_headers = TRANSACTION_HEADERS[:12]
    if headers[:12] != legacy_headers:
        raise ValueError("Judul kolom tab Transaksi belum sesuai. Periksa baris pertama Google Sheet.")
    missing = TRANSACTION_HEADERS[len(headers):]
    if missing:
        spreadsheet.batch_update({"requests": [{
            "updateCells": {
                "range": {
                    "sheetId": transaction_sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": len(headers),
                    "endColumnIndex": len(headers) + len(missing),
                },
                "rows": [{"values": make_cell_data(missing)}],
                "fields": "userEnteredValue",
            }
        }]})


def add_missing_asset_columns(spreadsheet, asset_sheet):
    headers = asset_sheet.row_values(1)
    legacy_headers = ASSET_HEADERS[:-1]
    if headers[: len(legacy_headers)] != legacy_headers:
        raise ValueError("Judul kolom tab Alat belum sesuai. Periksa baris pertama Google Sheet.")
    missing = ASSET_HEADERS[len(headers):]
    if missing:
        spreadsheet.batch_update({"requests": [{
            "updateCells": {
                "range": {
                    "sheetId": asset_sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": len(headers),
                    "endColumnIndex": len(headers) + len(missing),
                },
                "rows": [{"values": make_cell_data(missing)}],
                "fields": "userEnteredValue",
            }
        }]})


def update_cells_request(sheet_id, row_number, values):
    return {
        "updateCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row_number - 1,
                "endRowIndex": row_number,
                "startColumnIndex": 0,
                "endColumnIndex": len(values),
            },
            "rows": [{"values": make_cell_data(values)}],
            "fields": "userEnteredValue",
        }
    }


def transaction_id():
    now = datetime.now(TIMEZONE)
    return f"TX-{now:%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}"


def current_timestamp():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


def whatsapp_url(phone, message):
    normalized_phone = re.sub(r"\D", "", phone or "")
    if normalized_phone.startswith("00"):
        normalized_phone = normalized_phone[2:]
    if normalized_phone.startswith("0"):
        normalized_phone = "62" + normalized_phone[1:]
    elif normalized_phone.startswith("8"):
        normalized_phone = "62" + normalized_phone
    if len(normalized_phone) < 8:
        return ""
    return f"https://wa.me/{normalized_phone}?text={quote(message, safe='')}"


def show_records(records, alt_text, dashed_borders=False):
    if records:
        if dashed_borders:
            table = pd.DataFrame(records).style.set_properties(
                subset=["Kode Alat", "Status", "Kondisi"], **{"text-align": "center"}
            ).set_table_styles([
                {"selector": "th", "props": [
                    ("border", "1px dashed #8A9AAF"),
                    ("background-color", "#1D4ED8 !important"),
                    ("color", "#FFFFFF !important"),
                    ("font-weight", "bold"),
                ]},
                {"selector": "td", "props": [("border", "1px dashed #8A9AAF")]},
            ])
            st.table(table, hide_index=True, alt=alt_text)
        else:
            st.dataframe(records, hide_index=True, alt=alt_text)
    else:
        st.info("Belum ada data.")


def build_assets_pdf(records):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=14 * mm,
        title="Daftar Alat - Digital Inventory Control",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InventoryTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=13, leading=16, textColor=colors.HexColor("#172B4D"), alignment=0,
        spaceAfter=3,
    )
    note_style = ParagraphStyle(
        "InventoryNote", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7, leading=9, textColor=colors.HexColor("#52627A"), spaceAfter=7,
    )
    header_style = ParagraphStyle(
        "InventoryHeader", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=6.5, leading=8, textColor=colors.white, alignment=1, wordWrap="CJK",
    )
    cell_style = ParagraphStyle(
        "InventoryCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=6.2, leading=7.5, textColor=colors.HexColor("#172B4D"), wordWrap="CJK",
    )
    centered_cell_style = ParagraphStyle(
        "InventoryCenteredCell", parent=cell_style, alignment=1,
    )

    column_weights = [0.75, 1.35, 0.9, 1.15, 0.95, 0.7, 1.35, 1.35, 1.45, 1.0]
    total_weight = sum(column_weights)
    column_widths = [document.width * weight / total_weight for weight in column_weights]

    def paragraph(value, style):
        safe_value = escape(str(value or "")).replace("\n", "<br/>")
        return Paragraph(safe_value or "-", style)

    table_data = [[paragraph(header, header_style) for header in ASSET_HEADERS]]
    for record in records:
        table_data.append([
            paragraph(
                record.get(header, ""),
                centered_cell_style if header in {"Kode Alat", "Status", "Kondisi"} else cell_style,
            )
            for header in ASSET_HEADERS
        ])

    table = Table(table_data, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#8A9AAF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        *[("BACKGROUND", (0, row), (-1, row), colors.HexColor("#F3F6FB"))
          for row in range(2, len(table_data), 2)],
    ]))

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#52627A"))
        canvas.drawRightString(doc.pagesize[0] - 8 * mm, 7 * mm, f"Halaman {doc.page}")
        canvas.restoreState()

    story = [
        Paragraph("Daftar Alat", title_style),
        Paragraph(
            f"Digital Inventory Control • Dicetak {datetime.now(TIMEZONE):%d-%m-%Y %H:%M WIB} • {len(records)} alat",
            note_style,
        ),
        table,
    ]
    document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return buffer.getvalue()


def update_asset_details(spreadsheet, asset_sheet, code, name, rack, responsible, photo_url, type_brand):
    matching_rows = [
        (row_number, row)
        for row_number, row in enumerate(asset_sheet.get_all_values()[1:], start=2)
        if row and row[0].strip() == code
    ]
    if not matching_rows:
        st.error("Kode alat tidak ditemukan.")
        return
    if len(matching_rows) > 1:
        st.error("Kode alat muncul lebih dari sekali di Google Sheet. Rapikan data sebelum mengedit.")
        return
    if not name.strip():
        st.error("Nama alat wajib diisi.")
        return

    row_number, _ = matching_rows[0]
    editable_values = {
        1: name.strip(), 5: rack.strip(), 7: responsible.strip(),
        8: photo_url.strip(), 9: type_brand.strip(),
    }
    requests = []
    for column_index, value in editable_values.items():
        requests.append({
            "updateCells": {
                "range": {
                    "sheetId": asset_sheet.id,
                    "startRowIndex": row_number - 1,
                    "endRowIndex": row_number,
                    "startColumnIndex": column_index,
                    "endColumnIndex": column_index + 1,
                },
                "rows": [{"values": make_cell_data([value])}],
                "fields": "userEnteredValue",
            }
        })
    spreadsheet.batch_update({"requests": requests})
    st.session_state["notice"] = f"Data alat {code} berhasil diperbarui."
    st.rerun()


def derive_latest_transactions(transactions):
    latest = {}
    for transaction in transactions:
        code = transaction.get("Kode Alat", "").strip()
        timestamp = transaction.get("Tanggal", "")
        if code and (code not in latest or timestamp >= latest[code].get("Tanggal", "")):
            latest[code] = transaction
    return latest


def next_asset_code(assets):
    """Return the next unused asset code, keeping at least two digits."""
    used_numbers = []
    for asset in assets:
        match = re.fullmatch(r"E-(\d+)", asset.get("Kode Alat", "").strip(), re.IGNORECASE)
        if match:
            used_numbers.append(int(match.group(1)))

    return f"E-{max(used_numbers, default=0) + 1:02d}"


def asset_code_sort_key(code):
    """Sort numbered E-codes numerically, then other codes alphabetically."""
    code = str(code or "").strip()
    match = re.fullmatch(r"E-(\d+)", code, re.IGNORECASE)
    if match:
        return (0, int(match.group(1)), code.casefold())
    return (1, 0, code.casefold())


def count_assets_by(assets, field):
    counts = {}
    for asset in assets:
        value = str(asset.get(field) or "").strip() or "Belum diisi"
        counts[value] = counts.get(value, 0) + 1

    categories = sorted(counts, key=lambda value: (-counts[value], value.casefold()))
    return {
        "Kategori": categories,
        "Jumlah": [counts[category] for category in categories],
    }


def submit_new_asset(spreadsheet, asset_sheet, transaction_sheet, assets, values):
    code = values[0].strip().upper()
    expected_code = next_asset_code(assets)
    if code != expected_code:
        st.error(f"Nomor urut alat berubah. Muat ulang halaman; kode berikutnya adalah {expected_code}.")
        return
    if not re.fullmatch(r"E-\d{2,}", code):
        st.error("Gunakan format kode seperti E-01 atau E-100.")
        return
    if any(asset.get("Kode Alat", "").strip().upper() == code for asset in assets):
        st.error("Kode alat tersebut sudah terdaftar.")
        return

    name, condition, warehouse, rack, responsible, photo_url, type_brand, officer, note = values[1:]
    status = "Tersedia" if condition == "Baik" else condition
    asset_values = [code, name.strip(), condition, status, warehouse, rack.strip(), "", responsible.strip(), photo_url.strip(), type_brand.strip()]
    transaction_values = [
        transaction_id(),
        current_timestamp(),
        "Penerimaan",
        code,
        condition,
        "Penerimaan baru",
        warehouse,
        "",
        responsible.strip(),
        officer.strip(),
        "",
        note.strip(),
        "Tidak Perlu",
        "",
        "",
        "",
        "",
        "",
    ]

    append_new_asset_and_transaction(
        spreadsheet, asset_sheet, transaction_sheet, asset_values, transaction_values
    )
    st.session_state["notice"] = f"Alat {code} berhasil didaftarkan dan penerimaannya tercatat."
    st.rerun()


def submit_transaction(
    spreadsheet,
    asset_sheet,
    transaction_sheet,
    assets,
    transactions,
    transaction_type,
    code,
    condition,
    destination,
    rack,
    project_or_lender,
    responsible,
    recipient_phone,
    officer,
    due_date,
    note,
):
    physical_rows = asset_sheet.get_all_values()[1:]
    matching_rows = [
        (row_number, row)
        for row_number, row in enumerate(physical_rows, start=2)
        if row and row[0].strip() == code
    ]
    if not matching_rows:
        st.error("Kode alat tidak ditemukan.")
        return
    if len(matching_rows) > 1:
        st.error("Kode alat muncul lebih dari sekali di Google Sheet. Rapikan data sebelum transaksi.")
        return

    row_number, raw_asset = matching_rows[0]
    padded_asset = raw_asset + [""] * max(0, len(ASSET_HEADERS) - len(raw_asset))
    asset = dict(zip(ASSET_HEADERS, padded_asset[: len(ASSET_HEADERS)]))
    old_status = asset.get("Status", "").strip()
    old_location = display_location(asset.get("Lokasi", "").strip())
    updated = dict(asset)
    destination_label = ""
    due_text = ""
    approval_status = "Tidak Perlu"
    approval_token = ""

    if transaction_type == "Pembatalan Pengeluaran":
        events = [
            transaction
            for transaction in transactions
            if transaction.get("Kode Alat", "").strip() == code
        ]
        if len(events) < 2 or events[-1].get("Jenis Transaksi") not in OUTGOING_TYPES:
            st.error("Pembatalan latihan hanya tersedia untuk pengeluaran terakhir alat ini.")
            return
        if not note.strip():
            st.error("Isi alasan pembatalan latihan.")
            return

        previous_event = events[-2]
        previous_type = previous_event.get("Jenis Transaksi", "")
        if previous_type not in ("Penerimaan", "Pengembalian", "Pindah Gudang"):
            st.error("Status sebelum pengeluaran tidak dapat dipulihkan otomatis.")
            return

        condition = previous_event.get("Kondisi Saat Transaksi", "Baik")
        restored_location = previous_event.get("Lokasi Tujuan", "")
        if not restored_location:
            st.error("Lokasi sebelum pengeluaran tidak ditemukan di riwayat.")
            return
        updated["Kondisi"] = condition
        updated["Status"] = "Tersedia" if condition == "Baik" else condition
        updated["Lokasi"] = restored_location
        updated["Proyek/Penyewa"] = ""
        updated["Penanggung Jawab"] = previous_event.get("Penanggung Jawab", "")
        project_or_lender = events[-1].get("Proyek/Penyewa", "")
        responsible = previous_event.get("Penanggung Jawab", "")
        destination_label = restored_location
    elif transaction_type in OUTGOING_TYPES:
        if old_status != "Tersedia":
            st.error("Alat hanya dapat dikeluarkan jika statusnya Tersedia.")
            return
        if condition != "Baik":
            st.error("Alat rusak atau perlu perawatan tidak dapat dikeluarkan.")
            return
        if not project_or_lender.strip() or not responsible.strip() or not due_date:
            st.error("Isi proyek/penyewa/peminjam, penanggung jawab, dan tanggal rencana kembali.")
            return
        updated["Kondisi"] = condition
        updated["Status"] = "Menunggu Persetujuan"
        approval_status = "Menunggu Persetujuan"
        approval_token = secrets.token_urlsafe(32)
        if not recipient_phone.strip():
            st.error("Isi nomor telepon/WA penerima.")
            return
        updated["Status"] = "Menunggu Persetujuan"
        updated["Lokasi"] = project_or_lender.strip()
        updated["Proyek/Penyewa"] = project_or_lender.strip()
        updated["Penanggung Jawab"] = responsible.strip()
        destination_label = project_or_lender.strip()
        due_text = due_date.isoformat()
    elif transaction_type == "Pengembalian":
        if old_status not in ACTIVE_OUT_STATUSES:
            st.error("Alat ini tidak tercatat sedang dipakai, disewa, atau dipinjam.")
            return
        if destination not in WAREHOUSES:
            st.error("Pilih gudang tujuan pengembalian.")
            return
        updated["Kondisi"] = condition
        updated["Status"] = "Tersedia" if condition == "Baik" else condition
        updated["Lokasi"] = destination
        updated["Rak"] = rack.strip()
        updated["Proyek/Penyewa"] = ""
        updated["Penanggung Jawab"] = responsible.strip()
        destination_label = destination
    elif transaction_type == "Pindah Gudang":
        if old_status != "Tersedia":
            st.error("Perpindahan gudang hanya dapat dicatat untuk alat berstatus Tersedia.")
            return
        if destination not in WAREHOUSES or destination == old_location:
            st.error("Pilih gudang tujuan yang berbeda dari lokasi saat ini.")
            return
        updated["Lokasi"] = destination
        updated["Rak"] = rack.strip()
        destination_label = destination
    elif transaction_type == "Kehilangan":
        if old_status in ("Hilang", "Dihapus"):
            st.error("Alat ini sudah berstatus hilang atau dihapus.")
            return
        if not note.strip():
            st.error("Isi catatan kejadian kehilangan.")
            return
        updated["Status"] = "Hilang"
        updated["Kondisi"] = condition
        destination_label = "Hilang"
    elif transaction_type == "Penghapusan":
        if old_status not in ("Tersedia", "Rusak", "Perlu Perawatan", "Hilang"):
            st.error("Alat yang masih berada di proyek, disewakan, atau dipinjam tidak dapat dihapus.")
            return
        if not note.strip():
            st.error("Isi alasan penghapusan.")
            return
        updated["Status"] = "Dihapus"
        updated["Kondisi"] = condition
        destination_label = "Dihapus"

    updated_values = [updated.get(header, "") for header in ASSET_HEADERS]
    transaction_values = [
        transaction_id(),
        current_timestamp(),
        transaction_type,
        code,
        condition,
        old_location,
        destination_label,
        project_or_lender.strip() or asset.get("Proyek/Penyewa", ""),
        responsible.strip(),
        officer.strip(),
        due_text,
        note.strip(),
        approval_status,
        "",
        recipient_phone.strip() if transaction_type in OUTGOING_TYPES else "",
        "",
        approval_token,
        "",
    ]
    update_asset_and_append_transaction(
        spreadsheet,
        asset_sheet,
        transaction_sheet,
        row_number,
        updated_values,
        transaction_values,
    )
    if transaction_type in OUTGOING_TYPES:
        st.session_state["notice"] = f"Transaksi {transaction_type.lower()} untuk {code} tercatat dan menunggu persetujuan penerima."
    else:
        st.session_state["notice"] = f"Transaksi {transaction_type.lower()} untuk {code} berhasil dicatat."
    st.rerun()


def receipt_html(transaction, phone, approved_at):
    values = [
        ("ID Transaksi", transaction.get("ID Transaksi", "")),
        ("Jenis transaksi", transaction.get("Jenis Transaksi", "")),
        ("Kode alat", transaction.get("Kode Alat", "")),
        ("Kondisi saat keluar", transaction.get("Kondisi Saat Transaksi", "")),
        ("Proyek/Penyewa", transaction.get("Proyek/Penyewa", "")),
        ("Penanggung jawab", transaction.get("Penanggung Jawab", "")),
        ("Nama penerima", transaction.get("Nama Penerima", "")),
        ("Telepon/WA", phone),
        ("Tanggal rencana kembali", transaction.get("Tanggal Rencana Kembali", "")),
        ("Waktu persetujuan", approved_at),
    ]
    rows = "".join(f"<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>" for label, value in values)
    statement = transaction.get("Pernyataan Persetujuan") or CONSENT_STATEMENT
    return f"""<!doctype html><html lang=\"id\"><meta charset=\"utf-8\"><title>Bukti tanda terima {escape(transaction.get('Kode Alat', ''))}</title>
    <style>body{{font:16px Arial,sans-serif;max-width:760px;margin:40px auto;color:#222}}h1{{font-size:24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:10px;text-align:left}}th{{width:34%;background:#f2f4f7}}.statement{{margin-top:24px;padding:16px;border:1px solid #bbb}}</style>
    <h1>Bukti Persetujuan Penerimaan Alat</h1><table>{rows}</table>
    <p class=\"statement\">{escape(statement)}</p>
    <p>Dokumen ini dibuat otomatis oleh Digital Inventory Control.</p></html>"""


def approve_transaction(spreadsheet, asset_sheet, transaction_sheet, token, name, phone):
    raw_transactions = transaction_sheet.get_all_values()
    found = [(index + 1, row) for index, row in enumerate(raw_transactions[1:], start=1)
             if secrets.compare_digest(transaction_token_from_row(row), token)]
    if len(found) != 1:
        return None, "Tautan persetujuan tidak ditemukan atau tidak valid."
    transaction_row, raw_transaction = found[0]
    transaction = dict(zip(TRANSACTION_HEADERS, raw_transaction + [""] * (len(TRANSACTION_HEADERS) - len(raw_transaction))))
    if not transaction.get("Token Persetujuan"):
        transaction["Token Persetujuan"] = transaction_token_from_row(raw_transaction)
        transaction["Waktu Persetujuan"] = ""
    if transaction.get("Status Persetujuan") == "Disetujui":
        return {**transaction, "Telepon/WA Penerima": transaction.get("Telepon/WA Penerima", "")}, "already_approved"
    if transaction.get("Status Persetujuan") != "Menunggu Persetujuan":
        return None, "Transaksi ini tidak sedang menunggu persetujuan."

    asset_rows = asset_sheet.get_all_values()
    matches = [(index + 1, row) for index, row in enumerate(asset_rows[1:], start=1)
               if row and row[0] == transaction.get("Kode Alat")]
    if len(matches) != 1:
        return None, "Data alat tidak ditemukan secara unik di tab Alat."
    asset_row, raw_asset = matches[0]
    asset = dict(zip(ASSET_HEADERS, raw_asset + [""] * (len(ASSET_HEADERS) - len(raw_asset))))
    status_by_type = {
        "Pengeluaran ke Proyek": "Dipakai di Proyek",
        "Pengeluaran ke Proyek Sendiri": "Dipakai di Proyek",
        "Pengeluaran Sewa": "Disewa Keluar",
        "Peminjaman": "Dipinjam",
    }
    final_status = status_by_type.get(transaction.get("Jenis Transaksi", ""))
    if not final_status or asset.get("Status") != "Menunggu Persetujuan":
        return None, "Status alat sudah berubah. Minta Petugas Gudang memeriksa transaksi."

    approved_at = current_timestamp()
    transaction["Status Persetujuan"] = "Disetujui"
    transaction["Nama Penerima"] = name.strip()
    transaction["Penanggung Jawab"] = name.strip()
    transaction["Telepon/WA Penerima"] = phone.strip()
    transaction["Waktu Persetujuan"] = approved_at
    transaction["Pernyataan Persetujuan"] = CONSENT_STATEMENT
    updated_asset = [
        asset.get("Kode Alat", ""), asset.get("Nama Alat", ""), asset.get("Kondisi", ""),
        final_status, asset.get("Lokasi", ""), asset.get("Rak", ""),
        asset.get("Proyek/Penyewa", ""), name.strip(), asset.get("Foto Alat URL", ""),
        asset.get("Tipe/Merk", ""),
    ]
    updated_transaction = [transaction.get(header, "") for header in TRANSACTION_HEADERS]
    spreadsheet.batch_update({"requests": [
        update_cells_request(asset_sheet.id, asset_row, updated_asset),
        update_cells_request(transaction_sheet.id, transaction_row, updated_transaction),
    ]})
    return transaction, approved_at


st.caption("Developed by : mas_purnomo_st")
st.title("Digital Inventory Control")
st.caption("Sistem Inventaris Alat, Pantau Ketersediaan, Kondisi Alat & Lokasi")
if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

try:
    spreadsheet = connect_spreadsheet()
    asset_sheet = spreadsheet.worksheet("Alat")
    transaction_sheet = spreadsheet.worksheet("Transaksi")
    add_missing_asset_columns(spreadsheet, asset_sheet)
    add_missing_transaction_columns(spreadsheet, transaction_sheet)
    assets = read_records(asset_sheet, ASSET_HEADERS)
    transactions = read_records(transaction_sheet, TRANSACTION_HEADERS)
except Exception as error:
    st.error("Aplikasi belum dapat membaca Google Sheet.")
    st.caption("Pastikan koneksi internet dan izin service account masih aktif.")
    st.code(str(error))
    st.stop()

if approval_token:
    st.subheader("Persetujuan penerimaan alat")
    transaction = next(
        (item for item in transactions if item.get("Token Persetujuan") == approval_token),
        None,
    )
    if not transaction:
        st.error("Tautan persetujuan tidak valid atau sudah tidak tersedia.")
        st.stop()
    if transaction.get("Status Persetujuan") == "Disetujui":
        st.success("Persetujuan sudah tercatat.")
        recipient_name = transaction.get("Penanggung Jawab", "")
        approved_phone = transaction.get("Telepon/WA Penerima", "")
        st.download_button(
            "Unduh bukti tanda terima",
            data=receipt_html(transaction, approved_phone, transaction.get("Waktu Persetujuan", "")),
            file_name=f"Bukti_Tanda_Terima_{transaction.get('Kode Alat', 'Alat')}.html",
            mime="text/html",
            type="primary",
        )
        st.caption("Buka file unduhan, lalu cetak atau pilih Simpan sebagai PDF bila membutuhkan PDF.")
        st.stop()
    if transaction.get("Status Persetujuan") != "Menunggu Persetujuan":
        st.error("Transaksi ini tidak sedang menunggu persetujuan.")
        st.stop()

    st.write(f"**ID transaksi:** {transaction.get('ID Transaksi', '')}")
    st.write(f"**Alat:** {transaction.get('Kode Alat', '')} — kondisi {transaction.get('Kondisi Saat Transaksi', '')}")
    st.write(f"**Tujuan:** {transaction.get('Proyek/Penyewa', '')}")
    st.write(f"**Tanggal rencana kembali:** {transaction.get('Tanggal Rencana Kembali', '')}")
    st.info("Dengan menyetujui, Anda menyatakan telah menerima alat sesuai daftar dan bertanggung jawab atas penggunaannya.")
    with st.form("recipient_approval_form"):
        recipient_name = st.text_input("Nama penerima")
        recipient_phone = st.text_input("Telepon / WA")
        accepted = st.checkbox("Saya menyetujui pernyataan penerimaan dan tanggung jawab di atas.")
        approve_clicked = st.form_submit_button("Setujui dan buat bukti", type="primary")
    if approve_clicked:
        if not recipient_name.strip() or not recipient_phone.strip() or not accepted:
            st.error("Isi nama, nomor telepon/WA, dan centang persetujuan.")
        else:
            result, outcome = approve_transaction(
                spreadsheet, asset_sheet, transaction_sheet, approval_token,
                recipient_name, recipient_phone,
            )
            if result is None:
                st.error(outcome)
            else:
                st.success("Persetujuan tercatat. Memuat bukti tanda terima...")
                st.rerun()
    st.stop()

apply_navigation_styles()
menu_options = ["Ringkasan", "Daftar alat", "Catat transaksi", "Laporan"]
if "main_navigation" not in st.session_state:
    st.session_state.main_navigation = "Ringkasan"

with st.sidebar.container(border=True):
    st.markdown("**Menu**")
    for menu_option in menu_options:
        button_key = f"main_navigation_{menu_option.casefold().replace(' ', '_')}"
        if st.button(
            menu_option,
            key=button_key,
            type="primary",
            width="stretch",
        ):
            st.session_state.main_navigation = menu_option
            st.rerun()

menu = st.session_state.main_navigation

if menu == "Ringkasan":
    st.badge("RINGKASAN", icon=":material/dashboard:", color="blue")
    st.subheader("Ringkasan alat")
    st.caption("Ikhtisar kondisi inventaris berdasarkan data terbaru.")
    available_count = sum(asset.get("Status") == "Tersedia" for asset in assets)
    out_count = sum(asset.get("Status") in ACTIVE_OUT_STATUSES for asset in assets)
    care_count = sum(asset.get("Status") in ("Rusak", "Perlu Perawatan") for asset in assets)
    lost_count = sum(asset.get("Status") == "Hilang" for asset in assets)
    pending_count = sum(asset.get("Status") == "Menunggu Persetujuan" for asset in assets)
    with st.container(horizontal=True):
        st.metric("Total alat", len(assets), border=True)
        st.metric("Tersedia", available_count, border=True)
        st.metric("Sedang di luar", out_count, border=True)
        st.metric("Rusak / perawatan", care_count, border=True)
        st.metric("Hilang", lost_count, border=True)
        st.metric("Menunggu persetujuan", pending_count, border=True)

    if assets:
        status_summary = count_assets_by(assets, "Status")
        warehouse_summary = count_assets_by(assets, "Gudang")
        status_column, warehouse_column = st.columns(2)
        with status_column:
            with st.container(border=True):
                st.markdown("**Alat berdasarkan status**")
                st.bar_chart(
                    status_summary,
                    x="Kategori",
                    y="Jumlah",
                    horizontal=True,
                    alt="Jumlah alat pada setiap status",
                )
        with warehouse_column:
            with st.container(border=True):
                st.markdown("**Alat berdasarkan gudang**")
                st.bar_chart(
                    warehouse_summary,
                    x="Kategori",
                    y="Jumlah",
                    horizontal=True,
                    alt="Jumlah alat pada setiap gudang",
                )
    else:
        st.info("Belum ada data alat untuk ditampilkan.")

elif menu == "Daftar alat":
    st.badge("DAFTAR ALAT", icon=":material/inventory_2:", color="blue")
    st.subheader("Daftar alat")
    search = st.text_input("Cari kode atau nama alat", type="search")
    status_options = ["Semua"] + sorted({asset.get("Status", "") for asset in assets if asset.get("Status")})
    selected_status = st.selectbox("Status", status_options)
    filtered = sorted(
        [
            asset
            for asset in assets
            if (selected_status == "Semua" or asset.get("Status") == selected_status)
            and (
                not search.strip()
                or search.strip().casefold() in asset.get("Kode Alat", "").casefold()
                or search.strip().casefold() in asset.get("Nama Alat", "").casefold()
            )
        ],
        key=lambda asset: asset_code_sort_key(asset.get("Kode Alat", "")),
    )
    with st.container(key="asset_list_table"):
        show_records(filtered, "Daftar alat beserta status dan lokasi terkini", dashed_borders=True)
    pdf_data = build_assets_pdf(filtered) if filtered else b""
    st.download_button(
        "Unduh PDF daftar alat",
        data=pdf_data,
        file_name=f"daftar-alat-{datetime.now(TIMEZONE):%Y%m%d-%H%M}.pdf",
        mime="application/pdf",
        disabled=not filtered,
        help="PDF landscape; seluruh kolom muat selebar satu halaman dan baris berlanjut ke halaman berikutnya bila diperlukan.",
    )

    with st.expander("Edit data alat"):
        st.caption("Kode, kondisi, status, lokasi, dan proyek/penyewa dikelola melalui Catat transaksi agar riwayat stok tetap konsisten.")
        edit_codes = sorted(
            [asset.get("Kode Alat", "") for asset in assets if asset.get("Kode Alat")],
            key=asset_code_sort_key,
        )
        if not edit_codes:
            st.info("Belum ada alat yang dapat diedit.")
        else:
            edit_code = st.selectbox("Pilih kode alat", edit_codes, key="edit_asset_code")
            edit_asset = next(asset for asset in assets if asset.get("Kode Alat") == edit_code)
            with st.form("edit_asset_form"):
                edit_name = st.text_input("Nama alat", value=edit_asset.get("Nama Alat", ""), key=f"edit_name_{edit_code}")
                edit_rack = st.text_input("Rak", value=edit_asset.get("Rak", ""), key=f"edit_rack_{edit_code}")
                edit_responsible = st.text_input("Penanggung jawab", value=edit_asset.get("Penanggung Jawab", ""), key=f"edit_responsible_{edit_code}")
                edit_photo_url = st.text_input("Foto alat URL", value=edit_asset.get("Foto Alat URL", ""), key=f"edit_photo_{edit_code}")
                edit_type_brand = st.text_input("Tipe/Merk", value=edit_asset.get("Tipe/Merk", ""), key=f"edit_type_brand_{edit_code}")
                edit_submitted = st.form_submit_button("Simpan perubahan", type="primary")
            if edit_submitted:
                update_asset_details(
                    spreadsheet,
                    asset_sheet,
                    edit_code,
                    edit_name,
                    edit_rack,
                    edit_responsible,
                    edit_photo_url,
                    edit_type_brand,
                )

    with st.expander("Daftarkan alat baru"):
        with st.form("new_asset_form"):
            code = next_asset_code(assets)
            st.text_input("Nomor urut / Kode alat", value=code, disabled=True)
            st.caption("Kode dibuat otomatis berurutan dan mengikuti format E-01, E-02, dan seterusnya.")
            name = st.text_input("Nama alat")
            type_brand = st.text_input("Tipe/Merk", placeholder="Contoh: Bosch GSH 500")
            condition = st.selectbox("Kondisi saat diterima", CONDITIONS)
            warehouse = st.selectbox("Gudang", WAREHOUSES)
            rack = st.text_input("Rak (opsional)")
            responsible = st.text_input("Penanggung jawab (opsional)")
            photo_url = st.text_input("Foto alat URL (opsional)")
            st.text_input("Petugas yang mencatat", value=authenticated_user_name, disabled=True)
            officer = f"{authenticated_user_name} <{st.user.get('email', '')}>"
            note = st.text_input("Catatan penerimaan (opsional)")
            submitted = st.form_submit_button("Simpan alat", type="primary")
        if submitted:
            if not name.strip() or not officer.strip():
                st.error("Nama alat dan petugas wajib diisi.")
            else:
                submit_new_asset(
                    spreadsheet,
                    asset_sheet,
                    transaction_sheet,
                    assets,
                    [code, name, condition, warehouse, rack, responsible, photo_url, type_brand, officer, note],
                )

elif menu == "Catat transaksi":
    st.badge("CATAT TRANSAKSI", icon=":material/swap_horiz:", color="blue")
    st.subheader("Catat transaksi alat")
    transaction_type = st.selectbox("Jenis transaksi", TRANSACTION_TYPES)

    if transaction_type in ("Pengeluaran ke Proyek Sendiri", "Pengeluaran ke Proyek", "Pengeluaran Sewa", "Peminjaman", "Pindah Gudang"):
        eligible_assets = [asset for asset in assets if asset.get("Status") == "Tersedia"]
    elif transaction_type == "Pengembalian":
        eligible_assets = [asset for asset in assets if asset.get("Status") in ACTIVE_OUT_STATUSES]
    elif transaction_type == "Pembatalan Pengeluaran":
        latest = derive_latest_transactions(transactions)
        eligible_assets = [
            asset
            for asset in assets
            if asset.get("Status") in ACTIVE_OUT_STATUSES
            and latest.get(asset.get("Kode Alat", ""), {}).get("Jenis Transaksi") in OUTGOING_TYPES
        ]
    else:
        eligible_assets = [asset for asset in assets if asset.get("Status") != "Dihapus"]

    code_options = [asset.get("Kode Alat", "") for asset in eligible_assets if asset.get("Kode Alat")]
    if not code_options:
        st.info("Belum ada alat yang sesuai untuk jenis transaksi ini.")
    else:
        with st.form("transaction_form"):
            code = st.selectbox("Kode alat", code_options)
            if transaction_type == "Pembatalan Pengeluaran":
                st.info("Koreksi ini mengembalikan status alat sebelum pengeluaran latihan dan menyimpan jejak koreksinya.")
                condition = ""
            else:
                selected_asset = next((asset for asset in eligible_assets if asset.get("Kode Alat") == code), {})
                condition_default = selected_asset.get("Kondisi", "Baik")
                condition_index = CONDITIONS.index(condition_default) if condition_default in CONDITIONS else 0
                condition = st.selectbox("Kondisi saat transaksi", CONDITIONS, index=condition_index)

            destination = ""
            rack = ""
            project_or_lender = ""
            responsible = ""
            due_date = None
            if transaction_type in ("Pengeluaran ke Proyek Sendiri", "Pengeluaran ke Proyek", "Pengeluaran Sewa", "Peminjaman"):
                if transaction_type in ("Pengeluaran ke Proyek Sendiri", "Pengeluaran ke Proyek"):
                    project_or_lender = st.text_input("Nama proyek")
                elif transaction_type == "Pengeluaran Sewa":
                    project_or_lender = st.text_input("Nama penyewa")
                else:
                    project_or_lender = st.text_input("Nama peminjam")
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

            if transaction_type not in OUTGOING_TYPES:
                recipient_phone = ""
            st.text_input("Petugas yang mencatat", value=authenticated_user_name, disabled=True)
            officer = f"{authenticated_user_name} <{st.user.get('email', '')}>"
            note = st.text_area("Catatan / alasan")
            submitted = st.form_submit_button("Simpan transaksi", type="primary")

        if submitted:
            if not officer.strip():
                st.error("Nama petugas wajib diisi.")
            else:
                submit_transaction(
                    spreadsheet,
                    asset_sheet,
                    transaction_sheet,
                    assets,
                    transactions,
                    transaction_type,
                    code,
                    condition,
                    destination,
                    rack,
                    project_or_lender,
                    responsible,
                    recipient_phone,
                    officer,
                    due_date,
                    note,
                )

    pending_transactions = [
        transaction for transaction in transactions
        if transaction.get("Status Persetujuan") == "Menunggu Persetujuan"
        and transaction.get("Token Persetujuan")
    ]
    if pending_transactions:
        st.markdown("**Tautan persetujuan yang menunggu**")
        base_url = st.context.url.split("?", 1)[0]
        for transaction in pending_transactions:
            link = f"{base_url}?persetujuan={transaction['Token Persetujuan']}"
            st.write(f"{transaction.get('Kode Alat', '')} · {transaction.get('Proyek/Penyewa', '')} · {transaction.get('ID Transaksi', '')}")
            st.code(link, language=None)
            message = (
                "Halo, mohon konfirmasi penerimaan alat berikut.\n"
                f"ID transaksi: {transaction.get('ID Transaksi', '')}\n"
                f"Kode alat: {transaction.get('Kode Alat', '')}\n"
                f"Tujuan: {transaction.get('Proyek/Penyewa', '')}\n"
                f"Tanggal rencana kembali: {transaction.get('Tanggal Rencana Kembali', '')}\n\n"
                f"Buka tautan ini untuk meninjau dan menyetujui penerimaan:\n{link}"
            )
            recipient_phone = transaction.get("Telepon/WA Penerima", "")
            if not recipient_phone:
                recipient_phone = st.text_input(
                    "Nomor WhatsApp penerima",
                    key=f"pending_phone_{transaction.get('ID Transaksi', transaction.get('Kode Alat', 'alat'))}",
                )
            send_url = whatsapp_url(recipient_phone, message)
            if send_url:
                st.link_button("Kirim via WhatsApp", send_url)
            else:
                st.caption("Nomor WhatsApp belum tersedia atau formatnya tidak valid.")
        st.caption("Tombol membuka chat WhatsApp dengan pesan siap kirim; petugas tetap perlu menekan Kirim. Tautan localhost hanya berfungsi di komputer ini sampai aplikasi dihosting online.")

elif menu == "Laporan":
    st.badge("LAPORAN", icon=":material/analytics:", color="violet")
    st.subheader("Laporan kontrol alat")
    latest_transactions = derive_latest_transactions(transactions)
    today = datetime.now(TIMEZONE).date()
    overdue = []
    for asset in assets:
        if asset.get("Status") not in ACTIVE_OUT_STATUSES:
            continue
        latest = latest_transactions.get(asset.get("Kode Alat", ""), {})
        due_text = latest.get("Tanggal Rencana Kembali", "")
        try:
            due = date.fromisoformat(due_text[:10])
        except (ValueError, TypeError):
            continue
        if due < today:
            overdue.append({**asset, "Tanggal Rencana Kembali": due_text})

    st.markdown("**Terlambat kembali**")
    show_records(overdue, "Daftar alat yang melewati tanggal rencana kembali")

    st.markdown("**Rusak atau perlu perawatan**")
    needs_care = [asset for asset in assets if asset.get("Status") in ("Rusak", "Perlu Perawatan")]
    show_records(needs_care, "Daftar alat yang rusak atau perlu perawatan")

    st.markdown("**Hilang atau dihapus, untuk ditinjau sebagai kebutuhan pengadaan**")
    replacement_review = [asset for asset in assets if asset.get("Status") in ("Hilang", "Dihapus")]
    show_records(replacement_review, "Daftar alat hilang atau dihapus untuk ditinjau")

st.caption("Waktu transaksi dicatat otomatis. Petugas dicatat sesuai nama yang diisi pada formulir.")
