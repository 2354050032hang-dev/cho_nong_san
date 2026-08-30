import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app import db
from app.models import NongTrai

farm_bp = Blueprint("farm", __name__, template_folder="../templates/farm")


def luu_anh_bia(file):
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in {"png", "jpg", "jpeg", "webp"}:
            filename = f"{secrets.token_hex(8)}.{ext}"
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            return filename
    return None


@farm_bp.route("/nong-trai/tao", methods=["GET", "POST"])
@login_required
def create():
    if current_user.nong_trai:
        flash("Bạn đã có Trang nông trại rồi.", "info")
        return redirect(url_for("farm.profile", id=current_user.nong_trai.id))

    if request.method == "POST":
        ten = request.form.get("ten", "").strip()
        if not ten:
            flash("Vui lòng nhập tên nông trại.", "danger")
            return render_template("farm/create.html")

        nt = NongTrai(
            tai_khoan_id=current_user.id,
            ten=ten,
            dia_chi=request.form.get("dia_chi", "").strip(),
            mo_ta=request.form.get("mo_ta", "").strip(),
            anh_bia=luu_anh_bia(request.files.get("anh_bia")),
        )
        db.session.add(nt)
        db.session.commit()

        flash("Tạo Trang nông trại thành công!", "success")
        return redirect(url_for("farm.profile", id=nt.id))

    return render_template("farm/create.html")


@farm_bp.route("/nong-trai/<int:id>")
def profile(id):
    nt = NongTrai.query.get_or_404(id)
    san_pham_da_duyet = [sp for sp in nt.san_phams if sp.trang_thai_duyet == 1]
    return render_template("farm/profile.html", nong_trai=nt, san_phams=san_pham_da_duyet)


@farm_bp.route("/nong-trai/<int:id>/sua", methods=["GET", "POST"])
@login_required
def edit(id):
    nt = NongTrai.query.get_or_404(id)

    if nt.tai_khoan_id != current_user.id:
        flash("Bạn không có quyền sửa Trang nông trại này.", "danger")
        return redirect(url_for("farm.profile", id=id))

    if request.method == "POST":
        nt.ten = request.form.get("ten", "").strip()
        nt.dia_chi = request.form.get("dia_chi", "").strip()
        nt.mo_ta = request.form.get("mo_ta", "").strip()

        anh_moi = luu_anh_bia(request.files.get("anh_bia"))
        if anh_moi:
            nt.anh_bia = anh_moi

        db.session.commit()
        flash("Cập nhật Trang nông trại thành công!", "success")
        return redirect(url_for("farm.profile", id=nt.id))

    return render_template("farm/edit.html", nong_trai=nt)