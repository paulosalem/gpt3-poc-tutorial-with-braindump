import openai
import os
import pandas as pd
import logging

class BraindumpEngine:
    """
    The main class of the braindump engine. It stores the database and application parameters, as well as
    coordinates the calls to GPT-3 model, leveraging the preprocessor and postprocessor. In this manner,
    it provides the capability both to insert facts into the database and to query the database.
    """

    def __init__(self, 
                 database_file_path="./data/default_database.csv",
                 categories_file_path="./data/default_categories.csv",
                 gpt3_engine = "text-davinci-003", gpt3_temperature=0.1,
                 default_categories=["Family", "Work", "Friends", "Shopping", "Health", 
                                     "Finance", "Travel", "Home", "Pets", "Hobbies", "Other"]):
        

        self._database_file_path = database_file_path
        self._categories_file_path = categories_file_path
        self._categories = default_categories

        # Load the database or create it from scratch if needed
        try:
            self.database = pd.read_csv(self._database_file_path)
            logging.info(f"Loaded database from {self._database_file_path}.")
        except FileNotFoundError:
            self.database = pd.DataFrame(columns=["Category", "Type", "People", "Key", "Value"])
            self._save()
            logging.info(f"Created database in {self._database_file_path}.")
        

        # Load the categories file or create it from scratch if needed
        try:
            df_categories = pd.read_csv(self._categories_file_path)
            self._categories = df_categories["Category"].tolist()
            logging.info(f"Loaded categories {self._categories} from {self._categories_file_path}.")
        except FileNotFoundError:
            self.database = pd.DataFrame(default_categories, columns=["Category"])
            self._save()
            logging.info(f"Created categories {self._categories} in {self._categories_file_path}.")


        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.gpt3_parameters = {"engine": gpt3_engine, "temperature": gpt3_temperature, 
                                "max_tokens":200, "top_p":1.0, "frequency_penalty":0.0, 
                                "presence_penalty":0.0, "stop":None}

        self._current_extracted_facts = None

        # Create preprocessor and postprocessor for GPT-3 inputs and outputs, respectivelly
        self._preprocessor = BraindumpPreprocessor()
        self._postprocessor = BraindumpPostprocessor()

    def _save(self):
        logging.info(f"Database has {len(self.database)} facts.")
        logging.info(f"Available categories are {self._categories}")
        
        self.database.to_csv(self._database_file_path, index=False)
        pd.DataFrame(self._categories, columns=["Category"]).to_csv(self._categories_file_path, index=False)

        logging.info(f"Saved database in {self._database_file_path}.")
        logging.info(f"Saved allowed categories in {self._categories_file_path}.")
        
    #####################################
    # Facts insertion workflow methods
    #####################################

    def extract_facts(self, facts_utterance):
        """
        Extracts facts from a natural language utterance. Returns a list of tuples (category, type, people, key, value).
        """
        fact_tuples = self._postprocessor.string_to_tuples(self._gpt3_complete(self._preprocessor.extraction_prompt(facts_utterance, self._categories)))
        self._current_extracted_facts = fact_tuples
        return fact_tuples
    
    def has_extracted_facts(self):
        return self._current_extracted_facts is not None
    
    def extracted_facts(self):
        """
        Returns the current extracted facts as a list of dictionaries, for readability.
        """
        return [{"Category": fact[0], "Type": fact[1], "People": fact[2], "Key": fact[3], "Value": fact[4]} 
                 for fact in self._current_extracted_facts]

    def commit(self):
        """
        Commits the current extracted facts to the database. If no facts have been extracted, the method
        just does nothing.
        """	
        if self._current_extracted_facts is not None:
            self._insert_facts()
            self._current_extracted_facts = None
            self._save()
        else:
            logging.info("Nothing to commit.")
    
    def cancel(self):
        """
        Cancel the current extracted facts. If no facts have been extracted, the method just does nothing.
        """	
        if self._current_extracted_facts is not None:
            self._current_extracted_facts = None
        else:
            logging.info("Nothing to revert.")

    def _insert_facts(self, facts_utterance = None):
        """
        Inserts a fact into the database.
        """

        # reuse the extracted facts, if any
        if self._current_extracted_facts is None:
            fact_tuples = self.extract_facts(facts_utterance)
        else:
            fact_tuples = self._current_extracted_facts

        for fact_tuple in fact_tuples:
            logging.info(f"Database has {len(self.database)} facts before insertion.")
            logging.info(f"Inserting fact: {fact_tuple}")
            
            df_to_add = pd.DataFrame([fact_tuple], columns=["Category", "Type", "People", "Key", "Value"])
            self.database = pd.concat([self.database, df_to_add], ignore_index=True)
            
            logging.info(f"Database has {len(self.database)} facts after insertion.")


    #####################################
    # Search workflow methods
    #####################################

    def query(self, fact_query, categories=None, entry_types=None, people=None, show_none_if_no_query=False, verbose=False):
        """
        Queries the database for a fact.
        """
        if len(fact_query) > 0 or show_none_if_no_query:
            raw_original_terms = self._gpt3_complete(self._preprocessor.terms_extraction_prompt(fact_query))
            original_terms = self._postprocessor.extract_lines_from_result(raw_original_terms)
            if verbose:
                print(original_terms)

            augmented_terms = []
            for original_term in original_terms:
                raw_augmented_terms = self._gpt3_complete(self._preprocessor.terms_augmentation_prompt(original_term))
                augmented_terms += self._postprocessor.extract_lines_from_result(raw_augmented_terms)
            if verbose:
                print(augmented_terms)
            
            return self._search_dataframe(self._database_filtered_by(categories, entry_types, people),
                                        original_terms, augmented_terms)
        else:
            return self._database_filtered_by(categories, entry_types, people)

    def _search_dataframe(self, df, original_terms, augmented_terms):
        """
        Searches the specified database for the specified terms.
        """
        df = df.fillna("") # for readability below
        all_terms = original_terms + augmented_terms

        df_results = None
        for column in df.columns:
            df_result = df[df[column].str.contains("|".join(all_terms), case=False).fillna(False)]
            if df_results is None:
                df_results = df_result
            else:
                df_results = pd.concat([df_results, df_result])
        
        return df_results


    def _database_filtered_by(self, categories=None, entry_types=None, people=None):
        df = self.database

        def aux_filter(df, column, values):
            if values is not None and len(values) > 0:
                return df[self.database[column].str.lower().isin([v.lower() for v in values])]
            else:
                return df
        
        df = aux_filter(df, "Category", categories)
        df = aux_filter(df, "Type", entry_types)
        df = aux_filter(df, "People", people)
        
        return df
    
    def unique_categories_in_database(self):
        return self.database["Category"].unique().tolist()
    
    def unique_entry_types_in_database(self):
        return self.database["Type"].unique().tolist()
        
    def unique_people_in_database(self):
        return self.database["People"].unique().tolist()

    ##########################
    # Categories management
    ##########################
    def allowed_categories(self):
        return self._categories

    def update_categories(self, new_categories):
        self._categories = new_categories
        self._save()
    
    #############
    # GPT-3 API
    #############
    def _gpt3_complete(self, prompt, echo=False):

        response = openai.Completion.create(
            engine=self.gpt3_parameters["engine"],
            prompt=prompt,
            temperature=self.gpt3_parameters["temperature"],
            max_tokens=self.gpt3_parameters["max_tokens"],
            top_p=self.gpt3_parameters["top_p"],
            frequency_penalty=self.gpt3_parameters["frequency_penalty"],
            presence_penalty=self.gpt3_parameters["presence_penalty"],
            stop=self.gpt3_parameters["stop"],
            echo=echo
        )

        completion = response['choices'][0]['text']

        return completion

    def set_openai_api_key(self, key):
        openai.api_key = key    

