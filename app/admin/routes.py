from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models import SanPham, KiemDuyetSanPham

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.vai_tro_id != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/kiem-duyet")
@admin_required
def kiem_duyet():
    cho_duyet = SanPham.query.filter_by(trang_thai_duyet=0).order_by(SanPham.ngay_tao.asc()).all()
    return render_template("admin/kiem_duyet.html", products=cho_duyet)


@admin_bp.route("/kiem-duyet/<int:id>/duyet", methods=["POST"])
@admin_required
def duyet(id):
    sp = SanPham.query.get_or_404(id)
    sp.trang_thai_duyet = 1

    db.session.add(KiemDuyetSanPham(
        san_pham_id=sp.id,
        tai_khoan_duyet_id=current_user.id,
        trang_thai=1,
        ghi_chu=request.form.get("ghi_chu", "").strip(),
    ))
    db.session.commit()

    flash(f"Đã duyệt sản phẩm '{sp.ten}'.", "success")
    return redirect(url_for("admin.kiem_duyet"))


@admin_bp.route("/kiem-duyet/<int:id>/tu-choi", methods=["POST"])
@admin_required
def tu_choi(id):
    sp = SanPham.query.get_or_404(id)
    sp.trang_thai_duyet = 2

    db.session.add(KiemDuyetSanPham(
        san_pham_id=sp.id,
        tai_khoan_duyet_id=current_user.id,
        trang_thai=2,
        ghi_chu=request.form.get("ghi_chu", "").strip(),
    ))
    db.session.commit()

    flash(f"Đã từ chối sản phẩm '{sp.ten}'.", "info")
    return redirect(url_for("admin.kiem_duyet"))