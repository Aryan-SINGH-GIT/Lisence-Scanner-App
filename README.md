# License Scanner Webapp

A Django-based web application for scanning source code archives and detecting open source licenses. This tool helps developers and organizations identify license compliance issues in their codebases.

## 🚀 Features

- **File Upload**: Upload zip, tar, or tar.gz archives containing source code
- **License Detection**: Automatically detect licenses using ScanCode toolkit
- **Comprehensive Reports**: View detailed license reports with confidence scores
- **Filtering & Sorting**: Filter results by license type, file extension, and confidence level
- **Export Functionality**: Download reports as CSV files
- **Real-time Status**: Track scanning progress with AJAX updates
- **Modern UI**: Clean, responsive interface built with Bootstrap

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite (development), PostgreSQL (production ready)
- **License Detection**: ScanCode toolkit
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Deployment**: Vercel-ready with custom build script

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/scanner-webapp.git
   cd scanner-webapp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```
   3. **Install dependencies**
   ```bash
   pip install django
   pip install scancode-toolkit
   pip install requests
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

## 📁 Project Structure

```
scanner-webapp/
├── scanner/                 # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── forms.py            # Django forms
│   ├── utils.py            # License scanning utilities
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Admin interface
│   └── migrations/         # Database migrations
├── license_scanner/        # Django project settings
│   ├── settings.py         # Main settings
│   ├── settings_vercel.py  # Vercel deployment settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User uploaded files
├── manage.py               # Django management script
├── build.py                # Vercel build script
└── README.md               # This file
```

## 🎯 Usage

### Basic Workflow

1. **Upload Archive**: Navigate to the home page and upload a zip, tar, or tar.gz file containing source code
2. **Automatic Scanning**: The system automatically extracts and scans the files for license information
3. **View Results**: Browse the comprehensive report showing detected licenses, confidence scores, and file details
4. **Filter & Export**: Use filters to narrow down results and export reports as CSV

### Supported File Types

- **Archives**: `.zip`, `.tar`, `.tar.gz`, `.tgz`
- **Source Code**: Python, JavaScript, Java, C/C++, Go, Rust, and many more
- **License Files**: LICENSE, COPYING, README files
### Scan Options

- **Recursive Scanning**: Scan all subdirectories
- **Binary Files**: Option to include binary files (may slow processing)
- **File Type Filtering**: Scan all files, code files only, or custom extensions
- **Confidence Threshold**: Set minimum confidence level for license detection

## 🔍 API Endpointsv

- `GET /` - Home page with upload form
- `GET /report/<upload_id>/` - View scan results
- `GET /api/status/<upload_id>/` - Check scan status (AJAX)
- `GET /download/<upload_id>/` - Download report as CSV
- `GET /license-info/` - Licese information page

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

## 📊 Database Models

### Upload Model
- Stores information about uploaded files
- Tracks processing status and metadata
- Uses UUID for secure file identification

### LicenseReport Model
- Stores individual file scan results
- Includes license detection confidence scores
- Links to original upload for report generation

### LicenseType Model
- Predefined license types and descriptions
- Used for license information pages

## 🔧 Configuration

### Settings Files

- `settings.py` - Development settings
- `settings_vercel.py` - Production settings for Vercel
- `settings_backup.py` - Backup configuration

### Customization

You can customize the scanner by modifying:

- **File Extensions**: Edit `scannable_extensions` in `utils.py`
- **License Files**: Modify `license_files` list in `utils.py`
- **UI Styling**: Update templates and static files
- **Scan Options**: Modify `ScanOptionsForm` in `forms.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/scanner-webapp/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

## 🙏 Acknowledgments

- [ScanCode Toolkit](https://github.com/nexB/scancode-toolkit) for license detection
- [Django](https://www.djangoproject.com/) web framework
- [Bootstrap](https://getbootstrap.com/) for UI components

**Made with ❤️ for the open source community**
 
