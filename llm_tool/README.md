# LLM Tool for Odoo

Enhanced function calling framework with structured data storage, comprehensive error handling, and MCP integration. This module enables LLMs to interact with Odoo data and execute actions through a powerful and secure tool system.

## Overview

The LLM Tool module provides the foundation for AI function calling in Odoo, allowing LLMs to interact with business data, execute actions, and perform complex operations. With version 16.0.3.0.0, the module features a major refactoring with structured data storage in `body_json` and enhanced execution capabilities.

### Core Capabilities

- **Function Calling Framework** - Enable LLMs to execute Odoo methods and actions
- **Structured Data Storage** - Tool results stored in `body_json` format for better organization
- **MCP Integration** - Model Context Protocol compatibility for standardized tool definitions  
- **Security Framework** - User consent system and permission-based access control
- **Error Handling** - Comprehensive error propagation and recovery mechanisms
- **Schema Generation** - Automatic input schema detection from method signatures

## Key Features

### Enhanced Tool System (Version 16.0.3.0.0)

**Structured Message Format:**

```python
# New body_json format for tool messages
thread.message_post(
    body_json={
        "tool_call_id": "call_abc123",
        "function": "search_records",
        "arguments": {
            "model": "sale.order",
            "domain": [['state', '=', 'draft']],
            "limit": 10
        },
        "result": {
            "records": [...],
            "count": 5,
            "execution_time": 0.045
        },
        "status": "success"
    },
    llm_role="tool"
)
```

**Benefits of New Format:**
- **Better Organization**: All tool data in structured JSON format
- **Enhanced Debugging**: Clear separation of input, output, and metadata
- **Improved Analytics**: Easy analysis of tool usage patterns
- **MCP Compatibility**: Standard format for tool call tracking

### Tool Implementation Types

#### 1. Server Action Tools
Execute existing Odoo server actions:
```python
class LLMToolServerAction(models.Model):
    _name = "llm.tool.server.action"
    _inherit = "llm.tool"
    
    server_action_id = fields.Many2one('ir.actions.server', required=True)
    
    def server_action_execute(self, **kwargs):
        """Execute server action with parameters"""
        return self.server_action_id.with_context(**kwargs).run()
```

#### 2. Method Call Tools  
Call specific model methods:
```python
class LLMToolMethodCall(models.Model):
    _name = "llm.tool.method.call"
    _inherit = "llm.tool"
    
    target_model = fields.Char(required=True)
    target_method = fields.Char(required=True)
    
    def method_call_execute(self, record_ids=None, **kwargs):
        """Execute method on target records"""
        Model = self.env[self.target_model]
        records = Model.browse(record_ids) if record_ids else Model
        method = getattr(records, self.target_method)
        return method(**kwargs)
```

#### 3. Search Tools
Search and retrieve Odoo records:
```python
class LLMToolSearch(models.Model):
    _name = "llm.tool.search"
    _inherit = "llm.tool"
    
    def search_execute(self, model, domain=None, fields=None, limit=10, **kwargs):
        """Search records with domain and return specified fields"""
        Model = self.env[model]
        domain = domain or []
        
        records = Model.search(domain, limit=limit)
        
        if fields:
            return records.read(fields)
        else:
            return [{
                'id': rec.id,
                'name': rec.display_name,
                'model': model
            } for rec in records]
```

#### 4. Custom Function Tools
Execute custom Python functions:
```python
class LLMToolCustomFunction(models.Model):
    _name = "llm.tool.custom.function"
    _inherit = "llm.tool"
    
    function_code = fields.Text(required=True)
    
    def custom_function_execute(self, **kwargs):
        """Execute custom Python code safely"""
        # Safe execution environment
        safe_globals = {
            'env': self.env,
            'fields': fields,
            'models': models,
            '_': _,
            '__builtins__': {}  # Restricted builtins
        }
        
        exec(self.function_code, safe_globals, kwargs)
        return kwargs.get('result', 'Function executed successfully')
```

### Automatic Schema Generation

