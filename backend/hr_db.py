hr_database = {
    "EMP01": {"name": "Alice Johnson", "department": "Engineering", "salary": 120000, "status": "Active"},
    "EMP02": {"name": "Bob Smith", "department": "Marketing", "salary": 90000, "status": "Active"}
}

def execute_termination(emp_id: str) -> str:
    if emp_id in hr_database:
        hr_database[emp_id]["status"] = "Terminated"
        return f"CRITICAL: {hr_database[emp_id]['name']} has been TERMINATED."
    return "ERROR: Employee not found."