import de_kba_datagrabber as kba
import subprocess
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import glob
import os

updated_data = []
""" A list of strings that, if they appear in a notebook, will trigger a re-run of the notebook """



##### Update all datasources

# update kba data
kba.ensure_up_to_date(True)

# Get modified files from git
git_output = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD']).decode('utf-8')
modified_files = git_output.splitlines()

# If any of the kba FZ28 files have been updated, all notebooks using functions with fz28 in the name should be updated
if any(file.startswith('data/de-kba/fz28') for file in modified_files):
    updated_data.append('fz28')

print(f'Updated data: {updated_data}')



##### Re-run all notebooks that use updated data

if updated_data:
    notebooks = glob.glob('**/*.ipynb', recursive=True)
    for notebook_path in notebooks:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb_content = f.read()

            # Check if notebook uses updated data
            if any(data in nb_content for data in updated_data):
                print(f'Re-running notebook: {notebook_path}')
                try:
                    # Load and execute notebook
                    f.seek(0)
                    nb = nbformat.read(f, as_version=4)
                    ep = ExecutePreprocessor(timeout=600, allow_errors=True)
                    ep.preprocess(nb, {'metadata': {'path': os.path.dirname(notebook_path)}})

                    # Save executed notebook
                    # Note that this does not work if you run it directly in PyCharm because PyCharm steals the output plots and they wont get written to the resulting file anymore.
                    # Thus, this needs to be run from the command line.
                    with open(notebook_path, 'w', encoding='utf-8') as f:
                        nbformat.write(nb, f)
                except Exception as e:
                    print(f'Error executing {notebook_path}: {e}')
