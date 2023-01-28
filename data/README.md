# Braindump
Braindump is a prototype application for taking notes and converting them to a database that can be more easily queried later. It was built as a demo to show how to leverage GPT-3 to build Natural Language Proofs-of-Concept, as described in [my Data Science @ Microsoft blog article](xxxxxxxxxxxxxxxx).

It is a simple Python application that leverages [Streamlit](https://streamlit.io/) to provide a web interface. To actually call the GPT-3 model, you need to have a working [OpenAI API](https://openai.com/api/) key. 

## Project Structure

The project is structured as follows:
  - `notebooks/`: contains Jupyter notebooks used for prompt engineering.
  - `src/`: contains the source code for the final application.
  - `data/`: contains the data stored by the application.

## Running the Application

To run the application:

  1. Install the dependencies listed in `requirements.txt`. You can do this by running `pip install -r requirements.txt` from the root of the project. 
  2. Obtain you need to have a working [OpenAI API](https://openai.com/api/) key and make it available as an environment variable called `OPENAI_API_KEY`.
  3. Finally, launch the application with `run.sh` (on Linux) or `run.bat` (on Windows) from the root of the project.


## License

MIT License

Copyright (c) 2023 Paulo Salem da Silva

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.