**From Method Signatures:**
```python
def get_input_schema_from_method(self):
    """Generate JSON schema from method signature"""
    import inspect
    
    if self.implementation == 'search':
        method = self.search_execute
    elif self.implementation == 'method_call':
        method = self.method_call_execute
    else:
        return {}
    
    signature = inspect.signature(method)
    schema = {"type": "object", "properties": {}}
    
    for param_name, param in signature.parameters.items():
        if param_name in ['self', 'kwargs']:
            continue
            
        prop = {"type": "string"}  # Default type
        
        # Type hint detection
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                prop["type"] = "integer"
            elif param.annotation == bool:
                prop["type"] = "boolean"
            elif param.annotation == list:
                prop["type"] = "array"
        
        # Default value
        if param.default != inspect.Parameter.empty:
            prop["default"] = param.default
        
        schema["properties"][param_name] = prop
    
    return schema
```

**Manual Schema Definition:**
```python
# Custom JSON schema for complex tools
tool_schema = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query string",
            "minLength": 1
        },
        "filters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "status": {
                    "type": "string", 
                    "enum": ["draft", "confirmed", "done"]
                }
            }
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        }
    },
    "required": ["query"]
}
```

## Security Framework

### User Consent System

```python
class LLMTool(models.Model):
    _inherit = "llm.tool"
    
    requires_user_consent = fields.Boolean(
        default=False,
        help="Require user confirmation before execution"
    )
    
    destructive_hint = fields.Boolean(
        default=False, 
        help="Tool may modify or delete data"
    )
    
    read_only_hint = fields.Boolean(
        default=True,
        help="Tool only reads data without modifications"
    )
    
    def execute_with_consent(self, user_id, **kwargs):
        """Execute tool with user consent validation"""
        if self.requires_user_consent:
            consent = self._check_user_consent(user_id, **kwargs)
            if not consent:
                raise UserError("User consent required for this operation")
        
        return self.execute(**kwargs)
```

### Permission Framework

```python
def check_execution_permissions(self, user_id=None):
    """Check if user has permission to execute this tool"""
    user = self.env['res.users'].browse(user_id) if user_id else self.env.user
    
    # Check basic tool access
    if not user.has_group('llm.group_llm_user'):
        return False, "User not in LLM User group"
    
    # Check tool-specific permissions
    if self.destructive_hint and not user.has_group('llm.group_llm_manager'):
        return False, "Destructive operations require LLM Manager role"
    
    # Check model-specific permissions
    if hasattr(self, 'target_model'):
        Model = self.env[self.target_model]
        if not Model.check_access_rights('read', raise_exception=False):
            return False, f"No read access to {self.target_model}"
    
    return True, "Permission granted"
```

## Tool Execution Examples

### CRM Tools

```python
class CRMSearchTool(models.Model):
    _name = "llm.tool.crm.search"
    _inherit = "llm.tool"
    
    def crm_search_execute(self, query=None, stage=None, user_id=None, limit=10):
        """Search CRM opportunities with intelligent filtering"""
        domain = []
        
        if query:
            domain.extend([
                '|', '|',
                ('name', 'ilike', query),
                ('partner_id.name', 'ilike', query),
                ('description', 'ilike', query)
            ])
        
        if stage:
            domain.append(('stage_id.name', 'ilike', stage))
            
        if user_id:
            domain.append(('user_id', '=', user_id))
        
        opportunities = self.env['crm.lead'].search(domain, limit=limit)
        
        return {
            'count': len(opportunities),
            'opportunities': [{
                'id': opp.id,
                'name': opp.name,
                'partner': opp.partner_id.name,
                'stage': opp.stage_id.name,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'date_deadline': opp.date_deadline.isoformat() if opp.date_deadline else None
            } for opp in opportunities]
        }
```

### Inventory Tools

```python
class InventoryTool(models.Model):
    _name = "llm.tool.inventory"
    _inherit = "llm.tool"
    
    def inventory_check_execute(self, product_ids=None, location_id=None):
        """Check inventory levels for products"""
        domain = []
        
        if product_ids:
            domain.append(('product_id', 'in', product_ids))
        if location_id:
            domain.append(('location_id', '=', location_id))
        
        quants = self.env['stock.quant'].search(domain)
        
        inventory_data = {}
        for quant in quants:
            product_id = quant.product_id.id
            if product_id not in inventory_data:
                inventory_data[product_id] = {
                    'product_name': quant.product_id.name,
                    'total_quantity': 0,
                    'locations': []
                }
            
            inventory_data[product_id]['total_quantity'] += quant.quantity
            inventory_data[product_id]['locations'].append({
                'location': quant.location_id.name,
                'quantity': quant.quantity,
                'reserved_quantity': quant.reserved_quantity
            })
        
        return inventory_data
```

