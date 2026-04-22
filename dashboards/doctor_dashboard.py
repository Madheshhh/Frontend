# dashboards/doctor_dashboard.py
import os
import streamlit as st
import requests
import pandas as pd
from components.sidebar import sidebar
from components.charts import patient_line_chart, appointment_donut_chart
import matplotlib.pyplot as plt


def _resolve_api_base_url():
    env_value = os.environ.get("API_BASE_URL")
    if env_value:
        return env_value
    try:
        return st.secrets.get("API_BASE_URL", "http://127.0.0.1:5023")
    except Exception:
        return "http://127.0.0.1:5023"


API_BASE = _resolve_api_base_url()

def api_get(endpoint):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if r.status_code == 200:
            body = r.json()
            if isinstance(body, dict):
                return body.get("data", {})
        return None
    except Exception:
        return None


def api_post(endpoint, payload):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=5)
        body = r.json()
        if isinstance(body, dict):
            return body
        return {"status": "error", "message": "Invalid response format"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# All categories and their modules
CATEGORIES = {
    "A - Patient Clinical Data": {
        "title": "Patient Clinical Data Management",
        "description": "Patient records, medical history, diagnoses, and treatment plans",
        "icon": "🏥",
        "stats": {"modules": "6", "records": "45,230", "alerts": "12"},
        "modules": [
            ("A1", "Patient Demographics & Visit History", "Patient demographics and admission data", 5, 12500),
            ("A2", "Chronic Disease Patient Record", "Past medical records and conditions", 4, 8900),
            ("A3", "Pediatric Patient Clinical Data", "ICD codes and diagnosis tracking", 3, 15600),
            ("A4", "Geriatric Patient Health Record", "Care plans and treatment", 6, 7800),
            ("A5", "Patient Allergy & Immunization", "Patient vitals and monitoring", 4, 9200),
            ("A6", "Clinical Alert System", "Doctor notes and observations", 5, 11400)
        ]
    },
    "B - Laboratory Management": {
        "title": "Laboratory Management",
        "description": "Lab tests, results, equipment, and sample tracking",
        "icon": "🧪",
        "stats": {"modules": "5", "records": "12,840", "alerts": "5"},
        "modules": [
            ("B1", "Laboratory Test Management", "Test ordering system", 9, 22300),
            ("B2", "Automated Lab Result Interpretation", "AI result analysis", 6, 15800),
            ("B3", "Reference Range Validation", "Normal range database", 4, 12400),
            ("B4", "Follow-Up Test Recommendation", "Test suggestion system", 5, 9100),
            ("B5", "Pathology Report Management", "Pathology database", 7, 11200)
        ]
    },
    "C - Pharmacy & Medications": {
        "title": "Pharmacy & Medications",
        "description": "Drug inventory, prescriptions, and dispensing records",
        "icon": "💊",
        "stats": {"modules": "6", "records": "28,450", "alerts": "3"},
        "modules": [
            ("C1", "Drug-Drug Interaction Alert", "Interaction database", 7, 18500),
            ("C2", "Prescription Validation System", "Consistency checks", 5, 12300),
            ("C3", "Allergy-Aware Medication Alert", "Allergy cross-reference", 4, 9800),
            ("C4", "Polypharmacy Risk Detection", "Multiple drug analysis", 6, 11200),
            ("C5", "High-Risk Drug Monitoring", "Critical medication tracking", 5, 8700),
            ("C6", "Automated Prescription Audit", "Prescription review system", 4, 7300)
        ]
    },
    "D - Hospital Operations": {
        "title": "Hospital Operations",
        "description": "Bed management, admissions, and facility operations",
        "icon": "🏥",
        "stats": {"modules": "6", "records": "34,120", "alerts": "8"},
        "modules": [
            ("D1", "Bed Management System", "Bed allocation and tracking", 5, 8900),
            ("D2", "Patient Admission & Discharge", "Admission workflows", 7, 12400),
            ("D3", "Operating Room Scheduling", "OR booking system", 6, 5600),
            ("D4", "Emergency Department Triage", "ED patient management", 8, 4200),
            ("D5", "Ward Management System", "Ward operations", 5, 2100),
            ("D6", "Hospital Facility Management", "Facility tracking", 4, 920)
        ]
    },
    "E - Billing & Insurance": {
        "title": "Billing & Insurance",
        "description": "Patient billing, insurance claims, and payment processing",
        "icon": "💳",
        "stats": {"modules": "5", "records": "18,760", "alerts": "6"},
        "modules": [
            ("E1", "Patient Billing System", "Invoice generation", 8, 15600),
            ("E2", "Insurance Claims Management", "Claims processing", 6, 12300),
            ("E3", "Payment Processing", "Payment tracking", 5, 9800),
            ("E4", "Revenue Cycle Management", "Financial analytics", 7, 8900),
            ("E5", "Pricing & Tariff Management", "Price management", 4, 4160)
        ]
    },
    "F - HR & Staff Management": {
        "title": "HR & Staff Management",
        "description": "Employee records, scheduling, and performance tracking",
        "icon": "👥",
        "stats": {"modules": "5", "records": "5,240", "alerts": "2"},
        "modules": [
            ("F1", "Doctor & Staff Registry", "Employee database", 6, 2400),
            ("F2", "Shift Scheduling System", "Staff scheduling", 5, 8900),
            ("F3", "Attendance & Leave Management", "Time tracking", 4, 12100),
            ("F4", "Performance Evaluation", "Staff reviews", 3, 1800),
            ("F5", "Training & Certification", "Credential tracking", 4, 940)
        ]
    },
    "G - Compliance & Security": {
        "title": "Compliance & Security",
        "description": "Regulatory compliance, auditing, and data security",
        "icon": "🔒",
        "stats": {"modules": "4", "records": "156,300", "alerts": "1"},
        "modules": [
            ("G1", "Secure Electronic Health Record", "Main EHR database", 12, 45000),
            ("G2", "Role-Based Access Control", "Permission management", 8, 28900),
            ("G3", "Clinical Audit Trail & Logging", "Activity logging system", 6, 32100),
            ("G4", "Patient Consent & Privacy", "Privacy management", 5, 18700)
        ]
    },
    "H - Supply Chain": {
        "title": "Supply Chain & Inventory",
        "description": "Medical supplies, equipment, and vendor management",
        "icon": "📦",
        "stats": {"modules": "5", "records": "42,180", "alerts": "9"},
        "modules": [
            ("H1", "Medical Equipment Tracking", "Equipment inventory", 7, 12400),
            ("H2", "Supply Inventory Management", "Stock management", 8, 18900),
            ("H3", "Vendor & Procurement", "Supplier management", 5, 3200),
            ("H4", "Equipment Maintenance", "Maintenance schedules", 4, 5400),
            ("H5", "Pharmacy Inventory", "Drug stock tracking", 6, 2280)
        ]
    },
    "I - Analytics & Reporting": {
        "title": "Analytics & Reporting",
        "description": "Data analytics, KPIs, and business intelligence",
        "icon": "📊",
        "stats": {"modules": "4", "records": "125,600", "alerts": "4"},
        "modules": [
            ("I1", "Hospital Performance Dashboard", "KPI tracking and metrics", 15, 78900),
            ("I2", "Clinical Outcomes Analysis", "Treatment effectiveness", 12, 46700),
            ("I3", "Financial Analytics", "Revenue and cost analysis", 10, 32100),
            ("I4", "Predictive Analytics", "AI-powered predictions", 18, 18900)
        ]
    }
}

def doctor_dashboard():
    st.session_state.setdefault("view", "main")
    st.session_state.setdefault("selected_category", None)
    st.session_state.setdefault("selected_module", None)

    # Sidebar - but don't automatically trigger category view
    selected = sidebar([
        "Dashboard",
        "A - Patient Clinical Data",
        "B - Laboratory Management",
        "C - Pharmacy & Medications",
        "D - Hospital Operations",
        "E - Billing & Insurance",
        "F - HR & Staff Management",
        "G - Compliance & Security",
        "H - Supply Chain",
        "I - Analytics & Reporting"
    ])

    # Only change view if a category is explicitly selected AND it's not "Dashboard"
    if selected != "Dashboard" and selected in CATEGORIES and st.session_state.view == "main":
        # Don't auto-navigate, let button clicks handle it
        pass

    # ROUTER
    if st.session_state.view == "category":
        show_category_view()
    elif st.session_state.view == "module":
        show_module_detail()
    else:
        show_main_dashboard()

def show_main_dashboard():
    st.markdown("### Welcome back! Here's your hospital overview.")
    
    st.divider()

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Patients", "12,450", "+12% vs last month")
    c2.metric("⚠️ Active Alerts", "320", "-5% vs last month")
    c3.metric("📋 Lab Reports", "185", "+8% vs last month")
    c4.metric("💊 Prescriptions", "750", "+15% vs last month")

    st.divider()

    # Main content area
    main_col, side_col = st.columns([2, 1])
    
    with main_col:
        st.subheader("Your Patients Today")
        st.markdown("[All patients →](#)")
        
        # Patient 1 - Highlighted
        with st.container():
            p_col1, p_col2, p_col3 = st.columns([1, 5, 1])
            with p_col1:
                st.markdown("🕐 **10:30am**")
            with p_col2:
                st.markdown("**SH | Sarah Hostern**")
                st.caption("Diagnosis: Bronchi")
            with p_col3:
                st.button("📍", key="loc1")
                st.button("⋮", key="menu1")
        
        st.success("Currently Active")
        st.markdown("---")
        
        # Patient 2
        with st.container():
            p_col1, p_col2, p_col3 = st.columns([1, 5, 1])
            with p_col1:
                st.markdown("🕐 **11:00am**")
            with p_col2:
                st.markdown("**DS | Dakota Smith**")
                st.caption("Diagnosis: Stroke")
            with p_col3:
                st.button("📹", key="video1")
                st.button("⋮", key="menu2")
        
        st.markdown("---")
        
        # Patient 3
        with st.container():
            p_col1, p_col2, p_col3 = st.columns([1, 5, 1])
            with p_col1:
                st.markdown("🕐 **11:30am**")
            with p_col2:
                st.markdown("**JL | John Lane**")
                st.caption("Diagnosis: Liver")
            with p_col3:
                st.button("📞", key="call1")
                st.button("⋮", key="menu3")
        
        st.markdown("---")
        
        # Patient 4
        with st.container():
            p_col1, p_col2, p_col3 = st.columns([1, 5, 1])
            with p_col1:
                st.markdown("🕐 **12:00pm**")
            with p_col2:
                st.markdown("**MG | Maria Garcia**")
                st.caption("Diagnosis: Cardiac")
            with p_col3:
                st.button("📍", key="loc2")
                st.button("⋮", key="menu4")
        
        st.divider()
        
        # Charts section
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("### Patient Analytics")
            patient_line_chart()
        
        with chart_col2:
            st.markdown("### Appointments Overview")
            appointment_donut_chart()
    
    with side_col:
        st.subheader("Recent Activity")
        st.markdown("[View All](#)")
        
        # Activity 1
        st.markdown("👤 **New patient registration: John Smith**")
        st.caption("🕐 2 min ago • Reception")
        st.markdown("---")
        
        # Activity 2
        st.markdown("⚠️ **Critical lab result for Patient #4521**")
        st.caption("🕐 5 min ago • Lab")
        st.markdown("---")
        
        # Activity 3
        st.markdown("✅ **Surgery completed successfully - Room 5**")
        st.caption("🕐 12 min ago • Dr. Wilson")
        st.markdown("---")
        
        # Activity 4
        st.markdown("📊 **Monthly analytics report generated**")
        st.caption("🕐 25 min ago • System")
        st.markdown("---")
        
        # Activity 5
        st.markdown("👤 **Patient discharge: Emily Brown**")
        st.caption("🕐 1 hour ago • Ward B")
    
    st.divider()
    
    # System Categories Section
    st.markdown("## System Categories (A-I)")
    
    cols = st.columns(3)
    for idx, (key, cat) in enumerate(CATEGORIES.items()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"### {cat['icon']} {key}")
                st.caption(cat['description'])
                
                stat_cols = st.columns([1, 2, 1])
                with stat_cols[0]:
                    st.metric("Modules", cat['stats']['modules'])
                with stat_cols[1]:
                    st.metric("Records", cat['stats']['records'])
                with stat_cols[2]:
                    st.markdown(f"⚠️ {cat['stats']['alerts']}")
                    st.caption("Alerts")
                
                if st.button("View Details →", key=f"cat_{idx}", use_container_width=True):
                    st.session_state.selected_category = key
                    st.session_state.view = "category"
                    st.rerun()
                st.markdown("---")

def show_category_view():
    cat_key = st.session_state.selected_category
    category = CATEGORIES[cat_key]
    
    # Header with icon and title
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"# {category['icon']} {category['title']}")
        st.markdown(f"*{category['description']}*")
    with col2:
        st.button("📄 Export Data", use_container_width=True)
    
    st.divider()
    
    # Stats cards
    stats = category['stats']
    c1, c2, c3 = st.columns(3)
    c1.metric("⚡ Modules", stats['modules'])
    c2.metric("📊 Total Records", stats['records'])
    c3.metric("⚠️ Active Alerts", stats['alerts'])
    
    st.divider()
    st.markdown("## Modules")
    
    # Module cards in grid
    cols = st.columns(3)
    for idx, module in enumerate(category['modules']):
        code, name, desc, tables, records = module
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"### {code}")
                st.markdown(f"**{name}**")
                st.caption(desc)
                
                mcol1, mcol2 = st.columns(2)
                mcol1.metric("Tables", tables)
                mcol2.metric("Records", f"{records:,}")
                
                if st.button("→", key=f"mod_{code}", use_container_width=True):
                    st.session_state.selected_module = module
                    st.session_state.view = "module"
                    st.rerun()
                st.markdown("---")
    
    st.divider()
    if st.button("⬅ Back to Dashboard"):
        st.session_state.view = "main"
        st.rerun()



