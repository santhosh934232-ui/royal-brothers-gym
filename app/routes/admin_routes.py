"""
Royal Brothers Fitness Gym - Admin Routes
Hidden admin login + full dashboard: manage members, membership plans,
membership requests, contact messages, and statistics.

Admin sessions are kept completely separate from user sessions
(session["admin_id"] vs session["user_id"]), so being logged in as a
user does NOT grant admin access, and vice versa.

Registered in app/__init__.py under url_prefix="/api/admin", so full paths are:
    POST /api/admin/login
    POST /api/admin/logout
    GET  /api/admin/dashboard/stats
    GET  /api/admin/members
    GET  /api/admin/plans
    POST /api/admin/plans
    PUT  /api/admin/plans/<id>
    DELETE /api/admin/plans/<id>
    GET  /api/admin/membership-requests
    POST /api/admin/membership-requests/<id>/status
    DELETE /api/admin/membership-requests/<id>
    GET  /api/admin/messages
    POST /api/admin/messages/<id>/read
"""

from datetime import date, timedelta
from functools import wraps

from flask import Blueprint, request, session, jsonify, current_app
from werkzeug.security import check_password_hash

from ..models import (
    get_admin_by_username,
    get_admin_by_id,
    get_all_users,
    get_all_plans,
    get_plan_by_id,
    create_plan,
    update_plan,
    delete_plan,
    get_plan_usage_count,
    get_all_membership_requests,
    get_membership_request_by_id,
    update_membership_request_status,
    delete_membership_request,
    get_all_contact_messages,
    mark_message_as_read,
    get_dashboard_stats,
)

admin_bp = Blueprint("admin_bp", __name__)


