import json


class PlanResultsJsonFormatter:
    def format(self, plan, test_results, stats, total) -> str:
        data = {
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "started_at": plan.started_at.isoformat() if plan.started_at else None,
                "due_date": plan.due_date.isoformat() if plan.due_date else None,
            },
            "statistics": stats,
            "total": total,
            "results": [],
        }
        for test, result in test_results:
            entry = {
                "test_id": test.id,
                "case_id": test.case_id,
                "case_name": test.case.name,
                "status": test.last_status.name if test.last_status else "Untested",
            }
            if result:
                entry["comment"] = result.comment
                entry["execution_time"] = result.execution_time
                entry["executor"] = result.user.username if result.user else None
                entry["date"] = result.created_at.isoformat()
            data["results"].append(entry)
        return json.dumps(data, ensure_ascii=False, indent=2)
