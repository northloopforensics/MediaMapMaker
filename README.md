# MapMediaViewer

An interactive map application that visualizes media files (images/videos) and location data with timeline navigation and accuracy visualization.

## Features

- 📍 Interactive map with clustered markers
- 🖼️ Image and video media integration
- 📅 Timeline view with chronological sorting
- 🎯 GPS accuracy circle visualization (optional)
- 🔍 Filter by media type and time range
- 🔎 Search functionality for markers
- 📊 Supports CSV data import (including MasterMapData.csv)
- 💻 Standalone executable - no installation required

## Files

### Core Application Files
- **`map_viewer.py`** - Main executable server that displays the map
- **`csv_to_map.py`** - Map generator that converts CSV data to interactive HTML
- **`media_server.py`** - HTTP server for serving media files (port 8001)
- **`build_quick.py`** - Build script to compile the standalone executable

### Supporting Files
- **`map_icon.ico`** - Application icon
- **`media_markers_template.csv`** - Template for media marker CSV format

## Requirements

- Python 3.10+
- Required packages:
  - folium==0.19.5
  - pandas
  - pillow
  - pyinstaller==6.16.0

## Usage

### Option 1: Generate and View Map Directly

1. Place your CSV files in the workspace:
   - `media_markers_import.csv` - Your media markers
   - `MasterMapData.csv` - Event/location data

2. Run the map generator:
   ```bash
   python csv_to_map.py
   ```

3. The map will open automatically in your browser at `http://localhost:8001`

### Option 2: Build Standalone Executable

1. Generate the map HTML:
   ```bash
   python csv_to_map.py
   ```

2. Build the executable:
   ```bash
   python build_quick.py
   ```

3. The executable will be created at `dist/MapMediaViewer.exe`

4. To use the executable:
   - Place `MapMediaViewer.exe` in a folder
   - Place your `Media` folder in the same directory
   - Run the executable - the map will open in your browser

## CSV Data Format

### media_markers_import.csv
Required columns:
- `Address` - Location description
- `latitude` - Latitude coordinate
- `longitude` - Longitude coordinate
- `title` - Marker title
- `description` - Marker description
- `media_path` - Path to media file (relative to Media folder)
- `icon` - Icon type (camera, video, location, etc.)
- `color` - Marker color (red, blue, green, etc.)
- `date` - Date in YYYY-MM-DD format
- `time` - Time in HH:MM:SS format

### MasterMapData.csv
Required columns:
- `Latitude` - Latitude coordinate
- `Longitude` - Longitude coordinate
- `Accuracy` - GPS accuracy in meters (for circle visualization)
- `Date/Time` - Timestamp
- `Icon` - Icon type
- Additional columns for marker details

## Features Details

### Accuracy Circles
- Semi-transparent circles showing GPS accuracy zones
- Color-matched to marker types:
  - Light green: ATT Location
  - Orange: Ankle Monitor
- Can be enabled/disabled by modifying code

### Timeline Navigation
- Click timeline entries to navigate to markers
- Automatically opens marker popups
- Chronologically sorted entries
- Grouped by date

### Marker Clustering
- Automatic clustering at zoom levels
- Separate clusters for:
  - Images
  - Videos
  - ATT Location markers
  - Ankle Monitor markers

### Filtering
- Filter by media type (images/videos)
- Filter by event type (ATT/Ankle Monitor)
- Time range filtering with date pickers
- Search by title/description