### Report Generation Tools

```python
class ReportGenerationTool(models.Model):
    _name = "llm.tool.report.generation"
    _inherit = "llm.tool"
    
    def report_generate_execute(self, report_name, record_ids, format='pdf'):
        """Generate reports for specified records"""
        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(f"Report '{report_name}' not found")
        
        records = self.env[report.model].browse(record_ids)
        
        if format.lower() == 'pdf':
            pdf_content, _ = report._render_qweb_pdf(records.ids)
            return {
                'format': 'pdf',
                'content': base64.b64encode(pdf_content).decode(),
                'filename': f"{report_name}_{len(record_ids)}_records.pdf"
            }
        elif format.lower() == 'html':
            html_content, _ = report._render_qweb_html(records.ids)
            return {
                'format': 'html',
                'content': html_content,
                'filename': f"{report_name}_{len(record_ids)}_records.html"
            }
        else:
            raise UserError(f"Unsupported format: {format}")
```

## MCP Integration

### Tool Definition for MCP

```python
def get_mcp_tool_definition(self):
    """Generate MCP-compatible tool definition"""
    return {
        "name": self.name,
        "description": self.description,
        "inputSchema": {
            "type": "object",
            "properties": json.loads(self.input_schema or '{}').get('properties', {}),
            "required": json.loads(self.input_schema or '{}').get('required', [])
        }
    }

def execute_mcp_call(self, arguments):
    """Execute tool call from MCP client"""
    try:
        result = self.execute(**arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, default=str, indent=2)
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Error executing tool: {str(e)}"
                }
            ],
            "isError": True
        }
```

### MCP Server Integration

```python
class MCPToolServer(models.Model):
    _name = "llm.mcp.tool.server"
    _inherit = "llm.mcp.server"
    
    def get_available_tools(self):
        """Return all available tools for MCP clients"""
        tools = self.env['llm.tool'].search([('active', '=', True)])
        return [tool.get_mcp_tool_definition() for tool in tools]
    
    def call_tool(self, name, arguments):
        """Handle tool call from MCP client"""
        tool = self.env['llm.tool'].search([('name', '=', name)], limit=1)
        if not tool:
            raise UserError(f"Tool '{name}' not found")
        
        return tool.execute_mcp_call(arguments)
```

## Error Handling & Logging

### Comprehensive Error Management

```python
def execute_with_error_handling(self, **kwargs):
    """Execute tool with comprehensive error handling"""
    execution_start = time.time()
    
    try:
        # Validate inputs
        self._validate_execution_inputs(**kwargs)
        
        # Check permissions
        can_execute, error_msg = self.check_execution_permissions()
        if not can_execute:
            raise PermissionError(error_msg)
        
        # Execute tool
        result = self.execute(**kwargs)
        
        # Log successful execution
        self._log_tool_execution(
            status='success',
            duration=time.time() - execution_start,
            result_size=len(str(result))
        )
        
        return result
        
    except ValidationError as e:
        self._log_tool_execution(
            status='validation_error',
            error=str(e),
            duration=time.time() - execution_start
        )
        raise
        
    except PermissionError as e:
        self._log_tool_execution(
            status='permission_error', 
            error=str(e),
            duration=time.time() - execution_start
        )
        raise
        
    except Exception as e:
        self._log_tool_execution(
            status='execution_error',
            error=str(e),
            duration=time.time() - execution_start
        )
        raise UserError(f"Tool execution failed: {str(e)}")
```

### Execution Logging

```python
def _log_tool_execution(self, status, duration=None, error=None, result_size=None):
    """Log tool execution for monitoring and debugging"""
    log_data = {
        'tool_id': self.id,
        'tool_name': self.name,
        'user_id': self.env.uid,
        'status': status,
        'timestamp': fields.Datetime.now(),
        'duration': duration,
        'error_message': error,
        'result_size_bytes': result_size
    }
    
    # Create execution log record
    self.env['llm.tool.execution.log'].create(log_data)
    
    # Also log to system log for monitoring
    if status == 'success':
        _logger.info(f"Tool '{self.name}' executed successfully in {duration:.3f}s")
    else:
        _logger.warning(f"Tool '{self.name}' failed: {error}")
```

## API Reference

### Core Methods

