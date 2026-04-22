APPOINTMENT_SCHEMA = {
    "doctor": "string (name)",
    "doctor_id": "ObjectId",
    "patient_id": "ObjectId",
    "status": "string (pending|confirmed|completed|cancelled)",
    "datetime": "datetime",
    "notes": "string",
    "created_at": "datetime"
}
