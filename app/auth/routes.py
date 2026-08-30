from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db, bcrypt
from app.models import TaiKhoan, VaiTro

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/dang-ky", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("product.index"))

    vai_tro_list = VaiTro.query.filter(VaiTro.id.in_([2, 3])).all()

    if request.method == "POST":
        ho_ten = request.form.get("ho_ten", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        vai_tro_id = request.form.get("vai_tro_id", 3)

        if not ho_ten or not email or not password:
            flash("Vui lòng điền đầy đủ thông tin bắt buộc.", "danger")
            return render_template("auth/register.html", vai_tro_list=vai_tro_list)

        if password != confirm:
            flash("Mật khẩu xác nhận không khớp.", "danger")
            return render_template("auth/register.html", vai_tro_list=vai_tro_list)

        if TaiKhoan.query.filter_by(email=email).first():
            flash("Email đã được sử dụng.", "danger")
            return render_template("auth/register.html", vai_tro_list=vai_tro_list)

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_tk = TaiKhoan(ho_ten=ho_ten, email=email, mat_khau=hashed_pw, vai_tro_id=int(vai_tro_id))
        db.session.add(new_tk)
        db.session.commit()

        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", vai_tro_list=vai_tro_list)


@auth_bp.route("/dang-nhap", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("product.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        tk = TaiKhoan.query.filter_by(email=email).first()

        if tk and bcrypt.check_password_hash(tk.mat_khau, password):
            login_user(tk)
            flash(f"Chào mừng {tk.ho_ten}!", "success")
            return redirect(url_for("product.index"))
        else:
            flash("Email hoặc mật khẩu không đúng.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/dang-xuat")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))