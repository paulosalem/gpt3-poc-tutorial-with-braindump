import pytest
import os

import sys
sys.path.append('../../src/gpt-3')
from engine import BraindumpEngine

API_KEY = os.getenv("PERSONAL_OPENAI_API_KEY")
TEST_CATEGORIES = ["Family", "Work", "Friends", "Shopping", "Health", "Finance", "Travel", "Home", "Pets", "Hobbies", "Other"]

############################################################################################################
# Tests
############################################################################################################
def test_work():
    # Each NL utterance is mapped into the expected values.
    nl_utterances = [("sales guy email = jp@example.com", [('Work', 'Email', 'sales guy', 'email', 'jp@example.com')]),
                     ("my employee number is 12345678", [('Work', 'Document', '', 'employee number', '12345678')])
                    ]

    extract_and_check_all(nl_utterances)

def test_shopping_lists():
    # Each NL utterance is mapped into the expected values.
    nl_utterances = [("I need to buy milk, eggs, and bread", [('Shopping', 'List', '', 'milk', 'buy'), 
                                                              ('Shopping', 'List', '', 'eggs', 'buy'), 
                                                              ('Shopping', 'List', '', 'bread', 'buy')]),
                     ("Buy: diapers, baby cream, cotton", [('Shopping', 'List', '', 'diapers', 'buy'), 
                                                           ('Shopping', 'List', '', 'baby cream', 'buy'), 
                                                           ('Shopping', 'List', '', 'cotton', 'buy')])]

    extract_and_check_all(nl_utterances)

def test_ambiguous_travel():
    # Each NL utterance is mapped into the expected values.
    # But let's specify some valid potential ambiguities regarding travel utterances.
    # An ambiguous field is a field that can have multiple valid extractions. For example, the Category field can be either 
    # 'Travel' or 'Work', it can be specified as ['Travel', 'Work']. Se examples below.
    nl_utterances = [("remember to buy plane tickets to meet customer", [(['Travel', 'Work'], 'Reminder', 'customer', 'plane tickets', 'buy')]),
                     ("in jen's free time she told me she likes to travel", [(['Travel', 'Hobbies', 'Friends'], ['List', 'Note'], 'jen', ['free time', 'travel', 'hobbies'], ['travel', 'likes'])])
                    ]
    extract_and_check_all(nl_utterances)
        
############################################################################################################
# Helper functions
############################################################################################################

def extract_and_check_all(nl_utterances, max_attempts=10):
    """
    Helper function to extract facts from a list of natural language utterances and check if the
    extracted facts match the ground truth. Owing to the non-deterministic nature of the underlying
    NLP engine, the function will try to extract the facts up to `max_attempts` times before failing.
    """
    for nl_utterance, truth in nl_utterances:
        extract_and_check(nl_utterance, truth, max_attempts)

def extract_and_check(nl_utterance, truth, max_attempts):
    """
    Checks one specific NL extraction against the desired ground truth.
    """
    assert max_attempts > 0, "The maximum number of attempts must be greater than 0."
    try:
        engine = BraindumpEngine(default_categories=TEST_CATEGORIES, api_key=API_KEY)
        extracted_tuples = engine.extract_facts(nl_utterance)
        
        print("")
        print(f"NL UTTERANCE: {nl_utterance}")
        print(f"EXTRACTED: {extracted_tuples}")
        print("")

        # for each extracted tuple...
        for i in range(0, len(extracted_tuples)):
            extracted_tuple = extracted_tuples[i]
            expected_tuple_values = truth[i]
            # ... check each of its positions against ground truth
            for j in range(0, len(extracted_tuple)):
                must_be_expected_extraction(extracted_tuple[j], expected_tuple_values[j])
                
    except Exception as e:
        # if the test fails, try again up to `max_attempts` times
        if max_attempts > 1:
            print("Failed, but will retry...")
            extract_and_check(nl_utterance, truth, max_attempts-1)
        else:
            print("Failed too many times, giving up.")
            raise e

def must_be_expected_extraction(extracted_field, ground_truth):
    """
    Helper function to test if a valid element has been extracted. The given ground truth can
    be either a string or a list of valid strings, in which case the function will check if any
    of the valid strings is present in the extraction.
    """
    # normalize inputs
    extracted_field = extracted_field.strip().lower()
    if type(ground_truth) is not list:
        ground_truth = [ground_truth]
    
    expected_value_found = None
    for a_valid_option in ground_truth:
        # look for the normalized ground truth in the normalized extracted field (in full or in part)
        a_valid_option = a_valid_option.strip().lower()
        if a_valid_option in extracted_field:
            expected_value_found = a_valid_option
            break
    
    # something must have been found, otherwise the test breaks
    assert expected_value_found in extracted_field, f"The extracted value {extracted_field} does not match any of the ground truth values in {ground_truth}."