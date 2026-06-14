#!/usr/bin/env python3
"""
Mix-Data BPM Command Line Tool (User Version)

Usage:
    python3 bpm.py todos --token <token> --openid <openid> [options]
    python3 bpm.py dones --token <token> --openid <openid> [options]
    python3 bpm.py approve --token <token> --openid <openid> --task-id <id> --action <approve|reject> [options]
    python3 bpm.py comment --token <token> --openid <openid> --task-id <id> --action-name <name> --msg <message>
"""

import argparse
import json
import sys
from urllib import request
from urllib.error import URLError, HTTPError
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ApiResponse:
    code: int
    message: str
    data: Any = None
    @property
    def is_success(self): return self.code == 0


class BPMClient:
        def __init__(self, base_url: str = "http://localhost:8001", token: str = "", openid: str = "", auto_bind: bool = False):
            self.base_url = base_url.rstrip("/")
            self.token = token
            self.openid = openid

            # Auto-bind token if requested
            if auto_bind and token and openid:
                self.bind_token()

        def _call(self, method: str, endpoint: str, **kwargs) -> ApiResponse:
            try:
                # Construct URL
                url = f"{self.base_url}{endpoint}"

                # Prepare request
                if method == "GET":
                    params = kwargs.get("params", {})
                    if params:
                        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                        url += f"?{query_string}"
                    req = request.Request(url)
                else:
                    # POST request
                    json_data = kwargs.get("json", {})
                    req_data = json.dumps(json_data).encode('utf-8')
                    req = request.Request(
                        url,
                        data=req_data,
                        headers={"Content-Type": "application/json"}
                    )

                # Send request
                with request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return ApiResponse(
                        code=data.get("code", -1),
                        message=data.get("message", "Unknown error"),
                        data=data.get("data")
                    )
            except Exception as e:
                return ApiResponse(code=-1, message=str(e))

        def bind_token(self) -> ApiResponse:
            """Bind OpenID to token (one-time activation)

            This activates the token by binding it to your OpenID.
            Only needs to be called once. Subsequent calls will return success
            if already bound.

            Returns:
                ApiResponse with bind result
            """
            json_data = {
                "token": self.token,
                "openid": self.openid
            }

            return self._call("POST", "/api/bpm/token/bind", json=json_data)

        def get_todos(self, **kwargs) -> ApiResponse:
            params = {"openid": self.openid, "token": self.token}
            params.update({k: v for k, v in kwargs.items() if v is not None and k not in ["base_url"]})
            return self._call("GET", "/api/bpm/v2/todos", params=params)

        def get_dones(self, **kwargs) -> ApiResponse:
            params = {"openid": self.openid, "token": self.token}
            params.update({k: v for k, v in kwargs.items() if v is not None and k not in ["base_url"]})
            return self._call("GET", "/api/bpm/v2/dones", params=params)

        def approve_task(self, task_inst_id: str, action: str, comment: Optional[str] = None) -> ApiResponse:
            if action not in ["approve", "reject"]:
                raise ValueError("action must be 'approve' or 'reject'")
            data = {"openid": self.openid, "token": self.token, "task_inst_id": task_inst_id, "action": action}
            if comment:
                data["comment"] = comment
            return self._call("POST", "/api/bpm/v2/approve", json=data)

        def add_comment(self, task_inst_id: str, action_name: str, msg: str) -> ApiResponse:
            data = {
                "openid": self.openid,
                "token": self.token,
                "task_inst_id": task_inst_id,
                "action_name": action_name,
                "msg": msg
            }
            return self._call("POST", "/api/bpm/v2/comment", json=data)


def cmd_todos(args):
    """Query pending tasks"""
    client = BPMClient(
        base_url=args.base_url,
        token=args.token,
        openid=args.openid,
        auto_bind=args.auto_bind
    )
    response = client.get_todos(
        start=args.start,
        limit=args.limit,
        title=args.title,
        begin_date=args.begin_date,
        end_date=args.end_date,
        process_def_id=args.process_def_id
    )
    print_response(response, args.json)

def cmd_dones(args):
    """Query completed tasks"""
    client = BPMClient(
        base_url=args.base_url,
        token=args.token,
        openid=args.openid,
        auto_bind=args.auto_bind
    )
    response = client.get_dones(
        start=args.start,
        limit=args.limit,
        title=args.title,
        begin_date=args.begin_date,
        end_date=args.end_date,
        process_def_id=args.process_def_id
    )
    print_response(response, args.json)

def cmd_approve(args):
    """Approve or reject a task"""
    client = BPMClient(
        base_url=args.base_url,
        token=args.token,
        openid=args.openid,
        auto_bind=args.auto_bind
    )
    response = client.approve_task(
        task_inst_id=args.task_id,
        action=args.action,
        comment=args.comment
    )
    print_response(response, args.json)

