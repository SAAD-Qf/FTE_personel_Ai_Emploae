"""
Odoo MCP Server

Model Context Protocol (MCP) server for Odoo ERP integration.
Provides accounting, invoicing, and business management capabilities.

Features:
- Create and manage invoices
- Track payments and transactions
- Generate accounting reports
- Manage customers and vendors
- Monitor business metrics

Setup:
1. Install Odoo Community Edition (local or cloud)
2. Install dependencies: pip install xmlrpc-client requests
3. Configure Odoo connection in ~/.config/odoo_config.json
4. Run this server

Usage:
    python odoo_mcp_server.py --config ~/.config/odoo_config.json

Claude Code Configuration (~/.config/claude-code/mcp.json):
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["D:/Hackathon_0/FTE_personel_Ai_Emploae/scripts/odoo_mcp_server.py"],
      "env": {
        "ODOO_CONFIG": "C:/Users/YourName/.config/odoo_config.json"
      }
    }
  }
}

Odoo Config File (~/.config/odoo_config.json):
{
  "url": "http://localhost:8069",
  "db": "odoo_db",
  "username": "admin",
  "password": "admin_password",
  "api_key": ""
}
"""

import argparse
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not available. Install with: pip install mcp")

# Odoo XML-RPC imports
try:
    import xmlrpc.client
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False
    print("Odoo XML-RPC client not available. Install with: pip install xmlrpc-client")


