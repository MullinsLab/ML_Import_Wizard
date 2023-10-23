import logging
log = logging.getLogger('test')

import json
from http import HTTPStatus

from django.test import TestCase, TransactionTestCase, SimpleTestCase
from django.contrib.auth.models import User
from django.conf import settings

from unittest import skipIf

from .models import ImportScheme, ImportSchemeFile
from .utils.simple import dict_hash, sound_user_name, split_by_caps, stringalize, mached_name_choices, fancy_name, resolve_true, deep_exists
from .utils.cache import LRUCacheThing

class InclusionTest(TestCase):
    ''' A test to make sure the Import Wizard app is being included '''

    def test_true_is_true(self):
        ''' Makesure True is True '''
        self.assertTrue(True)
        
@skipIf("Genome" not in settings.ML_IMPORT_WIZARD["Importers"], "Don't include model tests")
class ModelTests(TestCase):
    '''  Tests of basic model functionality '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up whatever objects are going to be needed for all tests '''    

        cls.import_scheme = ImportScheme(
            name = 'Test Importer', 
            user = User.objects.first(), 
            importer = 'Genome',
        )
        cls.import_scheme.set_status_by_name("New")
        cls.import_scheme.save()

        cls.import_file_1 = ImportSchemeFile(name='test1.txt', import_scheme=cls.import_scheme)
        cls.import_file_1.save()
        
    def test_import_scheme_hash_should_be_the_correct_length(self):
        """ import_scheme has should be the 32 characters long """
        self.assertEqual(32, len(self.import_scheme.importer_hash))

    def test_import_scheme_hash_should_be_the_same_as_the_hash_of_the_raw_dict_from_settings(self):
        """ import_scheme has should be the same as the hash from the raw dict from settings """
        self.assertEqual(dict_hash(settings.ML_IMPORT_WIZARD['Importers']['Genome']), self.import_scheme.importer_hash)

    def test_import_file_name_should_be_file_id_padded_to_8_digits(self):
        """ import_file_name should be padded to 8 digits """
        self.assertEqual('00000001', self.import_file_1.file_name)

    def test_import_scheme_can_list_its_files(self):
        ''' Test that ImportScheme.list_files() works correctly '''

        self.assertEqual('test1.txt', self.import_scheme.list_files())

        import_file_2 = ImportSchemeFile(name='test2.txt', import_scheme=self.import_scheme)
        import_file_2.save()

        self.assertEqual('test1.txt, test2.txt', self.import_scheme.list_files())
        self.assertEqual('test1.txt<br>test2.txt', self.import_scheme.list_files(separator='<br>'))

    def test_import_scheme_file_has_correct_file_type(self):
        ''' ImportSchemeFile should have the correct type '''
        
        self.assertEqual('txt', self.import_file_1.type)

    def test_import_scheme_should_be_able_to_add_item_if_its_not_there(self):
        """ import_scheme should be able to add an item using .create_or_update_item """

        self.import_scheme_item = self.import_scheme.create_or_update_item(app="app", model= "model", field="field", strategy="raw_text", settings={"text": "this thing"})
        self.assertEqual("raw_text", self.import_scheme_item.strategy)

    def test_import_scheme_should_save_item_and_there_should_only_be_one_item(self):
        """ import_scheme should save the item after .create_or_update_item and there should only be one item """
        self.import_scheme_item = self.import_scheme.create_or_update_item(app="app", model= "model", field="field", strategy="raw_text", settings={"text": "this thing"})
        self.assertEqual("raw_text", self.import_scheme_item.strategy)

        self.import_scheme_item = self.import_scheme.create_or_update_item(app="app", model= "model", field="field", strategy="file_field", settings={"file_field": 102})
        self.assertEqual("file_field", self.import_scheme_item.strategy)

        self.assertEqual(self.import_scheme.items.count(), 1)

    def test_import_scheme_should_have_two_items_after_two_are_added(self):
        """ import_scheme should have two items after two are added and one is updated """
        import_scheme_item_1 = self.import_scheme.create_or_update_item(app="app", model= "model", field="field1", strategy="raw_text", settings={"text": "this thing"})
        self.assertEqual("raw_text", import_scheme_item_1.strategy)

        import_scheme_item_2 = self.import_scheme.create_or_update_item(app="app", model= "model", field="field1", strategy="file_field", settings={"file_field": 102})
        self.assertEqual("file_field", import_scheme_item_2.strategy)

        self.assertEqual(self.import_scheme.items.count(), 1)

        import_scheme_item_3 = self.import_scheme.create_or_update_item(app="app", model= "model", field="field2", strategy="stupid_test", settings={"file_field": 102})
        self.assertEqual("stupid_test", import_scheme_item_3.strategy)

        self.assertEqual(self.import_scheme.items.count(), 2)


