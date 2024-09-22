"""
Reformat the graph to create an edge list with int ID nodes seperated by tab
"""

import pandas as pd
import os


# for graphs exported from Communalytic that has node ID like "n132", removing the n
def remove_n_from_file(file_path: str):
    try:
        # Ensure the file path is valid and the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        # Construct the output file path
        fixed_file_path = os.path.join(
            os.path.dirname(file_path), "fixed_" + os.path.basename(file_path)
        )

        # Read from the input file and write to the output file
        with open(file_path, "r") as infile, open(fixed_file_path, "w") as outfile:
            temp = infile.read().replace("n", "")
            outfile.write(temp)

        print(f"File processed successfully. The fixed file is saved as {fixed_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


# convert the csv to tsv (tab seperated values)
def csv2tsv(file_name: str, directory: str = "."):
    # Read the CSV file without specifying column names
    df = pd.read_csv(os.path.join(directory, file_name))

    # Drop unwanted columns
    df = df.drop(columns=["~id", "~label"])

    df.to_csv(file_name, sep="\t", index=False, header=False)
    print(f"Converted {file_name} to TSV, removing n from node IDs...")
    remove_n_from_file(file_name)
    print(f"Done removing n from node IDs for {file_name}.")



if __name__ == "__main__":
    # first, convert all graphs generated from graph_tool to csv edge list
    os.system("python graphml2csv.py -i price_10000nodes.graphml")
    os.system("python graphml2csv.py -i price_1000000nodes.graphml")
    os.system("python graphml2csv.py -i blockmodel_200000nodes_100blocks.graphml")
    os.system("python graphml2csv.py -i complete_30000nodes.graphml")
    os.system("python graphml2csv.py -i dolphins.graphml")
    os.system("python graphml2csv.py -i email-Enron.graphml")
    os.system("python graphml2csv.py -i polblogs.graphml")

    # convert the csv to tsv
    csv2tsv("price_10000nodes-edges.csv")
    csv2tsv("price_1000000nodes-edges.csv")
    csv2tsv("blockmodel_200000nodes_100blocks-edges.csv")
    csv2tsv("complete_30000nodes-edges.csv")
    csv2tsv("dolphins-edges.csv")
    csv2tsv("email-Enron-edges.csv")
    csv2tsv("polblogs-edges.csv")
