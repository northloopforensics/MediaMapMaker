"""
CSV/XLSX to Interactive HTML Map Generator
Creates standalone HTML maps with media support via local web server
"""

import pandas as pd
from pathlib import Path
import folium
from folium import IFrame
from folium.plugins import MarkerCluster
import json
import base64
from urllib.parse import quote
import webbrowser
import sys
import os

# Handle PyInstaller bundled resources
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def add_sidebar_to_html(html_file, df, date_col='date', time_col='time'):
    """
    Add a collapsible sidebar with file tree organized chronologically by datetime.
    """
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Sort dataframe by datetime column for chronological order
    df_sorted = df.copy()
    if 'datetime' in df_sorted.columns:
        df_sorted['datetime'] = pd.to_datetime(df_sorted['datetime'], errors='coerce')
        df_sorted = df_sorted.sort_values('datetime')
    
    # Organize data chronologically
    from collections import defaultdict, OrderedDict
    tree = OrderedDict()
    
    for idx, row in df_sorted.iterrows():
        date = str(row.get(date_col, 'Unknown Date')) if date_col in row.index else 'Unknown Date'
        
        # Extract time from datetime column if available
        datetime_val = row.get('datetime', '') if 'datetime' in row.index else ''
        if pd.notna(datetime_val) and datetime_val != '':
            try:
                dt = pd.to_datetime(datetime_val)
                time = dt.strftime('%H:%M:%S')  # Extract time component
                date = dt.strftime('%Y-%m-%d')  # Use consistent date format
            except:
                time = str(row.get(time_col, '')) if time_col in row.index else ''
        else:
            time = str(row.get(time_col, '')) if time_col in row.index else ''
        
        title = str(row.get('title', 'Untitled'))
        media_path = str(row.get('media_path', ''))
        lat = row.get('latitude', 0)
        lon = row.get('longitude', 0)
        data_source = str(row.get('data_source', 'MediaMarkers'))
        
        if date and date != 'nan':
            if date not in tree:
                tree[date] = OrderedDict()
            if time not in tree[date]:
                tree[date][time] = []
            
            tree[date][time].append({
                'title': title,
                'path': media_path,
                'lat': lat,
                'lon': lon,
                'idx': idx,
                'datetime': str(datetime_val) if pd.notna(datetime_val) else '',
                'data_source': data_source
            })
    
    # Dates are already in chronological order from sorted dataframe
    sorted_dates = list(tree.keys())
    
    # Build sidebar HTML with professional styling
    sidebar_html = """
<style>
    #sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 380px;
        height: 100vh;
        background: #ffffff;
        box-shadow: 3px 0 10px rgba(0,0,0,0.15);
        overflow-y: auto;
        z-index: 1000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        transition: transform 0.3s ease-in-out;
    }
    
    #sidebar.collapsed {
        transform: translateX(-380px);
    }
    
    #sidebar-toggle {
        position: fixed;
        top: 10px;
        left: 390px;
        z-index: 1001;
        background: #ffffff;
        border: none;
        padding: 10px 14px;
        cursor: pointer;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: left 0.3s ease-in-out;
        font-size: 18px;
        color: #2c3e50;
    }
    
    #sidebar-toggle:hover {
        background: #f8f9fa;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    
    #sidebar.collapsed + #sidebar-toggle {
        left: 10px;
    }
    
    #sidebar-header {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 20px;
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    #sidebar-content {
        padding: 15px;
    }
    
    .filter-controls {
        background: linear-gradient(to bottom, #f8f9fa, #ffffff);
        padding: 18px;
        margin: 0 0 15px 0;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .filter-controls h4 {
        margin: 0 0 12px 0;
        font-size: 15px;
        font-weight: 600;
        color: #2c3e50;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .filter-option {
        display: flex;
        align-items: center;
        margin: 10px 0;
        padding: 8px 10px;
        background: white;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e1e4e8;
    }
    
    .filter-option:hover {
        background: #f6f8fa;
        border-color: #cbd2d9;
    }
    
    .filter-option input[type="checkbox"],
    .filter-option input[type="radio"] {
        width: 20px;
        height: 20px;
        margin-right: 10px;
        cursor: pointer;
        accent-color: #4a5568;
    }
    
    .filter-option label {
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        user-select: none;
        color: #24292e;
        flex-grow: 1;
    }
    
    .filter-stats {
        font-size: 12px;
        color: #586069;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #e1e4e8;
        text-align: center;
        font-weight: 500;
    }
    
    .stats {
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
        padding: 12px 15px;
        margin: 0 0 15px 0;
        border-radius: 8px;
        font-size: 13px;
        color: #2c3e50;
        border: 1px solid #a0aec0;
    }
    
    .stats strong {
        font-weight: 600;
    }
    
    .date-group {
        margin-bottom: 12px;
    }
    
    .date-header {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: white;
        padding: 12px 15px;
        cursor: pointer;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        font-weight: 500;
    }
    
    .date-header:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #5a6678 0%, #3d4858 100%);
    }
    
    .date-count {
        background: rgba(255,255,255,0.25);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .time-group {
        margin-left: 10px;
        margin-top: 8px;
    }
    
    .time-header {
        background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
        color: #2c3e50;
        padding: 10px 12px;
        cursor: pointer;
        border-radius: 6px;
        font-size: 13px;
        margin-bottom: 6px;
        transition: all 0.2s;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .time-header:hover {
        transform: translateX(2px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #d5dfe8 0%, #b0bac5 100%);
    }
    
    .file-item {
        background: #ffffff;
        padding: 10px 12px;
        margin: 4px 0 4px 10px;
        border-left: 4px solid #4a5568;
        cursor: pointer;
        border-radius: 6px;
        font-size: 13px;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        color: #24292e;
        border: 1px solid #e1e4e8;
        border-left-width: 4px;
    }
    
    .file-item:hover {
        background: #f6f8fa;
        transform: translateX(4px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .file-item.image {
        border-left-color: #718096;
    }
    
    .file-item.video {
        border-left-color: #2d3748;
    }
    
    .file-item.att_location {
        border-left-color: #00ff00;
    }
    
    .file-item.ankle_monitor {
        border-left-color: #ffff00;
    }
    
    .collapsed-content {
        display: none;
    }
    
    .arrow {
        transition: transform 0.3s;
        display: inline-block;
        font-size: 12px;
    }
    
    .arrow.down {
        transform: rotate(90deg);
    }
    
    #map {
        margin-left: 380px;
        transition: margin-left 0.3s ease-in-out;
    }
    
    #map.expanded {
        margin-left: 0;
    }
    
    /* Scrollbar styling for sidebar */
    #sidebar::-webkit-scrollbar {
        width: 8px;
    }
    
    #sidebar::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    #sidebar::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    #sidebar::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Toggle switch styles */
    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
        margin-right: 10px;
        vertical-align: middle;
    }
    
    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 24px;
    }
    
    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }
    
    input:checked + .toggle-slider {
        background-color: #4a5568;
    }
    
    input:checked + .toggle-slider:before {
        transform: translateX(26px);
    }
    
    .toggle-label {
        display: inline-block;
        vertical-align: middle;
        cursor: pointer;
        user-select: none;
    }
</style>

<div id="sidebar">
    <div id="sidebar-header">
        Location Timeline
    </div>
    <div id="sidebar-content">
        <div class="filter-controls">
            <h4>Filter by Media Type</h4>
            <div class="filter-option">
                <input type="radio" id="filter-both" name="media-filter" checked onchange="applyFilters()">
                <label for="filter-both">Show All (Images & Videos)</label>
            </div>
            <div class="filter-option">
                <input type="radio" id="filter-images" name="media-filter" onchange="applyFilters()">
                <label for="filter-images">Images Only</label>
            </div>
            <div class="filter-option">
                <input type="radio" id="filter-videos" name="media-filter" onchange="applyFilters()">
                <label for="filter-videos">Videos Only</label>
            </div>
        </div>
        <div class="filter-controls" style="margin-top: 10px;">
            <h4>Event Markers</h4>
            <div class="filter-option">
                <input type="checkbox" id="filter-att" checked onchange="applyFilters()">
                <label for="filter-att">ATT Location</label>
            </div>
            <div class="filter-option">
                <input type="checkbox" id="filter-ankle" checked onchange="applyFilters()">
                <label for="filter-ankle">Ankle Monitor Fix</label>
            </div>
        </div>
        <div class="filter-controls" style="margin-top: 10px;">
            <h4>Filter by Time Range</h4>
            <div style="margin: 10px 0;">
                <label style="font-size: 12px; color: #586069; display: block; margin-bottom: 4px;">Start Date & Time:</label>
                <input type="datetime-local" id="time-filter-start" onchange="applyFilters()" style="width: 100%; padding: 6px; border: 1px solid #e1e4e8; border-radius: 4px; font-size: 13px;">
            </div>
            <div style="margin: 10px 0;">
                <label style="font-size: 12px; color: #586069; display: block; margin-bottom: 4px;">End Date & Time:</label>
                <input type="datetime-local" id="time-filter-end" onchange="applyFilters()" style="width: 100%; padding: 6px; border: 1px solid #e1e4e8; border-radius: 4px; font-size: 13px;">
            </div>
            <button onclick="clearTimeFilter()" style="width: 100%; padding: 8px; background: #4a5568; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; margin-top: 5px;">
                Clear Time Filter
            </button>
        </div>
        <div class="stats">
            <strong>Total Entries:</strong> """ + str(len(df)) + """<br/>
            <strong>Date Ranges:</strong> """ + str(len(sorted_dates)) + """ days
        </div>
"""
    
    # Add date groups
    for date in sorted_dates:
        times = tree[date]
        total_files = sum(len(items) for items in times.values())
        
        sidebar_html += f"""
        <div class="date-group">
            <div class="date-header" onclick="toggleDate('date-{date.replace('/', '-').replace(' ', '_')}')">
                <span><span class="arrow" id="arrow-date-{date.replace('/', '-').replace(' ', '_')}">▶</span> 📅 {date}</span>
                <span class="date-count">{total_files} entries</span>
            </div>
            <div id="date-{date.replace('/', '-').replace(' ', '_')}" class="collapsed-content">
"""
        
        # Sort times
        sorted_times = sorted(times.keys())
        
        for time_val in sorted_times:
            items = times[time_val]
            time_display = time_val if time_val and time_val != 'nan' else 'No Time'
            time_id = f"{date.replace('/', '-').replace(' ', '_')}-{time_val.replace(':', '-').replace(' ', '_')}"
            
            sidebar_html += f"""
                <div class="time-group">
                    <div class="time-header" onclick="toggleTime('time-{time_id}')">
                        <span class="arrow" id="arrow-time-{time_id}">▶</span> 🕐 {time_display} ({len(items)} entries)
                    </div>
                    <div id="time-{time_id}" class="collapsed-content">
"""
            
            for item in items:
                # Determine type from data source or media path
                data_source = item.get('data_source', 'MediaMarkers')
                
                if data_source == 'MasterMapData':
                    # Event markers
                    if 'ATT Location' in item['title']:
                        file_type = 'att_location'
                        icon = '🟢'
                    else:
                        file_type = 'ankle_monitor'
                        icon = '🟡'
                else:
                    # Media markers
                    file_type = 'video' if any(ext in item['path'].lower() for ext in ['.mp4', '.mov', '.avi', '.wmv']) else 'image'
                    icon = '🎥' if file_type == 'video' else '📷'
                
                datetime_attr = item.get('datetime', '')
                
                sidebar_html += f"""
                        <div class="file-item {file_type}" data-type="{file_type}" data-datetime="{datetime_attr}" data-lat="{item['lat']}" data-lon="{item['lon']}" onclick="flyToMarker({item['lat']}, {item['lon']})">
                            {icon} {item['title'][:50]}{'...' if len(item['title']) > 50 else ''}
                        </div>
"""
            
            sidebar_html += """
                    </div>
                </div>
"""
        
        sidebar_html += """
            </div>
        </div>
"""
    
    sidebar_html += """
    </div>
</div>

<button id="sidebar-toggle" onclick="toggleSidebar()">☰</button>

<script>
    // Global references to marker clusters
    window.imageCluster = null;
    window.videoCluster = null;
    
    // Store marker metadata for filtering
    window.markerMetadata = [];
    window.allMarkers = [];
    
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const map = document.getElementById('map');
        sidebar.classList.toggle('collapsed');
        map.classList.toggle('expanded');
    }
    
    function toggleDate(id) {
        const content = document.getElementById(id);
        const arrow = document.getElementById('arrow-' + id);
        content.classList.toggle('collapsed-content');
        arrow.classList.toggle('down');
    }
    
    function toggleTime(id) {
        const content = document.getElementById(id);
        const arrow = document.getElementById('arrow-' + id);
        content.classList.toggle('collapsed-content');
        arrow.classList.toggle('down');
    }
    
    function flyToMarker(lat, lon) {
        // Fly to the marker location
        if (window.map_object) {
            window.map_object.setView([lat, lon], 18);
            
            // Find and open the popup for this marker
            // Search in all clusters
            const clusters = [window.imageCluster, window.videoCluster, window.attCluster, window.ankleCluster];
            let markerFound = false;
            
            clusters.forEach(cluster => {
                if (cluster && !markerFound) {
                    cluster.eachLayer(function(layer) {
                        // Check if this is a marker cluster or individual marker
                        if (layer.getAllChildMarkers) {
                            // It's a cluster, check all markers inside
                            const markers = layer.getAllChildMarkers();
                            markers.forEach(marker => {
                                const markerLatLng = marker.getLatLng();
                                if (Math.abs(markerLatLng.lat - lat) < 0.00001 && Math.abs(markerLatLng.lng - lon) < 0.00001) {
                                    // Zoom to unclustered view and open popup
                                    layer.zoomToShowLayer(marker, function() {
                                        setTimeout(() => marker.openPopup(), 300);
                                    });
                                    markerFound = true;
                                }
                            });
                        } else if (layer.getLatLng) {
                            // It's an individual marker
                            const markerLatLng = layer.getLatLng();
                            if (Math.abs(markerLatLng.lat - lat) < 0.00001 && Math.abs(markerLatLng.lng - lon) < 0.00001) {
                                layer.openPopup();
                                markerFound = true;
                            }
                        }
                    });
                }
            });
        }
    }
    
    function clearTimeFilter() {
        document.getElementById('time-filter-start').value = '';
        document.getElementById('time-filter-end').value = '';
        applyFilters();
    }
    
    
    function applyFilters() {
        // Determine which filter is selected
        const showBoth = document.getElementById('filter-both').checked;
        const showImages = document.getElementById('filter-images').checked;
        const showVideos = document.getElementById('filter-videos').checked;
        const showATT = document.getElementById('filter-att').checked;
        const showAnkle = document.getElementById('filter-ankle').checked;
        
        // Get time filter values
        const timeStart = document.getElementById('time-filter-start').value;
        const timeEnd = document.getElementById('time-filter-end').value;
        
        console.log('Applying filters:', {showBoth, showImages, showVideos, showATT, showAnkle, timeStart, timeEnd});
        console.log('Map object:', window.map_object);
        console.log('Image cluster:', window.imageCluster);
        console.log('Video cluster:', window.videoCluster);
        console.log('ATT cluster:', window.attCluster);
        console.log('Ankle cluster:', window.ankleCluster);
        
        // Store filtered coordinates for map filtering
        const filteredCoords = new Set();
        
        // Control marker clusters visibility using stored references
        if (window.map_object && window.imageCluster && window.videoCluster && window.attCluster && window.ankleCluster) {
            console.log('All objects found, applying filters...');
            
            // If time filter is active, we need to filter individual markers
            if (timeStart || timeEnd) {
                // First, collect all coordinates that pass the time filter
                const allFiles = document.querySelectorAll('.file-item');
                allFiles.forEach(item => {
                    const type = item.getAttribute('data-type');
                    const itemDateTime = item.getAttribute('data-datetime');
                    const lat = item.getAttribute('data-lat');
                    const lon = item.getAttribute('data-lon');
                    
                    // Check media type filter
                    let typeMatch = showBoth || (type === 'image' && showImages) || (type === 'video' && showVideos);
                    
                    // Check event type filter
                    if (type === 'att_location') {
                        typeMatch = showATT;
                    } else if (type === 'ankle_monitor') {
                        typeMatch = showAnkle;
                    }
                    
                    // Check time filter
                    let timeMatch = true;
                    if (itemDateTime && (timeStart || timeEnd)) {
                        const itemDate = new Date(itemDateTime);
                        if (timeStart && itemDate < new Date(timeStart)) {
                            timeMatch = false;
                        }
                        if (timeEnd && itemDate > new Date(timeEnd)) {
                            timeMatch = false;
                        }
                    }
                    
                    if (typeMatch && timeMatch) {
                        filteredCoords.add(`${lat},${lon}`);
                    }
                });
                
                // Now filter markers in all clusters
                console.log('Filtering markers by time, found', filteredCoords.size, 'matching coordinates');
                
                // Remove all markers first
                window.imageCluster.clearLayers();
                window.videoCluster.clearLayers();
                window.attCluster.clearLayers();
                window.ankleCluster.clearLayers();
                
                // Re-add only matching markers
                if (window.allMarkers) {
                    window.allMarkers.forEach(markerInfo => {
                        const coordKey = `${markerInfo.lat},${markerInfo.lon}`;
                        if (filteredCoords.has(coordKey)) {
                            if (markerInfo.type === 'image' && (showImages || showBoth)) {
                                markerInfo.marker.addTo(window.imageCluster);
                            } else if (markerInfo.type === 'video' && (showVideos || showBoth)) {
                                markerInfo.marker.addTo(window.videoCluster);
                            } else if (markerInfo.type === 'att_location' && showATT) {
                                markerInfo.marker.addTo(window.attCluster);
                            } else if (markerInfo.type === 'ankle_monitor' && showAnkle) {
                                markerInfo.marker.addTo(window.ankleCluster);
                            }
                        }
                    });
                }
                
                // Ensure all clusters are on the map
                if (!window.map_object.hasLayer(window.imageCluster)) {
                    window.map_object.addLayer(window.imageCluster);
                }
                if (!window.map_object.hasLayer(window.videoCluster)) {
                    window.map_object.addLayer(window.videoCluster);
                }
                if (!window.map_object.hasLayer(window.attCluster)) {
                    window.map_object.addLayer(window.attCluster);
                }
                if (!window.map_object.hasLayer(window.ankleCluster)) {
                    window.map_object.addLayer(window.ankleCluster);
                }
            } else {
                // No time filter - just use type filter
                // Populate filteredCoords with all markers that match type filters
                if (window.allMarkers) {
                    window.allMarkers.forEach(markerInfo => {
                        let shouldShow = false;
                        if (markerInfo.type === 'image' && (showImages || showBoth)) {
                            shouldShow = true;
                        } else if (markerInfo.type === 'video' && (showVideos || showBoth)) {
                            shouldShow = true;
                        } else if (markerInfo.type === 'att_location' && showATT) {
                            shouldShow = true;
                        } else if (markerInfo.type === 'ankle_monitor' && showAnkle) {
                            shouldShow = true;
                        }
                        
                        if (shouldShow) {
                            filteredCoords.add(`${markerInfo.lat},${markerInfo.lon}`);
                        }
                    });
                }
                
                // Handle image cluster
                if (showImages || showBoth) {
                    if (!window.map_object.hasLayer(window.imageCluster)) {
                        console.log('Adding image cluster to map');
                        window.map_object.addLayer(window.imageCluster);
                    }
                } else {
                    if (window.map_object.hasLayer(window.imageCluster)) {
                        console.log('Removing image cluster from map');
                        window.map_object.removeLayer(window.imageCluster);
                    }
                }
                
                // Handle video cluster
                if (showVideos || showBoth) {
                    if (!window.map_object.hasLayer(window.videoCluster)) {
                        console.log('Adding video cluster to map');
                        window.map_object.addLayer(window.videoCluster);
                    }
                } else {
                    if (window.map_object.hasLayer(window.videoCluster)) {
                        console.log('Removing video cluster from map');
                        window.map_object.removeLayer(window.videoCluster);
                    }
                }
                
                // Handle ATT cluster
                if (showATT) {
                    if (!window.map_object.hasLayer(window.attCluster)) {
                        console.log('Adding ATT cluster to map');
                        window.map_object.addLayer(window.attCluster);
                    }
                } else {
                    if (window.map_object.hasLayer(window.attCluster)) {
                        console.log('Removing ATT cluster from map');
                        window.map_object.removeLayer(window.attCluster);
                    }
                }
                
                // Handle ankle monitor cluster
                if (showAnkle) {
                    if (!window.map_object.hasLayer(window.ankleCluster)) {
                        console.log('Adding ankle monitor cluster to map');
                        window.map_object.addLayer(window.ankleCluster);
                    }
                } else {
                    if (window.map_object.hasLayer(window.ankleCluster)) {
                        console.log('Removing ankle monitor cluster from map');
                        window.map_object.removeLayer(window.ankleCluster);
                    }
                }
            }
        } else {
            console.warn('Missing required objects for filtering');
        }
        
        // Update sidebar items visibility
        const allFiles = document.querySelectorAll('.file-item');
        let visibleCount = 0;
        
        allFiles.forEach(item => {
            const type = item.getAttribute('data-type');
            const itemDateTime = item.getAttribute('data-datetime');
            
            // Check media type filter
            let typeMatch = showBoth || (type === 'image' && showImages) || (type === 'video' && showVideos);
            
            // Check event type filter
            if (type === 'att_location') {
                typeMatch = showATT;
            } else if (type === 'ankle_monitor') {
                typeMatch = showAnkle;
            }
            
            // Check time filter
            let timeMatch = true;
            if (itemDateTime && (timeStart || timeEnd)) {
                const itemDate = new Date(itemDateTime);
                if (timeStart && itemDate < new Date(timeStart)) {
                    timeMatch = false;
                }
                if (timeEnd && itemDate > new Date(timeEnd)) {
                    timeMatch = false;
                }
            }
            
            const shouldShow = typeMatch && timeMatch;
            
            if (shouldShow) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // Update stats
        document.getElementById('visible-count').textContent = visibleCount;
        document.getElementById('total-count').textContent = allFiles.length;
        
        // Hide empty time groups
        const timeGroups = document.querySelectorAll('.time-group');
        timeGroups.forEach(group => {
            const visibleFiles = group.querySelectorAll('.file-item[style="display: block;"], .file-item:not([style*="display: none"])');
            if (visibleFiles.length === 0 && (!showImages || !showVideos)) {
                group.style.display = 'none';
            } else {
                group.style.display = 'block';
            }
        });
        
        // Hide empty date groups
        const dateGroups = document.querySelectorAll('.date-group');
        dateGroups.forEach(group => {
            const visibleTimeGroups = group.querySelectorAll('.time-group[style="display: block;"], .time-group:not([style*="display: none"])');
            if (visibleTimeGroups.length === 0 && (!showImages || !showVideos)) {
                group.style.display = 'none';
            } else {
                group.style.display = 'block';
            }
        });
        
    }
    
    // Store map object globally
    document.addEventListener('DOMContentLoaded', function() {
        // Find the map object in the page
        for (let key in window) {
            if (key.startsWith('map_') && window[key].setView) {
                window.map_object = window[key];
                break;
            }
        }
        
        // Wait a bit for clusters to be fully loaded, then initialize
        setTimeout(function() {
            applyFilters();
        }, 100);
    });
</script>
"""
    
    # Insert sidebar before the map div
    html_content = html_content.replace(
        '<div class="folium-map"',
        sidebar_html + '<div class="folium-map"'
    )
    
    # Write back to file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def create_html_map(
    input_file,
    output_html="map_output.html",
    lat_col="latitude",
    lon_col="longitude",
    title_col="title",
    description_col="description",
    media_col="media_path",
    icon_col="icon",
    color_col="color",
    use_localhost=True,
    localhost_port=8001,
    auto_open=True
):
    """
    Create an interactive HTML map from CSV/XLSX file.
    
    Args:
        input_file: Path to CSV or XLSX file
        output_html: Output HTML filename
        lat_col: Column name for latitude
        lon_col: Column name for longitude
        title_col: Column name for marker title
        description_col: Column name for description
        media_col: Column name for media file paths
        icon_col: Column name for icon type
        color_col: Column name for marker color
        use_localhost: Use localhost URLs for media (requires server)
        localhost_port: Port for localhost server
        auto_open: Automatically open map in browser
    """
    
    print(f"\n{'='*70}")
    print("CSV/XLSX TO HTML MAP GENERATOR")
    print(f"{'='*70}\n")
    
    # Load data
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_file}")
        return None
    
    print(f"📂 Loading: {input_file}")
    
    if input_path.suffix.lower() == '.csv':
        df = pd.read_csv(input_file)
    elif input_path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(input_file)
    else:
        print(f"❌ Error: Unsupported file format. Use CSV or XLSX")
        return None
    
    print(f"   Total rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    # Load and merge MasterMapData.csv
    master_data_path = Path("MasterMapData.csv")
    if master_data_path.exists():
        print(f"\n📂 Loading MasterMapData.csv...")
        master_df = pd.read_csv(master_data_path)
        print(f"   Total rows: {len(master_df)}")
        
        # Normalize column names and prepare master data
        master_df = master_df.rename(columns={
            'LATITUDE': 'latitude',
            'LONGITUDE': 'longitude',
            'Date-Time CST': 'datetime',
            'Event': 'title',
            'ADDRESS': 'description',
            'ACCURACY IN METERS': 'accuracy_meters'
        })
        
        # Add required columns for consistency
        master_df['media_path'] = ''
        master_df['date'] = master_df['datetime']
        master_df['time'] = ''
        
        # Set colors based on event type
        master_df['color'] = master_df['title'].apply(
            lambda x: 'lightgreen' if 'ATT Location' in str(x) else 'orange'
        )
        master_df['icon'] = 'circle'
        master_df['data_source'] = 'MasterMapData'
        
        # Add source column to original data
        df['data_source'] = 'MediaMarkers'
        df['accuracy_meters'] = 0  # No accuracy data for media markers
        
        # Combine dataframes
        df = pd.concat([df, master_df], ignore_index=True, sort=False)
        print(f"   Combined total rows: {len(df)}")
    
    # Filter rows with valid coordinates
    df = df.dropna(subset=[lat_col, lon_col])
    print(f"   Rows with coordinates: {len(df)}")
    
    if len(df) == 0:
        print(f"❌ Error: No valid coordinates found in columns '{lat_col}' and '{lon_col}'")
        return None
    
    # Calculate map center
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    print(f"\n📍 Creating map centered at: {center_lat:.6f}, {center_lon:.6f}")
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add additional tile layers
    folium.TileLayer('CartoDB positron', name='Light Mode').add_to(m)
    
    # Add Google Satellite layer
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add Google Hybrid (Satellite with labels)
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Hybrid',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Create separate feature groups for images and videos
    from folium import FeatureGroup
    
    image_cluster = MarkerCluster(
        name='Images 📷',
        overlay=True,
        control=False,  # We'll control this via our custom filters
        icon_create_function=None,
        options={
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 18,
            'spiderfyDistanceMultiplier': 2
        }
    )
    
    video_cluster = MarkerCluster(
        name='Videos 🎥',
        overlay=True,
        control=False,  # We'll control this via our custom filters
        icon_create_function=None,
        options={
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 18,
            'spiderfyDistanceMultiplier': 2
        }
    )
    
    # Create clusters for event markers
    att_cluster = MarkerCluster(
        name='ATT Location 📍',
        overlay=True,
        control=False,
        icon_create_function=None,
        options={
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 18,
            'spiderfyDistanceMultiplier': 2
        }
    )
    
    ankle_cluster = MarkerCluster(
        name='Ankle Monitor 📍',
        overlay=True,
        control=False,
        icon_create_function=None,
        options={
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 18,
            'spiderfyDistanceMultiplier': 2
        }
    )
    
    # Create feature group for accuracy circles
    from folium import FeatureGroup
    accuracy_group = FeatureGroup(name='Accuracy Circles', overlay=True, control=False)
    
    image_cluster.add_to(m)
    video_cluster.add_to(m)
    att_cluster.add_to(m)
    ankle_cluster.add_to(m)
    accuracy_group.add_to(m)
    
    # Color mapping for markers
    color_map = {
        'red': 'red',
        'blue': 'blue',
        'green': 'green',
        'purple': 'purple',
        'orange': 'orange',
        'darkred': 'darkred',
        'lightred': 'lightred',
        'beige': 'beige',
        'darkblue': 'darkblue',
        'darkgreen': 'darkgreen',
        'cadetblue': 'cadetblue',
        'darkpurple': 'darkpurple',
        'white': 'white',
        'pink': 'pink',
        'lightblue': 'lightblue',
        'lightgreen': 'lightgreen',
        'gray': 'gray',
        'black': 'black',
        'lightgray': 'lightgray'
    }
    
    # Icon mapping
    icon_map = {
        'camera': 'camera',
        'video': 'video-camera',
        'photo': 'picture-o',
        'film': 'film',
        'play': 'play-circle',
        'location': 'map-marker',
        'home': 'home',
        'car': 'car',
        'flag': 'flag',
        'info': 'info-circle',
        'star': 'star',
        'circle': 'circle'
    }
    
    stats = {
        'total': 0,
        'with_media': 0,
        'images': 0,
        'videos': 0,
        'no_media': 0,
        'att_location': 0,
        'ankle_monitor': 0
    }
    
    # Track marker data for later injection
    marker_data = []
    
    media_base = Path(r"C:\Users\mactwo\Desktop\MapMediaWork\Media")
    
    print(f"\n📌 Adding markers...")
    
    for idx, row in df.iterrows():
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
            
            # Get marker properties
            title = str(row.get(title_col, 'Untitled')) if title_col in row.index else 'Untitled'
            description = str(row.get(description_col, '')) if description_col in row.index else ''
            media_path = str(row.get(media_col, '')) if media_col in row.index else ''
            icon_type = str(row.get(icon_col, 'camera')) if icon_col in row.index else 'camera'
            color = str(row.get(color_col, 'blue')) if color_col in row.index else 'blue'
            datetime_val = str(row.get('datetime', '')) if 'datetime' in row.index and pd.notna(row.get('datetime')) else ''
            data_source = str(row.get('data_source', 'MediaMarkers')) if 'data_source' in row.index else 'MediaMarkers'
            accuracy_meters = float(row.get('accuracy_meters', 0)) if 'accuracy_meters' in row.index and pd.notna(row.get('accuracy_meters')) else 0
            
            # Build popup HTML
            popup_html = f"<div style='font-family: Arial; max-width: 400px;'>"
            popup_html += f"<h3 style='margin-top: 0; color: #333;'>{title}</h3>"
            
            # Handle media
            has_media = False
            is_video_marker = False
            if media_path and media_path != 'nan' and media_col in row.index:
                file_path = Path(media_path)
                
                if file_path.exists():
                    has_media = True
                    stats['with_media'] += 1
                    
                    ext = file_path.suffix.lower()
                    is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
                    is_video = ext in ['.mp4', '.mov', '.avi', '.wmv', '.mkv', '.webm', '.m4v']
                    
                    is_video_marker = is_video  # Track if this is a video marker
                    
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    
                    if use_localhost:
                        # Create localhost URL
                        try:
                            relative_path = file_path.relative_to(media_base)
                            url_path = f"Media/{str(relative_path).replace(chr(92), '/')}"
                            encoded_path = quote(url_path)
                            media_url = f"http://localhost:{localhost_port}/{encoded_path}"
                        except ValueError:
                            # File not in media base, use absolute path
                            media_url = f"http://localhost:{localhost_port}/Media/{quote(str(file_path.name))}"
                        
                        if is_image:
                            popup_html += f"""
                            <img src="{media_url}" style="width: 100%; max-width: 400px; height: auto; border-radius: 5px; margin: 10px 0;"/>
                            <p style="margin: 5px 0; color: #666; font-size: 0.9em;">📷 {file_path.name} ({file_size_mb:.1f} MB)</p>
                            """
                            stats['images'] += 1
                        
                        elif is_video:
                            # Map video extensions to proper MIME types
                            mime_map = {
                                '.mp4': 'video/mp4',
                                '.m4v': 'video/mp4',
                                '.webm': 'video/webm',
                                '.ogv': 'video/ogg',
                                '.avi': 'video/x-msvideo',
                                '.mov': 'video/quicktime',
                                '.wmv': 'video/x-ms-wmv',
                                '.mkv': 'video/x-matroska'
                            }
                            mime_type = mime_map.get(ext.lower(), f'video/{ext[1:]}')
                            
                            popup_html += f"""
                            <video controls preload="metadata" style="width: 100%; max-width: 550px; height: 300px; border-radius: 5px; margin: 10px 0; background: #000;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                <source src="{media_url}" type="{mime_type}">
                                Your browser does not support this video format.
                            </video>
                            <div style="display:none; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; margin: 10px 0;">
                                <p style="margin: 0; color: #856404;">⚠️ Video preview not available. Click the button below to open the video in a new tab.</p>
                            </div>
                            <p style="margin: 5px 0; color: #666; font-size: 0.9em;">🎥 {file_path.name} ({file_size_mb:.1f} MB)</p>
                            <p style="margin: 5px 0;">
                                <a href="{media_url}" target="_blank" style="color: #0066cc; text-decoration: none; background: #007bff; color: white; padding: 8px 15px; border-radius: 3px; display: inline-block; font-weight: bold;">▶ Open Video in New Tab</a>
                            </p>
                            """
                            stats['videos'] += 1
                    else:
                        # Show file path only
                        popup_html += f"""
                        <p style="background: #f0f0f0; padding: 10px; border-radius: 3px; font-family: monospace; word-break: break-all; font-size: 0.85em;">
                        {file_path.absolute()}
                        </p>
                        <p style="margin: 5px 0; color: #666; font-size: 0.9em;">
                        {'📷 Image' if is_image else '🎥 Video'}: {file_path.name} ({file_size_mb:.1f} MB)
                        </p>
                        """
                        if is_image:
                            stats['images'] += 1
                        elif is_video:
                            stats['videos'] += 1
            
            if not has_media:
                stats['no_media'] += 1
            
            # Add description (remove Modified timestamp if present)
            if description and description != 'nan':
                # Remove the "Modified: YYYY-MM-DD HH:MM" portion from description
                import re
                clean_description = re.sub(r'\s*\|\s*Modified:\s*[\d\-:\s]+', '', description)
                popup_html += f"<p style='margin: 10px 0;'>{clean_description}</p>"
            
            # Add other metadata
            metadata_html = "<div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666;'>"
            
            for col in df.columns:
                if col not in [lat_col, lon_col, title_col, description_col, media_col, icon_col, color_col]:
                    if pd.notna(row[col]):
                        value = str(row[col])
                        if value and value != 'nan':
                            metadata_html += f"<b>{col}:</b> {value}<br/>"
            
            metadata_html += "</div>"
            popup_html += metadata_html
            popup_html += "</div>"
            
            # Create marker
            folium_color = color_map.get(color.lower(), 'blue')
            folium_icon = icon_map.get(icon_type.lower(), 'camera')
            
            # Determine which cluster to add marker to based on data source
            if data_source == 'MasterMapData':
                # Event markers from MasterMapData
                if 'ATT Location' in title:
                    target_cluster = att_cluster
                    marker_type = 'att_location'
                    stats['att_location'] += 1
                    folium_color = 'lightgreen'
                else:  # Ankle Monitor Fix or other events
                    target_cluster = ankle_cluster
                    marker_type = 'ankle_monitor'
                    stats['ankle_monitor'] += 1
                    folium_color = 'orange'
                
                folium_icon = 'circle'
            else:
                # Media markers
                target_cluster = video_cluster if is_video_marker else image_cluster
                marker_type = 'video' if is_video_marker else 'image'
            
            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=600),
                tooltip=title,
                icon=folium.Icon(color=folium_color, icon=folium_icon, prefix='fa')
            )
            marker.add_to(target_cluster)
            
            # Add accuracy circle if accuracy data exists
            if accuracy_meters > 0:
                # Map folium colors to CSS/hex colors for circles
                circle_color_map = {
                    'lightgreen': '#90EE90',
                    'orange': '#FFA500',
                    'blue': '#0000FF',
                    'red': '#FF0000',
                    'green': '#008000',
                    'purple': '#800080',
                    'darkred': '#8B0000',
                    'lightred': '#FFB6C1',
                    'beige': '#F5F5DC',
                    'darkblue': '#00008B',
                    'darkgreen': '#006400',
                    'cadetblue': '#5F9EA0',
                    'darkpurple': '#9400D3',
                    'white': '#FFFFFF',
                    'pink': '#FFC0CB',
                    'lightblue': '#ADD8E6',
                    'gray': '#808080',
                    'black': '#000000',
                    'lightgray': '#D3D3D3'
                }
                circle_color = circle_color_map.get(folium_color, '#0000FF')
                
                # Create the accuracy circle
                circle = folium.Circle(
                    location=[lat, lon],
                    radius=accuracy_meters,
                    color=circle_color,
                    fill=True,
                    fillColor=circle_color,
                    fillOpacity=0.15,
                    opacity=0.35,
                    weight=1,
                    tooltip=f'Accuracy: {accuracy_meters}m'
                )
                circle.add_to(accuracy_group)
            
            # Store marker data for filtering
            marker_data.append({
                'lat': lat,
                'lon': lon,
                'type': marker_type,
                'datetime': datetime_val,
                'title': title
            })
            
            stats['total'] += 1
            
            if (idx + 1) % 100 == 0:
                print(f"   Added {idx + 1} markers...")
        
        except Exception as e:
            print(f"⚠️  Warning: Could not add marker for row {idx}: {e}")
            continue
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    print(f"\n💾 Saving map to: {output_html}")
    m.save(output_html)
    
    # Inject cluster references into the HTML
    print(f"🔧 Injecting cluster references...")
    with open(output_html, 'r', encoding='utf-8') as f:
        map_html = f.read()
    
    # Find the variable names that Folium assigned to our clusters
    # Pattern to find cluster variable definitions
    import re
    cluster_pattern = r'var\s+(marker_cluster_[a-f0-9]+)\s+=\s+L\.markerClusterGroup'
    cluster_matches = re.findall(cluster_pattern, map_html)
    
    # Find the accuracy group feature group variable
    feature_group_pattern = r'var\s+(feature_group_[a-f0-9]+)\s+=\s+L\.featureGroup'
    feature_group_matches = re.findall(feature_group_pattern, map_html)
    accuracy_group_var = feature_group_matches[0] if feature_group_matches else None
    
    if len(cluster_matches) >= 4:
        # Assume first is images, second is videos, third is ATT, fourth is ankle monitor
        image_cluster_var = cluster_matches[0]
        video_cluster_var = cluster_matches[1]
        att_cluster_var = cluster_matches[2]
        ankle_cluster_var = cluster_matches[3]
        
        # Find the map variable name
        map_var_pattern = r'var\s+(map_[a-f0-9]+)\s+=\s+L\.map'
        map_var_matches = re.findall(map_var_pattern, map_html)
        map_var = map_var_matches[0] if map_var_matches else 'map'
        
        # Find where all clusters are added to the map and inject after that
        # Pattern: .addTo(map_xxxxx);
        
        # Find the last occurrence of the ankle cluster being added to the map
        add_to_pattern = f'{ankle_cluster_var}.addTo'
        last_addto_pos = map_html.rfind(add_to_pattern)
        
        if last_addto_pos != -1:
            # Find the semicolon after this addTo
            semicolon_pos = map_html.find(';', last_addto_pos)
            if semicolon_pos != -1:
                # Build marker data JSON
                marker_data_json = json.dumps(marker_data)
                
                # Inject right after the semicolon
                injection_script = f"""
        
        // Store cluster references globally for filtering
        window.imageCluster = {image_cluster_var};
        window.videoCluster = {video_cluster_var};
        window.attCluster = {att_cluster_var};
        window.ankleCluster = {ankle_cluster_var};
        window.accuracyGroup = {accuracy_group_var if accuracy_group_var else 'null'};
        window.map_object = {map_var};
        
        // Store all markers with metadata for time-based filtering
        window.allMarkersData = {marker_data_json};
        
        // Build allMarkers array by extracting markers from clusters
        window.allMarkers = [];
        {image_cluster_var}.eachLayer(function(marker) {{
            var latlng = marker.getLatLng();
            var markerData = window.allMarkersData.find(m => m.lat === latlng.lat && m.lon === latlng.lng);
            if (markerData) {{
                window.allMarkers.push({{
                    marker: marker,
                    lat: latlng.lat,
                    lon: latlng.lng,
                    type: 'image',
                    datetime: markerData.datetime
                }});
            }}
        }});
        {video_cluster_var}.eachLayer(function(marker) {{
            var latlng = marker.getLatLng();
            var markerData = window.allMarkersData.find(m => m.lat === latlng.lat && m.lon === latlng.lng);
            if (markerData) {{
                window.allMarkers.push({{
                    marker: marker,
                    lat: latlng.lat,
                    lon: latlng.lng,
                    type: 'video',
                    datetime: markerData.datetime
                }});
            }}
        }});
        {att_cluster_var}.eachLayer(function(marker) {{
            var latlng = marker.getLatLng();
            var markerData = window.allMarkersData.find(m => m.lat === latlng.lat && m.lon === latlng.lng);
            if (markerData) {{
                window.allMarkers.push({{
                    marker: marker,
                    lat: latlng.lat,
                    lon: latlng.lng,
                    type: 'att_location',
                    datetime: markerData.datetime
                }});
            }}
        }});
        {ankle_cluster_var}.eachLayer(function(marker) {{
            var latlng = marker.getLatLng();
            var markerData = window.allMarkersData.find(m => m.lat === latlng.lat && m.lon === latlng.lng);
            if (markerData) {{
                window.allMarkers.push({{
                    marker: marker,
                    lat: latlng.lat,
                    lon: latlng.lng,
                    type: 'ankle_monitor',
                    datetime: markerData.datetime
                }});
            }}
        }});
"""
                map_html = map_html[:semicolon_pos+1] + injection_script + map_html[semicolon_pos+1:]
        
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(map_html)
    
    # Add sidebar with file tree
    print(f"🌳 Adding sidebar with file tree...")
    add_sidebar_to_html(output_html, df, date_col='date', time_col='time')
    
    # Get file size
    html_size_kb = Path(output_html).stat().st_size / 1024
    
    print(f"\n✅ Map created successfully!")
    print(f"📦 File size: {html_size_kb:.1f} KB")
    print(f"\n📊 STATISTICS:")
    print(f"   Total markers:        {stats['total']}")
    print(f"   Media markers:        {stats['with_media']}")
    print(f"   - Images:             {stats['images']}")
    print(f"   - Videos:             {stats['videos']}")
    print(f"   Event markers:        {stats['att_location'] + stats['ankle_monitor']}")
    print(f"   - ATT Location:       {stats['att_location']}")
    print(f"   - Ankle Monitor:      {stats['ankle_monitor']}")
    print(f"   Without media:        {stats['no_media']}")
    
    if use_localhost:
        print(f"\n🌐 LOCALHOST SERVER REQUIRED:")
        print(f"   Media uses http://localhost:{localhost_port}")
        print(f"   Run: python media_server.py")
        print(f"   Keep server running while viewing the map")
    
    print(f"\n📍 TO VIEW:")
    print(f"   Open {output_html} in your web browser")
    
    if auto_open:
        print(f"\n🌐 Opening map in browser...")
        if use_localhost:
            webbrowser.open(f"http://localhost:8001/{output_html}")
        else:
            webbrowser.open(f"file://{Path(output_html).absolute()}")
    
    return output_html


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("QUICK START MENU")
    print("="*70)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "media_map_new.html"
        use_localhost = '--use-localhost' in sys.argv or '-l' in sys.argv
    else:
        # Use defaults - no user interaction
        # Check if running as bundled executable
        input_file = resource_path("media_markers_import.csv")
        output_file = "media_map_new.html"
        use_localhost = True
    
    if use_localhost:
        print("\nStarting server on port 8001...")
        # Check if server is already running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8001))
        sock.close()
        
        if result != 0:
            # Server not running, start it
            import subprocess
            server_process = subprocess.Popen(
                [sys.executable, 'media_server.py'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            print(f"✅ Server started on port 8001 (PID: {server_process.pid})")
            import time
            time.sleep(1)  # Give server time to start
        else:
            print("✅ Server already running on port 8001")
    
    # Create map
    create_html_map(
        input_file=input_file,
        output_html=output_file,
        use_localhost=use_localhost,
        auto_open=True
    )
    
    if use_localhost:
        print(f"\n🌐 Open in browser: http://localhost:8001/{output_file}")
    
    print("\n" + "="*70)
    print("✅ DONE!")
    print("="*70)

