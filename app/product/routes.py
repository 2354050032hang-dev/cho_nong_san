import os
import secrets
import string
import qrcode
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import (SanPham,DanhMuc,MaTruyXuat,MaQR,HinhAnhSanPham,YeuThich,MocTruyXuat,LoaiMocTruyXuat)
product_bp = Blueprint("product", __name__, template_folder="../templates/product")

load_dotenv()
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)
def sinh_ma_truy_xuat():
    while True:
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        code = f"NS-{suffix}"
        if not MaTruyXuat.query.filter_by(gia_tri_ma=code).first():
            return code


def luu_anh(file):
    if not file or not file.filename:
        print("KHÔNG NHẬN ĐƯỢC FILE ẢNH")
        return None

    if "." not in file.filename:
        print("FILE KHÔNG CÓ PHẦN MỞ RỘNG")
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()

    if ext not in {"png", "jpg", "jpeg", "webp"}:
        print("ĐỊNH DẠNG ẢNH KHÔNG HỢP LỆ:", ext)
        return None

    try:
        print("Đang upload ảnh:", file.filename)

        result = cloudinary.uploader.upload(
            file,
            folder="cho_nong_san/san_pham",
            resource_type="image"
        )

        url = result["secure_url"]

        print("UPLOAD CLOUDINARY THÀNH CÔNG")
        print(url)

        return url

    except Exception as e:
        print("LỖI CLOUDINARY:")
        print(e)
        return None

def sinh_qr(san_pham_id, gia_tri_ma):
    qr_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "qrcodes")
    os.makedirs(qr_folder, exist_ok=True)
    link = url_for("product.tra_cuu", ma=gia_tri_ma, _external=True)
    img = qrcode.make(link)
    filename = f"{gia_tri_ma}.png"
    img.save(os.path.join(qr_folder, filename))
    return filename, link


@product_bp.route("/")
def index():
    search = request.args.get("search", "").strip()
    co_truy_xuat = request.args.get("co_truy_xuat")
    danh_muc_id = request.args.get("danh_muc_id", type=int)

    query = SanPham.query.filter_by(trang_thai_duyet=1)

    if search:
        query = query.filter(SanPham.ten.ilike(f"%{search}%"))
    if co_truy_xuat:
        query = query.filter(SanPham.moc_truy_xuats.any())
    if danh_muc_id:
        query = query.filter_by(danh_muc_id=danh_muc_id)

    products = query.order_by(SanPham.ngay_tao.desc()).all()
    danh_mucs = DanhMuc.query.all()

    return render_template(
        "product/index.html",
        products=products, search=search, co_truy_xuat=co_truy_xuat,
        danh_mucs=danh_mucs, danh_muc_id=danh_muc_id,
    )

@product_bp.route("/san-pham/<int:id>")
def detail(id):
    product = SanPham.query.get_or_404(id)
    binh_luans = sorted(product.binh_luans, key=lambda b: b.ngay_tao, reverse=True)

    da_yeu_thich = False
    if current_user.is_authenticated:
        da_yeu_thich = YeuThich.query.filter_by(tai_khoan_id=current_user.id, san_pham_id=id).first() is not None

    return render_template("product/detail.html", product=product, binh_luans=binh_luans, da_yeu_thich=da_yeu_thich)