class OdooClient:
    """Odoo XML-RPC client for ERP operations."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize Odoo client.

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            db: Database name
            username: Odoo username
            password: Odoo password or API key
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.common = None
        self.models = None

        self._authenticate()

    def _authenticate(self):
        """Authenticate with Odoo server."""
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            self.uid = self.common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                raise Exception("Authentication failed. Check credentials.")

        except Exception as e:
            raise Exception(f"Odoo connection failed: {e}")

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model."""
        if not self.uid:
            raise Exception("Not authenticated")

        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def search_read(self, model: str, domain: List = None, fields: List = None, limit: int = 80) -> List[Dict]:
        """Search and read records from a model."""
        return self.execute(model, 'search_read', domain=domain or [], fields=fields, limit=limit)

    def create(self, model: str, values: Dict) -> int:
        """Create a record in a model."""
        return self.execute(model, 'create', values)

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """Update records in a model."""
        return self.execute(model, 'write', ids, values)

    def unlink(self, model: str, ids: List[int]) -> bool:
        """Delete records from a model."""
        return self.execute(model, 'unlink', ids)

    # Invoice operations
    def create_invoice(
        self,
        partner_id: int,
        invoice_type: str = 'out_invoice',
        lines: List[Dict] = None,
        payment_term: int = None,
        narrative: str = None
    ) -> int:
        """
        Create a customer invoice.

        Args:
            partner_id: Customer ID
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor)
            lines: Invoice line items [{'product_id': int, 'quantity': float, 'price_unit': float}]
            payment_term: Payment term ID
            narrative: Invoice narrative/description

        Returns:
            Invoice ID
        """
        invoice_vals = {
            'partner_id': partner_id,
            'move_type': invoice_type,
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'invoice_date_due': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'narrative': narrative or '',
        }

        if payment_term:
            invoice_vals['invoice_payment_term_id'] = payment_term

        invoice_id = self.create('account.move', invoice_vals)

        # Add invoice lines
        if lines:
            line_vals = []
            for line in lines:
                line_vals.append((0, 0, {
                    'product_id': line.get('product_id'),
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0),
                    'name': line.get('name', 'Service'),
                }))
            self.write('account.move', [invoice_id], {'invoice_line_ids': line_vals})

        return invoice_id

    def get_invoices(self, partner_id: int = None, state: str = 'posted', limit: int = 10) -> List[Dict]:
        """Get invoices."""
        domain = []
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        if state:
            domain.append(('state', '=', state))

        fields = ['id', 'name', 'partner_id', 'amount_total', 'amount_due', 'invoice_date', 'state']
        return self.search_read('account.move', domain=domain, fields=fields, limit=limit)

    def register_payment(self, invoice_id: int, amount: float, payment_method: str = 'manual') -> Dict:
        """Register a payment for an invoice."""
        # Create payment record
        payment_vals = {
            'move_ids': [(4, invoice_id)],
            'amount': amount,
            'payment_type': 'inbound',
            'payment_method_line_id': self._get_payment_method_id(payment_method),
            'date': datetime.now().strftime('%Y-%m-%d'),
        }

        payment_id = self.create('account.payment', payment_vals)
        self.execute('account.payment', 'action_post', [payment_id])

        return {'payment_id': payment_id, 'amount': amount, 'status': 'posted'}

    def _get_payment_method_id(self, method: str) -> int:
        """Get payment method ID."""
        methods = self.search_read('account.payment.method.line', fields=['id', 'name'], limit=10)
        for m in methods:
            if method.lower() in m.get('name', '').lower():
                return m['id']
        return methods[0]['id'] if methods else 1

    # Partner (Customer/Vendor) operations
    def create_partner(
        self,
        name: str,
        email: str = None,
        phone: str = None,
        is_customer: bool = True,
        is_vendor: bool = False
    ) -> int:
        """Create a business partner (customer or vendor)."""
        partner_vals = {
            'name': name,
            'email': email or '',
            'phone': phone or '',
            'customer_rank': 1 if is_customer else 0,
            'supplier_rank': 1 if is_vendor else 0,
        }
        return self.create('res.partner', partner_vals)

    def get_partners(self, search: str = None, limit: int = 20) -> List[Dict]:
        """Get partners."""
        domain = []
        if search:
            domain.append(('name', 'ilike', search))
        fields = ['id', 'name', 'email', 'phone', 'customer_rank', 'supplier_rank']
        return self.search_read('res.partner', domain=domain, fields=fields, limit=limit)

    # Product operations
    def create_product(
        self,
        name: str,
        list_price: float,
        product_type: str = 'service',
        description: str = None
    ) -> int:
        """Create a product."""
        product_vals = {
            'name': name,
            'list_price': list_price,
            'type': product_type,
            'description_sale': description or '',
        }
        return self.create('product.template', product_vals)

    def get_products(self, search: str = None, limit: int = 20) -> List[Dict]:
        """Get products."""
        domain = []
        if search:
            domain.append(('name', 'ilike', search))
        fields = ['id', 'name', 'list_price', 'type']
        return self.search_read('product.template', domain=domain, fields=fields, limit=limit)

    # Accounting reports
    def get_trial_balance(self, company_id: int = None) -> Dict:
        """Get trial balance report."""
        # Simplified - in production, use Odoo's accounting reports
        accounts = self.search_read(
            'account.account',
            fields=['code', 'name', 'balance'],
            limit=100
        )
        return {
            'accounts': accounts,
            'total_debit': sum(a['balance'] for a in accounts if a['balance'] > 0),
            'total_credit': sum(abs(a['balance']) for a in accounts if a['balance'] < 0),
        }

    def get_profit_loss(self, date_from: str = None, date_to: str = None) -> Dict:
        """Get profit and loss statement."""
        # Get income and expense accounts
        income_accounts = self.search_read(
            'account.account',
            domain=[('account_type', '=', 'income')],
            fields=['code', 'name', 'balance'],
            limit=50
        )
        expense_accounts = self.search_read(
            'account.account',
            domain=[('account_type', '=', 'expense')],
            fields=['code', 'name', 'balance'],
            limit=50
        )

        total_income = sum(a['balance'] for a in income_accounts)
        total_expense = sum(abs(a['balance']) for a in expense_accounts)

        return {
            'income': income_accounts,
            'expenses': expense_accounts,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': total_income - total_expense,
        }

    def get_balance_sheet(self) -> Dict:
        """Get balance sheet."""
        assets = self.search_read(
            'account.account',
            domain=[('account_type', '=', 'asset')],
            fields=['code', 'name', 'balance'],
            limit=50
        )
        liabilities = self.search_read(
            'account.account',
            domain=[('account_type', '=', 'liability')],
            fields=['code', 'name', 'balance'],
            limit=50
        )

        total_assets = sum(a['balance'] for a in assets if a['balance'] > 0)
        total_liabilities = sum(abs(a['balance']) for a in liabilities if a['balance'] < 0)

        return {
            'assets': assets,
            'liabilities': liabilities,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'equity': total_assets - total_liabilities,
        }

    # Business metrics
    def get_business_metrics(self) -> Dict:
        """Get key business metrics."""
        # Revenue this month
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        invoices = self.search_read(
            'account.move',
            domain=[
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', month_start)
            ],
            fields=['amount_total'],
            limit=100
        )
        monthly_revenue = sum(inv['amount_total'] for inv in invoices)

        # Outstanding invoices
        outstanding = self.search_read(
            'account.move',
            domain=[
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', '=', 'not_paid')
            ],
            fields=['amount_total', 'amount_due'],
            limit=100
        )
        outstanding_total = sum(inv['amount_due'] for inv in outstanding)

        # Customer count
        customer_count = len(self.search_read('res.partner', domain=[('customer_rank', '>', 0)], limit=1000))

        return {
            'monthly_revenue': monthly_revenue,
            'outstanding_invoices': len(outstanding),
            'outstanding_amount': outstanding_total,
            'customer_count': customer_count,
        }