# High-Risk Drug Management (Module 23) - integrated from Files/Files/frontend.py
def show_high_risk_drug_management_module():
    page = st.selectbox(
        "Module 23 Navigation",
        [
            "🏠 Master Dashboard",
            "💊 Drug Registry",
            "🔬 Monitoring Requirements",
            "🚨 Lab Alerts",
            "📋 Dose Adjustments",
            "📅 Monitoring Schedules",
            "⚙️ SQL Queries & Triggers",
            "🔗 Module Integration",
            "📜 Audit Log",
        ],
        key="m23_nav",
    )

    health = api_get("/health")
    if health:
        st.success("Module 23 API connected")
    else:
        st.warning("Module 23 API not reachable. Showing fallback demo data.")

    st.divider()

    if "Dashboard" in page:
        st.markdown("# ⚠️ High-Risk Drug Monitoring System")
        st.markdown("**Module 23** | Category: Pharmacy & Clinical Safety")
        st.markdown("---")

        stats = api_get("/api/dashboard/stats") or {
            "total_high_risk_drugs": 6,
            "active_alerts": 3,
            "critical_alerts": 2,
            "overdue_monitoring": 1,
            "monitoring_requirements": 3,
        }

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("High-Risk Drugs", stats.get("total_high_risk_drugs", 0))
        c2.metric("Active Alerts", stats.get("active_alerts", 0))
        c3.metric("Critical Alerts", stats.get("critical_alerts", 0))
        c4.metric("Overdue Tests", stats.get("overdue_monitoring", 0))
        c5.metric("Protocols", stats.get("monitoring_requirements", 0))

        st.markdown("### 🚨 Active Lab Alerts")
        alerts = api_get("/api/lab-alerts?status=Active") or [
            {
                "alert_id": "AL001",
                "patient_id": "P1021",
                "drug_name": "Warfarin",
                "test_name": "INR",
                "result_value": 5.2,
                "alert_level": "Critical",
                "action_required": "Hold warfarin, give Vitamin K",
            },
            {
                "alert_id": "AL002",
                "patient_id": "P1034",
                "drug_name": "Methotrexate",
                "test_name": "ANC",
                "result_value": 750,
                "alert_level": "High",
                "action_required": "Hold MTX, repeat CBC",
            },
        ]
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)

    elif "Drug Registry" in page:
        st.markdown("# 💊 High-Risk Drug Registry")
        st.markdown("---")

        tab1, tab2 = st.tabs(["📋 View Drugs", "➕ Add Drug"])

        with tab1:
            cat_filter = st.selectbox("Filter by Category", ["All", "Anticoagulant", "Chemotherapy", "Immunosuppressant"], key="m23_drug_filter")
            endpoint = f"/api/drugs?category={cat_filter}" if cat_filter != "All" else "/api/drugs"
            drugs = api_get(endpoint) or [
                {"drug_id": "D001", "name": "Warfarin", "category": "Anticoagulant", "risk_level": "High"},
                {"drug_id": "D002", "name": "Methotrexate", "category": "Chemotherapy", "risk_level": "Critical"},
                {"drug_id": "D003", "name": "Tacrolimus", "category": "Immunosuppressant", "risk_level": "High"},
            ]
            st.dataframe(pd.DataFrame(drugs), use_container_width=True, hide_index=True)

        with tab2:
            with st.form("m23_add_drug_form"):
                c1, c2 = st.columns(2)
                drug_id = c1.text_input("Drug ID *", placeholder="D007")
                name = c2.text_input("Drug Name *", placeholder="Rivaroxaban")
                generic_name = c1.text_input("Generic Name", placeholder="Rivaroxaban")
                category = c2.selectbox("Category", ["Anticoagulant", "Chemotherapy", "Immunosuppressant", "Other"], key="m23_add_cat")
                risk_level = c1.selectbox("Risk Level", ["High", "Critical", "Moderate"], key="m23_add_risk")
                mechanism = st.text_area("Mechanism of Action", height=80)
                dose_range = c2.text_input("Typical Dose Range", placeholder="10-20 mg/day")
                black_box = st.checkbox("Black Box Warning")
                submitted = st.form_submit_button("Register Drug")

                if submitted:
                    if drug_id and name:
                        result = api_post(
                            "/api/drugs",
                            {
                                "drug_id": drug_id,
                                "name": name,
                                "generic_name": generic_name,
                                "category": category,
                                "risk_level": risk_level,
                                "mechanism": mechanism,
                                "typical_dose_range": dose_range,
                                "black_box_warning": black_box,
                            },
                        )
                        if result.get("status") == "success":
                            st.success(f"Drug {name} registered successfully")
                        else:
                            st.error(result.get("message", "Failed to register drug"))
                    else:
                        st.warning("Drug ID and Name are required")

    elif "Monitoring Requirements" in page:
        st.markdown("# 🔬 Monitoring Requirements")
        st.markdown("---")

        drug_filter = st.text_input("Filter by Drug ID", "", key="m23_req_drug_filter")
        endpoint = f"/api/monitoring-requirements?drug_id={drug_filter}" if drug_filter else "/api/monitoring-requirements"
        reqs = api_get(endpoint) or [
            {"req_id": "MR001", "drug_id": "D001", "drug_name": "Warfarin", "monitoring_type": "Laboratory", "escalation_threshold": "INR > 4.0"},
            {"req_id": "MR003", "drug_id": "D003", "drug_name": "Tacrolimus", "monitoring_type": "TDM", "escalation_threshold": "Trough > 25"},
        ]
        st.dataframe(pd.DataFrame(reqs), use_container_width=True, hide_index=True)

    elif "Lab Alerts" in page:
        st.markdown("# 🚨 Lab Alerts Management")
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 Alert Dashboard", "🔍 Search Alerts", "➕ Create Alert"])

        with tab1:
            stats = api_get("/api/lab-alerts/stats") or {"total": 5, "by_level": {"Critical": 2}, "by_status": {"Active": 3, "Resolved": 1}}
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Alerts", stats.get("total", 0))
            c2.metric("Critical", stats.get("by_level", {}).get("Critical", 0))
            c3.metric("Active", stats.get("by_status", {}).get("Active", 0))
            c4.metric("Resolved", stats.get("by_status", {}).get("Resolved", 0))

            alerts = api_get("/api/lab-alerts") or []
            if alerts:
                st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)

        with tab2:
            pid = st.text_input("Search by Patient ID", placeholder="P1021", key="m23_alert_pid")
            status_sel = st.selectbox("Status Filter", ["All", "Active", "Pending", "Resolved"], key="m23_alert_status")
            if st.button("Search", key="m23_alert_search"):
                params = []
                if pid:
                    params.append(f"patient_id={pid}")
                if status_sel != "All":
                    params.append(f"status={status_sel}")
                endpoint = "/api/lab-alerts?" + "&".join(params) if params else "/api/lab-alerts"
                results = api_get(endpoint) or []
                if results:
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
                else:
                    st.info("No results")

        with tab3:
            with st.form("m23_create_alert_form"):
                c1, c2 = st.columns(2)
                alert_id = c1.text_input("Alert ID", placeholder="AL005")
                patient_id = c2.text_input("Patient ID", placeholder="P1021")
                drug_id = c1.text_input("Drug ID", placeholder="D001")
                drug_name = c2.text_input("Drug Name", placeholder="Warfarin")
                test_name = c1.text_input("Test Name", placeholder="INR")
                result_value = c2.number_input("Result Value", value=0.0, step=0.1)
                unit = c1.text_input("Unit", placeholder="ratio")
                normal_range = c2.text_input("Normal Range", placeholder="2.0-3.0")
                alert_level = st.selectbox("Alert Level", ["Normal", "High", "Critical"], key="m23_alert_level")
                action = st.text_area("Action Required", height=80)
                submitted = st.form_submit_button("Create Alert")

                if submitted:
                    result = api_post(
                        "/api/lab-alerts",
                        {
                            "alert_id": alert_id,
                            "patient_id": patient_id,
                            "drug_id": drug_id,
                            "drug_name": drug_name,
                            "test_name": test_name,
                            "result_value": result_value,
                            "unit": unit,
                            "normal_range": normal_range,
                            "alert_level": alert_level,
                            "status": "Active",
                            "action_required": action,
                        },
                    )
                    if result.get("status") == "success":
                        st.success("Alert created")
                    else:
                        st.error(result.get("message", "Failed to create alert"))

    elif "Dose Adjustments" in page:
        st.markdown("# 📋 Dose Adjustment Rules")
        st.markdown("---")

        tab1, tab2 = st.tabs(["📖 View Rules", "🧮 Evaluate Dose"])

        with tab1:
            adjs = api_get("/api/dose-adjustments") or []
            if adjs:
                st.dataframe(pd.DataFrame(adjs), use_container_width=True, hide_index=True)
            else:
                st.info("No rules found")

        with tab2:
            with st.form("m23_dose_eval_form"):
                c1, c2 = st.columns(2)
                pid = c1.text_input("Patient ID", value="P1021")
                drug_id_eval = c2.selectbox("Drug", ["D001", "D002", "D003"], key="m23_dose_drug")
                lab_test = c1.text_input("Lab Test", placeholder="INR")
                result_val = c2.number_input("Lab Result Value", value=5.2, step=0.1)
                if st.form_submit_button("Evaluate"):
                    result = api_post(
                        "/api/dose-adjustments/evaluate",
                        {
                            "patient_id": pid,
                            "drug_id": drug_id_eval,
                            "lab_test": lab_test,
                            "result_value": result_val,
                        },
                    )
                    if result.get("status") == "success":
                        raw_data = result.get("data")
                        suggestions = []
                        if isinstance(raw_data, dict):
                            suggestions = raw_data.get("suggestions", [])
                        if suggestions:
                            st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)
                        else:
                            st.info("No suggestion generated")
    elif "Monitoring Schedules" in page:
        st.markdown("# 📅 Monitoring Schedules")
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📋 View Schedules", "⏰ Overdue", "🗓️ Generate Schedule"])

        with tab1:
            pid_filter = st.text_input("Filter by Patient ID", "", key="m23_sched_pid")
            status_filter = st.selectbox("Status", ["All", "Upcoming", "Due Soon", "Overdue", "Scheduled", "Completed"], key="m23_sched_status")
            params = []
            if pid_filter:
                params.append(f"patient_id={pid_filter}")
            if status_filter != "All":
                params.append(f"status={status_filter}")
            endpoint = "/api/monitoring-schedules?" + "&".join(params) if params else "/api/monitoring-schedules"
            schedules = api_get(endpoint) or []
            if schedules:
                st.dataframe(pd.DataFrame(schedules), use_container_width=True, hide_index=True)
            else:
                st.info("No schedules found")

        with tab2:
            overdue = api_get("/api/procedures/overdue-schedules") or {"overdue_count": 0, "schedules": []}
            st.metric("Total Overdue", overdue.get("overdue_count", 0))
            if overdue.get("schedules"):
                st.dataframe(pd.DataFrame(overdue.get("schedules", [])), use_container_width=True, hide_index=True)

        with tab3:
            with st.form("m23_gen_schedule_form"):
                c1, c2 = st.columns(2)
                pid_gen = c1.text_input("Patient ID", value="P1099")
                drug_id_gen = c2.selectbox("Drug", ["D001", "D002", "D003"], key="m23_gen_drug")
                mode = st.radio("Schedule Mode", ["Standard", "Temporal (Intensive at start)"], horizontal=True)
                if st.form_submit_button("Generate Schedule"):
                    endpoint = "/api/procedures/temporal-schedule" if mode == "Temporal (Intensive at start)" else "/api/monitoring-schedules/generate"
                    result = api_post(endpoint, {"patient_id": pid_gen, "drug_id": drug_id_gen})
                    if result.get("status") == "success":
                        st.success("Schedule generated")
                        st.json(result.get("data", {}))

    elif "SQL" in page:
        st.markdown("# ⚙️ SQL Queries, Triggers & Stored Procedures")
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 Queries", "🔫 Triggers", "📦 Stored Procedures"])

        with tab1:
            st.code(
                """
SELECT * FROM lab_alerts
WHERE status = 'Active'
  AND alert_level = 'Critical'
ORDER BY created_at DESC;
""",
                language="sql",
            )
        with tab2:
            st.code(
                """
CREATE TRIGGER after_lab_alert_insert
AFTER INSERT ON lab_alerts
FOR EACH ROW
BEGIN
  IF NEW.alert_level = 'Critical' THEN
    INSERT INTO audit_log (event, patient_id, drug, message, timestamp)
    VALUES ('CRITICAL_ALERT_ESCALATION', NEW.patient_id, NEW.drug_name, CONCAT('Auto-escalated: ', NEW.test_name), NOW());
  END IF;
END;
""",
                language="sql",
            )
        with tab3:
            st.code(
                """
CREATE PROCEDURE evaluate_alert_conditions(
    IN p_patient_id VARCHAR(20),
    IN p_drug_id VARCHAR(10),
    IN p_lab_results JSON
)
BEGIN
  -- Compare lab values with thresholds and generate alerts
END;
""",
                language="sql",
            )

    elif "Integration" in page:
        st.markdown("# 🔗 Module Integration")
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["← From Module 21 & 22", "→ To Module 24 & 25", "🧪 Test Integration"])

        with tab1:
            st.markdown("### Inputs from Module 21 and Module 22")
            st.write("Module 21: patient demographics, renal/liver status, allergies, weight")
            st.write("Module 22: active prescriptions, drug + dose, start date, physician")

        with tab2:
            st.markdown("### Outputs to Module 24 and Module 25")
            st.write("Module 24: monitoring alerts, risk summary, dose recommendations")
            st.write("Module 25: critical alert escalation, adverse event details")

        with tab3:
            pid_test = st.text_input("Patient ID to test", value="P1021", key="m23_integration_pid")
            c1, c2, c3 = st.columns(3)
            if c1.button("Fetch from M21", key="m23_fetch_m21"):
                result = api_get(f"/api/integration/patient/{pid_test}")
                st.json(result if result else {"message": "M21 unavailable"})
            if c2.button("Fetch from M22", key="m23_fetch_m22"):
                result = api_get(f"/api/integration/prescriptions/{pid_test}")
                st.json(result if result else {"message": "M22 unavailable"})
            if c3.button("Provide to M24/M25", key="m23_provide_m24_m25"):
                result = api_get(f"/api/integration/provide/monitoring-data/{pid_test}")
                st.json(result if result else {"message": "No data"})

    elif "Audit" in page:
        st.markdown("# 📜 Audit Log")
        st.markdown("---")
        logs = api_get("/api/audit-log") or [
            {"action": "CREATE_ALERT", "detail": {"alert_id": "AL003"}, "timestamp": "2026-03-18T09:15:00"},
            {"action": "CRITICAL_ALERT_ESCALATION", "detail": {"patient_id": "P1056"}, "timestamp": "2026-03-18T09:16:00"},
        ]
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)

