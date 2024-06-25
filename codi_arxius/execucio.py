import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def run_notebook(notebook_path, output_path):
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
    except Exception as e:
        print(f"Error al ejecutar el notebook: {e}")

    with open(output_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

if __name__ == "__main__":
    notebook_path = 'prac2_visualitzacio.ipynb' 
    output_path = 'executat.ipynb'
    run_notebook(notebook_path, output_path)