class LRUCacheThingsTests(TestCase):
    """ Tests of the LRUCacheThing """

    @classmethod
    def setUpTestData(cls):
        """ Create a cache object """
        cls.cache = LRUCacheThing()
        cls.cache.store(key=1, value="test1")
        cls.cache.store(key="transaction", value="transaction test1", transaction=True)

    def test_cache_returns_thing_correctly(self):
        """ Cache should return a thing that it has been given """
        self.assertEqual(self.cache.find(key=1), "test1")
        self.assertEqual(self.cache.count, 1)

        self.cache.store(key=2, value="test2")
        self.assertEqual(self.cache.find(key=2), "test2")
        self.assertEqual(self.cache.count, 2)

    def test_cache_returns_none_with_bad_key(self):
        """ Cache should return None when given a key that doesn't exist """
        self.assertIs(self.cache.find(key=2), None)

    def test_cache_returns_value_stored_with_transaction(self):
        """ Cache should return a thing that it has been given in a transaction """
        self.assertEqual(self.cache.find(key="transaction"), "transaction test1")
        self.assertEqual(self.cache.transaction_count, 1)

    def test_cache_returns_none_with_transaction_after_rollback(self):
        """ Cache should return None for transaction after the transaction is rolled back"""
        self.assertEqual(self.cache.find(key="transaction"), "transaction test1")
        self.cache.rollback()
        self.assertIs(self.cache.find(key="transaction"), None)

    def test_cache_returns_value_stored_with_transaction_after_commit_and_rollback(self):
        """ Cache should return None when given a key that doesn't exist """
        self.assertEqual(self.cache.find(key="transaction"), "transaction test1")
        self.assertEqual(self.cache.count, 1)
        self.assertEqual(self.cache.transaction_count, 1)

        self.cache.commit()

        self.assertEqual(self.cache.find(key="transaction"), "transaction test1")
        self.assertEqual(self.cache.count, 2)
        self.assertEqual(self.cache.transaction_count, 0)

