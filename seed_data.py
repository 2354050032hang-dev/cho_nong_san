from app import create_app, db
from app.models import VaiTro, DanhMuc, LoaiMocTruyXuat

app = create_app()

with app.app_context():
    db.create_all()

    if not VaiTro.query.first():
        db.session.add_all([
            VaiTro(id=1, ten_vai_tro="Quản trị", mo_ta="Quản trị hệ thống"),
            VaiTro(id=2, ten_vai_tro="Người bán", mo_ta="Đăng bán sản phẩm"),
            VaiTro(id=3, ten_vai_tro="Người dùng", mo_ta="Mua hàng, tương tác"),
        ])

    if not DanhMuc.query.first():
        db.session.add_all([
            DanhMuc(ten="Rau củ"),
            DanhMuc(ten="Trái cây"),
            DanhMuc(ten="Ngũ cốc"),
            DanhMuc(ten="Thủy sản"),
        ])

    if not LoaiMocTruyXuat.query.first():
        db.session.add_all([
            LoaiMocTruyXuat(ten="Gieo trồng", thu_tu=1),
            LoaiMocTruyXuat(ten="Chăm sóc", thu_tu=2),
            LoaiMocTruyXuat(ten="Thu hoạch", thu_tu=3),
            LoaiMocTruyXuat(ten="Đóng gói", thu_tu=4),
        ])

    db.session.commit()
    print("Đã nạp dữ liệu tra cứu ban đầu thành công.")