import pytest

import sys
sys.path.append('../src/')
from engine import BraindumpEngine

all_categories = ["Family", "Work", "Friends", "Shopping", "Health", "Finance", "Travel", "Home", "Pets", "Hobbies", "Reminders",
                      "Ideas", "Email", "Phone", "Address", "Other"]
default_categories = ["Family", "Work", "Friends", "Shopping", "Ideas", "Health", "Other"]

def test_shopping_lists():

    engine = BraindumpEngine(default_categories=default_categories)
    nl_utterances = [("I need to buy milk, eggs, and bread", [('Shopping', 'List', '', 'milk', 'buy'), 
                                                              ('Shopping', 'List', '', 'eggs', 'buy'), 
                                                              ('Shopping', 'List', '', 'bread', 'buy')]),
                     ("Buy: diapers, baby cream, cotton", [('Shopping', 'List', '', 'diapers', 'buy'), 
                                                           ('Shopping', 'List', '', 'baby cream', 'buy'), 
                                                           ('Shopping', 'List', '', 'cotton', 'buy')])]

    for nl_utterance, truth in nl_utterances:
        extraction = engine.extract_facts(nl_utterance)
        assert extraction == truth
        
        print("")
        print(f"NL UTTERANCE: {nl_utterance}")
        print(f"EXTRACTED: {extraction}")
        print("")
        