def show_module_detail():
    code, name, desc, tables, records = st.session_state.selected_module
    cat_key = st.session_state.selected_category
    
    # Breadcrumb
    st.markdown(f"Category {cat_key.split('-')[0].strip()} > {name}")
    st.markdown(f"# {name}")
    st.markdown(f"*{desc}*")

    # High-Risk Drug Management (Module 23)
    is_high_risk_module = (
        code in {"C5", "D5"}
        or "high-risk drug monitoring" in name.lower()
    )
    if is_high_risk_module:
        show_high_risk_drug_management_module()
        st.divider()
        if st.button("⬅ Back to Modules", key="back_from_m23"):
            st.session_state.view = "category"
            st.rerun()
        return

    
    
    # Tabs
    tab = st.radio("", ["🏠 Home", "🔗 ER Diagram", "📋 Tables", "🔍 SQL Query", "⚡ Triggers", "📊 Output"], horizontal=True)
    st.divider()
    
    if tab == "🏠 Home":
        st.info(f"**{name}** - {desc}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Input Entities")
            st.success("1️⃣ Patient Form")
            st.success("2️⃣ Insurance Details")
            st.success("3️⃣ Emergency Contact")
        
        with col2:
            st.markdown("### Output Entities")
            st.success("1️⃣ Patient Record")
            st.success("2️⃣ Admission Summary")
            st.success("3️⃣ Patient ID")
    
    elif tab == "🔗 ER Diagram":
        st.markdown("### Entity Relationship Diagram")
        st.image("https://via.placeholder.com/900x500?text=ER+Diagram+for+" + code)
    
    elif tab == "📋 Tables":
        st.markdown("### Database Tables")
        st.table({
            "Table Name": ["patients", "insurance", "emergency_contacts", "admissions", "visit_history"],
            "Records": [12500, 8900, 6400, 15200, 22100],
            "Status": ["✅ Active", "✅ Active", "✅ Active", "✅ Active", "✅ Active"]
        })
    
    elif tab == "🔍 SQL Query":
        st.markdown("### Sample SQL Queries")
        st.code(f"""
-- Query for {name}
SELECT p.patient_id, p.name, p.age, i.insurance_type
FROM patients p
LEFT JOIN insurance i ON p.id = i.patient_id
WHERE p.status = 'active'
ORDER BY p.admission_date DESC
LIMIT 100;
""", language="sql")
        
        if st.button("▶️ Execute Query"):
            st.success("Query executed successfully! 1,234 rows returned.")
    
    elif tab == "⚡ Triggers":
        st.markdown("### Database Triggers")
        st.code(f"""
-- Trigger for {name}
CREATE TRIGGER after_patient_insert
AFTER INSERT ON patients
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs (entity_type, entity_id, action, timestamp)
  VALUES ('patient', NEW.patient_id, 'INSERT', NOW());
  
  -- Send notification
  INSERT INTO notifications (user_id, message)
  VALUES (NEW.assigned_doctor, CONCAT('New patient registered: ', NEW.name));
END;
""", language="sql")
    
    elif tab == "📊 Output":
        st.markdown("### Module Output")
        st.success("✅ Patient Registered Successfully")
        st.info("📋 Patient ID: PT-2024-001234")
        st.info("📅 Registration Date: January 08, 2026")
        
        st.markdown("#### Generated Records")
        st.json({
            "patient_id": "PT-2024-001234",
            "name": "John Doe",
            "age": 45,
            "admission_date": "2026-01-08",
            "status": "active"
        })
    
    st.divider()
    if st.button("⬅ Back to Modules"):
        st.session_state.view = "category"
        st.rerun()
