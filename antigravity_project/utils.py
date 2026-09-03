def calculate_metrics(data_points):
    if not data_points:
        return {"total": 0, "avg": 0}
    return {
        "count": len(data_points),
        "total": sum(data_points),
        "avg": sum(data_points) / len(data_points)
    }

def format_response(message, payload):
    return {"status": "success", "message": message, "data": payload}