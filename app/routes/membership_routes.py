"""
Royal Brothers Fitness Gym - Membership Routes
Lets the frontend fetch membership plans and lets logged-in users
request a plan (the "Get Started" workflow — Bug 3/6).

Registered in app/__init__.py under url_prefix="/api/membership", so full paths are:
    GET  /api/membership/plans
    GET  /api/membership/plans/<id>
    POST /api/membership/request
    GET  /api/membership/my-request
"""

from functools import wraps

from flask import Blueprint, request, session, jsonify

from ..models import (
    get_all_plans,
    get_plan_by_id,
    create_membership_request,
    get_active_or_pending_request,
    get_latest_membership_request,
)

membership_bp = Blueprint("membership_bp", __name__)


def login_required(f):
    """Blocks access unless the user is logged in (session has user_id)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Please log in first."}), 401
        return f(*args, **kwargs)
    return wrapper


# ============================================
# PLANS
# ============================================

@membership_bp.route("/plans", methods=["GET"])
def list_plans():
    plans = get_all_plans()
    return jsonify({"success": True, "plans": plans}), 200


@membership_bp.route("/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    plan = get_plan_by_id(plan_id)
    if not plan:
        return jsonify({"success": False, "message": "Plan not found."}), 404
    return jsonify({"success": True, "plan": plan}), 200


# ============================================
# MEMBERSHIP REQUEST ("Get Started" workflow)
# ============================================

@membership_bp.route("/request", methods=["POST"])
@login_required
def request_membership():
    data = request.get_json() if request.is_json else request.form
    plan_id = data.get("plan_id")

    if not plan_id:
        return jsonify({"success": False, "message": "Plan is required."}), 400

    plan = get_plan_by_id(plan_id)
    if not plan:
        return jsonify({"success": False, "message": "Selected plan does not exist."}), 404

    # Block duplicate requests (Bug 6) — only one active/pending at a time
    existing = get_active_or_pending_request(session["user_id"])
    if existing:
        if existing["status"] == "active":
            return jsonify({"success": False, "message": "You already have an active membership."}), 409
        return jsonify({"success": False, "message": "You already have a pending membership request."}), 409

    create_membership_request(session["user_id"], plan_id)

    return jsonify({
        "success": True,
        "message": "Your membership request has been submitted successfully. "
                    "Please visit Royal Brothers Fitness Gym to complete payment "
                    "and activate your membership."
    }), 201


@membership_bp.route("/my-request", methods=["GET"])
@login_required
def my_request():
    """Returns the user's latest membership request (any status),
    used by the Membership page (button states) and Profile page
    (membership card + expiry warning)."""
    latest = get_latest_membership_request(session["user_id"])
    return jsonify({"success": True, "request": latest}), 200