@product_bp.route("/dang-tin", methods=["GET", "POST"])
@login_required
def create():
    danh_mucs = DanhMuc.query.all()

    if request.method == "POST":
        ten = request.form.get("ten", "").strip()
        danh_muc_id = request.form.get("danh_muc_id")
        gia = request.form.get("gia", "")

        if not ten or not danh_muc_id or not gia:
            flash("Vui lòng điền đầy đủ thông tin bắt buộc.", "danger")
            return render_template("product/create.html", danh_mucs=danh_mucs)

        sp = SanPham(
            tai_khoan_id=current_user.id,
            nong_trai_id=current_user.nong_trai.id if current_user.nong_trai else None,
            danh_muc_id=int(danh_muc_id),
            ten=ten,
            mo_ta=request.form.get("mo_ta", "").strip(),
            gia=float(gia),
            so_luong=int(request.form.get("so_luong", 0) or 0),
            don_vi_tinh=request.form.get("don_vi_tinh", "kg").strip(),
            dia_chi=request.form.get("dia_chi", "").strip(),
            trang_thai_duyet=0,
        )
        db.session.add(sp)
        db.session.commit()

        ma = sinh_ma_truy_xuat()
        db.session.add(MaTruyXuat(san_pham_id=sp.id, gia_tri_ma=ma))
        db.session.commit()

        qr_filename, qr_link = sinh_qr(sp.id, ma)
        db.session.add(MaQR(san_pham_id=sp.id, duong_dan_anh_qr=qr_filename, noi_dung_qr=qr_link))
        db.session.commit()

        filename = luu_anh(request.files.get("hinh_anh"))
        if filename:
            db.session.add(HinhAnhSanPham(san_pham_id=sp.id, duong_dan=filename, la_anh_chinh=True))
            db.session.commit()

        flash("Đăng tin thành công! Sản phẩm đang chờ duyệt.", "success")
        return redirect(url_for("product.detail", id=sp.id))

    return render_template("product/create.html", danh_mucs=danh_mucs)
@product_bp.route("/truy-xuat/<ma>")
def tra_cuu_duong_dan(ma):
    mtx = MaTruyXuat.query.filter_by(gia_tri_ma=ma).first()
    if not mtx:
        flash("Không tìm thấy sản phẩm với mã này.", "danger")
        return redirect(url_for("product.index"))
    return redirect(url_for("product.detail", id=mtx.san_pham_id))
@product_bp.route("/san-pham/<int:id>/sua", methods=["GET", "POST"])
@login_required
def edit(id):
    sp = SanPham.query.get_or_404(id)

    if sp.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền sửa tin này.", "danger")
        return redirect(url_for("product.detail", id=id))

    danh_mucs = DanhMuc.query.all()

    if request.method == "POST":
        sp.ten = request.form.get("ten", "").strip()
        sp.danh_muc_id = int(request.form.get("danh_muc_id"))
        sp.mo_ta = request.form.get("mo_ta", "").strip()
        sp.gia = float(request.form.get("gia", 0))
        sp.so_luong = int(request.form.get("so_luong", 0) or 0)
        sp.don_vi_tinh = request.form.get("don_vi_tinh", "kg").strip()
        sp.dia_chi = request.form.get("dia_chi", "").strip()
        sp.trang_thai = int(request.form.get("trang_thai", 1))
        sp.ngay_cap_nhat = datetime.utcnow()

        new_image = luu_anh(request.files.get("hinh_anh"))
        if new_image:
            anh_chinh = HinhAnhSanPham.query.filter_by(san_pham_id=sp.id, la_anh_chinh=True).first()
            if anh_chinh:
                anh_chinh.duong_dan = new_image
            else:
                db.session.add(HinhAnhSanPham(san_pham_id=sp.id, duong_dan=new_image, la_anh_chinh=True))

        db.session.commit()
        flash("Cập nhật tin thành công!", "success")
        return redirect(url_for("product.detail", id=sp.id))
    return render_template("product/edit.html", product=sp, danh_mucs=danh_mucs)


@product_bp.route("/san-pham/<int:id>/xoa", methods=["POST"])
@login_required
def delete(id):
    sp = SanPham.query.get_or_404(id)

    if sp.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền xóa tin này.", "danger")
        return redirect(url_for("product.detail", id=id))

    db.session.delete(sp)
    db.session.commit()
    flash("Đã xóa tin đăng.", "info")
    return redirect(url_for("product.index"))