def admin_login_required(f):
    """Blocks access unless an admin is logged in (session has admin_id)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({"success": False, "message": "Admin login required."}), 401
        return f(*args, **kwargs)
    return wrapper


def get_request_data():
    if request.is_json:
        return request.get_json()
    return request.form


def _verify_admin_password(password):
    """Verifies the given plaintext password against the currently
    logged-in admin's stored hash. Used to gate all destructive delete
    actions behind a fresh password re-entry. Never logs the password
    itself -- only success/failure is ever recorded."""
    if not password:
        return False

    admin = get_admin_by_id(session.get("admin_id"))
    if not admin:
        return False

    return check_password_hash(admin["password_hash"], password)


# ============================================
# ADMIN LOGIN / LOGOUT
# ============================================

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = get_request_data()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    admin = get_admin_by_username(username)

    if not admin or not check_password_hash(admin["password_hash"], password):
        return jsonify({"success": False, "message": "Invalid admin credentials."}), 401

    session["admin_id"] = admin["id"]
    session["admin_username"] = admin["username"]

    return jsonify({"success": True, "message": "Admin login successful."}), 200


@admin_bp.route("/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    return jsonify({"success": True, "message": "Admin logged out."}), 200


@admin_bp.route("/me", methods=["GET"])
def admin_me():
    """Lets admin-dashboard.html check if an admin is currently logged in."""
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Not logged in."}), 401
    return jsonify({
        "success": True,
        "admin": {"id": session["admin_id"], "username": session["admin_username"]}
    }), 200


# ============================================
# DASHBOARD STATISTICS
# ============================================

@admin_bp.route("/dashboard/stats", methods=["GET"])
@admin_login_required
def dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify({"success": True, "stats": stats}), 200


# ============================================
# MANAGE MEMBERS
# ============================================

@admin_bp.route("/members", methods=["GET"])
@admin_login_required
def manage_members():
    users = get_all_users()
    return jsonify({"success": True, "members": users}), 200


# ============================================
# MANAGE MEMBERSHIP PLANS
# ============================================

@admin_bp.route("/plans", methods=["GET"])
@admin_login_required
def manage_plans():
    plans = get_all_plans()
    return jsonify({"success": True, "plans": plans}), 200


@admin_bp.route("/plans", methods=["POST"])
@admin_login_required
def add_plan():
    data = get_request_data()
    plan_name = (data.get("plan_name") or "").strip()
    duration_months = data.get("duration_months")
    price = data.get("price")
    features = (data.get("features") or "").strip()

    if not all([plan_name, duration_months, price]):
        return jsonify({"success": False, "message": "Plan name, duration, and price are required."}), 400

    plan_id = create_plan(plan_name, duration_months, price, features)
    return jsonify({"success": True, "message": "Plan created.", "plan_id": plan_id}), 201


@admin_bp.route("/plans/<int:plan_id>", methods=["PUT"])
@admin_login_required
def edit_plan(plan_id):
    data = get_request_data()
    plan_name = (data.get("plan_name") or "").strip()
    duration_months = data.get("duration_months")
    price = data.get("price")
    features = (data.get("features") or "").strip()

    if not all([plan_name, duration_months, price]):
        return jsonify({"success": False, "message": "Plan name, duration, and price are required."}), 400

    update_plan(plan_id, plan_name, duration_months, price, features)
    return jsonify({"success": True, "message": "Plan updated."}), 200


@admin_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
@admin_login_required
def remove_plan(plan_id):
    data = get_request_data()
    password = data.get("password") or ""

    if not _verify_admin_password(password):
        return jsonify({"success": False, "message": "Incorrect admin password."}), 401

    try:
        existing = get_plan_by_id(plan_id)
        if not existing:
            return jsonify({"success": False, "message": "Plan not found."}), 404

        usage_count = get_plan_usage_count(plan_id)
        if usage_count > 0:
            return jsonify({
                "success": False,
                "message": (
                    "This membership plan cannot be deleted because it is "
                    "already assigned to one or more membership requests."
                ),
            }), 400

        delete_plan(plan_id)
        return jsonify({"success": True, "message": "Plan deleted."}), 200

    except Exception:
        current_app.logger.exception(f"Failed to delete membership plan {plan_id}")
        return jsonify({
            "success": False,
            "message": "Something went wrong while deleting the plan. Please try again.",
        }), 500


# ============================================
# MANAGE MEMBERSHIP REQUESTS
# ============================================

@admin_bp.route("/membership-requests", methods=["GET"])
@admin_login_required
def manage_membership_requests():
    requests = get_all_membership_requests()
    return jsonify({"success": True, "requests": requests}), 200


@admin_bp.route("/membership-requests/<int:request_id>/status", methods=["POST"])
@admin_login_required
def change_membership_request_status(request_id):
    data = get_request_data()
    status = (data.get("status") or "").strip().lower()

    if status not in ("pending", "active", "rejected"):
        return jsonify({"success": False, "message": "Invalid status."}), 400

    existing = get_membership_request_by_id(request_id)
    if not existing:
        return jsonify({"success": False, "message": "Request not found."}), 404

    start_date = None
    expiry_date = None

    if status == "active":
        # Activating: set start date to today, expiry date based on the
        # plan's duration (e.g. 3 months -> today + 3 months).
        start_date = date.today()
        expiry_date = start_date + timedelta(days=30 * existing["duration_months"])

    update_membership_request_status(request_id, status, start_date, expiry_date)
    return jsonify({"success": True, "message": "Membership request updated."}), 200


@admin_bp.route("/membership-requests/<int:request_id>", methods=["DELETE"])
@admin_login_required
def remove_membership_request(request_id):
    data = get_request_data()
    password = data.get("password") or ""

    if not _verify_admin_password(password):
        return jsonify({"success": False, "message": "Incorrect admin password."}), 401

    try:
        existing = get_membership_request_by_id(request_id)
        if not existing:
            return jsonify({"success": False, "message": "Membership request not found."}), 404

        delete_membership_request(request_id)
        return jsonify({"success": True, "message": "Membership deleted."}), 200

    except Exception:
        current_app.logger.exception(f"Failed to delete membership request {request_id}")
        return jsonify({
            "success": False,
            "message": "Something went wrong while deleting the membership. Please try again.",
        }), 500


# ============================================
# CONTACT MESSAGES
# ============================================

@admin_bp.route("/messages", methods=["GET"])
@admin_login_required
def view_messages():
    messages = get_all_contact_messages()
    return jsonify({"success": True, "messages": messages}), 200


@admin_bp.route("/messages/<int:message_id>/read", methods=["POST"])
@admin_login_required
def read_message(message_id):
    mark_message_as_read(message_id)
    return jsonify({"success": True, "message": "Marked as read."}), 200
