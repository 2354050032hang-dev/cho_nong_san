from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return TaiKhoan.query.get(int(user_id))


class VaiTro(db.Model):
    __tablename__ = "vai_tro"
    id = db.Column(db.Integer, primary_key=True)
    ten_vai_tro = db.Column(db.Unicode(50), nullable=False)
    mo_ta = db.Column(db.Unicode(255))

    tai_khoans = db.relationship("TaiKhoan", backref="vai_tro", lazy=True)


class TaiKhoan(db.Model, UserMixin):
    __tablename__ = "tai_khoan"
    id = db.Column(db.Integer, primary_key=True)
    vai_tro_id = db.Column(db.Integer, db.ForeignKey("vai_tro.id"), nullable=False)
    ho_ten = db.Column(db.Unicode(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    so_dien_thoai = db.Column(db.String(20))
    mat_khau = db.Column(db.String(255), nullable=False)  # lưu chuỗi hash, không lưu mật khẩu gốc
    trang_thai = db.Column(db.Integer, default=1)  # 1 = hoạt động, 0 = khóa
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nong_trai = db.relationship("NongTrai", backref="chu_so_huu", uselist=False, cascade="all, delete-orphan")
    san_phams = db.relationship("SanPham", backref="nguoi_dang", lazy=True)
    binh_luans = db.relationship("BinhLuan", backref="tai_khoan", lazy=True)
    yeu_thichs = db.relationship("YeuThich", backref="tai_khoan", lazy=True)

    def get_id(self):
        return str(self.id)


class NongTrai(db.Model):
    __tablename__ = "nong_trai"
    id = db.Column(db.Integer, primary_key=True)
    tai_khoan_id = db.Column(db.Integer, db.ForeignKey("tai_khoan.id"), unique=True, nullable=False)
    ten = db.Column(db.Unicode(150), nullable=False)
    dia_chi = db.Column(db.Unicode(255))
    mo_ta = db.Column(db.UnicodeText)
    anh_bia = db.Column(db.String(255))
    trang_thai = db.Column(db.Integer, default=1)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    san_phams = db.relationship("SanPham", backref="nong_trai", lazy=True)


class DanhMuc(db.Model):
    __tablename__ = "danh_muc"
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.Unicode(50), nullable=False)
    mo_ta = db.Column(db.Unicode(255))

    san_phams = db.relationship("SanPham", backref="danh_muc", lazy=True)


class SanPham(db.Model):
    __tablename__ = "san_pham"
    id = db.Column(db.Integer, primary_key=True)
    tai_khoan_id = db.Column(db.Integer, db.ForeignKey("tai_khoan.id"), nullable=False)
    nong_trai_id = db.Column(db.Integer, db.ForeignKey("nong_trai.id"), nullable=True)
    danh_muc_id = db.Column(db.Integer, db.ForeignKey("danh_muc.id"), nullable=False)
    ten = db.Column(db.Unicode(150), nullable=False)
    mo_ta = db.Column(db.UnicodeText)
    gia = db.Column(db.Numeric(12, 2), nullable=False)
    so_luong = db.Column(db.Integer, default=0)
    don_vi_tinh = db.Column(db.Unicode(20), default="kg")
    dia_chi = db.Column(db.Unicode(255))
    trang_thai = db.Column(db.Integer, default=1)  # 1 = còn hàng, 0 = hết hàng
    trang_thai_duyet = db.Column(db.Integer, default=0)  # 0 = chờ duyệt, 1 = đã duyệt, 2 = từ chối
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    binh_luans = db.relationship("BinhLuan", backref="san_pham", lazy=True, cascade="all, delete-orphan")
    yeu_thichs = db.relationship("YeuThich", backref="san_pham", lazy=True, cascade="all, delete-orphan")
    ma_truy_xuat = db.relationship("MaTruyXuat", backref="san_pham", uselist=False, cascade="all, delete-orphan")
    ma_qr = db.relationship("MaQR", backref="san_pham", uselist=False, cascade="all, delete-orphan")
    hinh_anhs = db.relationship("HinhAnhSanPham", backref="san_pham", lazy=True, cascade="all, delete-orphan")
    moc_truy_xuats = db.relationship("MocTruyXuat", backref="san_pham", lazy=True, cascade="all, delete-orphan", order_by="MocTruyXuat.ngay_thuc_hien")
    kiem_duyets = db.relationship("KiemDuyetSanPham", backref="san_pham", lazy=True, cascade="all, delete-orphan")

    @property
    def diem_trung_binh(self):
        danh_gias = [b.danh_gia for b in self.binh_luans if b.danh_gia]
        return round(sum(danh_gias) / len(danh_gias), 1) if danh_gias else 0


class BinhLuan(db.Model):
    __tablename__ = "binh_luan"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), nullable=False)
    tai_khoan_id = db.Column(db.Integer, db.ForeignKey("tai_khoan.id"), nullable=False)
    noi_dung = db.Column(db.UnicodeText, nullable=False)
    danh_gia = db.Column(db.Integer)  # 1-5 sao, có thể null nếu chỉ bình luận
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class YeuThich(db.Model):
    __tablename__ = "yeu_thich"
    id = db.Column(db.Integer, primary_key=True)
    tai_khoan_id = db.Column(db.Integer, db.ForeignKey("tai_khoan.id"), nullable=False)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), nullable=False)
    ngay_luu = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("tai_khoan_id", "san_pham_id", name="uq_yeu_thich"),)


class MaTruyXuat(db.Model):
    __tablename__ = "ma_truy_xuat"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), unique=True, nullable=False)
    gia_tri_ma = db.Column(db.String(20), unique=True, nullable=False)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)


class MaQR(db.Model):
    __tablename__ = "ma_qr"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), unique=True, nullable=False)
    duong_dan_anh_qr = db.Column(db.String(255))
    noi_dung_qr = db.Column(db.String(255))
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)


class HinhAnhSanPham(db.Model):
    __tablename__ = "hinh_anh_san_pham"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), nullable=False)
    duong_dan = db.Column(db.String(255), nullable=False)
    la_anh_chinh = db.Column(db.Boolean, default=False)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)


class LoaiMocTruyXuat(db.Model):
    __tablename__ = "loai_moc_truy_xuat"
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.Unicode(50), nullable=False)
    mo_ta = db.Column(db.Unicode(255))
    thu_tu = db.Column(db.Integer, default=0)

    moc_truy_xuats = db.relationship("MocTruyXuat", backref="loai_moc", lazy=True)


class MocTruyXuat(db.Model):
    __tablename__ = "moc_truy_xuat"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), nullable=False)
    loai_moc_id = db.Column(db.Integer, db.ForeignKey("loai_moc_truy_xuat.id"), nullable=False)
    mo_ta = db.Column(db.UnicodeText)
    hinh_anh = db.Column(db.String(255))
    dia_diem = db.Column(db.Unicode(255))
    ngay_thuc_hien = db.Column(db.Date, nullable=False)


class KiemDuyetSanPham(db.Model):
    __tablename__ = "kiem_duyet_san_pham"
    id = db.Column(db.Integer, primary_key=True)
    san_pham_id = db.Column(db.Integer, db.ForeignKey("san_pham.id"), nullable=False)
    tai_khoan_duyet_id = db.Column(db.Integer, db.ForeignKey("tai_khoan.id"), nullable=False)
    trang_thai = db.Column(db.Integer, nullable=False)  # 1 = duyệt, 2 = từ chối
    ghi_chu = db.Column(db.UnicodeText)
    ngay_duyet = db.Column(db.DateTime, default=datetime.utcnow)