@product_bp.route("/san-pham/<int:id>/yeu-thich", methods=["POST"])
@login_required
def toggle_yeu_thich(id):
    existing = YeuThich.query.filter_by(tai_khoan_id=current_user.id, san_pham_id=id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Đã bỏ khỏi danh sách yêu thích.", "info")
    else:
        db.session.add(YeuThich(tai_khoan_id=current_user.id, san_pham_id=id))
        db.session.commit()
        flash("Đã lưu vào danh sách yêu thích!", "success")

    return redirect(url_for("product.detail", id=id))


@product_bp.route("/yeu-thich")
@login_required
def yeu_thich_list():
    danh_sach = YeuThich.query.filter_by(tai_khoan_id=current_user.id).order_by(YeuThich.ngay_luu.desc()).all()
    products = [yt.san_pham for yt in danh_sach]
    return render_template("product/yeu_thich.html", products=products)

@product_bp.route("/san-pham/<int:id>/moc-truy-xuat/them", methods=["GET", "POST"])
@login_required
def them_moc(id):
    sp = SanPham.query.get_or_404(id)

    if sp.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền chỉnh sửa truy xuất nguồn gốc của sản phẩm này.", "danger")
        return redirect(url_for("product.detail", id=id))

    loai_mocs = LoaiMocTruyXuat.query.order_by(LoaiMocTruyXuat.thu_tu).all()

    if request.method == "POST":
        loai_moc_id = request.form.get("loai_moc_id")
        ngay_thuc_hien_raw = request.form.get("ngay_thuc_hien", "")

        if not loai_moc_id or not ngay_thuc_hien_raw:
            flash("Vui lòng chọn loại mốc và ngày thực hiện.", "danger")
            return render_template("product/moc_form.html", product=sp, loai_mocs=loai_mocs)

        try:
            ngay = datetime.strptime(ngay_thuc_hien_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Ngày không hợp lệ.", "danger")
            return render_template("product/moc_form.html", product=sp, loai_mocs=loai_mocs)

        hinh_anh = luu_anh(request.files.get("hinh_anh"))

        moc = MocTruyXuat(
            san_pham_id=sp.id,
            loai_moc_id=int(loai_moc_id),
            mo_ta=request.form.get("mo_ta", "").strip(),
            dia_diem=request.form.get("dia_diem", "").strip(),
            hinh_anh=hinh_anh,
            ngay_thuc_hien=ngay,
        )
        db.session.add(moc)
        db.session.commit()

        flash("Đã thêm mốc truy xuất nguồn gốc!", "success")
        return redirect(url_for("product.detail", id=sp.id))

    return render_template("product/moc_form.html", product=sp, loai_mocs=loai_mocs)


@product_bp.route("/moc-truy-xuat/<int:moc_id>/xoa", methods=["POST"])
@login_required
def xoa_moc(moc_id):
    moc = MocTruyXuat.query.get_or_404(moc_id)

    if moc.san_pham.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền xóa mốc này.", "danger")
        return redirect(url_for("product.detail", id=moc.san_pham_id))

    san_pham_id = moc.san_pham_id
    db.session.delete(moc)
    db.session.commit()

    flash("Đã xóa mốc truy xuất.", "info")
    return redirect(url_for("product.detail", id=san_pham_id))
@product_bp.route('/tra-cuu')
def tra_cuu():
    # Lấy mã truy xuất người dùng nhập
    ma = request.args.get('ma', '').strip().upper()

    # Không nhập mã
    if not ma:
        flash('Vui lòng nhập mã truy xuất.', 'warning')
        return redirect(url_for('product.index'))

    # Tìm mã trong cơ sở dữ liệu
    ma_truy_xuat = MaTruyXuat.query.filter_by(
        gia_tri_ma=ma
    ).first()

    # Không tìm thấy
    if not ma_truy_xuat:
        flash(
            'Không tìm thấy sản phẩm với mã truy xuất này.',
            'danger'
        )
        return redirect(url_for('product.index'))

    # Tìm thấy → chuyển đến trang chi tiết sản phẩm
    return redirect(
        url_for(
            'product.detail',
            id=ma_truy_xuat.san_pham_id
        )
    )
