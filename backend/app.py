"""
Module 23: High-Risk Drug Monitoring System
Flask REST API Backend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from bson import ObjectId
import os
import requests
import sys
from pathlib import Path

try:
    from database.database import (
        high_risk_drugs,
        monitoring_requirements,
        lab_alerts,
        dose_adjustments,
        monitoring_schedules,
        audit_log,
        create_indexes,
        seed_data,
        trigger_on_lab_alert_insert,
        procedure_evaluate_alert_conditions,
        procedure_generate_monitoring_schedule,
        trigger_check_dose_adjustment,
    )
except ModuleNotFoundError:
    # Support running backend/app.py directly when backend+database are siblings under Frontend/.
    frontend_root = Path(__file__).resolve().parent.parent
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))
    from database.database import (
        high_risk_drugs,
        monitoring_requirements,
        lab_alerts,
        dose_adjustments,
        monitoring_schedules,
        audit_log,
        create_indexes,
        seed_data,
        trigger_on_lab_alert_insert,
        procedure_evaluate_alert_conditions,
        procedure_generate_monitoring_schedule,
        trigger_check_dose_adjustment,
    )

app = Flask(__name__)
CORS(app)

MODULE_21_URL = os.environ.get("MODULE_21_URL", "http://localhost:5021")
MODULE_22_URL = os.environ.get("MODULE_22_URL", "http://localhost:5022")
MODULE_24_URL = os.environ.get("MODULE_24_URL", "http://localhost:5024")
MODULE_25_URL = os.environ.get("MODULE_25_URL", "http://localhost:5025")


# ===== SPLIT PART 1 START: App setup, helpers, and core CRUD endpoints =====


def serialize(doc):
    if doc is None:
        return None
    doc = dict(doc)
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            doc[k] = v.isoformat()
        elif isinstance(v, list):
            doc[k] = [serialize(i) if isinstance(i, dict) else i for i in v]
        elif isinstance(v, dict):
            doc[k] = serialize(v)
    return doc


def success(data, message="OK", status=200):
    return jsonify({"status": "success", "message": message, "data": data}), status


def error(message, status=400):
    return jsonify({"status": "error", "message": message}), status


def log_audit(action, detail):
    audit_log.insert_one({"action": action, "detail": detail, "timestamp": datetime.utcnow()})


@app.route("/health", methods=["GET"])
def health():
    return success({"module": "23", "name": "High-Risk Drug Monitoring", "status": "running"})


@app.route("/api/drugs", methods=["GET"])
def get_all_drugs():
    category = request.args.get("category")
    query = {"category": category} if category else {}
    drugs = [serialize(d) for d in high_risk_drugs.find(query)]
    return success(drugs)


@app.route("/api/drugs", methods=["POST"])
def add_drug():
    data = request.json
    if not data or not data.get("drug_id") or not data.get("name"):
        return error("drug_id and name are required")
    data["created_at"] = datetime.utcnow()
    high_risk_drugs.insert_one(data)
    log_audit("ADD_DRUG", {"drug_id": data["drug_id"]})
    return success(serialize(data), "Drug added", 201)


@app.route("/api/lab-alerts", methods=["GET"])
def get_alerts():
    status_filter = request.args.get("status")
    patient_id = request.args.get("patient_id")
    query = {}
    if status_filter:
        query["status"] = status_filter
    if patient_id:
        query["patient_id"] = patient_id
    alerts = [serialize(a) for a in lab_alerts.find(query).sort("created_at", -1)]
    return success(alerts)


@app.route("/api/lab-alerts/stats", methods=["GET"])
def get_alert_stats():
    alerts = [serialize(a) for a in lab_alerts.find({})]
    by_level = {}
    by_status = {}
    for alert in alerts:
        level = alert.get("alert_level", "Unknown")
        status_value = alert.get("status", "Unknown")
        by_level[level] = by_level.get(level, 0) + 1
        by_status[status_value] = by_status.get(status_value, 0) + 1
    return success({"total": len(alerts), "by_level": by_level, "by_status": by_status})


@app.route("/api/lab-alerts", methods=["POST"])
def create_alert():
    data = request.json
    data["created_at"] = datetime.utcnow()
    data["resolved_at"] = None
    data["resolved_by"] = None
    lab_alerts.insert_one(data)
    trigger_on_lab_alert_insert(data)
    if data.get("alert_level") == "Critical":
        _notify_module_25(data)
    log_audit("CREATE_ALERT", {"alert_id": data.get("alert_id")})
    return success(serialize(data), "Alert created", 201)


# ===== SPLIT PART 2 START: Evaluation, schedules, integration, and stats endpoints =====


@app.route("/api/dose-adjustments/evaluate", methods=["POST"])
def evaluate_dose():
    body = request.json
    suggestions = trigger_check_dose_adjustment(
        body.get("patient_id"), body.get("drug_id"), body.get("lab_test"), body.get("result_value")
    )
    return success({"suggestions": suggestions, "patient_id": body.get("patient_id")})


@app.route("/api/dose-adjustments", methods=["GET"])
def get_dose_adjustments():
    drug_id = request.args.get("drug_id")
    query = {"drug_id": drug_id} if drug_id else {}
    adjustments = [serialize(a) for a in dose_adjustments.find(query)]
    return success(adjustments)


@app.route("/api/monitoring-requirements", methods=["GET"])
def get_monitoring_requirements():
    drug_id = request.args.get("drug_id")
    query = {"drug_id": drug_id} if drug_id else {}
    requirements = [serialize(r) for r in monitoring_requirements.find(query)]
    return success(requirements)


@app.route("/api/monitoring-schedules", methods=["GET"])
def get_monitoring_schedules():
    patient_id = request.args.get("patient_id")
    status_filter = request.args.get("status")
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if status_filter:
        query["status"] = status_filter
    schedules = [serialize(s) for s in monitoring_schedules.find(query).sort("next_due", 1)]
    return success(schedules)


@app.route("/api/monitoring-schedules/generate", methods=["POST"])
def generate_schedule():
    body = request.json
    result = procedure_generate_monitoring_schedule(body.get("patient_id"), body.get("drug_id"))
    return success(result)


@app.route("/api/procedures/temporal-schedule", methods=["POST"])
def generate_temporal_schedule():
    body = request.json or {}
    patient_id = body.get("patient_id")
    drug_id = body.get("drug_id")
    result = procedure_generate_monitoring_schedule(patient_id, drug_id)
    # Tag newly created schedules for UI clarity when temporal mode is selected.
    monitoring_schedules.update_many(
        {"patient_id": patient_id, "drug_id": drug_id, "status": "Scheduled"},
        {"$set": {"priority": "High", "status": "Due Soon"}},
    )
    return success({"mode": "temporal", **result})


@app.route("/api/procedures/evaluate-alerts", methods=["POST"])
def run_evaluate_alerts():
    body = request.json
    result = procedure_evaluate_alert_conditions(body.get("patient_id"), body.get("drug_id"), body.get("lab_results", {}))
    return success(result)


@app.route("/api/procedures/overdue-schedules", methods=["GET"])
def get_overdue_schedules():
    now = datetime.utcnow()
    overdue = [
        serialize(s)
        for s in monitoring_schedules.find({"next_due": {"$lt": now}, "status": {"$ne": "Completed"}}).sort("next_due", 1)
    ]
    return success({"overdue_count": len(overdue), "schedules": overdue})


@app.route("/api/integration/patient/<patient_id>", methods=["GET"])
def get_patient_from_module21(patient_id):
    try:
        response = requests.get(f"{MODULE_21_URL}/api/patients/{patient_id}", timeout=5)
        if response.status_code == 200:
            return success(response.json().get("data", {}))
        return error(f"Module 21 returned {response.status_code}")
    except Exception:
        return success(
            {
                "patient_id": patient_id,
                "name": f"Patient {patient_id}",
                "age": 58,
                "weight_kg": 72,
                "renal_function": "CrCl 45 mL/min",
                "liver_status": "Normal",
                "allergies": [],
                "source": "mock_fallback",
            }
        )


@app.route("/api/integration/prescriptions/<patient_id>", methods=["GET"])
def get_prescriptions_from_module22(patient_id):
    try:
        response = requests.get(f"{MODULE_22_URL}/api/prescriptions/{patient_id}", timeout=5)
        if response.status_code == 200:
            return success(response.json().get("data", {}))
        return error(f"Module 22 returned {response.status_code}")
    except Exception:
        return success(
            {
                "patient_id": patient_id,
                "prescriptions": [
                    {
                        "drug_id": "D001",
                        "drug_name": "Warfarin",
                        "dose": "5 mg",
                        "frequency": "OD",
                        "start_date": datetime.utcnow().date().isoformat(),
                        "physician": "Dr. Demo",
                    }
                ],
                "source": "mock_fallback",
            }
        )


@app.route("/api/integration/provide/monitoring-data/<patient_id>", methods=["GET"])
def provide_data_for_module24_25(patient_id):
    active_alerts = [serialize(a) for a in lab_alerts.find({"patient_id": patient_id, "status": "Active"})]
    overdue = [serialize(s) for s in monitoring_schedules.find({"patient_id": patient_id, "next_due": {"$lt": datetime.utcnow()}})]
    data = {
        "patient_id": patient_id,
        "active_alerts": active_alerts,
        "alert_count": len(active_alerts),
        "overdue_monitoring": overdue,
        "risk_summary": {
            "critical_alerts": sum(1 for a in active_alerts if a.get("alert_level") == "Critical"),
            "high_alerts": sum(1 for a in active_alerts if a.get("alert_level") == "High"),
            "overdue_tests": len(overdue),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
    log_audit("DATA_PROVIDED_TO_MODULE_24_25", {"patient_id": patient_id})
    return success(data)


@app.route("/api/audit-log", methods=["GET"])
def get_audit_log():
    limit = int(request.args.get("limit", 100))
    logs = [serialize(a) for a in audit_log.find({}).sort("timestamp", -1).limit(limit)]
    return success(logs)


@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    now = datetime.utcnow()
    return success(
        {
            "total_high_risk_drugs": high_risk_drugs.count_documents({}),
            "active_alerts": lab_alerts.count_documents({"status": "Active"}),
            "critical_alerts": lab_alerts.count_documents({"status": "Active", "alert_level": "Critical"}),
            "overdue_monitoring": monitoring_schedules.count_documents({"next_due": {"$lt": now}}),
            "due_today": monitoring_schedules.count_documents({"next_due": {"$gte": now, "$lt": now + timedelta(days=1)}}),
            "monitoring_requirements": monitoring_requirements.count_documents({}),
        }
    )


# ===== SPLIT PART 3 START: External notification helper + app bootstrap =====


def _notify_module_25(alert_doc):
    try:
        requests.post(
            f"{MODULE_25_URL}/api/adverse-events",
            json={
                "source_module": "23",
                "patient_id": alert_doc.get("patient_id"),
                "drug_id": alert_doc.get("drug_id"),
                "event_type": "CRITICAL_LAB_ALERT",
                "description": f"Critical {alert_doc.get('test_name')} value: {alert_doc.get('result_value')}",
            },
            timeout=3,
        )
    except Exception:
        pass


if __name__ == "__main__":
    create_indexes()
    seed_data()
    port = int(os.environ.get("PORT", 5023))
    print(f"Module 23 API running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
