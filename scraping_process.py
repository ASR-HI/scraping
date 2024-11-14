import subprocess

query_terms = ["devops","Multimodal llm","llm","blockchain"]
scripts = ["sciencedirectScraping.py"]
processes = []

for query in query_terms:
    for script in scripts:
        command = f"python {script} --query \"{query}\""
        process = subprocess.Popen(command, shell=True)
        processes.append(process)

for process in processes:
    process.wait()
