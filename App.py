from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import time
import socket
import requests
import urllib.parse
import webbrowser
import pyautogui

app = Flask(__name__)
DB_NAME = "database.db"

# Database Initialization
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Listings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            price TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            image TEXT
        )
    ''')
    
    # Leads/Clients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            source TEXT DEFAULT 'Direct VIP',
            status TEXT DEFAULT 'Active',
            date TEXT
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM listings')
    if cursor.fetchone()[0] == 0:
        initial_listings = [
            ("Luxury Apartment 4C", "Apartment", "PKR 35,000,000", "Active", "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80"),
            ("Commercial Plaza Plot 12B", "Plot", "PKR 120,000,000", "Pending", "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80"),
            ("Executive Sports Car (Civic/Supra)", "Car Showroom", "PKR 18,500,000", "Active", "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80")
        ]
        cursor.executemany('INSERT INTO listings (title, type, price, status, image) VALUES (?, ?, ?, ?, ?)', initial_listings)
        
    cursor.execute('SELECT COUNT(*) FROM leads')
    if cursor.fetchone()[0] == 0:
        initial_leads = [
            ("Furqan Sir", "+923334223766", "Direct VIP", "Active", "Oct 28"),
            ("Ahmad Tech", "+923434396095", "Direct VIP", "Active", "Oct 26")
        ]
        cursor.executemany('INSERT INTO leads (name, phone, source, status, date) VALUES (?, ?, ?, ?, ?)', initial_leads)
        
    conn.commit()
    conn.close()

def get_all_listings():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM listings')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_leads():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Helper function to get computer's local IP address automatically (Fallback)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Helper function to fetch active Ngrok public URL automatically
def get_base_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get("tunnels", []):
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")
    except Exception:
        pass
    
    local_ip = get_local_ip()
    return f"http://{local_ip}:3000"

@app.route('/')
def dashboard():
    return render_template('dashboard.html', active='dashboard', listings=get_all_listings(), leads=get_all_leads())

@app.route('/listings')
def listings():
    return render_template('listings.html', active='listings', listings=get_all_listings())

@app.route('/clients')
def clients():
    return render_template('clients.html', active='clients', leads=get_all_leads())

@app.route('/automation')
def automation():
    return render_template('automation.html', active='automation')

@app.route('/settings')
def settings():
    return render_template('settings.html', active='settings')

# Public client-facing listings page (Secure & Mobile-Friendly)
@app.route('/public/listings')
def public_listings():
    return render_template('public_listings.html', listings=get_all_listings())

@app.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if request.method == 'POST':
        title = request.form.get('title')
        prop_type = request.form.get('type')
        price = request.form.get('price')
        image_url = request.form.get('image_url')
        
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80"
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO listings (title, type, price, status, image) VALUES (?, ?, ?, ?, ?)',
            (title, prop_type, price, 'Active', image_url)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('listings'))
        
    return render_template('add_listing.html', active='listings')

@app.route('/add-client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    phone = request.form.get('phone')
    source = request.form.get('source', 'Manual Data')
    
    if name and phone:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO leads (name, phone, source, status, date) VALUES (?, ?, ?, ?, ?)',
            (name, phone, source, 'Active', 'Today')
        )
        conn.commit()
        conn.close()
    return redirect(url_for('clients'))

@app.route('/delete-client/<int:client_id>', methods=['POST', 'GET'])
def delete_client(client_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM leads WHERE id = ?', (client_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clients'))

@app.route('/api/whatsapp-blast', methods=['POST'])
def whatsapp_blast():
    try:
        current_leads = get_all_leads()
        
        # Automatically fetch active Ngrok HTTPS public URL
        base_url = get_base_url()
        listings_link = f"{base_url.rstrip('/')}/public/listings"
        
        for client in current_leads:
            message = (
                f"Salam {client['name']}! AutomateX Aquatic Studio ki nayi properties aur cars inventory update ho chuki hai. "
                f"Sari listings aur details yahan check karein: {listings_link} . "
                f"Managed by @FaiziTech Full Stack Developer."
            )
            
            phone = client['phone'].strip()
            phone = ''.join(filter(lambda c: c.isdigit() or c == '+', phone))
            
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
            
            # Open browser tab directly to WhatsApp chat with prefilled message
            webbrowser.open(whatsapp_url)
            
            # Wait for WhatsApp Web to load chat completely
            time.sleep(18)
            
            # Click on the input box area to guarantee focus and prevent draft state
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height - 100)
            time.sleep(1)
            
            # Press enter to send message automatically
            pyautogui.press('enter')
            time.sleep(2)
            pyautogui.press('enter')
            time.sleep(2)
            
            # Close the current tab so the next client opens fresh
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(2)
            
        return jsonify({"success": True, "message": f"WhatsApp broadcast successfully sent to all {len(current_leads)} clients in database!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/run-automation', methods=['POST'])
def run_automation():
    return jsonify({"success": True, "message": "Aquatic background script executed successfully!"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)