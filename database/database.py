"""
Module 23: High-Risk Drug Monitoring System
MongoDB Database Layer
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "module23_highrisk_drugs"

USE_MOCK_DB = os.environ.get("USE_MOCK_DB", "0") == "1"

if USE_MOCK_DB:
    import mongomock

    client = mongomock.MongoClient()
    db = client[DB_NAME]
else:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        db = client[DB_NAME]
    except Exception:
        # Fallback for local development when MongoDB service is unavailable.
        import mongomock

        client = mongomock.MongoClient()
        db = client[DB_NAME]

# Collections
high_risk_drugs = db["high_risk_drugs"]
monitoring_requirements = db["monitoring_requirements"]
lab_alerts = db["lab_alerts"]
dose_adjustments = db["dose_adjustments"]
monitoring_schedules = db["monitoring_schedules"]
audit_log = db["audit_log"]


# ===== SPLIT PART 1 START: DB config, collections, and indexes =====


def create_indexes():
    high_risk_drugs.create_index([("drug_id", ASCENDING)], unique=True)
    high_risk_drugs.create_index([("category", ASCENDING)])
    monitoring_requirements.create_index([("drug_id", ASCENDING)])
    lab_alerts.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)])
    lab_alerts.create_index([("status", ASCENDING)])
    dose_adjustments.create_index([("patient_id", ASCENDING), ("drug_id", ASCENDING)])
    monitoring_schedules.create_index([("patient_id", ASCENDING), ("next_due", ASCENDING)])


# ===== SPLIT PART 2 START: Seed data for Module 23 collections =====


def seed_data():
    if high_risk_drugs.count_documents({}) > 0:
        return

    drugs = [
        {
            "drug_id": "D001",
            "name": "Warfarin",
            "generic_name": "Warfarin Sodium",
            "category": "Anticoagulant",
            "risk_level": "High",
            "mechanism": "Vitamin K antagonist",
            "typical_dose_range": "2-10 mg/day",
            "black_box_warning": True,
            "monitoring_parameters": ["INR", "PT", "Bleeding signs"],
            "contraindications": ["Active bleeding", "Pregnancy"],
            "created_at": datetime.utcnow(),
        },
        {
            "drug_id": "D002",
            "name": "Methotrexate",
            "generic_name": "Methotrexate",
            "category": "Chemotherapy",
            "risk_level": "Critical",
            "mechanism": "Folate antagonist / DMARD",
            "typical_dose_range": "7.5-25 mg/week",
            "black_box_warning": True,
            "monitoring_parameters": ["CBC", "LFT", "Creatinine", "Chest X-ray"],
            "contraindications": ["Pregnancy", "Liver disease", "Immunodeficiency"],
            "created_at": datetime.utcnow(),
        },
        {
            "drug_id": "D003",
            "name": "Tacrolimus",
            "generic_name": "Tacrolimus",
            "category": "Immunosuppressant",
            "risk_level": "High",
            "mechanism": "Calcineurin inhibitor",
            "typical_dose_range": "0.05-0.3 mg/kg/day",
            "black_box_warning": True,
            "monitoring_parameters": ["Tacrolimus level", "Creatinine", "K+", "Glucose", "BP"],
            "contraindications": ["Hypersensitivity to tacrolimus"],
            "created_at": datetime.utcnow(),
        },
    ]

    requirements = [
        {
            "req_id": "MR001",
            "drug_id": "D001",
            "drug_name": "Warfarin",
            "monitoring_type": "Laboratory",
            "lab_tests": [
                {
                    "test": "INR",
                    "frequency": "Weekly until stable, then monthly",
                    "target_range": "2.0-3.0",
                    "critical_low": 1.5,
                    "critical_high": 4.0,
                    "unit": "ratio",
                },
                {"test": "PT", "frequency": "With INR", "target_range": "Normal", "unit": "seconds"},
            ],
            "clinical_monitoring": ["Signs of bleeding", "Bruising", "Blood in urine/stool"],
            "baseline_tests": ["INR", "CBC", "LFT", "Renal function"],
            "escalation_threshold": "INR > 4.0 or active bleeding",
            "created_at": datetime.utcnow(),
        },
        {
            "req_id": "MR002",
            "drug_id": "D002",
            "drug_name": "Methotrexate",
            "monitoring_type": "Laboratory",
            "lab_tests": [
                {
                    "test": "CBC",
                    "frequency": "Every 2-4 weeks",
                    "target_range": "Normal",
                    "critical_low": None,
                    "critical_high": None,
                    "unit": "cells/uL",
                },
                {"test": "LFT", "frequency": "Every 4-8 weeks", "target_range": "< 3x ULN", "unit": "U/L"},
                {"test": "Creatinine", "frequency": "Every 4-8 weeks", "target_range": "Normal", "unit": "mg/dL"},
            ],
            "clinical_monitoring": ["Mucositis", "Nausea/vomiting", "Pulmonary symptoms"],
            "baseline_tests": ["CBC", "LFT", "RFT", "CXR", "Albumin"],
            "escalation_threshold": "ANC < 1000 or AST/ALT > 3x ULN",
            "created_at": datetime.utcnow(),
        },
    ]

    adjustments = [
        {
            "adj_id": "DA001",
            "drug_id": "D001",
            "drug_name": "Warfarin",
            "parameter": "INR",
            "rules": [
                {"condition": "INR < 1.5", "action": "Increase dose by 10-20%", "urgency": "Routine"},
                {"condition": "INR 1.5-1.9", "action": "Increase dose by 5-10%", "urgency": "Routine"},
                {"condition": "INR 2.0-3.0", "action": "No change (therapeutic)", "urgency": "None"},
                {"condition": "INR 3.1-4.0", "action": "Decrease dose by 5-10%", "urgency": "Routine"},
                {
                    "condition": "INR > 4.0",
                    "action": "Hold dose, recheck in 1-2 days, consider Vitamin K",
                    "urgency": "Urgent",
                },
            ],
            "renal_adjustment": "Use with caution in CKD; increased bleeding risk",
            "hepatic_adjustment": "Avoid in severe hepatic impairment",
            "created_at": datetime.utcnow(),
        }
    ]

    lab_alerts_data = [
        {
            "alert_id": "AL001",
            "patient_id": "P1021",
            "drug_id": "D001",
            "drug_name": "Warfarin",
            "test_name": "INR",
            "result_value": 5.2,
            "unit": "ratio",
            "normal_range": "2.0-3.0",
            "alert_level": "Critical",
            "status": "Active",
            "action_required": "Hold warfarin, give Vitamin K 2.5mg PO",
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "resolved_at": None,
            "resolved_by": None,
        }
    ]

    schedules = [
        {
            "schedule_id": "SC001",
            "patient_id": "P1021",
            "drug_id": "D001",
            "drug_name": "Warfarin",
            "test_name": "INR",
            "last_done": datetime.utcnow() - timedelta(days=3),
            "next_due": datetime.utcnow() + timedelta(days=4),
            "frequency_days": 7,
            "status": "Upcoming",
            "priority": "Routine",
        }
    ]

    high_risk_drugs.insert_many(drugs)
    monitoring_requirements.insert_many(requirements)
    dose_adjustments.insert_many(adjustments)
    lab_alerts.insert_many(lab_alerts_data)
    monitoring_schedules.insert_many(schedules)


# ===== SPLIT PART 3 START: Trigger and stored-procedure style helpers =====


def trigger_on_lab_alert_insert(alert_doc):
    if alert_doc.get("alert_level") == "Critical":
        audit_log.insert_one(
            {
                "event": "CRITICAL_ALERT_ESCALATION",
                "alert_id": alert_doc.get("alert_id"),
                "patient_id": alert_doc.get("patient_id"),
                "drug": alert_doc.get("drug_name"),
                "test": alert_doc.get("test_name"),
                "value": alert_doc.get("result_value"),
                "message": f"AUTO-ESCALATED: Critical lab value detected for {alert_doc.get('drug_name')}",
                "timestamp": datetime.utcnow(),
            }
        )
    return True


def trigger_check_dose_adjustment(patient_id, drug_id, lab_test, result_value):
    adj = dose_adjustments.find_one({"drug_id": drug_id})
    suggestions = []
    if adj:
        for rule in adj.get("rules", []):
            suggestions.append(
                {
                    "condition": rule["condition"],
                    "action": rule["action"],
                    "urgency": rule["urgency"],
                }
            )
    return suggestions


def procedure_evaluate_alert_conditions(patient_id, drug_id, lab_results: dict):
    new_alerts = []
    req = monitoring_requirements.find_one({"drug_id": drug_id})
    if not req:
        return {"status": "No monitoring requirement found", "alerts": []}

    for lab in req.get("lab_tests", []):
        test_name = lab["test"]
        if test_name in lab_results:
            val = lab_results[test_name]
            critical_high = lab.get("critical_high")
            critical_low = lab.get("critical_low")

            level = "Normal"
            if critical_high and val > critical_high:
                level = "Critical"
            elif critical_low and val < critical_low:
                level = "Critical"
            elif critical_high and val > critical_high * 0.85:
                level = "High"

            if level != "Normal":
                alert = {
                    "alert_id": f"AL{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "patient_id": patient_id,
                    "drug_id": drug_id,
                    "test_name": test_name,
                    "result_value": val,
                    "unit": lab.get("unit", ""),
                    "normal_range": lab.get("target_range", ""),
                    "alert_level": level,
                    "status": "Active",
                    "action_required": "Review required",
                    "created_at": datetime.utcnow(),
                    "resolved_at": None,
                    "resolved_by": None,
                }
                lab_alerts.insert_one(alert)
                trigger_on_lab_alert_insert(alert)
                new_alerts.append(alert)

    return {"status": "Evaluated", "alerts_generated": len(new_alerts), "alerts": new_alerts}


def procedure_generate_monitoring_schedule(patient_id, drug_id):
    req = monitoring_requirements.find_one({"drug_id": drug_id})
    if not req:
        return {"status": "No requirement found"}

    created = []
    for lab in req.get("lab_tests", []):
        schedule = {
            "schedule_id": f"SC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{lab['test']}",
            "patient_id": patient_id,
            "drug_id": drug_id,
            "drug_name": req.get("drug_name"),
            "test_name": lab["test"],
            "last_done": None,
            "next_due": datetime.utcnow() + timedelta(days=1),
            "frequency_days": 7,
            "status": "Scheduled",
            "priority": "Routine",
        }
        monitoring_schedules.insert_one(schedule)
        created.append(schedule["test_name"])

    return {"status": "Schedule created", "tests_scheduled": created}
