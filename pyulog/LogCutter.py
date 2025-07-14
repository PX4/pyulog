/****************************************************************************
 *
 *   Copyright (c) 2024 Applied Aeronautics. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/
/**
 * @AA-LogCutter.py
 * PX4 ULG Log File Splitter
 *
 * @author Ryan Johnston <rjohnston@AppliedAeronautics.com>
 */



import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import struct

def read_ulog_header_and_definitions(file_path):
    try:
        print(f"Reading ULog header and definitions from {file_path}")
        with open(file_path, 'rb') as f:
            magic_bytes = f.read(8)
            print(f"Magic bytes: {magic_bytes}")
            if magic_bytes != b'\x55\x4c\x6f\x67\x01\x12\x35\x01':
                raise ValueError("Invalid ULog file format.")

            version = f.read(1)
            timestamp = f.read(8)
            print(f"Version: {version}, Timestamp: {timestamp}")

            header_length_bytes = f.read(2)
            header_length = struct.unpack('<H', header_length_bytes)[0]
            print(f"Header length: {header_length}")

            remaining_header_length = header_length - 17
            header_messages = f.read(remaining_header_length)
            print(f"Read {remaining_header_length} bytes of header messages")

            full_header = magic_bytes + version + timestamp + header_length_bytes + header_messages

            definitions = b''
            while True:
                msg_header = f.read(3)
                if not msg_header:
                    print("End of file reached unexpectedly while reading definitions.")
                    break

                msg_size = struct.unpack('<H', msg_header[:2])[0]
                msg_type = msg_header[2:3]

                message_data = f.read(msg_size)
                definitions += msg_header + message_data
                print(f"Read message type: {msg_type}, size: {msg_size}")

                if msg_type == b'D':
                    print("Reached the start of the data section.")
                    break

            rest_of_file = f.read()
            print(f"Read {len(rest_of_file)} bytes of data section.")

        return full_header, definitions, rest_of_file

    except Exception as e:
        print(f"Error reading ULog header and definitions: {e}")
        raise


def cut_file(file_path, percentage, save_path):
    try:
        print(f"Cutting file {file_path} at {percentage}% and saving to {save_path}")
        
        header, definitions, rest_of_file = read_ulog_header_and_definitions(file_path)
        data_section = rest_of_file

        data_size = len(data_section)
        cut_size = int(data_size * (percentage / 100.0))
        print(f"Data size: {data_size}, Cut size: {cut_size}")

        part1_data = data_section[:cut_size]
        part2_data = data_section[cut_size:]

        save_part1_path = f"{save_path}_part1.ulg"
        print(f"Saving first part to {save_part1_path}")
        with open(save_part1_path, 'wb') as f:
            f.write(header + definitions + part1_data)
        print(f"Saved first part successfully.")

        if part2_data:
            save_part2_path = f"{save_path}_part2.ulg"
            print(f"Saving second part to {save_part2_path}")
            with open(save_part2_path, 'wb') as f:
                f.write(header + definitions + part2_data)
            print(f"Saved second part successfully.")
            messagebox.showinfo("Success", f"Files saved:\n{save_part1_path}\n{save_part2_path}")
        else:
            messagebox.showinfo("Success", f"File saved:\n{save_part1_path}")

    except Exception as e:
        print(f"Error cutting file: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


def ask_percentage():
    percentage = simpledialog.askfloat("Cut Percentage", "Enter the percentage to cut the file at (0-100):", minvalue=0, maxvalue=100)
    print(f"User entered percentage: {percentage}")
    return percentage


def save_file():
    save_path = filedialog.asksaveasfilename(defaultextension=".ulg", filetypes=[("PX4 Log Files", "*.ulg"), ("All Files", "*.*")])
    print(f"User selected save path: {save_path}")
    return save_path


def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PX4 Log Files", "*.ulg"), ("All Files", "*.*")])
    print(f"User selected file: {file_path}")
    
    if file_path:
        percentage = ask_percentage()
        if percentage is not None:
            save_path = save_file()
            if save_path:
                cut_file(file_path, percentage, save_path)
            else:
                messagebox.showwarning("No Save Path", "No save path selected. Operation cancelled.")
        else:
            messagebox.showwarning("No Percentage", "No percentage entered. Operation cancelled.")
    else:
        messagebox.showwarning("No File Selected", "No file selected. Operation cancelled.")


def create_app():
    root = tk.Tk()
    root.title("PX4 Log Cutter")

    open_button = tk.Button(root, text="Open PX4 Log File", command=select_file)
    open_button.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    create_app()
