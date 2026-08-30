import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app import create_app, db


load_dotenv()

app = create_app()

SQLSERVER_URL = os.getenv("SQLSERVER_URL")

if not SQLSERVER_URL:
    raise RuntimeError("Không tìm thấy SQLSERVER_URL trong file .env")


# =========================================================
# CÁC BẢNG THEO ĐÚNG THỨ TỰ KHÓA NGOẠI
# =========================================================

TABLES = [
    (
        "vai_tro",
        [
            "id",
            "ten_vai_tro",
            "mo_ta",
        ],
    ),

    (
        "tai_khoan",
        [
            "id",
            "vai_tro_id",
            "ho_ten",
            "email",
            "so_dien_thoai",
            "mat_khau",
            "trang_thai",
            "ngay_tao",
            "ngay_cap_nhat",
        ],
    ),

    (
        "nong_trai",
        [
            "id",
            "tai_khoan_id",
            "ten",
            "dia_chi",
            "mo_ta",
            "anh_bia",
            "trang_thai",
            "ngay_tao",
            "ngay_cap_nhat",
        ],
    ),

    (
        "danh_muc",
        [
            "id",
            "ten",
            "mo_ta",
        ],
    ),

    (
        "san_pham",
        [
            "id",
            "tai_khoan_id",
            "nong_trai_id",
            "danh_muc_id",
            "ten",
            "mo_ta",
            "gia",
            "so_luong",
            "don_vi_tinh",
            "dia_chi",
            "trang_thai",
            "trang_thai_duyet",
            "ngay_tao",
            "ngay_cap_nhat",
        ],
    ),

    (
        "binh_luan",
        [
            "id",
            "san_pham_id",
            "tai_khoan_id",
            "noi_dung",
            "danh_gia",
            "ngay_tao",
            "ngay_cap_nhat",
        ],
    ),

    (
        "yeu_thich",
        [
            "id",
            "tai_khoan_id",
            "san_pham_id",
            "ngay_luu",
        ],
    ),

    (
        "ma_truy_xuat",
        [
            "id",
            "san_pham_id",
            "gia_tri_ma",
            "ngay_tao",
        ],
    ),

    (
        "ma_qr",
        [
            "id",
            "san_pham_id",
            "duong_dan_anh_qr",
            "noi_dung_qr",
            "ngay_tao",
        ],
    ),

    (
        "hinh_anh_san_pham",
        [
            "id",
            "san_pham_id",
            "duong_dan",
            "la_anh_chinh",
            "ngay_tao",
        ],
    ),

    (
        "loai_moc_truy_xuat",
        [
            "id",
            "ten",
            "mo_ta",
            "thu_tu",
        ],
    ),

    (
        "moc_truy_xuat",
        [
            "id",
            "san_pham_id",
            "loai_moc_id",
            "mo_ta",
            "hinh_anh",
            "dia_diem",
            "ngay_thuc_hien",
        ],
    ),

    (
        "kiem_duyet_san_pham",
        [
            "id",
            "san_pham_id",
            "tai_khoan_duyet_id",
            "trang_thai",
            "ghi_chu",
            "ngay_duyet",
        ],
    ),
]


# =========================================================
# KẾT NỐI SQL SERVER
# =========================================================

sqlserver_engine = create_engine(SQLSERVER_URL)


with app.app_context():

    postgres_engine = db.engine

    print("=" * 60)
    print("BAT DAU CHUYEN DU LIEU")
    print("=" * 60)


    # =====================================================
    # KIỂM TRA SUPABASE ĐANG TRỐNG
    # =====================================================

    with postgres_engine.connect() as pg_conn:

        for table_name, _ in TABLES:

            count = pg_conn.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()

            if count > 0:
                raise RuntimeError(
                    f"Bang {table_name} tren Supabase da co "
                    f"{count} dong. Dung migration de tranh trung du lieu."
                )

    print("✓ Supabase đang trống, có thể bắt đầu.")


    # =====================================================
    # ĐỌC SQL SERVER + GHI POSTGRESQL
    # =====================================================

    with sqlserver_engine.connect() as sql_conn:

        with postgres_engine.begin() as pg_conn:

            for table_name, columns in TABLES:

                column_list = ", ".join(columns)

                # Đọc dữ liệu từ SQL Server
                result = sql_conn.execute(
                    text(
                        f"""
                        SELECT {column_list}
                        FROM dbo.{table_name}
                        ORDER BY id
                        """
                    )
                )

                rows = result.mappings().all()

                if not rows:
                    print(
                        f"- {table_name}: "
                        f"SQL Server không có dữ liệu."
                    )
                    continue

                # Tạo câu INSERT PostgreSQL
                parameters = ", ".join(
                    f":{column}"
                    for column in columns
                )

                insert_sql = text(
                    f"""
                    INSERT INTO {table_name}
                    ({column_list})
                    VALUES
                    ({parameters})
                    """
                )

                # Chuyển RowMapping -> dict
                data = [
                    dict(row)
                    for row in rows
                ]

                # Insert nhiều dòng một lần
                pg_conn.execute(
                    insert_sql,
                    data
                )

                print(
                    f"✓ {table_name}: "
                    f"{len(data)} dong"
                )


    # =====================================================
    # CẬP NHẬT SEQUENCE ID CỦA POSTGRESQL
    # =====================================================

    print("\nDang cap nhat sequence ID...")

    with postgres_engine.begin() as pg_conn:

        for table_name, _ in TABLES:

            max_id = pg_conn.execute(
                text(
                    f"""
                    SELECT MAX(id)
                    FROM {table_name}
                    """
                )
            ).scalar()

            if max_id is None:
                continue

            sequence_name = pg_conn.execute(
                text(
                    """
                    SELECT pg_get_serial_sequence(
                        :table_name,
                        'id'
                    )
                    """
                ),
                {
                    "table_name":
                        f"public.{table_name}"
                },
            ).scalar()

            if sequence_name:

                pg_conn.execute(
                    text(
                        """
                        SELECT setval(
                            CAST(:sequence_name AS regclass),
                            :max_id,
                            true
                        )
                        """
                    ),
                    {
                        "sequence_name": sequence_name,
                        "max_id": max_id,
                    },
                )

                print(
                    f"✓ {table_name}: "
                    f"sequence -> {max_id}"
                )


    # =====================================================
    # KIỂM TRA KẾT QUẢ
    # =====================================================

    print("\n" + "=" * 60)
    print("KET QUA SAU KHI CHUYEN")
    print("=" * 60)

    with postgres_engine.connect() as pg_conn:

        for table_name, _ in TABLES:

            count = pg_conn.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    """
                )
            ).scalar()

            print(
                f"{table_name:<25}: {count}"
            )


    print("\n============================================")
    print("HOAN TAT CHUYEN SQL SERVER -> SUPABASE")
    print("============================================")