import unittest

from osint_casebuilder.modules.username_mutator import generate_username_variants


class TestGenerateUsernameVariants(unittest.TestCase):
    def test_returns_sorted_list(self):
        result = generate_username_variants("john.doe")
        self.assertIsInstance(result, list)
        self.assertEqual(result, sorted(result))

    def test_returns_unique_values(self):
        result = generate_username_variants("john.doe")
        self.assertEqual(len(result), len(set(result)))

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(generate_username_variants(""), [])

    def test_whitespace_input_returns_empty_list(self):
        self.assertEqual(generate_username_variants("   "), [])

    def test_normalized_base_included(self):
        # Input is lowercased and stripped; the normalized base must be present.
        result = generate_username_variants("  Linus  ")
        self.assertIn("linus", result)

    def test_nickname_derived_forms_included(self):
        # nickname_mapper maps "michael" -> ["mike", "mic", "mikey"].
        result = generate_username_variants("michael")
        self.assertIn("mike", result)
        self.assertIn("mikey", result)

    def test_two_part_initialisms_and_combined(self):
        result = generate_username_variants("john.doe")
        # Initialisms: first-initial + surname, and name + surname-initial.
        self.assertIn("jdoe", result)
        self.assertIn("johnd", result)
        # Combined form with no separator.
        self.assertIn("johndoe", result)

    def test_leet_speak_substitution_present(self):
        # LEET_MAP maps 'o' -> ['0'], so "bob" yields "b0b".
        result = generate_username_variants("bob")
        self.assertIn("bob", result)
        self.assertIn("b0b", result)


if __name__ == "__main__":
    unittest.main()
