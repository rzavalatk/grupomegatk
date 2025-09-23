import json
import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    """Extension of mail.message to handle tool operations."""

    _inherit = "mail.message"

    def get_tool_calls(self):
        """Get tool calls from assistant message body_json."""
        self.ensure_one()
        if self.llm_role != "assistant" or not self.body_json:
            return []
        return self.body_json.get("tool_calls", [])

    def has_tool_calls(self):
        """Check if assistant message has tool calls."""
        self.ensure_one()
        return bool(self.get_tool_calls())

    def post_tool_call(self, tool_call, thread_model=None):
        """Create a tool message from tool call data.

        Args:
            tool_call (dict): Tool call data from LLM response
            thread_model (recordset): The thread model that owns this message

        Returns:
            mail.message: The created tool message
        """
        if not self._validate_tool_call(tool_call):
            raise UserError(f"Invalid tool call: {tool_call}")

        function = tool_call.get("function", {})
        tool_name = function.get("name", "unknown_tool")

        # Validate tool exists in thread if thread model is provided
        if thread_model and hasattr(thread_model, "tool_ids"):
            if not thread_model.tool_ids.filtered(lambda t: t.name == tool_name):
                raise UserError(f"Tool '{tool_name}' not found in thread")

        # Validate and parse arguments
        arguments = self._parse_tool_arguments(function.get("arguments", "{}"))

        tool_data = {
            "type": "tool_execution",
            "tool_call_id": tool_call["id"],
            "tool_call": tool_call,
            "status": "requested",
            "tool_name": tool_name,
            "arguments": arguments,
        }

        _logger.debug(f"Creating tool message for {tool_name} with args: {arguments}")

        # Create the message on the thread model if provided, otherwise on self
        if thread_model:
            return thread_model.message_post(
                body=f"Executing {tool_name}",
                body_json=tool_data,
                llm_role="tool",
                author_id=False,
            )
        else:
            # If called on a message record, use its model and res_id
            return self.env["mail.message"].create(
                {
                    "model": self.model,
                    "res_id": self.res_id,
                    "body_json": tool_data,
                    "subtype_xmlid": "llm.mt_tool",
                    "author_id": False,
                    "body": f"Executing {tool_name}",
                }
            )

    def execute_tool_call(self, thread_model=None):
        """Execute a tool call for this message and update it with the result.

        Args:
            thread_model (recordset): The thread model that owns this message

        Yields:
            dict: Status updates for streaming

        Returns:
            mail.message: The updated tool message
        """
        self.ensure_one()

        if self.llm_role != "tool":
            raise UserError("Can only execute tool calls on tool messages")

        tool_data = self.get_tool_data()
        if not tool_data:
            _logger.error(f"No tool data found in message {self.id}")
            raise UserError("Invalid tool message format")

        if tool_data.get("status") != "requested":
            _logger.warning(
                f"Tool message {self.id} status is not 'requested': {tool_data.get('status')}"
            )
            return self

        tool_call_def = tool_data.get("tool_call")
        if not tool_call_def:
            raise UserError("No tool call definition found in message")

        fn = tool_call_def.get("function", {})
        name = fn.get("name", "unknown_tool")
        args = fn.get("arguments")

        # Emit tool_called event
        yield {
            "type": "tool_called",
            "tool_data": {
                "tool_call_id": tool_data.get("tool_call_id"),
                "tool_name": name,
                "arguments": self._parse_tool_arguments(args) if args else {},
                "status": "executing"
            }
        }

        # Update status to executing
        tool_data["status"] = "executing"
        self.write({"body_json": tool_data})
        yield {"type": "message_update", "message": self.message_format()[0]}

        # Execute tool and update message
        try:
            with self.env.cr.savepoint():
                result = self._execute_tool_with_context(name, args, thread_model)
                if result is None:
                    raise UserError(f"No result returned from tool '{name}'")

                # Update tool data with result
                tool_data["status"] = "completed"
                tool_data["result"] = result
                self.write({"body_json": tool_data})

                # Emit tool_succeeded event
                yield {
                    "type": "tool_succeeded",
                    "tool_data": {
                        "tool_call_id": tool_data.get("tool_call_id"),
                        "tool_name": name,
                        "arguments": self._parse_tool_arguments(args) if args else {},
                        "status": "completed",
                        "result": result
                    }
                }

        except Exception as e:
            _logger.error(f"Error executing tool {name}: {e}")
            # Update tool data with error
            tool_data["status"] = "error"
            tool_data["error"] = str(e)
            self.write({"body_json": tool_data})
            
            # Emit tool_failed event
            yield {
                "type": "tool_failed",
                "tool_data": {
                    "tool_call_id": tool_data.get("tool_call_id"),
                    "tool_name": name,
                    "arguments": self._parse_tool_arguments(args) if args else {},
                    "status": "error",
                    "error": str(e)
                }
            }
            
        yield {"type": "message_update", "message": self.message_format()[0]}
        return self

    def _validate_tool_call(self, tool_call):
        """Validate tool call structure.

        Args:
            tool_call (dict): Tool call data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(tool_call, dict):
            _logger.error(f"Tool call is not a dict: {tool_call}")
            return False

        if not tool_call.get("id"):
            _logger.error(f"Tool call missing ID: {tool_call}")
            return False

        function = tool_call.get("function", {})
        if not function.get("name"):
            _logger.error(f"Tool call missing function name: {tool_call}")
            return False

        return True

    def _parse_tool_arguments(self, arguments_str):
        """Parse and validate tool arguments.

        Args:
            arguments_str (str or dict): Tool arguments to parse

        Returns:
            dict: Parsed arguments
        """
        try:
            if isinstance(arguments_str, str):
                return json.loads(arguments_str)
            elif isinstance(arguments_str, dict):
                return arguments_str
            else:
                _logger.warning(f"Unexpected arguments type: {type(arguments_str)}")
                return {}
        except json.JSONDecodeError as e:
            _logger.error(f"Invalid JSON in tool arguments: {arguments_str}")
            raise UserError(f"Invalid tool arguments format: {e}") from e

    def _execute_tool_with_context(self, tool_name, arguments_str, thread_model=None):
        """Execute a tool with proper context.

        Args:
            tool_name (str): Name of the tool to execute
            arguments_str (str): Tool arguments as JSON string
            thread_model (recordset): The thread model that owns this message

        Returns:
            Any: Tool execution result
        """
        if not thread_model:
            # Try to get thread model from message context
            if self.model and self.res_id:
                thread_model = self.env[self.model].browse(self.res_id)
            else:
                raise UserError("No thread model available for tool execution")

        # Find the tool in the thread
        if not hasattr(thread_model, "tool_ids"):
            raise UserError(f"Thread model {thread_model._name} does not support tools")

        tool = thread_model.tool_ids.filtered(lambda t: t.name == tool_name)[:1]
        if not tool:
            raise UserError(f"Tool '{tool_name}' not found in thread")

        # Parse arguments
        arguments = (
            json.loads(arguments_str)
            if isinstance(arguments_str, str)
            else arguments_str
        )

        # Execute with message context
        return tool.with_context(message=self).execute(arguments)

    def create_tool_error_message(self, tool_call, error_msg, thread_model=None):
        """Create an error tool message.

        Args:
            tool_call (dict): Tool call data
            error_msg (str): Error message
            thread_model (recordset): The thread model that owns this message

        Returns:
            mail.message: The created error message
        """
        tool_data = {
            "type": "tool_execution",
            "tool_call_id": tool_call.get("id", "unknown"),
            "tool_call": tool_call,
            "status": "error",
            "error": error_msg,
            "tool_name": tool_call.get("function", {}).get("name", "unknown_tool"),
        }

        if thread_model:
            return thread_model.message_post(
                body_json=tool_data, llm_role="tool", author_id=False
            )
        else:
            return self.env["mail.message"].create(
                {
                    "model": self.model,
                    "res_id": self.res_id,
                    "body_json": tool_data,
                    "subtype_xmlid": "llm.mt_tool",
                    "author_id": False,
                }
            )

    def get_tool_data(self):
        """Get tool data from body_json if this is a tool message.

        Returns:
            dict or None: Tool data if this is a tool message, None otherwise
        """
        self.ensure_one()
        if self.llm_role == "tool" and self.body_json:
            return self.body_json
        return None

    def is_tool_message_with_status(self, status):
        """Check if this is a tool message with a specific status.

        Args:
            status (str): Status to check for ('requested', 'executing', 'completed', 'error')

        Returns:
            bool: True if this is a tool message with the specified status
        """
        self.ensure_one()
        tool_data = self.get_tool_data()
        if not tool_data:
            return False
        return tool_data.get("status") == status
