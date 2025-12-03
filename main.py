from fastapi import FastAPI, Request,Body
from typing import Annotated
from datetime import datetime
import zlib
import zipfile
import uvicorn
import io
import os
import configparser

config = configparser.ConfigParser()
config['CRASH_REPORTER'] = {
    'HOST': '0.0.0.0',
    'PORT': '8000',
    'REPORT_DIR': './'
}
if not os.path.exists("./config.ini"):
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
else:
    config.read('./config.ini')

app = FastAPI()

@app.post("/report")
async def crash_report(UserID : str,compressed : Annotated[bytes, Body()]):
    crash_data = zlib.decompress(compressed);
    
    data_size = len(crash_data)

    if data_size < 3:
        return

    time_now = datetime.now()
    zip_filename = time_now.strftime("%Y-%m-%d")
    
    buffer = io.BytesIO(crash_data)
    crash_files = {}
    
    while buffer.tell() < data_size:
        current_pos = buffer.tell()
    
        if buffer.read(3) == b'CR1':
            crash_data_dir_length = int.from_bytes(buffer.read(4),byteorder='little')
            crash_data_dir = buffer.read(crash_data_dir_length).decode("ansi")
           
            crash_data_filename_length = int.from_bytes(buffer.read(4),byteorder='little')
            crash_data_filename = buffer.read(crash_data_filename_length).decode("ansi")
            
            crash_data_uncompressed_size = int.from_bytes(buffer.read(4),byteorder='little')
            crash_data_file_count = int.from_bytes(buffer.read(4),byteorder='little')
            
            if crash_data_uncompressed_size != data_size:
                return #invalid

            zip_filename = crash_data_dir
        else:
            buffer.seek(current_pos)

        file_index = int.from_bytes(buffer.read(4),byteorder='little')
        filename_length = int.from_bytes(buffer.read(4),byteorder='little')
        filename = buffer.read(filename_length).decode("ansi")

        file_data_length = int.from_bytes(buffer.read(4),byteorder='little')
        crash_files[filename] = buffer.read(file_data_length)


    zip_filename = zip_filename.replace('\0','')


    zip_path = f"{config["CRASH_REPORTER"]["REPORT_DIR"]}/{zip_filename}.zip"
    retry_index = 0
    while os.path.exists(zip_path):
        retry_index += 1
        zip_path = f"{config["CRASH_REPORTER"]["REPORT_DIR"]}/{zip_filename}_{retry_index}.zip"
        
    with zipfile.ZipFile(zip_path, 'w') as crash_zip:
        for out_filename, out_data in crash_files.items():
            crash_zip.writestr(out_filename,out_data)

    print(f"Crash saved to {zip_path}")

    

if __name__ == "__main__":

    if not os.path.exists(config["CRASH_REPORTER"]["REPORT_DIR"]):
        os.makedirs(config["CRASH_REPORTER"]["REPORT_DIR"])

    uvicorn.run(app, host=config["CRASH_REPORTER"]["HOST"], port=int(config["CRASH_REPORTER"]["PORT"]))