```python
# Execute tool with arguments
def execute(self, **kwargs):
    """Main execution method - implemented by subclasses"""

# Get tool definition for AI models
def get_tool_definition(self):
    """Return tool definition in OpenAI function calling format"""

# Validate execution permissions
def check_execution_permissions(self, user_id=None):
    """Check if user can execute this tool"""

# Generate input schema
def get_input_schema(self):
    """Return JSON schema for tool inputs"""

# MCP integration
def get_mcp_tool_definition(self):
    """Return MCP-compatible tool definition"""
```

### Tool Registration

```python
@api.model
def _get_available_implementations(self):
    """Return available tool implementation types"""
    return [
        ('search', 'Search Records'),
        ('server_action', 'Server Action'),
        ('method_call', 'Method Call'),
        ('custom_function', 'Custom Function')
    ]
```

## Performance Optimizations

### Execution Caching

```python
@api.model
@tools.ormcache('tool_id', 'cache_key')
def _get_cached_execution_result(self, tool_id, cache_key):
    """Cache tool execution results for read-only operations"""
    return self._execute_without_cache()

def execute_with_cache(self, **kwargs):
    """Execute with result caching for read-only tools"""
    if not self.read_only_hint:
        return self.execute(**kwargs)
    
    cache_key = self._generate_cache_key(**kwargs)
    return self._get_cached_execution_result(self.id, cache_key)
```

### Batch Operations

```python
def execute_batch(self, operation_list):
    """Execute multiple tool operations in batch"""
    results = []
    
    # Group operations by type for optimization
    grouped_ops = self._group_operations_by_type(operation_list)
    
    for op_type, operations in grouped_ops.items():
        if op_type == 'search':
            # Batch search operations
            batch_results = self._execute_batch_search(operations)
        elif op_type == 'method_call':
            # Batch method calls
            batch_results = self._execute_batch_method_calls(operations)
        else:
            # Execute individually
            batch_results = [self.execute(**op) for op in operations]
        
        results.extend(batch_results)
    
    return results
```

## Migration Notes

### Version 16.0.3.0.0 Changes

**Major Refactoring:**
- **Tool message format** changed to structured `body_json` format
- **Enhanced execution** with better error handling and logging
- **MCP integration** added for standardized tool definitions
- **Security improvements** with enhanced permission framework

**Migration Script:** Automatically converts existing tool messages:
```python
def migrate_tool_messages(env):
    """Convert old tool messages to new body_json format"""
    tool_messages = env['mail.message'].search([
        ('llm_role', '=', 'tool'),
        ('body_json', '=', False)
    ])
    
    for message in tool_messages:
        # Extract tool data from old format
        old_data = message._extract_legacy_tool_data()
        
        # Convert to new format
        new_format = {
            "tool_call_id": old_data.get('call_id'),
            "function": old_data.get('function_name'),
            "arguments": old_data.get('arguments', {}),
            "result": old_data.get('result'),
            "status": "success" if old_data.get('result') else "error"
        }
        
        message.body_json = new_format
```

**Breaking Changes:** None for end users - internal message format only

## Technical Specifications

### Module Information

- **Name**: LLM Tool
- **Version**: 16.0.3.0.0
- **Category**: Technical
- **License**: LGPL-3
- **Dependencies**: `llm`, `mail`
- **Author**: Apexive Solutions LLC

### Key Models

- **`llm.tool`**: Base tool framework
- **`llm.tool.execution.log`**: Execution logging and monitoring
- **Tool implementation models**: Various specialized tool types

### Security Features

- User consent system for sensitive operations
- Permission-based access control
- Execution logging and audit trails
- Safe execution environments for custom code

## Related Modules

- **`llm`**: Base infrastructure and messaging system
- **`llm_assistant`**: Assistant configuration with tool selection
- **`llm_thread`**: Chat interface with tool execution display
- **`llm_tool_knowledge`**: Knowledge base search tool
- **`llm_mcp`**: Model Context Protocol server implementation

## Support & Resources

- **Documentation**: [GitHub Repository](https://github.com/apexive/odoo-llm)
- **Architecture Guide**: [OVERVIEW.md](../OVERVIEW.md)
- **Tool Examples**: [Tool Development Guide](examples/)
- **Community**: [GitHub Discussions](https://github.com/apexive/odoo-llm/discussions)

## License

This module is licensed under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).

---

*© 2025 Apexive Solutions LLC. All rights reserved.*
