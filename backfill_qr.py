from app import create_app, db
from app.models import SanPham, MaQR
from app.product.routes import sinh_qr

app = create_app()

with app.app_context():

    # Cần request context nếu hàm sinh_qr sử dụng url_for()
    with app.test_request_context(
        base_url="http://127.0.0.1:5000/"
    ):

        # Lấy tất cả sản phẩm đã có mã truy xuất
        san_phams = SanPham.query.filter(
            SanPham.ma_truy_xuat.has()
        ).all()

        so_luong = 0

        for sp in san_phams:

            # Nếu đã có QR và đã có file ảnh thì bỏ qua
            if (
                sp.ma_qr
                and sp.ma_qr.duong_dan_anh_qr
            ):
                continue

            ma_truy_xuat = sp.ma_truy_xuat.gia_tri_ma

            # Tạo file ảnh QR
            qr_filename, qr_link = sinh_qr(
                sp.id,
                ma_truy_xuat
            )

            # Trường hợp đã có bản ghi ma_qr nhưng đường dẫn NULL
            if sp.ma_qr:

                sp.ma_qr.duong_dan_anh_qr = qr_filename
                sp.ma_qr.noi_dung_qr = qr_link

            # Trường hợp chưa có bản ghi ma_qr
            else:

                ma_qr = MaQR(
                    san_pham_id=sp.id,
                    duong_dan_anh_qr=qr_filename,
                    noi_dung_qr=qr_link
                )

                db.session.add(ma_qr)

            so_luong += 1

            print(
                f"✓ {sp.id} - {sp.ten} "
                f"→ {qr_filename}"
            )

        # Chỉ commit 1 lần ở cuối
        db.session.commit()

        print(
            f"\nHoàn tất. Đã tạo/cập nhật QR "
            f"cho {so_luong} sản phẩm."
        )