class OdooMCPServer:
    """MCP Server for Odoo ERP operations."""

    def __init__(self, config_path: str):
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP library not available")
        if not ODOO_AVAILABLE:
            raise RuntimeError("Odoo XML-RPC client not available")

        self.server = Server("odoo-mcp")
        self.config_path = Path(config_path)
        self.odoo_client = None

        self._load_config()
        self._setup_handlers()

    def _load_config(self):
        """Load Odoo configuration."""
        if not self.config_path.exists():
            # Create default config
            default_config = {
                "url": "http://localhost:8069",
                "db": "odoo",
                "username": "admin",
                "password": "admin"
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(default_config, indent=2))
            print(f"Created default config at {self.config_path}", file=sys.stderr)

        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

        # Initialize Odoo client
        try:
            self.odoo_client = OdooClient(
                url=self.config['url'],
                db=self.config['db'],
                username=self.config['username'],
                password=self.config['password']
            )
            print(f"Connected to Odoo at {self.config['url']}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not connect to Odoo: {e}", file=sys.stderr)
            self.odoo_client = None

    def _setup_handlers(self):
        """Setup MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="odoo_create_invoice",
                    description="Create a customer or vendor invoice in Odoo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "partner_id": {
                                "type": "integer",
                                "description": "Customer/Vendor ID"
                            },
                            "invoice_type": {
                                "type": "string",
                                "enum": ["out_invoice", "in_invoice"],
                                "description": "Invoice type (out_invoice for customer, in_invoice for vendor)"
                            },
                            "lines": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "product_id": {"type": "integer"},
                                        "quantity": {"type": "number"},
                                        "price_unit": {"type": "number"},
                                        "name": {"type": "string"}
                                    }
                                },
                                "description": "Invoice line items"
                            },
                            "narrative": {
                                "type": "string",
                                "description": "Invoice description/narrative"
                            }
                        },
                        "required": ["partner_id"]
                    }
                ),
                Tool(
                    name="odoo_get_invoices",
                    description="Get invoices from Odoo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "partner_id": {
                                "type": "integer",
                                "description": "Filter by partner ID (optional)"
                            },
                            "state": {
                                "type": "string",
                                "enum": ["draft", "posted", "cancel"],
                                "description": "Filter by state"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum results"
                            }
                        }
                    }
                ),
                Tool(
                    name="odoo_register_payment",
                    description="Register a payment for an invoice",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "invoice_id": {
                                "type": "integer",
                                "description": "Invoice ID"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Payment amount"
                            },
                            "payment_method": {
                                "type": "string",
                                "description": "Payment method (manual, bank, etc.)"
                            }
                        },
                        "required": ["invoice_id", "amount"]
                    }
                ),
                Tool(
                    name="odoo_create_partner",
                    description="Create a new customer or vendor",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Partner name"
                            },
                            "email": {
                                "type": "string",
                                "description": "Email address"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number"
                            },
                            "is_customer": {
                                "type": "boolean",
                                "default": True,
                                "description": "Is a customer"
                            },
                            "is_vendor": {
                                "type": "boolean",
                                "default": False,
                                "description": "Is a vendor"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="odoo_get_partners",
                    description="Search for partners (customers/vendors)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search": {
                                "type": "string",
                                "description": "Search term"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20
                            }
                        }
                    }
                ),
                Tool(
                    name="odoo_get_business_metrics",
                    description="Get key business metrics (revenue, outstanding invoices, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="odoo_get_profit_loss",
                    description="Get profit and loss statement",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date_from": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    }
                ),
                Tool(
                    name="odoo_create_product",
                    description="Create a new product/service",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Product name"
                            },
                            "list_price": {
                                "type": "number",
                                "description": "Sale price"
                            },
                            "product_type": {
                                "type": "string",
                                "enum": ["product", "service"],
                                "default": "service"
                            },
                            "description": {
                                "type": "string",
                                "description": "Product description"
                            }
                        },
                        "required": ["name", "list_price"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if not self.odoo_client:
                return [TextContent(
                    type="text",
                    text="Error: Not connected to Odoo. Check configuration and server status."
                )]

            try:
                if name == "odoo_create_invoice":
                    result = self.odoo_client.create_invoice(
                        partner_id=arguments["partner_id"],
                        invoice_type=arguments.get("invoice_type", "out_invoice"),
                        lines=arguments.get("lines"),
                        narrative=arguments.get("narrative")
                    )
                    return [TextContent(
                        type="text",
                        text=f"Invoice created successfully!\n\nInvoice ID: {result}\n\nThe invoice has been created in Odoo and is ready for review and sending."
                    )]

                elif name == "odoo_get_invoices":
                    results = self.odoo_client.get_invoices(
                        partner_id=arguments.get("partner_id"),
                        state=arguments.get("state"),
                        limit=arguments.get("limit", 10)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]

                elif name == "odoo_register_payment":
                    result = self.odoo_client.register_payment(
                        invoice_id=arguments["invoice_id"],
                        amount=arguments["amount"],
                        payment_method=arguments.get("payment_method", "manual")
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "odoo_create_partner":
                    result = self.odoo_client.create_partner(
                        name=arguments["name"],
                        email=arguments.get("email"),
                        phone=arguments.get("phone"),
                        is_customer=arguments.get("is_customer", True),
                        is_vendor=arguments.get("is_vendor", False)
                    )
                    return [TextContent(
                        type="text",
                        text=f"Partner created successfully!\n\nPartner ID: {result}\n\nThe partner has been added to Odoo."
                    )]

                elif name == "odoo_get_partners":
                    results = self.odoo_client.get_partners(
                        search=arguments.get("search"),
                        limit=arguments.get("limit", 20)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]

                elif name == "odoo_get_business_metrics":
                    results = self.odoo_client.get_business_metrics()
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]

                elif name == "odoo_get_profit_loss":
                    results = self.odoo_client.get_profit_loss(
                        date_from=arguments.get("date_from"),
                        date_to=arguments.get("date_to")
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]

                elif name == "odoo_create_product":
                    result = self.odoo_client.create_product(
                        name=arguments["name"],
                        list_price=arguments["list_price"],
                        product_type=arguments.get("product_type", "service"),
                        description=arguments.get("description")
                    )
                    return [TextContent(
                        type="text",
                        text=f"Product created successfully!\n\nProduct ID: {result}\n\nThe product has been added to Odoo."
                    )]

                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]

            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Odoo MCP Server for AI Employee'
    )
    parser.add_argument(
        '--config-path',
        type=str,
        default=str(Path.home() / '.config' / 'odoo_config.json'),
        help='Path to Odoo configuration JSON file'
    )
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test Odoo connection and exit'
    )

    args = parser.parse_args()

    if not MCP_AVAILABLE:
        print("Error: MCP library not installed")
        print("Install with: pip install mcp")
        sys.exit(1)

    if not ODOO_AVAILABLE:
        print("Error: Odoo XML-RPC client not installed")
        print("Install with: pip install xmlrpc-client")
        sys.exit(1)

    # Test connection if requested
    if args.test_connection:
        try:
            config_path = Path(args.config_path)
            if not config_path.exists():
                print(f"Config file not found: {config_path}")
                print("Run once without --test-connection to create default config")
                sys.exit(1)

            with open(config_path, 'r') as f:
                config = json.load(f)

            client = OdooClient(
                url=config['url'],
                db=config['db'],
                username=config['username'],
                password=config['password']
            )

            # Test by getting business metrics
            metrics = client.get_business_metrics()
            print("✓ Connected to Odoo successfully!")
            print(f"\nBusiness Metrics:")
            print(f"  Monthly Revenue: ${metrics['monthly_revenue']:.2f}")
            print(f"  Outstanding Invoices: {metrics['outstanding_invoices']}")
            print(f"  Outstanding Amount: ${metrics['outstanding_amount']:.2f}")
            print(f"  Customer Count: {metrics['customer_count']}")

        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
        return

    # Run server
    server = OdooMCPServer(config_path=args.config_path)

    print("Odoo MCP Server starting...", file=sys.stderr)
    import asyncio
    asyncio.run(server.run())


if __name__ == '__main__':
    main()