class SimpleUtilsTest(TestCase):
    ''' Tests for functions from the utils.simple module '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up dome dicts to test with '''
        cls.dict1 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test'}}
        cls.dict2 = {'test': {'count': 1, 'name': 'my test', 'number': 89.3}}
        cls.dict3 = {'test': {'count': 1, 'number': 89.3, 'name': 'my test 3'}}

    # dict_hash() tests
    def test_dict_hash_returns_correct_hash(self):
        """ dict_hash() should return c7a98aa3381012984c03edeaf7049096 when the input is self.dict1 """
        self.assertEqual('c7a98aa3381012984c03edeaf7049096', dict_hash(self.dict1))

    def test_dict_hash_returns_same_hash_with_different_order(self):
        """ dict_hash() should return the same hash when the input is the same except for the order of the elements """
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict2))

    def test_dict_hash_returns_same_hash_with_the_same_dict(self):
        """ dict_hash() should return the same hash when the input is the same """
        self.assertEqual(dict_hash(self.dict1), dict_hash(self.dict1))
    
    def test_dict_hash_returns_different_hash_with_the_different_dict(self):
        """ dict_hash() should return different hashes when the input is different """
        self.assertNotEqual(dict_hash(self.dict1), dict_hash(self.dict3))
    
    # Stringalization tests
    def test_stringalize_returns_a_string_when_given_an_int(self):
        """ stringalize() should return a string when given an int """
        self.assertEqual("1", stringalize(1))

    def test_stringalize_returns_a_string_when_given_a_string(self):
        """ stringalize() should return a string when given a string """
        self.assertEqual("string", stringalize("string"))

    def test_stringalize_returns_a_string_when_given_a_set(self):
        """ stringalize() should return a string when given a set """
        self.assertEqual("1, 2", stringalize({1, "2"}))

    def test_stringalize_returns_a_string_when_given_a_list(self):
        """ stringalize() should return a string when given a list """
        self.assertEqual("1, 2", stringalize(["1", 3-1]))

    def test_stringalize_returns_a_string_when_given_a_tuple(self):
        """ stringalize() should return a string when given a tuple """
        self.assertEqual("1, 2", stringalize((1, '2')))

    # List manipulation tests
    def test_mached_name_choices_should_return_doubled_list_of_tuples(self):
        """ mached_name_choices() should return a list that is composed of the members of the input list duplicated as a tuple """
        self.assertEqual([(1, 1), ("test", "test")], mached_name_choices([1, "test"]))

    # string formatting tests
    def test_split_by_caps_returns_list_of_words_split_by_capital_letters(self):
        """ split_by_caps() should return a list of words split by capital letters """
        self.assertEqual(split_by_caps('MyTest'), ['My', 'Test'])
    
    def test_split_by_caps_returns_a_one_item_list_when_given_a_string_with_no_caps(self):
        """ split_by_caps() should return a list of one word when given a string with no capital letters """
        self.assertEqual(split_by_caps("mytest"), ["mytest"])

    def test_fancy_name_returns_string_initial_caps_when_given_a_string(self):
        """ fancy_name() should return a string with initial caps when given a string """
        self.assertEqual("My Test!", fancy_name("my test!"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_string(self):
        """ fancy_name() should return a string with initial caps when given a string """
        self.assertEqual("My Test", fancy_name("my test"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_underscored_string(self):
        """ fancy_name() should return a string with initial caps when given an underscored string """
        self.assertEqual("My Test", fancy_name("my_test"))

    def test_fancy_name_returns_string_initial_caps_when_given_a_camelcased_string(self):
        """ fancy_name() should return a string with initial caps when given a CamelCased string """
        self.assertEqual("My Test", fancy_name("myTest"))

    def test_fancy_name_returns_string_with_capital_id(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) """
        self.assertEqual("My ID Test", fancy_name("my_id test"))

    def test_fancy_name_returns_string_with_capital_id_at_the_beginning_of_a_string(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) at the beginning of a string """
        self.assertEqual("ID My ID Test", fancy_name("Id my_id test"))

    def test_fancy_name_returns_string_with_capital_id_at_the_end_of_a_string(self):
        """ fancy_name should return the word ID as caps, instead of title case (Id) at the end of a string """
        self.assertEqual("My ID Test ID", fancy_name("my_id test_id"))

    def test_fancy_name_returns_capital_id_if_string_is_id(self):
        """ fancy_name() should return ID if the string is just id """
        self.assertEqual("ID", fancy_name("id"))

    # resolve_true tests
    def test_yes_resolves_to_true(self):
        """ resolve_true() should return False when given no, reguardless of case """
        self.assertEqual(resolve_true("Yes"), True)
        self.assertEqual(resolve_true("yes"), True)
        self.assertEqual(resolve_true("YeS"), True)

    def test_no_resolves_to_false(self):
        """ resolve_true() should return True when given yes, reguardless of case """
        self.assertEqual(resolve_true("no"), False)
        self.assertEqual(resolve_true("No"), False)
        self.assertEqual(resolve_true("nO"), False)

    def test_yes_resolves_to_true(self):
        """ resolve_true() should return False when given no, reguardless of case """
        self.assertEqual(resolve_true("true"), True)
        self.assertEqual(resolve_true("True"), True)
        self.assertEqual(resolve_true("trUe"), True)

    def test_no_resolves_to_false(self):
        """ resolve_true() should return True when given yes, reguardless of case """
        self.assertEqual(resolve_true("false"), False)
        self.assertEqual(resolve_true("False"), False)
        self.assertEqual(resolve_true("faLse"), False)

    def test_emptystring_resolves_to_false(self):
        """ resolve_true() should return False when given '' """
        self.assertEqual(resolve_true(""), False)

    def test_string0_resolves_to_false(self):
        """ resolve_true() should return False when given '0' """
        self.assertEqual(resolve_true("0"), False)

    def test_none_resolves_to_none(self):
        """ resolve_true() should return None when given None """
        self.assertEqual(resolve_true(None), None)

    # Deep exists tests
    def test_deep_exists_returns_false_with_no_dict(self):
        """ deep_exists() should return False when not given a dict """
        self.assertEqual(deep_exists(), False)

    def test_deep_exists_returns_false_with_no_list(self):
        """ deep_exists() should return False when not given a list """
        self.assertEqual(deep_exists(dictionary={"1": "3"}), False)

    def test_deep_exists_returns_false_if_a_key_doesnt_exist(self):
        """ deep_exists() should return False when a given key is not in the list """
        self.assertEqual(deep_exists(dictionary={"1": "3"}, keys=["7"]), False)

    def test_deep_exists_returns_false_if_dict_isnt_a_dict(self):
        """ deep_exists() should return False when dict isn't an actual dict """
        self.assertEqual(deep_exists(dictionary="cat", keys=["bob"]), False)

    def test_deep_exists_returns_false_if_keys_isnt_a_list(self):
        """ deep_exists() should return False when dict isn't an actual dict """
        self.assertEqual(deep_exists(dictionary={"cat": "test"}, keys="cat"), False)

    def test_deep_exists_returns_true_if_first_key_is_in_dict(self):
        """ deep_exists() should return True when key is in dict """
        self.assertEqual(deep_exists(dictionary={"cat": "test"}, keys=["cat"]), True)

    def test_deep_exists_returns_false_if_a_key_doesnt_exist_recursively(self):
        """ deep_exists() should return False when a given key is not in the list, recursively """
        self.assertEqual(deep_exists(dictionary={"1": {"3": "test"}}, keys=["1", "7"]), False)

    def test_deep_exists_returns_true_if_a_key_exists_recursively(self):
        """ deep_exists() should return True when a given key is not in the list, recursively """
        self.assertEqual(deep_exists(dictionary={"1": {"3": "test"}}, keys=["1", "3"]), True)

    def test_deep_exists_returns_true_if_a_key_exists_recursively_and_there_is_excess_dictionary(self):
        """ deep_exists() should return True when a given key is not in the list, recursively, and there is excess dictionary """
        self.assertEqual(deep_exists(dictionary={"1": {"3": {5: "test"}}}, keys=["1", "3"]), True)


class SoundUserNameTests(TestCase):
    ''' Tests for sound_user_name, a function that returns a good name for a user '''

    @classmethod
    def setUpTestData(cls):
        ''' Set up some users to test with '''

        cls.user1 = User(username='username')
        cls.user2 = User(username='username', first_name='first_name')
        cls.user3 = User(username='username', last_name='last_name')
        cls.user4 = User(username='username', first_name='first_name', last_name='last_name')

    def test_sound_user_name_with_only_username_returns_username(self):
        self.assertEqual(sound_user_name(self.user1), 'username')
    
    def test_sound_user_name_with_username_and_first_name_returns_first_name(self):
        self.assertEqual(sound_user_name(self.user2), 'first_name')
    
    def test_sound_user_name_with_username_and_last_name_returns_last_name(self):
        self.assertEqual(sound_user_name(self.user3), 'last_name')

    def test_sound_user_name_with_all_names_returns_first_name_last_name(self):
        self.assertEqual(sound_user_name(self.user4), 'first_name last_name')


@skipIf("Genome" not in settings.ML_IMPORT_WIZARD["Importers"], "Don't include template and view tests")
class TemplateAndViewTests(SimpleTestCase):
    ''' Test the templates/views in Import Wizard '''

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        ''' Set up whatever objects are going to be needed for all tests '''

        cls.user = User.objects.create(username='testuser')
        cls.user.set_password('12345')
        cls.user.save()

        # cls.import_scheme = ImportScheme(
        #     name = 'Test Importer', 
        #     user = cls.user, 
        #     importer = 'Genome',
        #     status = 0,
        # )
        # cls.import_scheme.save()
    
    def setUp(self):
        ''' Log in the user '''

        try:
            self.user = User.objects.get(username="testuser")
        except User.DoesNotExist:
            self.user = User.objects.create(username='testuser')
            self.user.set_password('12345')
            self.user.save()

        self.client.login(username=self.user.username, password='12345')


    def test_root_should_have_genome_and_integrations_items_and_template_is_manager(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as including the Imports from settings '''

        response = self.client.get("/import/")
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'ml_import_wizard/manager.html')
        self.assertContains(response, 'Genome')
        self.assertContains(response, 'integration')

    def test_genome_should_have_form_name_and_template_is_new_scheme(self):
        ''' Make sure we're getting a success status code and hitting the correct template, as well as getting a form. '''

        response = self.client.get("/import/Genome")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'ml_import_wizard/new_scheme.html')
        # self.assertContains(response, '<form class="form-horizontal"')

    def test_genome_post_should_result_in_new_ImportScheme_object_have_template_manager(self):
        ''' Use /import/Genome to add a genome import, test the return status, '''
        response = self.client.post("/import/Genome", data={'name': 'Test Importer from Page', 'description': 'testing'})

        import_scheme = ImportScheme.objects.filter(user_id=self.user.id).first()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(import_scheme.name, 'Test Importer from Page')

    # def test_genome_get_should_list_test_importer(self):
    #     ''' /import/Genome should have the importer we created in the previous test '''
        response = self.client.get("/import/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'ml_import_wizard/manager.html')
        self.assertContains(response, 'Test Importer from Page')