def cmd_comment(args):
    """Add comment to a task without completing it"""
    client = BPMClient(
        base_url=args.base_url,
        token=args.token,
        openid=args.openid,
        auto_bind=args.auto_bind
    )
    response = client.add_comment(
        task_inst_id=args.task_id,
        action_name=args.action_name,
        msg=args.msg
    )
    print_response(response, args.json)


def print_response(response, as_json=False):
    """Print API response"""
    if as_json:
        print(json.dumps({
            "success": response.is_success,
            "code": response.code,
            "message": response.message,
            "data": response.data
        }, indent=2, ensure_ascii=False))
    else:
        if response.is_success:
            print(f"✓ {response.message}")
            if response.data and isinstance(response.data, dict):
                if "items" in response.data or "list" in response.data:
                    items = response.data.get("items") or response.data.get("list", [])
                    total = response.data.get("total", len(items))
                    print(f"Total: {total} tasks")
                    for item in items:
                        task_id = item.get("taskInstId", item.get("task_inst_id", "N/A"))[:20]
                        title = item.get("title", "N/A")
                        print(f"  [{task_id}] {title}")
        else:
            print(f"✗ {response.message}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Mix-Data BPM CLI Tool (User Version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query pending tasks (auto-bind token)
  python3 bpm.py todos --token YOUR_TOKEN --openid YOUR_OPENID --auto-bind

  # Query pending tasks with filters
  python3 bpm.py todos --token YOUR_TOKEN --openid YOUR_OPENID --title "请假" --limit 10

  # Approve a task
  python3 bpm.py approve --token YOUR_TOKEN --openid YOUR_OPENID --task-id TASK_ID --action approve --comment "同意"

  # Reject a task
  python3 bpm.py approve --token YOUR_TOKEN --openid YOUR_OPENID --task-id TASK_ID --action reject --comment "需要补充材料"

  # Add comment without completing
  python3 bpm.py comment --token YOUR_TOKEN --openid YOUR_OPENID --task-id TASK_ID --action-name review --msg "请补充相关材料"

Note:
  --auto-bind will automatically bind your token to openid on first use.
  Only needs to be done once. After binding, you can omit --auto-bind.
        """
    )
    parser.add_argument("--base-url", default="http://localhost:8001", help="API base URL")
    parser.add_argument("--token", required=True, help="Your auth token")
    parser.add_argument("--openid", required=True, help="Your Feishu openid")
    parser.add_argument("--auto-bind", action="store_true", help="Automatically bind token to openid on first use")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # todos command
    todos_parser = subparsers.add_parser("todos", help="Query pending tasks")
    todos_parser.add_argument("--start", type=int, default=0, help="Pagination start")
    todos_parser.add_argument("--limit", type=int, default=20, help="Items per page")
    todos_parser.add_argument("--title", help="Search by title")
    todos_parser.add_argument("--begin-date", help="Start date (yyyy-MM-dd)")
    todos_parser.add_argument("--end-date", help="End date (yyyy-MM-dd)")
    todos_parser.add_argument("--process-def-id", help="Filter by process definition ID")

    # dones command
    dones_parser = subparsers.add_parser("dones", help="Query completed tasks")
    dones_parser.add_argument("--start", type=int, default=0, help="Pagination start")
    dones_parser.add_argument("--limit", type=int, default=20, help="Items per page")
    dones_parser.add_argument("--title", help="Search by title")
    dones_parser.add_argument("--begin-date", help="Start date (yyyy-MM-dd)")
    dones_parser.add_argument("--end-date", help="End date (yyyy-MM-dd)")
    dones_parser.add_argument("--process-def-id", help="Filter by process definition ID")

    # approve command
    approve_parser = subparsers.add_parser("approve", help="Approve or reject a task")
    approve_parser.add_argument("--task-id", required=True, help="Task instance ID")
    approve_parser.add_argument("--action", required=True, choices=["approve", "reject"], help="Action to take")
    approve_parser.add_argument("--comment", help="Approval comment")

    # comment command
    comment_parser = subparsers.add_parser("comment", help="Add comment to task without completing")
    comment_parser.add_argument("--task-id", required=True, help="Task instance ID")
    comment_parser.add_argument("--action-name", required=True, help="Action name (e.g., review, comment)")
    comment_parser.add_argument("--msg", required=True, help="Comment message")

    args = parser.parse_args()

    if args.command == "todos":
        cmd_todos(args)
    elif args.command == "dones":
        cmd_dones(args)
    elif args.command == "approve":
        cmd_approve(args)
    elif args.command == "comment":
        cmd_comment(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
