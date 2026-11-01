def debug_sql_functions():
    """Debug route to check SQL functions, triggers and stored procedures"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"error": "Authentication required and admin privileges required"}), 401
        
    try:
        # Try to execute functions and procedures
        result = {
            "functions": {},
            "triggers": {},
            "procedures": {}
        }
        
        # Test age calculation function
        patient = Patient.query.filter(Patient.date_of_birth.isnot(None)).first()
        if patient and patient.date_of_birth:
            try:
                age = db.session.execute(
                    text("SELECT dbo.CalculatePatientAge(:birth_date) AS age"), 
                    {"birth_date": patient.date_of_birth}
                ).fetchone()
                result["functions"]["CalculatePatientAge"] = {
                    "status": "success" if age else "error",
                    "result": age[0] if age else None,
                    "patient_id": patient.id,
                    "birth_date": patient.date_of_birth.strftime('%Y-%m-%d')
                }
            except Exception as e:
                result["functions"]["CalculatePatientAge"] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Check UpdateLastModified trigger
        try:
            triggers = db.session.execute(text(
                "SELECT name, object_id, parent_object_id FROM sys.triggers WHERE name = 'UpdateLastModified'"
            )).fetchone()
            result["triggers"]["UpdateLastModified"] = {
                "status": "exists" if triggers else "not found",
                "details": dict(zip(['name', 'object_id', 'parent_object_id'], triggers)) if triggers else None
            }
        except Exception as e:
            result["triggers"]["UpdateLastModified"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check AuditMedicalRecordsChanges trigger
        try:
            triggers = db.session.execute(text(
                "SELECT name, object_id, parent_object_id FROM sys.triggers WHERE name = 'AuditMedicalRecordsChanges'"
            )).fetchone()
            result["triggers"]["AuditMedicalRecordsChanges"] = {
                "status": "exists" if triggers else "not found",
                "details": dict(zip(['name', 'object_id', 'parent_object_id'], triggers)) if triggers else None
            }
        except Exception as e:
            result["triggers"]["AuditMedicalRecordsChanges"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check GetPatientAppointments procedure
        try:
            procedures = db.session.execute(text(
                "SELECT name, object_id FROM sys.procedures WHERE name = 'GetPatientAppointments'"
            )).fetchone()
            result["procedures"]["GetPatientAppointments"] = {
                "status": "exists" if procedures else "not found",
                "details": dict(zip(['name', 'object_id'], procedures)) if procedures else None
            }
        except Exception as e:
            result["procedures"]["GetPatientAppointments"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check ClassifyPatientRisk procedure
        try:
            procedures = db.session.execute(text(
                "SELECT name, object_id FROM sys.procedures WHERE name = 'ClassifyPatientRisk'"
            )).fetchone()
            result["procedures"]["ClassifyPatientRisk"] = {
                "status": "exists" if procedures else "not found",
                "details": dict(zip(['name', 'object_id'], procedures)) if procedures else None
            }
        except Exception as e:
            result["procedures"]["ClassifyPatientRisk"] = {
                "status": "error",
                "error": str(e)
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 