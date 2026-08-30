from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import BinhLuan, SanPham

comment_bp = Blueprint("comment", __name__)


@comment_bp.route("/san-pham/<int:san_pham_id>/binh-luan", methods=["POST"])
@login_required
def them(san_pham_id):
    sp = SanPham.query.get_or_404(san_pham_id)

    noi_dung = request.form.get("noi_dung", "").strip()
    danh_gia_raw = request.form.get("danh_gia", "")

    if not noi_dung:
        flash("Vui lòng nhập nội dung bình luận.", "danger")
        return redirect(url_for("product.detail", id=san_pham_id))

    danh_gia = None
    if danh_gia_raw.isdigit() and 1 <= int(danh_gia_raw) <= 5:
        danh_gia = int(danh_gia_raw)

    bl = BinhLuan(
        san_pham_id=sp.id,
        tai_khoan_id=current_user.id,
        noi_dung=noi_dung,
        danh_gia=danh_gia,
    )
    db.session.add(bl)
    db.session.commit()

    flash("Đã gửi bình luận!", "success")
    return redirect(url_for("product.detail", id=san_pham_id))


@comment_bp.route("/binh-luan/<int:id>/xoa", methods=["POST"])
@login_required
def xoa(id):
    bl = BinhLuan.query.get_or_404(id)

    if bl.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền xóa bình luận này.", "danger")
        return redirect(url_for("product.detail", id=bl.san_pham_id))

    san_pham_id = bl.san_pham_id
    db.session.delete(bl)
    db.session.commit()

    flash("Đã xóa bình luận.", "info")
    return redirect(url_for("product.detail", id=san_pham_id))