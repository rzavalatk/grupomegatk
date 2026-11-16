from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestPartnerCommercialLock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lock_group = cls.env.ref(
            "partner_commercial_lock.group_no_reassign_partner_commercial"
        )
        cls.seller = new_test_user(
            cls.env,
            login="commercial_lock_seller",
            groups="base.group_user,base.group_partner_manager,"
                   "partner_commercial_lock.group_no_reassign_partner_commercial",
        )
        cls.other_seller = new_test_user(
            cls.env,
            login="commercial_lock_other_seller",
            groups="base.group_user,base.group_partner_manager",
        )
        cls.manager = new_test_user(
            cls.env,
            login="commercial_lock_manager",
            groups="base.group_user,base.group_partner_manager",
        )
        cls.technician = new_test_user(
            cls.env,
            login="commercial_lock_technician",
            groups="base.group_user,base.group_partner_manager,"
                   "partner_commercial_lock.group_no_reassign_partner_commercial",
        )
        cls.customer = cls.env["res.partner"].create({
            "name": "Commercial lock test customer",
            "user_id": cls.seller.id,
        })
        cls.unassigned = cls.env["res.partner"].create({
            "name": "Commercial lock test unassigned",
            "user_id": False,
        })

    def test_seller_can_read_current_commercial(self):
        values = self.customer.with_user(self.seller).read(["user_id"])[0]
        self.assertEqual(values["user_id"][0], self.seller.id)

    def test_seller_cannot_reassign(self):
        with self.assertRaises(AccessError):
            self.customer.with_user(self.seller).write({
                "user_id": self.other_seller.id,
            })
        self.assertEqual(self.customer.user_id, self.seller)

    def test_seller_cannot_clear_commercial(self):
        with self.assertRaises(AccessError):
            self.customer.with_user(self.seller).write({"user_id": False})
        self.assertEqual(self.customer.user_id, self.seller)

    def test_seller_cannot_claim_unassigned_contact(self):
        with self.assertRaises(AccessError):
            self.unassigned.with_user(self.seller).write({
                "user_id": self.seller.id,
            })
        self.assertFalse(self.unassigned.user_id)

    def test_other_contact_fields_keep_existing_write_permissions(self):
        self.customer.with_user(self.seller).write({"ref": "Other edit"})
        self.assertEqual(self.customer.ref, "Other edit")

    def test_same_commercial_does_not_block_other_edits(self):
        self.customer.with_user(self.seller).write({
            "user_id": self.seller.id,
            "ref": "Same commercial",
        })
        self.assertEqual(self.customer.user_id, self.seller)
        self.assertEqual(self.customer.ref, "Same commercial")

    def test_unassigned_to_unassigned_is_not_reassignment(self):
        self.unassigned.with_user(self.seller).write({
            "user_id": False,
            "ref": "Unassigned retained",
        })
        self.assertFalse(self.unassigned.user_id)

    def test_rejected_batch_does_not_partially_write(self):
        batch = (self.unassigned | self.customer).with_user(self.seller)
        before = (self.unassigned.ref, self.customer.ref)
        with self.assertRaises(AccessError):
            batch.write({"user_id": False, "ref": "Must not persist"})
        self.assertFalse(self.unassigned.user_id)
        self.assertEqual(self.customer.user_id, self.seller)
        self.assertEqual((self.unassigned.ref, self.customer.ref), before)

    def test_context_cannot_disable_the_guard(self):
        for context in (
            {"import_file": True},
            {"tracking_disable": True},
            {"skip_commercial_lock": True, "check_access_rights": False},
            {"allowed_company_ids": self.seller.company_ids.ids},
        ):
            with self.subTest(context=context), self.assertRaises(AccessError):
                self.customer.with_user(self.seller).with_context(**context).write({
                    "user_id": self.other_seller.id,
                })

    def test_sudo_does_not_remove_named_seller_restriction(self):
        with self.assertRaises(AccessError):
            self.customer.with_user(self.seller).sudo().write({"user_id": False})

    def test_unrestricted_user_keeps_existing_permissions(self):
        self.customer.with_user(self.manager).write({
            "user_id": self.other_seller.id,
        })
        self.assertEqual(self.customer.user_id, self.other_seller)

    def test_technician_cannot_reassign_but_can_edit_other_fields(self):
        with self.assertRaises(AccessError):
            self.customer.with_user(self.technician).write({
                "user_id": self.other_seller.id,
            })
        self.customer.with_user(self.technician).write({"ref": "Technical edit"})
        self.assertEqual(self.customer.user_id, self.seller)
        self.assertEqual(self.customer.ref, "Technical edit")

    def test_settings_group_does_not_bypass_explicit_restriction(self):
        self.technician.write({
            "groups_id": [(4, self.env.ref("base.group_system").id)],
        })
        with self.assertRaises(AccessError):
            self.customer.with_user(self.technician).write({"user_id": False})
        self.assertEqual(self.customer.user_id, self.seller)

    def test_restriction_is_per_user_in_the_same_environment(self):
        self.assertTrue(
            self.customer.with_user(self.seller).commercial_assignment_locked
        )
        self.assertFalse(
            self.customer.with_user(self.manager).commercial_assignment_locked
        )
        self.assertTrue(
            self.customer.with_user(self.seller).commercial_assignment_locked
        )

    def test_assigning_and_removing_group_updates_the_guard(self):
        self.other_seller.write({"groups_id": [(4, self.lock_group.id)]})
        with self.assertRaises(AccessError):
            self.customer.with_user(self.other_seller).write({"user_id": False})
        self.other_seller.write({"groups_id": [(3, self.lock_group.id)]})
        self.customer.with_user(self.other_seller).write({"user_id": False})
        self.assertFalse(self.customer.user_id)