class BraindumpPreprocessor:
    """
    Preprocessor for the user input to GPT-3. Notably, includes the mechanisms to build prompts.
    """

    def extraction_prompt(self, x, categories):
        
        prompt =\
f"""
Extract pieces of personal information, like phone numbers, email addresses, names, trivia, reminders, etc., as tuples with the following format: (Category, Type, People, Key, Value)
Assume everything mentioned refers to the same thing. Constraints:
  - Allowed Categories: {', '.join(categories)}
  - Allowed Types: "List", "Email", "Phone", "Address", "Reminder", "Note", "Doubt", "Wish", "Other"
  - People contain the name or description of the people concerned, or is empty if irrelevant.
  
Example input: "Mom's phone number is 555-555-5555"
Example output: ("Family", "Phone", "mom", "mom's number", "555-555-5555")

Example input: "Need to do: lab work, ultrasound, buy aspirin"
Example output: 
("Health", "List", "", "to do", "lab work")
("Health", "List", "", "to do", "ultrasound")
("Shopping", "List", "", "aspirin", "buy")	

Input: {x}
Output: 

"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt 

    def terms_extraction_prompt(self, query):

        prompt = \
f"""
Extract the main entities (one per line) in the following sentence: "{query}"
"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt

    def terms_augmentation_prompt(self, terms):
        prompt = \
f"""
List some synonyms to the following terms: "{terms}"
Synonyms (one synonym per line):
"""
        logging.info(f"GPT-3 Prompt: {prompt}")
        return prompt
    

class BraindumpPostprocessor:
    """
    Postprocessor for the GPT-3 raw outputs.
    """

    def extract_lines_from_result(self, result):
        """
        Extracts the lines from the result string.
        """
        lines = [line for line in result.split('\n') if len(line) > 0]
        return lines

    def string_to_tuples(self, s):
        """"
        Converts a string that looks like a tuple to an actual Python tuple.
        """
        return [eval(s.strip()) for s in self.extract_lines_from_result(s)]
    
    def extract_terms_from_all_results(self, results):
        """
        Extracts the terms from the result string.
        """
        terms = []
        for result in results:
            terms.append(self.extract_lines_from_result(result))
        return terms