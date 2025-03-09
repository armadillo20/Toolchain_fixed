import csv
import os

def read_csv():
    with open('./execution_traces/file.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            print(row)  # Ogni 'row' è una lista di valori


def write_csv():
    cartella = './execution_traces_results'
    file_csv = os.path.join(cartella, 'file_results.csv')

    # Crea la cartella se non esiste
    os.makedirs(cartella, exist_ok=True)  # 'exist_ok=True' evita errori se la cartella esiste già

    # Scrivi il file CSV nella cartella
    with open(file_csv, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['Alice', 30, 'Roma'])