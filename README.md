This Flask-based Python web application is designed to handle the uploading, processing (auto converting images of voter list to xlsx), and downloading of PDF files. Here's an explanation of its main purposes and features:

### 1. **User Session Management**
   - The app uses sessions to store user-specific data (e.g., username) to maintain state across requests. This is done using the Flask `Session` module.

### 2. **File Upload and Processing**
   - The app allows users to upload either a single PDF file or a ZIP file containing multiple PDFs.
   - After upload, the files are processed based on user input, such as language (`Marathi` or `English`) and format (1 or 2). These correspond to predefined processing functions imported from separate modules.
   - The uploaded files are first validated for type (PDF or ZIP).
   - If the uploaded file is a ZIP, it is extracted, and each PDF inside is processed individually.
   - The PDF processing occurs using the following functions:
     - For Marathi: `do_marathi`, `do_marathi_format2`
     - For English: `do_english`, `do_english_format2`
   - These functions likely perform text extraction or formatting tasks specific to the selected language and format.

### 3. **Post-Processing and File Conversion**
   - After processing the PDFs, the results are stored in JSON format, and in case of single PDF uploads, post-processing occurs, where an Excel file (`.xlsx`) is generated.
   - The processed files (e.g., JSON, XLSX) are then made available for download.

### 4. **File Cleanup**
   - The app ensures that uploaded files and processed results are cleaned up after they are used:
     - Uploaded files are removed after processing.
     - Processed results are deleted after a set delay (5 seconds), using a separate thread.

### 5. **Socket Communication**
   - Socket communication is used to provide real-time updates to users. The app emits socket messages at various stages (e.g., upon connection, disconnection, or during the processing of files).
   - This allows the application to inform the user in real-time about the status of file processing.

### 6. **Download Process**
   - Once files are processed, the user can download the result (either a ZIP or Excel file) via a generated download URL.
   - If the file no longer exists (due to deletion), the user is notified that the file has already been downloaded or doesn't exist.

### 7. **Multi-language PDF Processing**
   - The app processes PDFs in two languages (Marathi and English) using different formats. This flexibility supports customized handling of documents depending on the language and format selected by the user.

### 8. **Error Handling and Feedback**
   - The app has a simple error-handling mechanism that notifies users when an error is encountered during file processing using socket messages.
   - Additionally, errors during file upload or processing result in rendering an error page.

### 9. **Stopping the Server**
   - There's an endpoint (`/stop`) to stop the server, which returns a message indicating the server will stop (though the actual stopping of the server is not implemented).

### 10. **Template Usage**
   - The app uses HTML templates (likely `upload.html` and `success.html`) to display the upload form and success/download messages after processing.

### 11. **Threading**
   - The app uses threading for tasks like deleting files after a delay to avoid blocking the main process.

### Key Imports and External Dependencies:
- **Flask**: Used for routing, sessions, and serving the app.
- **SocketIO**: For real-time communication.
- **Werkzeug**: To secure filenames.
- **Zipfile**: To handle ZIP file extraction.
- **Tempfile**: To manage temporary directories for unzipping and processing files.

### Potential Use Cases:
- Automating the extraction and formatting of text or data from PDFs based on specific languages and formats.
- Batch processing of multiple PDFs in a ZIP file.
- Providing a downloadable result, which could be useful for users needing reports, formatted text, or other structured outputs from PDFs.

### Installation
pip install -r requirements.txt

### Get started
python app.py
