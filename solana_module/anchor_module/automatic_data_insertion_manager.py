# MIT License
#
# Copyright (c) 2025 Manuel Boi - Università degli Studi di Cagliari
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import csv
import os
from solana_module.anchor_module.utils import anchor_base_path

def read_csv():
    with open(f'{anchor_base_path}/execution_traces/file.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            print(row)  # Ogni 'row' è una lista di valori


def write_csv():
    cartella = f'{anchor_base_path}/execution_traces_results'
    file_csv = os.path.join(cartella, 'file_results.csv')

    # Crea la cartella se non esiste
    os.makedirs(cartella, exist_ok=True)  # 'exist_ok=True' evita errori se la cartella esiste già

    # Scrivi il file CSV nella cartella
    with open(file_csv, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['Alice', 30, 'Roma'])