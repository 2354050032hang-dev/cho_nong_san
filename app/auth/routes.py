from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db, bcrypt
from app.models import TaiKhoan, VaiTro


auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="../templates/auth"
)


# =========================================================
# ĐĂNG KÝ
# =========================================================

@auth_bp.route("/dang-ky", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("product.index"))

    vai_tro_list = VaiTro.query.filter(
        VaiTro.id.in_([2, 3])
    ).all()

    if request.method == "POST":

        ho_ten = request.form.get("ho_ten", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        vai_tro_id = request.form.get("vai_tro_id", 3)

        # Kiểm tra dữ liệu bắt buộc
        if not ho_ten or not email or not password:

            flash(
                "Vui lòng điền đầy đủ thông tin bắt buộc.",
                "danger"
            )

            return render_template(
                "auth/register.html",
                vai_tro_list=vai_tro_list
            )

        # Kiểm tra xác nhận mật khẩu
        if password != confirm:

            flash(
                "Mật khẩu xác nhận không khớp.",
                "danger"
            )

            return render_template(
                "auth/register.html",
                vai_tro_list=vai_tro_list
            )

        # Kiểm tra email đã tồn tại
        if TaiKhoan.query.filter_by(email=email).first():

            flash(
                "Email đã được sử dụng.",
                "danger"
            )

            return render_template(
                "auth/register.html",
                vai_tro_list=vai_tro_list
            )

        # Mã hóa mật khẩu
        hashed_pw = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        new_tk = TaiKhoan(
            ho_ten=ho_ten,
            email=email,
            mat_khau=hashed_pw,
            vai_tro_id=int(vai_tro_id)
        )

        db.session.add(new_tk)
        db.session.commit()

        flash(
            "Đăng ký thành công! Vui lòng đăng nhập.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html",
        vai_tro_list=vai_tro_list
    )


# =========================================================
# ĐĂNG NHẬP
# =========================================================

@auth_bp.route("/dang-nhap", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("product.index"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        tk = TaiKhoan.query.filter_by(
            email=email
        ).first()

        if tk and bcrypt.check_password_hash(
            tk.mat_khau,
            password
        ):

            # Tài khoản bị khóa
            if tk.trang_thai == 0:

                flash(
                    "Tài khoản này đã bị khóa. "
                    "Vui lòng liên hệ quản trị viên.",
                    "danger"
                )

                return render_template(
                    "auth/login.html"
                )

            login_user(tk)

            flash(
                f"Chào mừng {tk.ho_ten}!",
                "success"
            )

            return redirect(
                url_for("product.index")
            )

        else:

            flash(
                "Email hoặc mật khẩu không đúng.",
                "danger"
            )

    return render_template(
        "auth/login.html"
    )


# =========================================================
# THÔNG TIN TÀI KHOẢN
# =========================================================

@auth_bp.route(
    "/tai-khoan",
    methods=["GET", "POST"]
)
@login_required
def tai_khoan():

    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        # =================================================
        # CẬP NHẬT HỌ TÊN
        # =================================================

        if action == "update_profile":

            ho_ten = request.form.get(
                "ho_ten",
                ""
            ).strip()

            if not ho_ten:

                flash(
                    "Họ tên không được để trống.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )

            if len(ho_ten) > 100:

                flash(
                    "Họ tên không được vượt quá 100 ký tự.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )

            # Cập nhật tên
            current_user.ho_ten = ho_ten

            db.session.commit()

            flash(
                "Cập nhật thông tin thành công.",
                "success"
            )

            return redirect(
                url_for("auth.tai_khoan")
            )


        # =================================================
        # ĐỔI MẬT KHẨU
        # =================================================

        elif action == "change_password":

            mat_khau_hien_tai = request.form.get(
                "mat_khau_hien_tai",
                ""
            )

            mat_khau_moi = request.form.get(
                "mat_khau_moi",
                ""
            )

            xac_nhan_mat_khau = request.form.get(
                "xac_nhan_mat_khau",
                ""
            )

            # Không được bỏ trống
            if (
                not mat_khau_hien_tai
                or not mat_khau_moi
                or not xac_nhan_mat_khau
            ):

                flash(
                    "Vui lòng nhập đầy đủ thông tin mật khẩu.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )


            # Kiểm tra mật khẩu hiện tại
            if not bcrypt.check_password_hash(
                current_user.mat_khau,
                mat_khau_hien_tai
            ):

                flash(
                    "Mật khẩu hiện tại không chính xác.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )


            # Mật khẩu mới tối thiểu 6 ký tự
            if len(mat_khau_moi) < 6:

                flash(
                    "Mật khẩu mới phải có ít nhất 6 ký tự.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )


            # Xác nhận mật khẩu
            if mat_khau_moi != xac_nhan_mat_khau:

                flash(
                    "Xác nhận mật khẩu mới không khớp.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )


            # Không cho mật khẩu mới giống mật khẩu cũ
            if bcrypt.check_password_hash(
                current_user.mat_khau,
                mat_khau_moi
            ):

                flash(
                    "Mật khẩu mới phải khác mật khẩu hiện tại.",
                    "danger"
                )

                return redirect(
                    url_for("auth.tai_khoan")
                )


            # Mã hóa mật khẩu mới
            hashed_pw = bcrypt.generate_password_hash(
                mat_khau_moi
            ).decode("utf-8")

            current_user.mat_khau = hashed_pw

            db.session.commit()

            flash(
                "Đổi mật khẩu thành công.",
                "success"
            )

            return redirect(
                url_for("auth.tai_khoan")
            )


    return render_template(
        "auth/tai_khoan.html"
    )


# =========================================================
# ĐĂNG XUẤT
# =========================================================

@auth_bp.route("/dang-xuat")
@login_required
def logout():

    logout_user()

    flash(
        "Bạn đã đăng xuất.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )