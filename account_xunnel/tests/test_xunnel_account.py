from psycopg2 import IntegrityError
from odoo.tools import mute_logger
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

now = datetime.now


class TestXunnelAccount(TransactionCase):
	pass